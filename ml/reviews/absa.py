# %% [markdown]
# # Phase 4 — ABSA: Multi-Aspect Sentiment Classification (DistilBERT)
# Predicts sentiment for 6 aspects: fit, quality, delivery, price, material, comfort
# Input: data/ml/reviews/reviews_features_full.parquet
# Output: data/ml/models/absa/distilbert_absa + product_aspect_summaries.parquet

# %%
# Install once (uncomment if needed)
# !pip install transformers datasets torch accelerate scikit-learn pandas numpy

# %%
import os
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.metrics import classification_report
from sklearn.model_selection import train_test_split
import torch
import torch.nn as nn
from transformers import AutoTokenizer, DistilBertModel, Trainer, TrainingArguments
from datasets import Dataset

# ==============================
# CORRECT PATHS FOR YOUR PC
# ==============================
PROJECT_ROOT = Path("C:/Users/ND.COM/Desktop/ML DB Project")
DATA_DIR = PROJECT_ROOT / "data" / "ml" / "reviews" / "reviews_preprocessed"
MODEL_DIR = PROJECT_ROOT / "data" / "ml" / "models" / "absa"

# Create folders
MODEL_DIR.mkdir(parents=True, exist_ok=True)

print(f"Loading data from: {DATA_DIR}")
print(f"Model will be saved to: {MODEL_DIR}")

# ==============================
# 1) Load data
# ==============================
df = pd.read_parquet(DATA_DIR / "reviews_features_full.parquet")
print(f"Loaded {len(df):,} reviews")

ASPECT_LIST = ['fit', 'quality', 'delivery', 'price', 'material', 'comfort']
aspect_norm_cols = [f'aspect_{a}_norm' for a in ASPECT_LIST]

# Fill missing aspect columns
for col in aspect_norm_cols:
    if col not in df.columns:
        df[col] = np.nan

# Convert [0-1] → label: 0=neg, 1=neu, 2=pos
def score_to_label(x):
    if pd.isna(x): return 1
    if x <= 0.4: return 0
    if x < 0.6: return 1
    return 2

for a, col in zip(ASPECT_LIST, aspect_norm_cols):
    df[f'{a}_label'] = df[col].apply(score_to_label)

df = df[df['text_for_training'].notna()].copy()

# Split
train_df, temp_df = train_test_split(df, test_size=0.2, random_state=42, stratify=df['synthetic_sentiment_label'])
val_df, test_df = train_test_split(temp_df, test_size=0.5, random_state=42)
print(f"Train: {len(train_df)} | Val: {len(val_df)} | Test: {len(test_df)}")

# To HF Dataset
def df_to_dataset(df_part):
    records = []
    for _, row in df_part.iterrows():
        rec = {'text': str(row['text_for_training'])}
        for a in ASPECT_LIST:
            rec[f'label_{a}'] = int(row[f'{a}_label'])
        records.append(rec)
    return Dataset.from_pandas(pd.DataFrame(records))

train_ds = df_to_dataset(train_df)
val_ds = df_to_dataset(val_df)
test_ds = df_to_dataset(test_df)

# ==============================
# 2) Model
# ==============================
MODEL_NAME = "distilbert-base-uncased"
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

class DistilBERTMultiAspect(nn.Module):
    def __init__(self, model_name=MODEL_NAME, aspects=ASPECT_LIST, num_classes=3):
        super().__init__()
        self.aspects = aspects
        self.encoder = DistilBertModel.from_pretrained(model_name)
        hidden = self.encoder.config.hidden_size
        self.dropout = nn.Dropout(0.3)
        self.heads = nn.ModuleDict({a: nn.Linear(hidden, num_classes) for a in aspects})

    def forward(self, input_ids=None, attention_mask=None, labels=None):
        out = self.encoder(input_ids=input_ids, attention_mask=attention_mask)
        pooled = self.dropout(out.last_hidden_state[:, 0])
        logits = {a: head(pooled) for a, head in self.heads.items()}

        loss = None
        if labels is not None:
            loss_fct = nn.CrossEntropyLoss()
            loss = sum(loss_fct(logits[a], labels[a]) for a in self.aspects) / len(self.aspects)

        return {'loss': loss, 'logits': logits}

model = DistilBERTMultiAspect()
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
model.to(device)
print(f"Model on {device}")

# ==============================
# 3) Tokenize
# ==============================
def tokenize(batch):
    return tokenizer(batch['text'], truncation=True, padding=True, max_length=128)

train_ds = train_ds.map(tokenize, batched=True)
val_ds = val_ds.map(tokenize, batched=True)
test_ds = test_ds.map(tokenize, batched=True)

train_ds.set_format('torch', columns=['input_ids', 'attention_mask'] + [f'label_{a}' for a in ASPECT_LIST])
val_ds.set_format('torch', columns=['input_ids', 'attention_mask'] + [f'label_{a}' for a in ASPECT_LIST])
test_ds.set_format('torch', columns=['input_ids', 'attention_mask'] + [f'label_{a}' for a in ASPECT_LIST])

# ==============================
# 4) Custom Trainer
# ==============================
class ABSATrainer(Trainer):
    def compute_loss(self, model, inputs, return_outputs=False):
        labels = {a: inputs.pop(f'label_{a}').to(model.device) for a in ASPECT_LIST}
        outputs = model(**inputs, labels=labels)
        loss = outputs['loss']
        return (loss, outputs) if return_outputs else loss

# ==============================
# 5) Train
# ==============================
training_args = TrainingArguments(
    output_dir=str(MODEL_DIR / "checkpoints"),
    eval_strategy="epoch",
    save_strategy="epoch",
    per_device_train_batch_size=16,
    per_device_eval_batch_size=32,
    num_train_epochs=3,
    learning_rate=3e-5,
    weight_decay=0.01,
    load_best_model_at_end=True,
    fp16=torch.cuda.is_available(),
    logging_steps=100,
    report_to="none",
)

trainer = ABSATrainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
)

print("Starting ABSA training...")
trainer.train()

# Save final model
final_path = MODEL_DIR / "distilbert_absa"
final_path.mkdir(parents=True, exist_ok=True)
trainer.save_model(str(final_path))
tokenizer.save_pretrained(str(final_path))
print(f"Model saved to: {final_path}")

# ==============================
# 6) Inference + Product Aggregation
# ==============================
print("Running inference on all reviews...")
model.eval()
all_preds = []

with torch.no_grad():
    for i in range(0, len(df), 256):
        texts = df['text_for_training'].fillna('').iloc[i:i+256].tolist()
        inputs = tokenizer(texts, truncation=True, padding=True, max_length=128, return_tensors='pt').to(device)
        outputs = model(**inputs)
        batch_preds = torch.stack([torch.argmax(outputs['logits'][a], dim=1) for a in ASPECT_LIST], dim=1)
        all_preds.append(batch_preds.cpu().numpy())

all_preds = np.vstack(all_preds)
label_to_star = {0: 1.0, 1: 3.0, 2: 5.0}
stars = np.vectorize(label_to_star.get)(all_preds)

prod_agg = pd.DataFrame({'article_id': df['article_id'].values})
for i, a in enumerate(ASPECT_LIST):
    prod_agg[f'{a}_stars'] = stars[:, i]

agg = prod_agg.groupby('article_id').mean().round(1).reset_index()

def meaning(x):
    if x >= 4.5: return "excellent"
    if x >= 3.5: return "good"
    if x >= 2.5: return "average"
    if x >= 1.5: return "poor"
    return "very poor"

for a in ASPECT_LIST:
    agg[f'{a}_meaning'] = agg[f'{a}_stars'].apply(meaning)

output_file = MODEL_DIR / "product_aspect_summaries.parquet"
agg.to_parquet(output_file, index=False)
print(f"\nProduct aspect summaries saved:\n{output_file}")

# Sample
print("\nSample product aspect ratings:")
sample = agg.sample(1).iloc[0]
for a in ASPECT_LIST:
    print(f"  • {a.title():9}: {sample[f'{a}_stars']} stars → {sample[f'{a}_meaning']}")

print("\nABSA PHASE COMPLETE! You're ready for Phase 5.")