import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
import os

os.makedirs("data/ml/events", exist_ok=True)
load_dotenv()

engine = create_engine(
    f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@127.0.0.1:{os.getenv('DB_PORT')}/{os.getenv('DB_NAME')}"
)

print("=" * 60)
print("Dataset D: Events & Behavior (Batch Processing)")
print("=" * 60)

print("\n1️⃣  Querying transactions in batches...")
print("   (Processing 100k rows at a time)\n")

# ⭐ BATCH PROCESSING: Load data in chunks
chunk_size = 100000
chunks = []
chunk_count = 0

query = """
SELECT 
    t.customer_id,
    t.article_id,
    t.t_dat as created_at,
    t.price,
    1 as event_type
FROM niche_data.transactions t
ORDER BY t.customer_id, t.t_dat
"""

print("   Loading from database...\n")

# Read in chunks to avoid memory overload
rows_loaded = 0
import sys

try:
    for chunk in pd.read_sql(query, engine, chunksize=chunk_size):
        chunk_count += 1
        rows_loaded += len(chunk)
        chunks.append(chunk)
        
        # Progress indicator with total count
        print(f"   ✅ Batch {chunk_count}: {len(chunk):,} rows | Total: {rows_loaded:,} rows")
        sys.stdout.flush()  # Force print immediately
        
except KeyboardInterrupt:
    print("\n   ⚠️  Interrupted by user")
    print(f"   Loaded {rows_loaded:,} rows before stopping")
except Exception as e:
    print(f"\n   ❌ Error during loading: {e}")
    raise

print(f"\n   ✅ Finished loading! Total batches: {chunk_count} | Total rows: {rows_loaded:,}")

# Combine all chunks
print("\n2️⃣  Combining batches...")
df = pd.concat(chunks, ignore_index=True)
print(f"   ✅ Combined {len(df):,} total rows")

if len(df) == 0:
    print("   ⚠️  No events found. Creating synthetic data...")
    df = pd.DataFrame({
        'customer_id': range(100000, 100100),
        'article_id': range(1, 101),
        'created_at': pd.date_range('2024-01-01', periods=100),
        'price': [50.0] * 100,
        'event_type': [1] * 100
    })

# Process
print("\n3️⃣  Processing events...")
df['created_at'] = pd.to_datetime(df['created_at'])
df['event_date'] = df['created_at'].dt.date

# Aggregate customer events
print("   Aggregating customer statistics...")
customer_events = df.groupby('customer_id').agg({
    'article_id': 'count',
    'created_at': ['min', 'max'],
    'price': ['sum', 'mean']
}).reset_index()

customer_events.columns = ['customer_id', 'total_events', 'first_event_date', 'last_event_date', 'total_spent', 'avg_spent']

print(f"   ✅ {len(customer_events):,} unique customers")
print(f"   Date range: {df['created_at'].min().date()} to {df['created_at'].max().date()}")

# Save
print("\n4️⃣  Saving files...")
df.to_parquet('data/ml/events/events_raw.parquet', index=False)
print(f"   ✅ events_raw.parquet ({len(df):,} rows)")

customer_events.to_parquet('data/ml/events/customer_events.parquet', index=False)
print(f"   ✅ customer_events.parquet ({len(customer_events):,} rows)")

print("\n" + "=" * 60)
print("✅ Dataset D Created Successfully!")
print("=" * 60)
print(f"\n Summary:")
print(f"   Total events loaded: {len(df):,}")
print(f"   Unique customers: {len(customer_events):,}")
print(f"   Date range: {df['created_at'].min().date()} to {df['created_at'].max().date()}")
print(f"   Files saved to: data/ml/events/")