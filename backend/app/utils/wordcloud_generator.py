import pandas as pd
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import os
import io
import base64

class WordCloudGenerator:
    def __init__(self):
        try:
            # Try multiple locations or fail gracefully
            # Determine paths relative to backend/app/utils
            current_dir = os.path.dirname(os.path.abspath(__file__))
            # Go up to 'layr' root: utils -> app -> backend -> layr
            project_root = os.path.abspath(os.path.join(current_dir, "../../../"))
            
            paths = [
                os.path.join(project_root, "data/ml/reviews/reviews_preprocessed/reviews_preprocessed.parquet"),
                "../data/ml/reviews/reviews_preprocessed/reviews_preprocessed.parquet", 
                "data/ml/reviews/reviews_preprocessed/reviews_preprocessed.parquet"
            ]
            self.df = None
            for p in paths:
                if os.path.exists(p):
                    self.df = pd.read_parquet(p)
                    print(f"WordCloud loaded from: {p}")
                    break
            
            if self.df is None:
                print("WordCloud: reviews_preprocessed.parquet not found. Wordcloud generation disabled.")
            elif "clean_text" not in self.df.columns:
                print("WordCloud: clean_text column missing. Wordcloud generation disabled.")
                self.df = None

        except Exception as e:
            print(f"WordCloud initialization failed: {e}")
            self.df = None

        self.out_dir = "app/static/wordclouds"
        os.makedirs(self.out_dir, exist_ok=True)

    def generate_for_product(self, product_id):
        if self.df is None:
            return None
            
        subset = self.df[self.df["article_id"] == product_id]

        if subset.empty:
            return None

        # Combine all clean text
        text = " ".join(subset["clean_text"].tolist())

        # Create the wordcloud
        wc = WordCloud(
            width=1000,
            height=600,
            background_color="white",
            max_words=200
        ).generate(text)

        # Save to file
        filepath = os.path.join(self.out_dir, f"{product_id}.png")
        wc.to_file(filepath)

        return filepath

    def generate_base64(self, product_id):
        if self.df is None:
            return None

        subset = self.df[self.df["article_id"] == product_id]

        if subset.empty:
            return None

        text = " ".join(subset["clean_text"].tolist())

        wc = WordCloud(
            width=1000,
            height=600,
            background_color="white",
            max_words=200
        ).generate(text)

        img_buffer = io.BytesIO()
        wc.to_image().save(img_buffer, format="PNG")
        img_buffer.seek(0)

        img_base64 = base64.b64encode(img_buffer.read()).decode("utf-8")
        return img_base64


wordcloud_gen = WordCloudGenerator()
