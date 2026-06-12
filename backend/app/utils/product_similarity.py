import numpy as np
try:
    import faiss
except ImportError:
    print("FAISS not available. Product similarity disabled.")
    faiss = None
import pandas as pd

import os

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMBEDDINGS_DIR = os.path.join(BASE_DIR, "models", "embeddings")

class ProductSimilarity:
    def __init__(self):
        self.embeddings = None
        self.index = None
        self.product_map = None
        self.idx_to_pid = {}
        self.pid_to_idx = {}
        
        try:
            # Load product embeddings
            emb_path = os.path.join(EMBEDDINGS_DIR, "product_embeddings.npy")
            if os.path.exists(emb_path):
                self.embeddings = np.load(emb_path)
    
            # Load FAISS index
            index_path = os.path.join(EMBEDDINGS_DIR, "faiss_product_index.index")
            if faiss and os.path.exists(index_path):
                self.index = faiss.read_index(index_path)
    
            # Load product ID mapping
            map_path = os.path.join(EMBEDDINGS_DIR, "product_ids.parquet")
            if os.path.exists(map_path):
                self.product_map = pd.read_parquet(map_path)
    
                # Convert to dicts for speed
                self.idx_to_pid = dict(zip(self.product_map.index, self.product_map['article_id']))
                self.pid_to_idx = dict(zip(self.product_map['article_id'], self.product_map.index))
                
            print(f"Product similarity loaded: {len(self.idx_to_pid)} items")
        except Exception as e:
            print(f"Error loading product similarity models: {e}")

    def get_similar_by_id(self, product_id, k=10):
        if self.index is None or self.embeddings is None:
            return None

        if product_id not in self.pid_to_idx:
            return None

        row_idx = self.pid_to_idx[product_id]

        query_vec = self.embeddings[row_idx].astype("float32").reshape(1, -1)
        distances, indices = self.index.search(query_vec, k + 1)

        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx == row_idx:
                continue
            results.append({
                "product_id": self.idx_to_pid[idx],
                "similarity": float(1 - dist)
            })

        return results[:k]

product_sim = ProductSimilarity()
