import pandas as pd
import numpy as np
import random
from datetime import datetime, timedelta

# ──────────────────────────────────────────────
# CONFIG
# ──────────────────────────────────────────────
CATEGORIES = ['Food', 'Rent', 'Utilities', 'Transport',
              'Entertainment', 'Healthcare', 'Shopping']

PAYMENT_METHODS = ['Cash', 'Credit Card', 'Debit Card', 'UPI']

AMOUNT_RANGES = {
    'Food':          (5,   80),
    'Rent':          (800, 1500),
    'Utilities':     (40,  200),
    'Transport':     (3,   50),
    'Entertainment': (10,  100),
    'Healthcare':    (15,  300),
    'Shopping':      (10,  250),
}

FOOD_NOTES       = ['Lunch', 'Groceries', 'Dinner out', 'Coffee', 'Snacks', 'Takeaway']
TRANSPORT_NOTES  = ['Uber', 'Bus pass', 'Fuel', 'Metro', 'Auto rickshaw']
ENTERTAIN_NOTES  = ['Netflix', 'Cinema', 'Concert', 'Book', 'Game purchase']
HEALTH_NOTES     = ['Pharmacy', 'Doctor visit', 'Lab test', 'Gym membership', 'Vitamins']
SHOPPING_NOTES   = ['Clothes', 'Electronics', 'Home goods', 'Gift', 'Accessories']
UTILITY_NOTES    = ['Electricity', 'Internet', 'Water', 'Gas', 'Phone bill']


def _pick_note(category: str) -> str:
    mapping = {
        'Food':          FOOD_NOTES,
        'Transport':     TRANSPORT_NOTES,
        'Entertainment': ENTERTAIN_NOTES,
        'Healthcare':    HEALTH_NOTES,
        'Shopping':      SHOPPING_NOTES,
        'Utilities':     UTILITY_NOTES,
    }
    pool = mapping.get(category, [''])
    return random.choice(pool)


def generate_synthetic_expenses(
    start_date: str = '2024-01-01',
    end_date:   str = '2024-12-31',
    seed:       int = 42,
) -> pd.DataFrame:
    """
    Generate a realistic synthetic expense dataset.

    Realism improvements over the original:
    - Seasonal spend variation (higher Nov-Dec shopping / entertainment).
    - Weekend uplift for Food & Entertainment.
    - Occasional large one-off Healthcare bills (mimics real life).
    - Descriptive notes for every transaction.
    - Fixed random seed for reproducibility.
    """
    np.random.seed(seed)
    random.seed(seed)

    dates = pd.date_range(start=start_date, end=end_date, freq='D')
    records = []

    for date in dates:
        is_weekend   = date.dayofweek >= 5
        is_holiday_q = date.month in (11, 12)   # Nov-Dec – shopping/entertainment spike

        # ── RENT (once per month on the 1st) ──────────────────────────────
        if date.day == 1:
            records.append({
                'date':           date.strftime('%Y-%m-%d'),
                'category':       'Rent',
                'amount':         round(random.uniform(*AMOUNT_RANGES['Rent']), 2),
                'payment_method': 'Debit Card',
                'note':           'Monthly rent',
            })

        # ── UTILITIES (once per month on 5th) ─────────────────────────────
        if date.day == 5:
            for note in random.sample(UTILITY_NOTES, k=random.randint(1, 3)):
                records.append({
                    'date':           date.strftime('%Y-%m-%d'),
                    'category':       'Utilities',
                    'amount':         round(random.uniform(*AMOUNT_RANGES['Utilities']), 2),
                    'payment_method': random.choice(PAYMENT_METHODS),
                    'note':           note,
                })

        # ── DAILY TRANSACTIONS ────────────────────────────────────────────
        # Poisson mean varies by day type and season
        base_mean = 1.6 if is_weekend else 1.1
        if is_holiday_q:
            base_mean *= 1.3
        num_txns = np.random.poisson(base_mean)

        for _ in range(num_txns):
            # Weekend: more Food & Entertainment; weekday: more Transport
            if is_weekend:
                cat = random.choices(
                    ['Food', 'Entertainment', 'Shopping', 'Healthcare', 'Transport'],
                    weights=[35, 25, 20, 10, 10]
                )[0]
            else:
                cat = random.choices(
                    ['Food', 'Transport', 'Shopping', 'Healthcare', 'Entertainment'],
                    weights=[35, 30, 15, 12, 8]
                )[0]

            low, high = AMOUNT_RANGES[cat]
            # Occasional spike for Healthcare
            if cat == 'Healthcare' and random.random() < 0.08:
                amount = round(random.uniform(300, 800), 2)
            else:
                amount = round(random.uniform(low, high), 2)

            records.append({
                'date':           date.strftime('%Y-%m-%d'),
                'category':       cat,
                'amount':         amount,
                'payment_method': random.choice(PAYMENT_METHODS),
                'note':           _pick_note(cat),
            })

    df = pd.DataFrame(records)
    # Ensure correct column order and types
    df = df[['date', 'category', 'amount', 'payment_method', 'note']]
    df['amount'] = df['amount'].astype(float)
    return df


# ── Quick sanity-check when run directly ──────────────────────────────────────
if __name__ == '__main__':
    df = generate_synthetic_expenses()
    print(f"Generated {len(df):,} records  |  date range: {df['date'].min()} → {df['date'].max()}")
    print(df.groupby('category')['amount'].agg(['count', 'sum', 'mean']).round(2))