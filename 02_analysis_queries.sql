-- ============================================================
-- Dilli Electric Auto — EV Market Intelligence Tool
-- Phase 3: SQL Analysis Queries
-- Database: SQLite / PostgreSQL compatible
-- Data: market_clean.csv (loaded as table `ev_sales`)
-- ============================================================

-- TABLE STRUCTURE REFERENCE:
-- Maker          TEXT    — manufacturer name
-- Maker_Group    TEXT    — brand group (DEA, Mahindra, YC, Others...)
-- Month          TEXT    — JAN to DEC
-- Month_Num      INT     — 1 to 12
-- Registerations INT     — units registered
-- State          TEXT    — one of 11 states
-- Is_DEA         INT     — 1 if Dilli Electric Auto, else 0
-- Annual_Total   INT     — total units that maker sold in that state all year


-- ── Q1: Overall Market Share by Maker Group ─────────────────
-- Business Question: Who dominates the EV 3W market?
SELECT
    Maker_Group,
    SUM(Registerations)                                          AS Total_Units,
    ROUND(SUM(Registerations) * 100.0 / SUM(SUM(Registerations)) OVER (), 2) AS Market_Share_Pct
FROM ev_sales
GROUP BY Maker_Group
ORDER BY Total_Units DESC;


-- ── Q2: Top 10 Individual Makers Nationally ─────────────────
-- Business Question: Who are DEA's biggest direct competitors?
SELECT
    Maker,
    Maker_Group,
    SUM(Registerations) AS Total_Units
FROM ev_sales
GROUP BY Maker, Maker_Group
ORDER BY Total_Units DESC
LIMIT 10;


-- ── Q3: Monthly Sales Trend — DEA vs Top Competitor ─────────
-- Business Question: Is DEA growing or declining month-on-month?
SELECT
    Month,
    Month_Num,
    SUM(CASE WHEN Maker_Group = 'Dilli Electric Auto' THEN Registerations ELSE 0 END) AS DEA_Units,
    SUM(CASE WHEN Maker = 'BAJAJ AUTO LTD'            THEN Registerations ELSE 0 END) AS Bajaj_Units,
    SUM(CASE WHEN Maker = 'YC ELECTRIC VEHICLE'       THEN Registerations ELSE 0 END) AS YC_Units
FROM ev_sales
GROUP BY Month, Month_Num
ORDER BY Month_Num;


-- ── Q4: State-wise Market Share — DEA Performance ───────────
-- Business Question: Which states should DEA focus on?
WITH state_total AS (
    SELECT State, SUM(Registerations) AS State_Market
    FROM ev_sales
    GROUP BY State
),
dea_state AS (
    SELECT State, SUM(Registerations) AS DEA_Sales
    FROM ev_sales
    WHERE Maker_Group = 'Dilli Electric Auto'
    GROUP BY State
)
SELECT
    d.State,
    d.DEA_Sales,
    s.State_Market,
    ROUND(d.DEA_Sales * 100.0 / s.State_Market, 2) AS DEA_Share_Pct
FROM dea_state d
JOIN state_total s ON d.State = s.State
ORDER BY DEA_Share_Pct DESC;


-- ── Q5: Seasonal Demand Index ───────────────────────────────
-- Business Question: Which months see highest industry demand?
SELECT
    Month,
    Month_Num,
    SUM(Registerations) AS Industry_Total,
    ROUND(SUM(Registerations) * 100.0 / SUM(SUM(Registerations)) OVER (), 2) AS Month_Share_Pct,
    RANK() OVER (ORDER BY SUM(Registerations) DESC) AS Demand_Rank
FROM ev_sales
GROUP BY Month, Month_Num
ORDER BY Month_Num;


-- ── Q6: DEA Month-over-Month Growth Rate ────────────────────
-- Business Question: Is DEA accelerating or slowing down?
WITH dea_monthly AS (
    SELECT
        Month_Num,
        Month,
        SUM(Registerations) AS Units
    FROM ev_sales
    WHERE Maker_Group = 'Dilli Electric Auto'
    GROUP BY Month_Num, Month
)
SELECT
    Month,
    Units,
    LAG(Units) OVER (ORDER BY Month_Num)  AS Prev_Month_Units,
    ROUND(
        (Units - LAG(Units) OVER (ORDER BY Month_Num)) * 100.0
        / NULLIF(LAG(Units) OVER (ORDER BY Month_Num), 0),
    2) AS MoM_Growth_Pct
FROM dea_monthly
ORDER BY Month_Num;


-- ── Q7: Competitor Concentration — Herfindahl Index Proxy ───
-- Business Question: How competitive is each state?
-- (Higher score = more concentrated = dominated by 1-2 players)
SELECT
    State,
    COUNT(DISTINCT Maker)                     AS Active_Makers,
    SUM(Registerations)                        AS Total_Units,
    MAX(SUM(Registerations)) OVER (PARTITION BY State) AS State_Max,
    ROUND(
        MAX(Registerations) * 100.0 / NULLIF(SUM(Registerations), 0)
    , 2)                                       AS Top_Maker_Dominance_Pct
FROM ev_sales
GROUP BY State, Maker
-- wrap as subquery to aggregate per state
ORDER BY State;


-- ── Q8: Pareto Analysis — 80% of Sales from Which Makers? ───
-- Business Question: Which makers drive 80% of market volume?
WITH maker_totals AS (
    SELECT
        Maker,
        SUM(Registerations) AS Units
    FROM ev_sales
    GROUP BY Maker
),
ranked AS (
    SELECT
        Maker,
        Units,
        SUM(Units) OVER (ORDER BY Units DESC
                         ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS Running_Total,
        SUM(Units) OVER ()                                                   AS Grand_Total
    FROM maker_totals
)
SELECT
    Maker,
    Units,
    ROUND(Running_Total * 100.0 / Grand_Total, 2) AS Cumulative_Share_Pct
FROM ranked
WHERE Running_Total * 1.0 / Grand_Total <= 0.80
ORDER BY Units DESC;


-- ── Q9: DEA Untapped State Opportunity ──────────────────────
-- Business Question: Where is the market large but DEA share is low?
WITH state_total AS (
    SELECT State, SUM(Registerations) AS Market_Size
    FROM ev_sales GROUP BY State
),
dea_state AS (
    SELECT State, SUM(Registerations) AS DEA_Units
    FROM ev_sales
    WHERE Maker_Group = 'Dilli Electric Auto'
    GROUP BY State
)
SELECT
    s.State,
    s.Market_Size,
    COALESCE(d.DEA_Units, 0)                                           AS DEA_Units,
    ROUND(COALESCE(d.DEA_Units, 0) * 100.0 / s.Market_Size, 2)        AS DEA_Share_Pct,
    CASE
        WHEN s.Market_Size > 50000 AND COALESCE(d.DEA_Units,0)*100.0/s.Market_Size < 3
        THEN 'HIGH OPPORTUNITY'
        WHEN s.Market_Size > 20000 AND COALESCE(d.DEA_Units,0)*100.0/s.Market_Size < 5
        THEN 'MEDIUM OPPORTUNITY'
        ELSE 'Stable'
    END AS Opportunity_Flag
FROM state_total s
LEFT JOIN dea_state d ON s.State = d.State
ORDER BY Market_Size DESC;


-- ── Q10: Window Function — Running Total for DEA ────────────
-- Business Question: What is DEA's cumulative sales trajectory?
SELECT
    Month,
    Month_Num,
    SUM(Registerations)                                              AS Monthly_Units,
    SUM(SUM(Registerations)) OVER (ORDER BY Month_Num
                                   ROWS BETWEEN UNBOUNDED PRECEDING
                                   AND CURRENT ROW)                  AS Cumulative_Units,
    ROUND(AVG(SUM(Registerations)) OVER (ORDER BY Month_Num
                                         ROWS BETWEEN 2 PRECEDING
                                         AND CURRENT ROW), 0)        AS Rolling_3M_Avg
FROM ev_sales
WHERE Maker_Group = 'Dilli Electric Auto'
GROUP BY Month, Month_Num
ORDER BY Month_Num;
