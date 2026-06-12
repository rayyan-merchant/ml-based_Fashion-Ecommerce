import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import joblib
import os

class ComplaintExtractor:
    def __init__(self):
        self.df = None
        self.vectorizer = None
        self.article_map = None
        
        try:
            # Determine base paths relative to this file
            # file is in: backend/app/utils/complaint_extractor.py
            current_dir = os.path.dirname(os.path.abspath(__file__))
            backend_dir = os.path.dirname(os.path.dirname(current_dir)) # backend
            project_root = os.path.dirname(backend_dir) # layr
            
            # Construct absolute paths to data
            data_ml_dir = os.path.join(project_root, "data", "ml")
            
            reviews_path = os.path.join(data_ml_dir, "reviews", "reviews_preprocessed", "reviews_preprocessed.parquet")
            
            if os.path.exists(reviews_path):
                self.df = pd.read_parquet(reviews_path)
            
            # Load TF-IDF vectorizer - try imported sentiment loader path first
            
            from app.utils.sentiment_loader import find_vectorizer
            vec_path = find_vectorizer()
            
            if vec_path:
                self.vectorizer = joblib.load(vec_path)
            
            # Only proceed if we have the reviews data
            if self.df is not None and self.vectorizer is not None:
                # Ensure all needed columns exist
                # reviews_preprocessed.parquet has 'vader_label' or 'synthetic_sentiment_label'
                if "sentiment_label" not in self.df.columns and "vader_label" in self.df.columns:
                    self.df = self.df.rename(columns={"vader_label": "sentiment_label"})
                
                required = {"clean_text", "sentiment_label", "article_id", "category_id"}
                if not required.issubset(self.df.columns):
                    print("[WARNING] ComplaintExtractor: Missing required columns in dataset")
                    self.df = None
                else:
                    print("[INFO] ComplaintExtractor loaded successfully")
            else:
                print("[WARNING] ComplaintExtractor: Missing data files. Feature disabled.")
                self.df = None
                
        except Exception as e:
            print(f"[ERROR] ComplaintExtractor initialization failed: {e}")
            self.df = None

    def get_top_complaints(self, category_id, top_n=15):
        if self.df is None:
            return None
            
        df_cat = self.df[self.df["category_id"] == category_id]

        if df_cat.empty:
            return None

        # Filter negative + neutral reviews for complaints
        df_neg = df_cat[df_cat["sentiment_label"].isin(["negative", "neutral"])]

        if df_neg.empty:
            return []

        texts = df_neg["clean_text"].tolist()

        # Compute TF-IDF matrix
        tfidf = self.vectorizer.transform(texts)
        scores = np.asarray(tfidf.sum(axis=0)).ravel()

        feature_names = self.vectorizer.get_feature_names_out()
        top_idx = scores.argsort()[::-1][:top_n]

        complaints = [
            {"keyword": feature_names[i], "score": float(scores[i])}
            for i in top_idx
        ]

        # Get example reviews for context
        example_reviews = df_neg[["review_text", "sentiment_label"]].head(10).to_dict(orient="records")

        return complaints, example_reviews


complaint_extractor = ComplaintExtractor()
