# Phase 4 — Sentiment Classification: Baselines (TF-IDF) + DistilBERT
# Jupyter notebook cells. Copy-paste into a notebook.

# %% [markdown]
# # Sentiment Classification
# This notebook trains:
# 1. Classical baselines: TF-IDF + Logistic Regression, SVM, Naive Bayes
# 2. Transformer: DistilBERT fine-tuning (HuggingFace Trainer)
#
# Inputs (from Phase 1/3):
# - data/ml/train.parquet
# - data/ml/val.parquet
# - data/ml/test.parquet
# - data/ml/reviews_tfidf_vectorizer_full.pkl (optional) / or recompute
# - data/ml/reviews_tfidf_full.npz (optional)

# %% [markdown]
# ## 0) Install / imports

# %%
# Run these once in the environment
# !pip install -q scikit-learn transformers datasets evaluate sentence-transformers torch tqdm joblib

# %%
import os
import pickle
import json
import numpy as np
import pandas as pd
from pathlib import Path
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.naive_bayes import MultinomialNB
from sklearn.svm import LinearSVC
from sklearn.pipeline import Pipeline
from sklearn.metrics import accuracy_score, f1_score, precision_score, recall_score, confusion_matrix, classification_report
from sklearn.model_selection import GridSearchCV
from sklearn.utils.class_weight import compute_class_weight
import joblib

# Transformers / HF
import torch
from transformers import AutoTokenizer, AutoModelForSequenceClassification, TrainingArguments, Trainer
from transformers import DataCollatorWithPadding
from datasets import Dataset
import evaluate
from pathlib import Path

project_root = Path.cwd().parent.parent
# Output directory
ML_DIR = project_root / "data/ml/reviews/reviews_preprocessed"
ML_DIR.mkdir(parents=True, exist_ok=True)


# set paths
out_dir = Path()
ARTIFACTS_DIR = out_dir / 'models' / 'sentiment'
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)

# Repro
RANDOM_STATE = 42

# %% [markdown]
# ## 1) Load data

# %%
train = pd.read_parquet(ML_DIR / 'train.parquet')
val = pd.read_parquet(ML_DIR / 'val.parquet')
test = pd.read_parquet(ML_DIR / 'test.parquet')
print(len(train), len(val), len(test))

# Ensure label column exists. Use 'sentiment_label' (negative/neutral/positive) or derive from rating
label_col = 'sentiment_label'
if label_col not in train.columns:
    # derive from rating
    def label_from_rating(r):
        if r <= 2:
            return 'negative'
        if r == 3:
            return 'neutral'
        return 'positive'
    for df in (train, val, test):
        df['sentiment_label'] = df['rating'].apply(label_from_rating)

# Compact label encoding
labels = sorted(train['sentiment_label'].unique())
label2id = {l:i for i,l in enumerate(labels)}
id2label = {i:l for l,i in label2id.items()}
print('labels', labels)

for df in (train, val, test):
    df['label_id'] = df['sentiment_label'].map(label2id)

# Text column
TEXT_COL = 'text_for_training' if 'text_for_training' in train.columns else 'clean_text'

# Quick class balance
print(train['sentiment_label'].value_counts())

# %% [markdown]
# ## 2) Classical baselines: TF-IDF + LR / SVM / NB
# We'll use TF-IDF (max_features=20k) and train three models.

# %%
TFIDF_FEATURES = 20000
vectorizer_path = ARTIFACTS_DIR / 'tfidf_vectorizer.pkl'
tfidf_matrix_path = ARTIFACTS_DIR / 'tfidf_train.npz'

# If a saved vectorizer exists (from Phase 3), load it. Otherwise fit.
if (ML_DIR / 'reviews_tfidf_vectorizer_full.pkl').exists():
    print('Loading precomputed TF-IDF vectorizer from Phase 3')
    with open(ML_DIR / 'reviews_tfidf_vectorizer_full.pkl','rb') as f:
        vectorizer = pickle.load(f)
else:
    print('Fitting TF-IDF on training data...')
    vectorizer = TfidfVectorizer(stop_words='english', max_features=TFIDF_FEATURES)
    vectorizer.fit(train[TEXT_COL].fillna(''))
    with open(vectorizer_path,'wb') as f:
        pickle.dump(vectorizer, f)

X_train = vectorizer.transform(train[TEXT_COL].fillna(''))
X_val = vectorizer.transform(val[TEXT_COL].fillna(''))
X_test = vectorizer.transform(test[TEXT_COL].fillna(''))

y_train = train['label_id'].values
y_val = val['label_id'].values
y_test = test['label_id'].values

print('Shapes:', X_train.shape, X_val.shape, X_test.shape)

# compute class weights for handling imbalance in classical models
class_weights = compute_class_weight('balanced', classes=np.unique(y_train), y=y_train)
class_weight_dict = {i:w for i,w in enumerate(class_weights)}
print('class weights:', class_weight_dict)

# Helper: evaluation

def eval_and_print(model, X, y_true, name='model'):
    y_pred = model.predict(X)
    acc = accuracy_score(y_true, y_pred)
    f1 = f1_score(y_true, y_pred, average='macro')
    print(f"{name} — Acc: {acc:.4f}  F1-macro: {f1:.4f}")
    print(classification_report(y_true, y_pred, target_names=labels))
    return {'acc':acc, 'f1_macro':f1}

# %% [markdown]
# ### 2.1 Logistic Regression

# %%
lr = LogisticRegression(max_iter=200, class_weight='balanced', random_state=RANDOM_STATE)
lr.fit(X_train, y_train)
joblib.dump(lr, ARTIFACTS_DIR / 'lr_tfidf.joblib')
eval_and_print(lr, X_val, y_val, 'LogReg(TFIDF)')

# %% [markdown]
# ### 2.2 Linear SVM

# %%
svm = LinearSVC(class_weight='balanced', max_iter=10000, random_state=RANDOM_STATE)
svm.fit(X_train, y_train)
joblib.dump(svm, ARTIFACTS_DIR / 'svm_tfidf.joblib')
eval_and_print(svm, X_val, y_val, 'LinearSVC(TFIDF)')

# %% [markdown]
# ### 2.3 Multinomial Naive Bayes

# %%
nb = MultinomialNB()
nb.fit(X_train, y_train)
joblib.dump(nb, ARTIFACTS_DIR / 'nb_tfidf.joblib')
eval_and_print(nb, X_val, y_val, 'MultinomialNB(TFIDF)')

# %% [markdown]
# Save evaluation summary
# %%
results = {}
for name,model in [('lr',lr),('svm',svm),('nb',nb)]:
    results[name] = eval_and_print(model, X_test, y_test, name)

with open(ARTIFACTS_DIR / 'baseline_results.json','w') as f:
    json.dump(results, f)

# %% [markdown]
# ## 3) DistilBERT Fine-tuning (HuggingFace Trainer)
# We'll fine-tune a DistilBERT sequence classification model on the train/val splits.

# %%
MODEL_NAME = 'distilbert-base-uncased'
NUM_LABELS = len(labels)
BATCH_SIZE = 32
EPOCHS = 3
OUTPUT_DIR = str(ARTIFACTS_DIR / 'distilbert')

# tokenizer & model
tokenizer = AutoTokenizer.from_pretrained(MODEL_NAME)

# Prepare HuggingFace datasets
train_ds = Dataset.from_pandas(train[[TEXT_COL,'label_id']].rename(columns={TEXT_COL:'text','label_id':'label'}))
val_ds = Dataset.from_pandas(val[[TEXT_COL,'label_id']].rename(columns={TEXT_COL:'text','label_id':'label'}))
test_ds = Dataset.from_pandas(test[[TEXT_COL,'label_id']].rename(columns={TEXT_COL:'text','label_id':'label'}))

# tokenize
def tokenize_fn(batch):
    return tokenizer(batch['text'], truncation=True, padding='max_length', max_length=128)

train_ds = train_ds.map(tokenize_fn, batched=True)
val_ds = val_ds.map(tokenize_fn, batched=True)
test_ds = test_ds.map(tokenize_fn, batched=True)

train_ds.set_format(type='torch', columns=['input_ids','attention_mask','label'])
val_ds.set_format(type='torch', columns=['input_ids','attention_mask','label'])
test_ds.set_format(type='torch', columns=['input_ids','attention_mask','label'])

# Simple standard model (class weights are handled automatically by Trainer)
model = AutoModelForSequenceClassification.from_pretrained(
    MODEL_NAME, 
    num_labels=NUM_LABELS,
    label2id=label2id,
    id2label=id2label
)

data_collator = DataCollatorWithPadding(tokenizer=tokenizer)

# Modern metrics (no deprecated load_metric)
accuracy = evaluate.load("accuracy")
f1 = evaluate.load("f1")

def compute_metrics(eval_pred):
    logits, labels = eval_pred
    preds = np.argmax(logits, axis=1)
    return {
        'accuracy': accuracy.compute(predictions=preds, references=labels)['accuracy'],
        'f1_macro': f1.compute(predictions=preds, references=labels, average='macro')['f1']
    }

training_args = TrainingArguments(
    output_dir=OUTPUT_DIR,
    eval_strategy='epoch',
    save_strategy='epoch',
    per_device_train_batch_size=BATCH_SIZE,
    per_device_eval_batch_size=BATCH_SIZE,
    num_train_epochs=EPOCHS,
    weight_decay=0.01,
    load_best_model_at_end=True,
    metric_for_best_model='f1_macro',
    greater_is_better=True,
    logging_steps=100,
    fp16=torch.cuda.is_available(),
    seed=RANDOM_STATE,
)

trainer = Trainer(
    model=model,
    args=training_args,
    train_dataset=train_ds,
    eval_dataset=val_ds,
    tokenizer=tokenizer,
    data_collator=data_collator,
    compute_metrics=compute_metrics,
)

trainer.train()
trainer.save_model(OUTPUT_DIR)
tokenizer.save_pretrained(OUTPUT_DIR)

metrics = trainer.evaluate(test_ds)
print("Test set results:", metrics)

with open(ARTIFACTS_DIR / 'label_mapping.json', 'w') as f:
    json.dump({'label2id': label2id, 'id2label': id2label}, f)
# %% [markdown]
# ## Notes & next steps
# - You now have baseline classical models and a fine-tuned DistilBERT model saved under `data/ml/models/sentiment/`.
# - For production, consider: model quantization, TorchScript/ONNX export, and wrapping in a FastAPI endpoint.
# - Evaluate confusion matrices and per-class metrics to find biases.

# %%
print('Done')
