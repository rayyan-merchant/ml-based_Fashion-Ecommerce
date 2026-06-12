"""
Sentiment Models Loader - Using only joblib/pkl models (no transformers)
"""
import joblib
import os
import numpy as np

# Get the base path for models
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MODELS_DIR = os.path.join(BASE_DIR, "models", "sentiment")
DATA_ML_DIR = os.path.join(os.path.dirname(BASE_DIR), "data", "ml")
ML_REVIEWS_DIR = os.path.join(os.path.dirname(os.path.dirname(BASE_DIR)), "ml", "reviews", "models", "sentiment")


def find_vectorizer():
    """Find the TF-IDF vectorizer in various possible locations"""
    possible_paths = [
        os.path.join(MODELS_DIR, "reviews_tfidf_vectorizer.pkl"),
        os.path.join(MODELS_DIR, "tfidf_vectorizer.pkl"),
        os.path.join(DATA_ML_DIR, "reviews_tfidf_vectorizer.pkl"),
        os.path.join(DATA_ML_DIR, "tfidf_vectorizer.pkl"),
        os.path.join(ML_REVIEWS_DIR, "reviews_tfidf_vectorizer.pkl"),
        os.path.join(ML_REVIEWS_DIR, "tfidf_vectorizer.pkl"),
        "models/sentiment/reviews_tfidf_vectorizer.pkl",
        "data/ml/reviews_tfidf_vectorizer.pkl",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return path
    return None


class SentimentModels:
    """
    Sentiment analysis using TF-IDF based models (joblib).
    Does NOT require transformer models.
    """
    
    def __init__(self):
        self.models_loaded = False
        self.lr = None
        self.svm = None
        self.nb = None
        self.vectorizer = None
        
        try:
            # Find and load TF-IDF models
            lr_path = os.path.join(MODELS_DIR, "lr_tfidf.joblib")
            svm_path = os.path.join(MODELS_DIR, "svm_tfidf.joblib")
            nb_path = os.path.join(MODELS_DIR, "nb_tfidf.joblib")
            
            if os.path.exists(lr_path):
                self.lr = joblib.load(lr_path)
            if os.path.exists(svm_path):
                self.svm = joblib.load(svm_path)
            if os.path.exists(nb_path):
                self.nb = joblib.load(nb_path)
            
            # Find and load vectorizer
            vectorizer_path = find_vectorizer()
            if vectorizer_path:
                self.vectorizer = joblib.load(vectorizer_path)
                print(f"[INFO] Loaded TF-IDF vectorizer from: {vectorizer_path}")
            else:
                print("[WARNING] TF-IDF vectorizer not found. Sentiment predictions may not work.")
            
            self.models_loaded = self.lr is not None and self.vectorizer is not None
            
            if self.models_loaded:
                print("[INFO] Sentiment models loaded successfully (TF-IDF based)")
            else:
                print("[WARNING] Some sentiment models could not be loaded")
                
        except Exception as e:
            print(f"[ERROR] Error loading sentiment models: {e}")
            self.models_loaded = False
    
    def predict(self, text: str, model: str = "lr") -> dict:
        """
        Predict sentiment for given text.
        
        Args:
            text: Input text to analyze
            model: Which model to use ('lr', 'svm', 'nb', or 'ensemble')
        
        Returns:
            Dictionary with label and confidence scores
        """
        if not self.models_loaded or not self.vectorizer:
            return {
                "label": "unknown",
                "confidence": 0.0,
                "error": "Models not loaded"
            }
        
        try:
            # Vectorize the text
            vec = self.vectorizer.transform([text])
            
            # Map sentiment values
            label_map = {0: "negative", 1: "neutral", 2: "positive"}
            # Some models might use different mappings
            alt_label_map = {-1: "negative", 0: "neutral", 1: "positive"}
            
            if model == "ensemble":
                # Use majority voting from all models
                predictions = []
                if self.lr:
                    predictions.append(self.lr.predict(vec)[0])
                if self.svm:
                    predictions.append(self.svm.predict(vec)[0])
                if self.nb:
                    predictions.append(self.nb.predict(vec)[0])
                
                if predictions:
                    # Majority vote
                    from collections import Counter
                    pred = Counter(predictions).most_common(1)[0][0]
                else:
                    pred = 1  # neutral fallback
            else:
                # Use specific model
                model_obj = getattr(self, model, self.lr)
                if model_obj is None:
                    model_obj = self.lr
                pred = model_obj.predict(vec)[0]
            
            # Get label
            if pred in label_map:
                label = label_map[pred]
            elif pred in alt_label_map:
                label = alt_label_map[pred]
            else:
                label = str(pred)
            
            # Try to get probabilities if available
            confidence = 0.8  # default confidence
            model_obj = getattr(self, model if model != "ensemble" else "lr", self.lr)
            if model_obj and hasattr(model_obj, 'predict_proba'):
                try:
                    probs = model_obj.predict_proba(vec)[0]
                    confidence = float(max(probs))
                except:
                    pass
            
            return {
                "label": label,
                "confidence": confidence,
                "model_used": model
            }
            
        except Exception as e:
            return {
                "label": "error",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def predict_all(self, text: str) -> dict:
        """Get predictions from all models"""
        if not self.models_loaded:
            return {"error": "Models not loaded"}
        
        results = {}
        for model_name in ["lr", "svm", "nb"]:
            results[model_name] = self.predict(text, model_name)
        
        results["ensemble"] = self.predict(text, "ensemble")
        return results
    
    def get_sentiment_summary(self, texts: list) -> dict:
        """
        Get sentiment distribution for a list of texts.
        
        Args:
            texts: List of text strings
        
        Returns:
            Dictionary with counts and percentages
        """
        if not texts:
            return {"positive": 0, "neutral": 0, "negative": 0, "total": 0}
        
        sentiments = {"positive": 0, "neutral": 0, "negative": 0}
        
        for text in texts:
            result = self.predict(text, "ensemble")
            label = result.get("label", "neutral")
            if label in sentiments:
                sentiments[label] += 1
        
        total = len(texts)
        return {
            "positive": sentiments["positive"],
            "neutral": sentiments["neutral"],
            "negative": sentiments["negative"],
            "total": total,
            "positive_pct": round(sentiments["positive"] / total * 100, 1) if total else 0,
            "neutral_pct": round(sentiments["neutral"] / total * 100, 1) if total else 0,
            "negative_pct": round(sentiments["negative"] / total * 100, 1) if total else 0,
        }


# Lazy loading - only instantiate when needed
_sentiment_models = None

def get_sentiment_models() -> SentimentModels:
    """Get or create the sentiment models instance"""
    global _sentiment_models
    if _sentiment_models is None:
        _sentiment_models = SentimentModels()
    return _sentiment_models

# For backward compatibility
sentiment_models = None
try:
    sentiment_models = SentimentModels()
except Exception as e:
    print(f"[ERROR] Could not initialize sentiment models: {e}")
