import numpy as np
try:
    import faiss
except ImportError:
    print("FAISS not available. Similarity search disabled.")
    faiss = None
import pandas as pd

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "models", "embeddings")

class ReviewSimilarity:
    def __init__(self):
        self.embeddings = None
        self.index = None
        self.review_map = None
        self.id_to_idx = {}
        self.idx_to_id = {}
        
        try:
            # Load embeddings
            emb_path = os.path.join(EMBEDDINGS_DIR, "review_embeddings.npy")
            if os.path.exists(emb_path):
                self.embeddings = np.load(emb_path)
    
            # Load FAISS index
            index_path = os.path.join(EMBEDDINGS_DIR, "faiss_review_index.index")
            if faiss and os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
    
            # Load mapping review_id -> row index
            map_path = os.path.join(EMBEDDINGS_DIR, "review_ids.parquet")
            if os.path.exists(map_path):
                self.review_map = pd.read_parquet(map_path)
                # review_map columns: ["review_id", "idx"]
                
                # To speed lookup
                self.id_to_idx = dict(zip(self.review_map.review_id, self.review_map.idx))
                self.idx_to_id = dict(zip(self.review_map.idx, self.review_map.review_id))
                
            print(f"Review similarity loaded: {len(self.id_to_idx)} items")
        except Exception as e:
            print(f"Error loading review similarity models: {e}")

    def get_similar_by_id(self, review_id, k=10):
        if self.index is None or self.embeddings is None:
            return None
            
        if review_id not in self.id_to_idx:
            return None

        row_idx = self.id_to_idx[review_id]

        query_vec = self.embeddings[row_idx].astype("float32").reshape(1, -1)
        distances, indices = self.index.search(query_vec, k + 1)  # includes itself

        # Filter out the review itself
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == row_idx:
                continue
            results.append({
                "similar_review_id": self.idx_to_id[idx],
                "score": float(1 - dist)   # convert FAISS distance to similarity
            })

        return results[:k]

    def get_similar_by_text(self, text, model, k=10):
        # Encode new text
        emb = model.encode([text], convert_to_numpy=True).astype("float32")

        distances, indices = self.index.search(emb, k)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            results.append({
                "review_id": self.idx_to_id[idx],
                "score": float(1 - dist)
            })
        return results

review_sim = ReviewSimilarity()
