from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.openapi.utils import get_openapi
from fastapi.staticfiles import StaticFiles
import os

from app.db.database import Base, engine
from app.routers import (
    admins,
    articles,
    categories,
    customers,
    events,
    orders,
    order_items,
    recommendations,
    hybrid_recommendations,
    reviews,
    sections,
    transactions,
    wishlist,
    cart,
    segmentation,
    timeseries,
    ml_dashboard
)
from app.customer_auth import router as customer_auth_router
from app.services.recommendation_service import RecommendationService
from app.services.hybrid_recommendation_service import HybridRecommendationService
app = FastAPI(
    title="LAYR API",
    description="FastAPI backend for e-commerce project",
    version="1.0.0"
)

# Reviews - NLP/Sentiment Routers
# Now using robust loading (joblib/pkl) or failing gracefully
from app.routers import sentiment
from app.routers import review_similarity
from app.routers import product_similarity
from app.routers import product_wordcloud
from app.routers import category_complaints


# ---- Initialize Recommendation Services ----
recommendation_service = None
hybrid_service = None
BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CF_MODEL_DIR = os.path.join(os.path.dirname(__file__), "models", "recommendations")
CB_MODEL_DIR = os.path.join(BACKEND_DIR, "data", "content_based_model")


@app.on_event("startup")
async def startup_event():
    """Load recommendation models on app startup"""
    global recommendation_service, hybrid_service
    try:
        import logging
        logger = logging.getLogger(__name__)
        logger.info("Loading recommendation models...")
        
        # Load CF-only service
        recommendation_service = RecommendationService(model_dir=CF_MODEL_DIR)
        recommendations.set_recommendation_service(recommendation_service)
        
        # Load Hybrid service (CF + CB)
        hybrid_service = HybridRecommendationService(
            cf_model_dir=CF_MODEL_DIR,
            cb_model_dir=CB_MODEL_DIR
        )
        hybrid_recommendations.set_hybrid_recommendation_service(hybrid_service)
        
        logger.info("Recommendation services loaded successfully")
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Could not load recommendation services: {e}")
        logger.warning("Recommendation endpoints will return 503 (Service Unavailable)")


IMAGES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "filtered_images"))
os.makedirs(IMAGES_DIR, exist_ok=True)

app.mount("/images", StaticFiles(directory=IMAGES_DIR), name="images")

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---- Register Routers ---
app.include_router(admins.router)  # Router already has /admins prefix defined
app.include_router(customer_auth_router)  # Customer auth routes (already has /customers/auth prefix)
app.include_router(articles.router, prefix="/articles", tags=["Articles"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(customers.router, prefix="/customers", tags=["Customers"])
app.include_router(events.router, prefix="/events", tags=["Events"])
app.include_router(orders.router, prefix="/orders", tags=["Orders"])
app.include_router(order_items.router, prefix="/order-items", tags=["Order Items"])
app.include_router(recommendations.router, prefix="/recommendations", tags=["Recommendations"])
app.include_router(hybrid_recommendations.router, prefix="/hybrid-recommendations", tags=["Hybrid Recommendations"])
app.include_router(reviews.router, prefix="/reviews", tags=["Reviews"])
app.include_router(transactions.router, prefix="/transactions", tags=["Transactions"])
app.include_router(wishlist.router, prefix="/wishlist", tags=["Wishlist"])
app.include_router(cart.router, prefix="/cart", tags=["Cart"])
app.include_router(sections.router, prefix="/sections", tags=["Sections"])
app.include_router(segmentation.router, prefix="/segmentation",tags=["Segmentation"])
app.include_router(timeseries.timeseries_router, prefix="/forecasting", tags=["Forecasting"])
app.include_router(ml_dashboard.router, tags=["ML Dashboard"])
# NLP/Sentiment routers
app.include_router(sentiment.router)
app.include_router(review_similarity.router)
app.include_router(product_similarity.router)
app.include_router(product_wordcloud.router)
app.include_router(category_complaints.router)

# ---- Root ----
@app.get("/")
def root():
    return {"message": "Welcome to the LAYR E-Commerce API"}


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema

    openapi_schema = get_openapi(
        title="E-Commerce API",
        version="1.0.0",
        description="E-Commerce Database Project API",
        routes=app.routes,
    )

    # Forcefully wipe ALL existing security schemes
    openapi_schema["components"]["securitySchemes"] = {}

    # Insert ONLY our scheme
    openapi_schema["components"]["securitySchemes"]["BearerAuth"] = {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "Paste your JWT token from /admins/login or /customers/auth/login"
    }

    # Apply BearerAuth globally
    for path, path_item in openapi_schema["paths"].items():
        for method in path_item:
            if method in ["get", "post", "put", "delete", "patch"]:
                if "security" not in path_item[method]:
                    path_item[method]["security"] = [{"BearerAuth": []}]

    app.openapi_schema = openapi_schema
    return app.openapi_schema
