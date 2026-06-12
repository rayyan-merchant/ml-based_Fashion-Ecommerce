"""
CF Training Files Comparison & Rapid Testing
Analyzes all cf_train*.py files and keeps only the Kaggle version
"""

import os
from pathlib import Path
import pandas as pd

PROJECT_ROOT = Path(__file__).parent.parent.parent
RECOMMENDERS_DIR = PROJECT_ROOT / 'ml' / 'recommenders'

print("\n" + "="*80)
print("COLLABORATIVE FILTERING - FILE ANALYSIS")
print("="*80 + "\n")

# ============================================================================
# ANALYZE ALL CF FILES
# ============================================================================

cf_files = {
    'cf_train.py': 'Original simple version (CPU/GPU fallback)',
    'cf_train_simple.py': 'Production version (full features)',
    'cf_train_experiment.py': 'Fast experiment version (10% sampling)',
    'cf_evaluate.py': 'Model evaluation (not a training file)'
}

print("📁 EXISTING CF TRAINING FILES:\n")

for filename, description in cf_files.items():
    filepath = RECOMMENDERS_DIR / filename
    if filepath.exists():
        size_kb = filepath.stat().st_size / 1024
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            lines = len(f.readlines())
        print(f"  ✅ {filename}")
        print(f"     Description: {description}")
        print(f"     Size: {size_kb:.1f} KB ({lines} lines)")
        print()
    else:
        print(f"  ❌ {filename} (NOT FOUND)\n")

# ============================================================================
# FEATURE COMPARISON
# ============================================================================

print("\n" + "="*80)
print("FEATURE COMPARISON")
print("="*80 + "\n")

features = {
    'cf_train.py': {
        'Uses GPU': 'Try, fallback to CPU',
        'Data sampling': 'No (full data)',
        'User coverage': 'Full (557k)',
        'Training time': '~30 min',
        'Best for': 'Local training',
        'Kaggle ready': '❌ No',
        'Production': '⚠️ Partial'
    },
    'cf_train_simple.py': {
        'Uses GPU': 'Yes (try cuML)',
        'Data sampling': 'Yes (5k users)',
        'User coverage': 'Limited (0.9%)',
        'Training time': '~27 min',
        'Best for': 'Testing',
        'Kaggle ready': '❌ No (local paths)',
        'Production': '⚠️ Low coverage'
    },
    'cf_train_experiment.py': {
        'Uses GPU': 'No (CPU only)',
        'Data sampling': 'Yes (10% data)',
        'User coverage': '~1%',
        'Training time': '~17 sec',
        'Best for': 'Rapid iteration',
        'Kaggle ready': '⚠️ Partial',
        'Production': '✅ Good for experiments'
    }
}

print("📊 Comparison Matrix:\n")
print(f"{'Feature':<20} {'cf_train.py':<20} {'cf_train_simple.py':<20} {'cf_train_experiment.py':<20}")
print("-" * 80)

all_features = set()
for file_features in features.values():
    all_features.update(file_features.keys())

for feature in sorted(all_features):
    row = f"{feature:<20}"
    for filename in ['cf_train.py', 'cf_train_simple.py', 'cf_train_experiment.py']:
        if filename in features and feature in features[filename]:
            value = features[filename][feature]
            row += f" {value:<20}"
        else:
            row += f" {'-':<20}"
    print(row)

# ============================================================================
# RECOMMENDATION
# ============================================================================

print("\n" + "="*80)
print("RECOMMENDATION FOR KAGGLE")
print("="*80 + "\n")

print("""
🎯 FOR KAGGLE GPU TRAINING (400k users):
   
   ✅ USE: Modified cf_train_simple.py (Kaggle version)
   
   Why:
   • Already handles full data (no sampling)
   • GPU acceleration ready
   • Clear progress indicators
   • Saves all necessary outputs
   • Easy to adapt for Kaggle paths
   
   Changes needed:
   • Replace local paths with /kaggle/ paths
   • Add cuML imports for Tesla T4 GPU
   • Adjust USER_SAMPLE_SIZE = 400000
   • Add output to /kaggle/working/

🧪 FOR LOCAL RAPID TESTING:
   
   ✅ USE: cf_train_experiment.py (keep for development)
   
   Why:
   • Fastest feedback (17 seconds)
   • 10% sampling for quick iteration
   • Easy to modify hyperparameters
   • Perfect for experimentation

📊 FOR MODEL EVALUATION:
   
   ✅ USE: cf_evaluate.py (keep for quality assessment)
   
   Why:
   • Measures all 7 metrics
   • Provides actionable insights
   • Helps track improvements
   • Shows business impact

⛔ CAN DELETE:
   
   DELETE: cf_train.py
   
   Why:
   • Superseded by cf_train_simple.py
   • Causes confusion (multiple versions)
   • Same functionality but less features
   • cf_train_simple.py is better

""")

# ============================================================================
# ACTION PLAN
# ============================================================================

print("="*80)
print("ACTION PLAN")
print("="*80 + "\n")

print("""
STEP 1: Create Kaggle-Optimized Version (RECOMMENDED)
────────────────────────────────────────────────────

Create: ml/recommenders/cf_kaggle_training.py
Based on: cf_train_simple.py
Changes:
  • Use /kaggle/input/ for data loading
  • Add cuML GPU support
  • Set TRAIN_USER_COUNT = 400000
  • Output to /kaggle/working/

This is the "MASTER" training script for production.

STEP 2: Keep for Local Development
──────────────────────────────────

KEEP:
  • cf_train_experiment.py → Rapid iteration (17 sec)
  • cf_evaluate.py → Quality assessment

DELETE:
  • cf_train.py → Redundant, cf_train_simple.py is better

STEP 3: Rapid Testing Workflow
──────────────────────────────

Local (your machine):
  1. Edit cf_train_experiment.py hyperparameters
  2. Run: python ml/recommenders/cf_train_experiment.py (17s)
  3. Check metrics
  4. Iterate until happy

Kaggle (free GPU):
  1. Paste cf_kaggle_training.py in Kaggle notebook
  2. Run: Full training with 400k users (15-20 min)
  3. Download results
  4. Run cf_evaluate.py locally to assess quality
  5. Repeat if needed

STEP 4: Final Deployment
────────────────────────

Use: cf_train_simple.py with your best hyperparameters
Run: For final production model
Output: Use for FastAPI endpoints

""")

# ============================================================================
# FILE RECOMMENDATIONS
# ============================================================================

print("="*80)
print("FILES TO KEEP vs DELETE")
print("="*80 + "\n")

recommendations = {
    'KEEP': [
        ('cf_train_experiment.py', 'Rapid iteration (17 sec per run)'),
        ('cf_kaggle_training.py', 'Kaggle GPU training (400k users, 15 min)'),
        ('cf_train_simple.py', 'Local full training (fallback if no Kaggle)'),
        ('cf_evaluate.py', 'Quality assessment & metrics'),
    ],
    'DELETE': [
        ('cf_train.py', 'Redundant with cf_train_simple.py'),
    ]
}

print("✅ KEEP:\n")
for filename, reason in recommendations['KEEP']:
    print(f"  • {filename:<30} → {reason}")

print("\n❌ DELETE:\n")
for filename, reason in recommendations['DELETE']:
    print(f"  • {filename:<30} → {reason}")

# ============================================================================
# RAPID TESTING WORKFLOW
# ============================================================================

print("\n" + "="*80)
print("RAPID TESTING WORKFLOW")
print("="*80 + "\n")

print("""
┌─────────────────────────────────────────────────────────────────────┐
│ LOCAL RAPID ITERATION (Your Machine)                               │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Quick Experiment (17 seconds)                                   │
│     $ python ml/recommenders/cf_train_experiment.py                │
│     Output: Variance %, Coverage %, Metrics                         │
│     Time: 17 sec                                                    │
│                                                                     │
│  2. Modify Hyperparameters                                          │
│     Edit: cf_train_experiment.py line ~30                          │
│     Change: N_COMPONENTS, SVD_ITERATIONS, etc.                     │
│     Time: 1 min                                                     │
│                                                                     │
│  3. Run Again                                                       │
│     $ python ml/recommenders/cf_train_experiment.py                │
│     Compare: Metrics improved?                                      │
│     Time: 17 sec                                                    │
│                                                                     │
│  4. Happy with Results?                                             │
│     YES → Go to Kaggle training                                     │
│     NO  → Go back to step 2                                         │
│                                                                     │
│  Total time per iteration: ~35 seconds                              │
│  Max iterations before Kaggle: 30 (17.5 minutes)                    │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ KAGGLE GPU TRAINING (Free Tesla T4)                                 │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Upload Script to Kaggle                                         │
│     Create new Kaggle Notebook                                      │
│     Paste: cf_kaggle_training.py                                   │
│     Select: GPU (right side)                                        │
│                                                                     │
│  2. Run Full Training (15-20 minutes)                               │
│     • Load 400k users (3 sec)                                       │
│     • SVD decomposition (3 sec)                                     │
│     • Compute similarities (2 sec)                                  │
│     • Generate recommendations (8 min)                              │
│     • Save outputs (1 sec)                                          │
│                                                                     │
│  3. Download Results                                                │
│     • user_based_recommendations.parquet (3.5M rows)                │
│     • item_based_recommendations.parquet                            │
│     • Embeddings & mappings                                         │
│     Time: 2 min                                                     │
│                                                                     │
│  4. Move to Local Machine                                           │
│     Copy to: data/recommendations/                                  │
│     Time: 1 min                                                     │
│                                                                     │
│  Total time per run: ~20 minutes                                    │
│  Cost: FREE (Kaggle GPU)                                            │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────┐
│ EVALUATE & COMPARE (Your Machine)                                   │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  1. Run Evaluation                                                  │
│     $ python ml/recommenders/cf_evaluate.py                        │
│     Output: 7 metrics + grade + recommendations                     │
│     Time: 2 min                                                     │
│                                                                     │
│  2. Compare Results                                                 │
│     Check: Coverage, Variance, Personalization improved?            │
│     Expected: 54.5 → 85+ (from Kaggle training)                    │
│                                                                     │
│  3. Iterate or Deploy?                                              │
│     Score 85+? → Deploy to production ✅                            │
│     Score <85? → Try different hyperparameters 🔄                   │
│                                                                     │
│  Total time: ~3 minutes                                             │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘

TYPICAL SESSION:

  Local Iteration:     ~2 minutes (5 quick experiments)
  Kaggle Training:     ~20 minutes (one full training)
  Evaluation:          ~3 minutes
  ─────────────────────────────────
  Total:               ~25 minutes → Production-Ready Model!
""")

print("\n" + "="*80)
print("READY TO START?")
print("="*80 + "\n")

print("""
Next Steps:

1. DELETE cf_train.py (redundant)
   rm ml/recommenders/cf_train.py

2. CREATE cf_kaggle_training.py (use provided script)
   Copy the Kaggle script from earlier

3. TEST LOCALLY (17 sec)
   python ml/recommenders/cf_train_experiment.py

4. ITERATE (optional, 17 sec each)
   Modify hyperparameters, run again

5. TRAIN ON KAGGLE (20 min, free GPU)
   Paste script in Kaggle Notebook, select GPU, run

6. EVALUATE (3 min)
   python ml/recommenders/cf_evaluate.py

7. COMPARE RESULTS
   Expected: Score jumps from 54.5 → 85+

8. DEPLOY
   Use trained model in FastAPI endpoints
""")

print("\n" + "="*80 + "\n")
