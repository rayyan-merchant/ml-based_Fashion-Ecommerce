"""
generate_reviews_from_transactions.py

Generates synthetic reviews anchored to real transactions.
Fully debugged version with:
 - fixed timezone handling (Python 3.12)
 - fixed datetime comparisons
 - correct CSV escaping for COPY
 - safe quoting (no \x01)

Requirements:
  pip install psycopg2-binary faker tqdm
"""

import os
import random
import json
import io
from datetime import datetime, timedelta, timezone
from faker import Faker
from tqdm import tqdm
import psycopg2

# -----------------------
# CONFIG
# -----------------------
TOTAL_REVIEWS = 300000
TRUNCATE_BEFORE_INSERT = True
NON_ENGLISH_PCT = 0.05
DUPLICATE_PCT = 0.02
RANDOM_SEED = 12345
BATCH_SIZE = 25_000
DB_CONN = os.getenv("PG_CONN", "host=localhost dbname=fashion_db user=postgres password=rayyan123 port=5432")

TARGET_SCHEMA = "niche_data"
TARGET_TABLE = "reviews"
TRANSACTIONS_TABLE = f"{TARGET_SCHEMA}.transactions"
CUSTOMERS_TABLE = f"{TARGET_SCHEMA}.customers"
ARTICLES_TABLE = f"{TARGET_SCHEMA}.articles"

MAX_REVIEWS_PER_ARTICLE = None
MIN_GAP_DAYS = 3
MAX_GAP_DAYS = 14

random.seed(RANDOM_SEED)
fake = Faker()
Faker.seed(RANDOM_SEED)

GLOBAL_ASPECTS = ["fit", "size", "quality", "material", "color", "price", "delivery", "packaging", "service", "comfort"]
EMOJI_LIST = ["😊", "😍", "😡", "🙃", "😂", "👍", "👎", "😭", "🤩"]
SLANG_PHRASES = ["tbh", "ngl", "lowkey", "highkey", "dope", "solid", "meh", "kinda", "IMO"]

NON_ENG_PHRASES = [
    ("es", ["El material es bueno pero el tamaño es pequeño.", "Entrega rápida y buen precio."]),
    ("fr", ["La qualité est correcte mais la taille est trop petite.", "Très satisfait de l'achat."]),
    ("ur", ["مواد اچھی ہیں لیکن سائز چھوٹا ہے۔", "ڈیلیوری جلدی ہوئی۔"])
]

POSITIVE_TEMPLATES = [
    "Loved this! The {aspect} is great and it {verb_phrase}. Will buy again {emoji}",
    "Really happy with the {aspect}. {context_sentence} Totally worth the price.",
    "Excellent quality and fast delivery. {short_comment}",
    "So comfy and looks premium. {context_sentence} Highly recommend!",
    "Exactly as described — fits well and the color is rich. {emoji}"
]

NEGATIVE_TEMPLATES = [
    "Disappointed. The {aspect} is poor and it {verb_phrase}. Would not recommend.",
    "Bad quality. {context_sentence} Packaging was awful and delivery was late.",
    "Terrible experience — broke after one use. {emoji}",
    "Runs small and the material feels cheap. Not worth the price.",
    "Returned it. Customer service didn't help. {short_comment}"
]

NEUTRAL_TEMPLATES = [
    "It's okay. {context_sentence} Nothing special.",
    "Average product. {short_comment} Might be fine for everyday use.",
    "Mediocre — neither great nor terrible.",
    "Good for the price, but don't expect premium quality.",
    "Does the job. Delivery was fine."
]

MIXED_TEMPLATES = [
    "Design is beautiful but quality is lacking. {context_sentence}",
    "Fit is perfect, but stitching could be better. {short_comment}",
    "Amazing color, but it arrived with a small tear. {emoji}",
    "Love the look; hate the delivery time. {context_sentence}",
    "Great price, but service could be faster."
]

# -----------------------
# HELPERS
# -----------------------
def random_short_comment():
    return random.choice(["Wore it yesterday.", "Got compliments.", "Not what I expected.", "Feels okay."])

def random_context_sentence():
    return random.choice([
        "Wore it to a wedding and it looked great.",
        "Used it daily for a week and no issues.",
        "Packaging was neat and secure.",
        "Customer service handled my query quickly."
    ])

def maybe_misspell(word):
    if random.random() < 0.05 and len(word) > 4:
        i = random.randint(1, len(word)-2)
        return word[:i] + word[i+1] + word[i] + word[i+2:]
    return word

def compose_review_text(template, aspect, long=False, use_slang=False, sarcasm=False):
    verb_phrases = [
        "held up well", "fell apart quickly", "feels premium", "feels cheap",
        "is exactly like the photos", "is smaller than expected"
    ]

    s = template.format(
        aspect=aspect,
        verb_phrase=random.choice(verb_phrases),
        context_sentence=random_context_sentence(),
        short_comment=random_short_comment(),
        emoji=random.choice(EMOJI_LIST)
    )

    if use_slang and random.random() < 0.4:
        s += " " + random.choice(SLANG_PHRASES)

    if random.random() < 0.05:
        words = s.split(" ")
        idx = random.randint(0, len(words)-1)
        words[idx] = maybe_misspell(words[idx])
        s = " ".join(words)

    if sarcasm:
        s += " " + random.choice(["Yeah, sure 🙃", "Great… not."])

    return s.strip()

def compute_sentiment_label_from_rating(r):
    if r <= 2:
        return "negative"
    elif r == 3:
        return "neutral"
    return "positive"

def word_count(text):
    return len(text.split()) if text else 0

# -----------------------
# DB HELPERS
# -----------------------
def reservoir_sample_transactions(conn, total_sample):
    cur = conn.cursor(name="stream_txn")
    cur.itersize = 10000
    cur.execute(f"SELECT transaction_id, customer_id, article_id, t_dat FROM {TRANSACTIONS_TABLE}")

    reservoir = []
    count = 0
    for row in cur:
        count += 1
        if len(reservoir) < total_sample:
            reservoir.append(row)
        else:
            s = random.randint(1, count)
            if s <= total_sample:
                reservoir[s-1] = row

    cur.close()
    print(f"Reservoir sampling complete: scanned {count} rows, sampled {len(reservoir)}")
    return reservoir

def copy_rows_to_db(conn, buffer):
    buffer.seek(0)
    cur = conn.cursor()

    copy_sql = f"""
    COPY {TARGET_SCHEMA}.{TARGET_TABLE}
    (customer_id, article_id, rating, review_text, created_at,
     verified_purchase, helpful_votes, sentiment_label, aspect_terms,
     language, review_length, review_source)
    FROM STDIN WITH CSV DELIMITER ',' QUOTE '\"' ESCAPE '\"'
    """

    try:
        cur.copy_expert(copy_sql, buffer)
        conn.commit()
    except Exception as e:
        conn.rollback()
        print("COPY failed:", e)
        raise
    finally:
        cur.close()

    buffer.truncate(0)
    buffer.seek(0)

# -----------------------
# MAIN
# -----------------------
def main():
    conn = psycopg2.connect(DB_CONN)
    conn.autocommit = False
    cur = conn.cursor()

    # Count transactions
    cur.execute(f"SELECT COUNT(*) FROM {TRANSACTIONS_TABLE}")
    tx_count = cur.fetchone()[0]
    print("Total transactions:", tx_count)

    if tx_count == 0:
        print("No transactions found. Abort.")
        return

    sample_size = min(TOTAL_REVIEWS, tx_count)
    sampled_rows = reservoir_sample_transactions(conn, sample_size)

    if TRUNCATE_BEFORE_INSERT:
        print("Truncating reviews table...")
        cur.execute(f"TRUNCATE TABLE {TARGET_SCHEMA}.{TARGET_TABLE} RESTART IDENTITY CASCADE")
        conn.commit()

    # Prepare duplicate pool
    duplicate_texts = []
    dup_pool_size = int(sample_size * DUPLICATE_PCT)
    for _ in range(min(dup_pool_size, 5000)):
        template = random.choice(POSITIVE_TEMPLATES + NEGATIVE_TEMPLATES + NEUTRAL_TEMPLATES + MIXED_TEMPLATES)
        txt = compose_review_text(template, random.choice(GLOBAL_ASPECTS))
        duplicate_texts.append(txt)

    buffer = io.StringIO()
    rows_in_buffer = 0
    total_written = 0

    # Process each transaction
    for txn in tqdm(sampled_rows, desc="Generating reviews"):
        txn_id, customer_id, article_id, t_dat = txn

        # Ensure t_dat is datetime
        if isinstance(t_dat, datetime):
            tdt = t_dat
        else:
            tdt = datetime.combine(t_dat, datetime.min.time())

        # Rating
        r = random.choices([1,2,3,4,5], weights=[6,9,20,35,30])[0]

        # Template
        if r >= 4:
            template = random.choice(POSITIVE_TEMPLATES)
        elif r == 3:
            template = random.choice(NEUTRAL_TEMPLATES)
        else:
            template = random.choice(NEGATIVE_TEMPLATES + MIXED_TEMPLATES)

        # Review text
        aspect = random.choice(GLOBAL_ASPECTS)

        if duplicate_texts and random.random() < DUPLICATE_PCT:
            review_text = random.choice(duplicate_texts)
        else:
            review_text = compose_review_text(template, aspect)

        # Language
        if random.random() < NON_ENGLISH_PCT:
            lang_code, phrases = random.choice(NON_ENG_PHRASES)
            review_text = random.choice(phrases)
            language = lang_code
        else:
            language = "en"

        # created_at
        gap_days = random.randint(MIN_GAP_DAYS, MAX_GAP_DAYS)
        created_at = tdt + timedelta(days=gap_days, seconds=random.randint(0, 86400))
        created_at = created_at.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        if created_at > now:
            created_at = now - timedelta(seconds=random.randint(0, 3600))

        # Other fields
        verified_purchase = True
        helpful_votes = int(random.random() * (21 if r >= 4 else 6))
        aspect_terms = json.dumps(random.sample(GLOBAL_ASPECTS, k=random.randint(1, 3)), ensure_ascii=False)
        review_length = word_count(review_text)
        review_source = random.choice(["web", "mobile", "app"])
        sentiment_label = compute_sentiment_label_from_rating(r)

        # Clean CSV fields
        clean_text = review_text.replace("\n", " ").replace("\r", " ").replace('"', '""')
        clean_aspects = aspect_terms.replace('"', '""')

        row = (
            f"{customer_id},"
            f"{article_id},"
            f"{r},"
            f"\"{clean_text}\","
            f"{created_at.isoformat()},"
            f"{'true' if verified_purchase else 'false'},"
            f"{helpful_votes},"
            f"{sentiment_label},"
            f"\"{clean_aspects}\","
            f"{language},"
            f"{review_length},"
            f"{review_source}\n"
        )

        buffer.write(row)
        rows_in_buffer += 1
        total_written += 1

        if rows_in_buffer >= BATCH_SIZE:
            copy_rows_to_db(conn, buffer)
            rows_in_buffer = 0

    if rows_in_buffer > 0:
        copy_rows_to_db(conn, buffer)

    print("Total reviews written:", total_written)
    conn.close()


if __name__ == "__main__":
    main()
