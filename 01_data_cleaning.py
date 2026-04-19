# ============================================================
# Dilli Electric Auto — EV Market Intelligence Tool
# Phase 2: Data Cleaning
# Author: Aarav
# Data Source: VAHAN Dashboard (2025)
# ============================================================

import pandas as pd
import os

# ── 1. Load Raw Data ─────────────────────────────────────────
df = pd.read_csv('market_master.csv')

# ── 2. Clean Column Names ────────────────────────────────────
df.columns = df.columns.str.strip()

# ── 3. Basic Info ────────────────────────────────────────────
print("=== RAW DATA OVERVIEW ===")
print(f"Shape        : {df.shape}")
print(f"Columns      : {df.columns.tolist()}")
print(f"Null Values  :\n{df.isnull().sum()}")
print(f"Data Types   :\n{df.dtypes}")

# ── 4. Fix Data Types ────────────────────────────────────────
# Month: convert to ordered categorical for correct sorting
month_order = ['JAN','FEB','MAR','APR','MAY','JUN',
               'JUL','AUG','SEP','OCT','NOV','DEC']
df['Month'] = pd.Categorical(df['Month'].str.strip(), categories=month_order, ordered=True)

# Registrations: ensure integer
df['Registerations'] = df['Registerations'].astype(int)

# Strip whitespace from string columns
df['Maker']       = df['Maker'].str.strip()
df['Maker_Group'] = df['Maker_Group'].str.strip()
df['State']       = df['State'].str.strip()

# ── 5. Add Month Number column (useful for ML later) ─────────
df['Month_Num'] = df['Month'].cat.codes + 1  # JAN=1, FEB=2 ... DEC=12

# ── 6. Add a Flag: Is this Dilli Electric Auto? ──────────────
df['Is_DEA'] = df['Maker_Group'].apply(lambda x: 1 if x == 'Dilli Electric Auto' else 0)

# ── 7. Remove rows where registrations are zero across all months
#    (Keep zeros — they are valid data points showing no activity)
#    But flag makers who had ZERO registrations ALL year
annual = df.groupby(['Maker','State'])['Registerations'].sum().reset_index()
annual.columns = ['Maker','State','Annual_Total']
zero_makers = annual[annual['Annual_Total'] == 0][['Maker','State']]
print(f"\nMakers with 0 registrations all year: {len(zero_makers)}")

# Merge annual total back for reference (don't drop zeros — keep for SQL analysis)
df = df.merge(annual, on=['Maker','State'], how='left')

# ── 8. Summary Stats ─────────────────────────────────────────
print("\n=== CLEANED DATA OVERVIEW ===")
print(f"Shape        : {df.shape}")
print(f"Total Regs   : {df['Registerations'].sum():,}")
print(f"States       : {sorted(df['State'].unique().tolist())}")
print(f"Maker Groups : {sorted(df['Maker_Group'].unique().tolist())}")
print(f"Unique Makers: {df['Maker'].nunique()}")

# ── 9. Market Share by Maker Group ──────────────────────────
total = df['Registerations'].sum()
group_share = (df.groupby('Maker_Group')['Registerations']
                 .sum()
                 .sort_values(ascending=False)
                 .reset_index())
group_share['Market_Share_%'] = (group_share['Registerations'] / total * 100).round(2)
print("\n=== MARKET SHARE BY GROUP ===")
print(group_share.to_string(index=False))

# ── 10. DEA Performance ──────────────────────────────────────
dea = df[df['Maker_Group'] == 'Dilli Electric Auto']
print(f"\n=== DILLI ELECTRIC AUTO ===")
print(f"Total Registrations : {dea['Registerations'].sum():,}")
print(f"States Active In    : {dea[dea['Registerations']>0]['State'].nunique()}")
print(f"Best Month          : {dea.groupby('Month')['Registerations'].sum().idxmax()}")
print(f"Best State          : {dea.groupby('State')['Registerations'].sum().idxmax()}")

# ── 11. Save Clean File ──────────────────────────────────────
os.makedirs('data', exist_ok=True)
df.to_csv('data/market_clean.csv', index=False)
print("\n✅ Cleaned file saved to: data/market_clean.csv")
