#!/usr/bin/env python3
"""
UK Lending Risk Dashboard - Data Preprocessing
Aggregates housing data from UK-HPI file, computes risk scores, and exports JSON for the dashboard.
"""

import csv
import json
import math
from collections import defaultdict
from datetime import datetime

class SanitizedJSONEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles Infinity and NaN values."""
    def encode(self, o):
        if isinstance(o, float):
            if math.isinf(o) or math.isnan(o):
                return 'null'
        return super().encode(o)
    
    def iterencode(self, o, _one_shot=False):
        """Encode object while handling special float values."""
        for chunk in super().iterencode(o, _one_shot):
            yield chunk

DATA_DIR = "Data"
OUTPUT_FILE = "dashboard_data.json"

def sanitize_inf_nan(obj):
    """Recursively sanitize Infinity and NaN values in nested structures."""
    if isinstance(obj, dict):
        return {k: sanitize_inf_nan(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_inf_nan(item) for item in obj]
    elif isinstance(obj, float):
        if math.isinf(obj) or math.isnan(obj):
            return None
        return obj
    return obj

# Regions that appear in both price data and repo data
REGIONS = [
    "East Midlands", "East of England", "London", "North East",
    "North West", "South East", "South West", "West Midlands Region",
    "Yorkshire and The Humber", "England", "Wales"
]

REGION_CODES = {
    "East Midlands": "E12000004",
    "East of England": "E12000006",
    "London": "E12000007",
    "North East": "E12000001",
    "North West": "E12000002",
    "South East": "E12000008",
    "South West": "E12000009",
    "West Midlands Region": "E12000005",
    "Yorkshire and The Humber": "E12000003",
    "England": "E92000001",
    "Wales": "W92000004",
}

# LA code prefix → region mapping for deprivation aggregation
# English regions by LA code prefix patterns
LA_TO_REGION = {
    "E08000001": "North West", "E08000002": "North West", "E08000003": "North West",
    "E08000004": "North West", "E08000005": "North West", "E08000006": "North West",
    "E08000007": "North West", "E08000008": "North West", "E08000009": "North West",
    "E08000010": "North West", "E08000011": "North West", "E08000012": "North West",
    "E08000013": "North West", "E08000014": "North West", "E08000015": "North West",
    "E08000016": "Yorkshire and The Humber", "E08000017": "Yorkshire and The Humber",
    "E08000018": "Yorkshire and The Humber", "E08000019": "Yorkshire and The Humber",
    "E08000021": "North East", "E08000022": "North East",
    "E08000023": "North East", "E08000024": "North East",
    "E08000025": "West Midlands Region", "E08000026": "West Midlands Region",
    "E08000027": "West Midlands Region", "E08000028": "West Midlands Region",
    "E08000029": "West Midlands Region", "E08000030": "West Midlands Region",
    "E08000031": "West Midlands Region",
    "E08000032": "Yorkshire and The Humber", "E08000033": "Yorkshire and The Humber",
    "E08000034": "Yorkshire and The Humber", "E08000035": "Yorkshire and The Humber",
    "E08000036": "Yorkshire and The Humber", "E08000037": "North East",
}

# Map LA codes to regions using ONS region codes
def get_region_for_la(la_code):
    """Map a Local Authority code to its region."""
    if la_code in LA_TO_REGION:
        return LA_TO_REGION[la_code]
    # London boroughs
    if la_code.startswith("E09"):
        return "London"
    # Welsh LAs
    if la_code.startswith("W"):
        return "Wales"
    return None


def load_uk_hpi():
    """Load UK-HPI file and extract prices/indices by region and date."""
    print("Loading UK-HPI data...")
    prices = defaultdict(dict)
    indices = defaultdict(dict)
    filepath = f"{DATA_DIR}/UK-HPI-full-file-2025-12.csv"

    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["RegionName"].strip()
            if region not in REGIONS:
                continue

            # Parse date: DD/MM/YYYY → YYYY-MM-DD
            try:
                raw_date = row["Date"].strip()
                dt = datetime.strptime(raw_date, "%d/%m/%Y")
                date = dt.strftime("%Y-%m-%d")
            except ValueError:
                continue

            # Only 2010 onwards for the dashboard
            if date < "2010-01-01":
                continue

            try:
                avg_price = float(row["AveragePrice"]) if row["AveragePrice"] else None
                index_val = float(row["Index"]) if row["Index"] else None
                annual_change = float(row["12m%Change"]) if row["12m%Change"] else None
                monthly_change = float(row["1m%Change"]) if row["1m%Change"] else None
            except (ValueError, KeyError):
                continue

            # Store price data
            if avg_price:
                prices[region][date] = {
                    "price": avg_price,
                    "annual_change": annual_change,
                    "monthly_change": monthly_change,
                }

            # Store index data
            if index_val:
                indices[region][date] = index_val

    print(f"  Loaded prices for {len(prices)} regions")
    print(f"  Loaded indices for {len(indices)} regions")
    return prices, indices


def load_repossessions():
    """Load repossession data by region and date."""
    print("Loading repossessions...")
    repos = defaultdict(dict)
    filepath = f"{DATA_DIR}/Repossession-2025-12.csv"

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["RegionName"].strip()
            if region not in REGIONS:
                continue
            # Parse date from DD/MM/YYYY to YYYY-MM-DD
            raw_date = row["date"].strip()
            try:
                dt = datetime.strptime(raw_date, "%d/%m/%Y")
                date = dt.strftime("%Y-%m-%d")
            except ValueError:
                continue
            try:
                volume = int(row["SalesVolume"]) if row["SalesVolume"] else 0
            except (ValueError, KeyError):
                volume = 0
            repos[region][date] = volume

    print(f"  Loaded repos for {len(repos)} regions")
    return repos


def load_deprivation():
    """Load deprivation data aggregated by LA district."""
    print("Loading deprivation data...")
    filepath = f"{DATA_DIR}/IoD2025 Local Authority District Summaries (lower-tier) - Rank of average rank.csv"

    la_data = []
    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            la_code = row["Local Authority District code (2024)"].strip()
            la_name = row["Local Authority District name (2024)"].strip()
            try:
                imd_rank = int(row["Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)"].strip())
                income_rank = int(row["Income - Rank (where 1 is most deprived) "].strip())
                employment_rank = int(row["Employment - Rank (where 1 is most deprived) "].strip())
                barriers_rank = int(row["Barriers to Housing and Services - Rank (where 1 is most deprived) "].strip())
            except (ValueError, KeyError):
                continue

            region = get_region_for_la(la_code)
            la_data.append({
                "la_code": la_code,
                "la_name": la_name,
                "region": region,
                "imd_rank": imd_rank,
                "income_rank": income_rank,
                "employment_rank": employment_rank,
                "barriers_rank": barriers_rank,
            })

    # Aggregate to regional level
    max_rank = 296  # total number of LAs
    regional_deprivation = {}
    region_groups = defaultdict(list)

    for la in la_data:
        if la["region"] and la["region"] in REGIONS:
            region_groups[la["region"]].append(la)

    for region, las in region_groups.items():
        avg_imd = sum(la["imd_rank"] for la in las) / len(las)
        avg_income = sum(la["income_rank"] for la in las) / len(las)
        avg_employment = sum(la["employment_rank"] for la in las) / len(las)
        avg_barriers = sum(la["barriers_rank"] for la in las) / len(las)

        # Normalized deprivation score (0=least deprived, 1=most deprived)
        dep_score = 1 - (avg_imd / max_rank)

        regional_deprivation[region] = {
            "avg_imd_rank": round(avg_imd, 1),
            "avg_income_rank": round(avg_income, 1),
            "avg_employment_rank": round(avg_employment, 1),
            "avg_barriers_rank": round(avg_barriers, 1),
            "deprivation_score": round(dep_score, 4),
            "num_las": len(las),
        }

    print(f"  Aggregated deprivation for {len(regional_deprivation)} regions")
    return regional_deprivation, la_data

def load_epc():
    """Load and aggregate EPC data by region and integer EPC rating (1-7)."""
    print("Loading EPC data...")
    filepath = f"{DATA_DIR}/AtomBank_Nationwide_EPC_Risk1.csv"
    
    epc_stats = defaultdict(lambda: {"count": 0, "total_bill": 0, "total_cost_per_sqm": 0})
    regional_epc_stats = defaultdict(lambda: defaultdict(lambda: {"count": 0}))
    
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                try:
                    green_score = float(row["green_score"])
                    total_bill = float(row["total_energy_bill"]) if row["total_energy_bill"] else None
                    cost_per_sqm = float(row["energy_cost_per_sqm"]) if row["energy_cost_per_sqm"] else None
                    postcode = row.get("POSTCODE", "").strip()
                    
                    if green_score is not None:
                        # Bucket continuous score to integer rating (1-7)
                        rating = int(round(green_score))
                        rating = max(1, min(7, rating))  # Clamp to 1-7
                        
                        # Global stats
                        epc_stats[rating]["count"] += 1
                        if total_bill:
                            epc_stats[rating]["total_bill"] += total_bill
                        if cost_per_sqm:
                            epc_stats[rating]["total_cost_per_sqm"] += cost_per_sqm
                        
                        # Regional stats
                        if postcode:
                            region = postcodeToRegion(postcode)
                            if region:
                                regional_epc_stats[region][rating]["count"] += 1
                
                except (ValueError, KeyError):
                    continue
        
        # Calculate global averages and format for display
        epc_data = {}
        total_count = sum(s["count"] for s in epc_stats.values())
        for rating in sorted(epc_stats.keys()):
            stats = epc_stats[rating]
            count = stats["count"]
            epc_data[rating] = {
                "count": count,
                "percentage": round(count / total_count * 100, 2) if total_count > 0 else 0,
                "avg_energy_bill": round(stats["total_bill"] / count, 2) if count > 0 else 0,
                "avg_cost_per_sqm": round(stats["total_cost_per_sqm"] / count, 2) if count > 0 else 0,
            }
        
        # Format regional data: region -> rating -> count
        epc_by_region = {}
        for region, rating_data in regional_epc_stats.items():
            epc_by_region[region] = {}
            for rating in sorted(rating_data.keys()):
                epc_by_region[region][rating] = rating_data[rating]["count"]
        
        print(f"  Loaded EPC data for {total_count} properties across {len(epc_by_region)} regions (bucketed to 7 ratings)")
        return epc_data, epc_by_region
    except FileNotFoundError:
        print(f"  Warning: EPC file not found at {filepath}")
        return {}, {}

def postcodeToRegion(postcode):
    """Map UK postcode to region."""
    if not postcode:
        return None
    
    prefix = postcode[:2].upper()
    
    # North East
    if prefix in ["NE", "SR", "DH"]:
        return "North East"
    # North West
    elif prefix in ["LA", "M", "BL", "WN", "PR", "BB", "FY", "CH"]:
        return "North West"
    # Yorkshire and The Humber
    elif prefix in ["YO", "HX", "HD", "OL", "SK", "DN", "LS", "S", "BD"]:
        return "Yorkshire and The Humber"
    # West Midlands
    elif prefix in ["WV", "W", "DY", "B", "CV", "ST"]:
        return "West Midlands Region"
    # East Midlands
    elif prefix in ["DE", "NG", "LE", "LN", "PE", "NN"]:
        return "East Midlands"
    # East of England
    elif prefix in ["CB", "PE", "NR", "IP", "CO", "SS", "AL", "SG", "CM", "EN", "LU", "MK"]:
        return "East of England"
    # London
    elif prefix in ["E", "EC", "N", "NC", "NW", "SE", "SW", "W", "WC", "EC"]:
        return "London"
    # South East
    elif prefix in ["RH", "CR", "BR", "SE", "TN", "BN", "GU", "RG", "PO", "HP", "SL", "OX"]:
        return "South East"
    # South West
    elif prefix in ["EX", "PL", "TR", "TQ", "TA", "BA", "DT", "SP", "GL", "SN", "BS"]:
        return "South West"
    
    return None

def risk_model(prices, repos, deprivation):
    """Compute lending risk scores per region using logistic regression fitted on repossessions."""
    from sklearn.linear_model import LogisticRegression
    from sklearn.preprocessing import StandardScaler
    import numpy as np

    print("Computing risk scores...")

    # Get common date range (repos data: 2016-2025)
    all_repo_dates = set()
    for region_dates in repos.values():
        all_repo_dates.update(region_dates.keys())
    repo_date_range = sorted(all_repo_dates)

    # Split for backtest
    train_cutoff = "2023-01-01"
    train_dates = [d for d in repo_date_range if d < train_cutoff]
    test_dates  = [d for d in repo_date_range if d >= train_cutoff]

    # Exclude aggregate regions
    scoring_regions = [r for r in REGIONS if r not in ["England", "Wales"]]

    # ------------------------------------------------------------------ #
    # 1. Build per-region feature matrix and repossession target          #
    # ------------------------------------------------------------------ #
    risk_results = {}

    for region in scoring_regions:
        region_prices = prices.get(region, {})
        region_repos  = repos.get(region, {})

        # Repo counts
        train_repos = [region_repos.get(d, 0) for d in train_dates]
        test_repos  = [region_repos.get(d, 0) for d in test_dates]
        all_repos   = [region_repos.get(d, 0) for d in repo_date_range]

        avg_repos_train = sum(train_repos) / max(len(train_repos), 1)
        avg_repos_test  = sum(test_repos)  / max(len(test_repos),  1)
        avg_repos_all   = sum(all_repos)   / max(len(all_repos),   1)
        total_repos     = sum(all_repos)

        # HPI features
        annual_changes = [
            v["annual_change"] for v in region_prices.values()
            if v.get("annual_change") is not None
        ]
        avg_annual_change = sum(annual_changes) / max(len(annual_changes), 1) if annual_changes else 0.0

        recent_changes = [
            region_prices[d]["annual_change"]
            for d in sorted(region_prices)[-12:]
            if region_prices[d].get("annual_change") is not None
        ]
        recent_hpi_trend = sum(recent_changes) / max(len(recent_changes), 1) if recent_changes else 0.0

        # Deprivation
        dep_score = deprivation.get(region, {}).get("deprivation_score", 0.5)

        # Latest price
        latest_dates = sorted(region_prices.keys())
        latest_price = region_prices[latest_dates[-1]]["price"] if latest_dates else None

        risk_results[region] = {
            "avg_repos_train":    round(avg_repos_train, 2),
            "avg_repos_test":     round(avg_repos_test,  2),
            "avg_repos_all":      round(avg_repos_all,   2),
            "total_repos":        total_repos,
            "avg_annual_hpi_change": round(avg_annual_change,  2),
            "recent_hpi_trend":   round(recent_hpi_trend, 2),
            "deprivation_score":  dep_score,
            "latest_price":       latest_price,
        }

    # ------------------------------------------------------------------ #
    # 2. Fit logistic regression on TRAINING regions/period               #
    #    Target: above-median repossession rate in the train window        #
    #    Features: recent_hpi_trend, deprivation_score, latest_price       #
    # ------------------------------------------------------------------ #
    regions_with_data = [
        r for r in scoring_regions
        if risk_results[r]["latest_price"] is not None
    ]

    X_raw = np.array([
        [
            risk_results[r]["recent_hpi_trend"],
            risk_results[r]["deprivation_score"],
            risk_results[r]["latest_price"],
        ]
        for r in regions_with_data
    ])

    # Binary target: 1 if avg train repos is above the median across regions
    train_repo_vals = np.array([risk_results[r]["avg_repos_train"] for r in regions_with_data])
    median_repos    = np.median(train_repo_vals)
    y               = (train_repo_vals > median_repos).astype(int)

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X_raw)

    model = LogisticRegression(max_iter=1000, random_state=42)
    model.fit(X_scaled, y)

    # ------------------------------------------------------------------ #
    # 3. Predict repossession probability for every region (full period)  #
    # ------------------------------------------------------------------ #
    proba_high_risk = model.predict_proba(X_scaled)[:, 1]  # P(above-median repos)

    for region, prob in zip(regions_with_data, proba_high_risk):
        data = risk_results[region]
        data["risk_score"]       = round(float(prob), 4)
        data["opportunity_score"] = round(1.0 - float(prob), 4)

    # Regions missing latest_price fall back to neutral score
    for region in scoring_regions:
        if region not in regions_with_data:
            risk_results[region]["risk_score"]       = 0.5
            risk_results[region]["opportunity_score"] = 0.5

    # ------------------------------------------------------------------ #
    # 4. Rank by risk                                                     #
    # ------------------------------------------------------------------ #
    sorted_by_risk = sorted(risk_results.items(), key=lambda x: x[1]["risk_score"], reverse=True)
    for rank, (region, data) in enumerate(sorted_by_risk, 1):
        data["risk_rank"] = rank

    print(f"  Computed risk scores for {len(risk_results)} regions")
    print(f"  Model coefficients — HPI trend: {model.coef_[0][0]:.3f}, "
          f"Deprivation: {model.coef_[0][1]:.3f}, "
          f"Latest price: {model.coef_[0][2]:.3f}")
    return risk_results


def compute_backtest(prices, repos, risk_results):
    """Backtest: train risk model on 2016-2022, test on 2023-2025."""
    print("Computing backtest validation...")

    scoring_regions = [r for r in REGIONS if r not in ["England", "Wales"]]

    # Get repo dates
    all_repo_dates = set()
    for region_dates in repos.values():
        all_repo_dates.update(region_dates.keys())
    repo_date_range = sorted(all_repo_dates)

    train_cutoff = "2023-01-01"
    train_dates = [d for d in repo_date_range if d < train_cutoff]
    test_dates = [d for d in repo_date_range if d >= train_cutoff]

    # For each region, compute train-period risk rank vs test-period actual repo rank
    train_avg_repos = {}
    test_avg_repos = {}

    for region in scoring_regions:
        t_repos = [repos[region].get(d, 0) for d in train_dates if d in repos.get(region, {})]
        s_repos = [repos[region].get(d, 0) for d in test_dates if d in repos.get(region, {})]
        train_avg_repos[region] = sum(t_repos) / max(len(t_repos), 1)
        test_avg_repos[region] = sum(s_repos) / max(len(s_repos), 1)

    # Rank both
    train_ranked = sorted(scoring_regions, key=lambda r: train_avg_repos[r], reverse=True)
    test_ranked = sorted(scoring_regions, key=lambda r: test_avg_repos[r], reverse=True)

    train_ranks = {r: i+1 for i, r in enumerate(train_ranked)}
    test_ranks = {r: i+1 for i, r in enumerate(test_ranked)}

    # Spearman correlation
    n = len(scoring_regions)
    d_squared_sum = sum((train_ranks[r] - test_ranks[r])**2 for r in scoring_regions)
    spearman = 1 - (6 * d_squared_sum) / (n * (n**2 - 1))

    # Risk score rank vs test repo rank
    risk_ranked = sorted(scoring_regions, key=lambda r: risk_results[r]["risk_score"], reverse=True)
    risk_ranks = {r: i+1 for i, r in enumerate(risk_ranked)}
    d_squared_risk = sum((risk_ranks[r] - test_ranks[r])**2 for r in scoring_regions)
    spearman_risk = 1 - (6 * d_squared_risk) / (n * (n**2 - 1))

    backtest = {
        "train_period": f"{train_dates[0]} to {train_dates[-1]}",
        "test_period": f"{test_dates[0]} to {test_dates[-1]}",
        "spearman_train_vs_test": round(spearman, 4),
        "spearman_risk_vs_test": round(spearman_risk, 4),
        "regions": {}
    }

    for region in scoring_regions:
        backtest["regions"][region] = {
            "train_avg_repos": round(train_avg_repos[region], 2),
            "test_avg_repos": round(test_avg_repos[region], 2),
            "train_rank": train_ranks[region],
            "test_rank": test_ranks[region],
            "risk_rank": risk_ranks[region],
        }

    print(f"  Spearman (train vs test repos): {spearman:.4f}")
    print(f"  Spearman (risk score vs test repos): {spearman_risk:.4f}")
    return backtest


def build_time_series(prices, indices, repos):
    """Build time series data for charts."""
    print("Building time series for charts...")

    # Get all dates from 2016 onwards
    all_dates = set()
    for region_dates in repos.values():
        all_dates.update(region_dates.keys())
    dates = sorted(all_dates)

    # Extended dates for price trends (from 2010)
    price_dates = set()
    for region_data in prices.values():
        for d in region_data:
            if d >= "2010-01-01":
                price_dates.add(d)
    price_dates = sorted(price_dates)

    # Price time series
    price_series = {}
    for region in REGIONS:
        series = []
        for d in price_dates:
            val = prices.get(region, {}).get(d, {})
            if isinstance(val, dict) and val.get("price"):
                series.append({"date": d, "price": val["price"], "annual_change": val.get("annual_change")})
        price_series[region] = series

    # Index time series
    index_series = {}
    for region in REGIONS:
        series = []
        for d in price_dates:
            val = indices.get(region, {}).get(d)
            if val is not None:
                series.append({"date": d, "index": val})
        index_series[region] = series

    # Repo time series
    repo_series = {}
    for region in REGIONS:
        series = []
        for d in dates:
            vol = repos.get(region, {}).get(d, None)
            if vol is not None:
                series.append({"date": d, "volume": vol})
        repo_series[region] = series

    return {
        "price_dates": price_dates,
        "repo_dates": dates,
        "prices": price_series,
        "indices": index_series,
        "repos": repo_series,
    }

"""
market_data.py
==============
Loads 2-year market data from local CSVs:
  - S&P 500       → data/S&P_20-26.csv
                    Date (yyyy-mm-dd), Close (float)
  - Euro Stoxx 50 → data/Euro Stoxx 50 Historical Results Price Data.csv
                    Date (dd/mm/yyyy), Change % (x.xx%)
  - GBP to USD    → data/GBP to USD Historical Exchage Rates.csv
                    Date (dd/mm/yyyy), Change % (x.xx%)

Public API
----------
    from market_data import load_market_data
    market = load_market_data()        # dict — drop into output["market_data"]
"""

import csv
import os
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Paths (relative to the script / preprocess.py location)
# ---------------------------------------------------------------------------

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")

SP500_FILE      = os.path.join(DATA_DIR, "S&P_20-26.csv")
STOXX_FILE      = os.path.join(DATA_DIR, "Euro Stoxx 50 Historical Results Price Data.csv")
GBPUSD_FILE     = os.path.join(DATA_DIR, "GBP to USD Historical Exchage Rates.csv")

CUTOFF = datetime.today() - timedelta(days=2 * 365)


# ---------------------------------------------------------------------------
# Private helpers
# ---------------------------------------------------------------------------

def _parse_date_iso(raw: str) -> datetime | None:
    """Parse yyyy-mm-dd dates (S&P CSV)."""
    raw = raw.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _parse_date_dmy(raw: str) -> datetime | None:
    """Parse dd/mm/yyyy dates (Euro Stoxx / GBP-USD CSVs)."""
    raw = raw.strip()
    for fmt in ("%d/%m/%Y", "%d-%m-%Y"):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    return None


def _parse_pct(raw: str) -> float | None:
    """
    Convert a change-% string to a plain float.
    Handles:  '1.23%'  '-0.45%'  '1.23'  '-0.45'
    """
    raw = raw.strip().replace("%", "").replace(",", ".")
    try:
        return round(float(raw), 4)
    except ValueError:
        return None


def _find_col(headers: list[str], candidates: list[str]) -> str | None:
    """Case-insensitive column name lookup."""
    lower = [h.lower().strip() for h in headers]
    for c in candidates:
        if c.lower() in lower:
            return headers[lower.index(c.lower())]
    return None


# ---------------------------------------------------------------------------
# Loaders
# ---------------------------------------------------------------------------

def _load_sp500() -> list[dict]:
    """
    Returns list of:
        {
            "date": "yyyy-mm-dd",
            "close": float,
            "change_pct": float | None
        }
    sorted ascending, filtered to last 2 years.
    """
    rows = []
    cutoff_with_lookback = CUTOFF - timedelta(days=5)  # grab one prior trading day
    print("Loading S&P 500 market data...")

    with open(SP500_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        date_col = _find_col(reader.fieldnames, ["Date", "date"])
        close_col = _find_col(reader.fieldnames, ["Close", "close", "Price", "price"])
        if not date_col or not close_col:
            raise ValueError(
                f"S&P CSV: could not find Date/Close columns. "
                f"Found: {reader.fieldnames}"
            )

        for row in reader:
            dt = _parse_date_iso(row[date_col])
            if dt is None or dt < cutoff_with_lookback:
                continue
            try:
                close = round(float(row[close_col].replace(",", "")), 2)
            except ValueError:
                continue
            rows.append({"date": dt.strftime("%Y-%m-%d"), "close": close, "_dt": dt})

    # Sort ascending
    rows.sort(key=lambda r: r["date"])

    # --- NEW: compute daily percentage change ---
    prev_close = None
    for r in rows:
        if prev_close is None:
            r["change_pct"] = None
        else:
            r["change_pct"] = round((r["close"] - prev_close) / prev_close*100, 4)
        prev_close = r["close"]

    return rows


def _load_stoxx50() -> list[dict]:
    """
    Returns list of:
        {"date": "dd/mm/yyyy", "change_pct": float}
    sorted ascending, filtered to last 2 years.
    """
    rows = []
    with open(STOXX_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        date_col   = _find_col(reader.fieldnames, ["Date", "date"])
        change_col = _find_col(
            reader.fieldnames,
            ["Change %", "change %", "Change%", "change%", "Chg%", "chg%", "Change"],
        )

        if not date_col or not change_col:
            raise ValueError(
                f"Euro Stoxx CSV: could not find Date/Change% columns. "
                f"Found: {reader.fieldnames}"
            )

        for row in reader:
            dt = _parse_date_dmy(row[date_col])
            if dt is None or dt < CUTOFF:
                continue
            pct = _parse_pct(row[change_col])
            if pct is None:
                continue
            rows.append({"date": dt.strftime("%d/%m/%Y"), "change_pct": pct})

    rows.sort(key=lambda r: datetime.strptime(r["date"], "%d/%m/%Y"))
    return rows


def _load_gbpusd() -> list[dict]:
    """
    Returns list of:
        {"date": "dd/mm/yyyy", "change_pct": float}
    sorted ascending, filtered to last 2 years.
    """
    rows = []
    with open(GBPUSD_FILE, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        date_col   = _find_col(reader.fieldnames, ["Date", "date"])
        change_col = _find_col(
            reader.fieldnames,
            ["Change %", "change %", "Change%", "change%", "Chg%", "chg%", "Change"],
        )

        if not date_col or not change_col:
            raise ValueError(
                f"GBP/USD CSV: could not find Date/Change% columns. "
                f"Found: {reader.fieldnames}"
            )

        for row in reader:
            dt = _parse_date_dmy(row[date_col])
            if dt is None or dt < CUTOFF:
                continue
            pct = _parse_pct(row[change_col])
            if pct is None:
                continue
            rows.append({"date": dt.strftime("%d/%m/%Y"), "change_pct": pct})

    rows.sort(key=lambda r: datetime.strptime(r["date"], "%d/%m/%Y"))
    return rows


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def load_market_data() -> dict:
    """
    Load all three market data sources and return a unified dict:

        {
            "sp500": [
                {"date": "2024-03-10", "close": 5123.41},
                ...
            ],
            "euro_stoxx_50": [
                {"date": "10/03/2024", "change_pct": -0.42},
                ...
            ],
            "gbp_usd": [
                {"date": "10/03/2024", "change_pct": 0.31},
                ...
            ],
            "meta": {
                "sp500_count": 504,
                "euro_stoxx_count": 502,
                "gbp_usd_count": 502,
                "period_start": "2024-03-10",
                "period_end":   "2026-03-10"
            }
        }

    Raises FileNotFoundError / ValueError with a clear message if a CSV
    is missing or has unexpected column names.
    """
    print("  Loading S&P 500 …")
    sp500 = _load_sp500()
    print(f"    → {len(sp500)} rows")

    print("  Loading Euro Stoxx 50 …")
    stoxx = _load_stoxx50()
    print(f"    → {len(stoxx)} rows")

    print("  Loading GBP/USD …")
    gbpusd = _load_gbpusd()
    print(f"    → {len(gbpusd)} rows")

    # Derive overall period from S&P (ISO dates, easy to compare)
    period_start = sp500[0]["date"]  if sp500  else "N/A"
    period_end   = sp500[-1]["date"] if sp500  else "N/A"

    return {
        "sp500":         sp500,
        "euro_stoxx_50": stoxx,
        "gbp_usd":       gbpusd,
        "meta": {
            "sp500_count":      len(sp500),
            "euro_stoxx_count": len(stoxx),
            "gbp_usd_count":    len(gbpusd),
            "period_start":     period_start,
            "period_end":       period_end,
        },
    }

def main():
    print("=" * 60)
    print("UK Lending Risk Dashboard - Data Preprocessing")
    print("=" * 60)

    # Load data
    prices, indices = load_uk_hpi()
    repos = load_repossessions()
    deprivation, la_data = load_deprivation()
    epc_data, epc_by_region = load_epc()

    # Compute risk scores
    risk_results = risk_model(prices, repos, deprivation)
    print(risk_results)

    # Backtest
    backtest = compute_backtest(prices, repos, risk_results)

    # Time series for charts
    time_series = build_time_series(prices, indices, repos)

    market_data = load_market_data()

    # Capital allocation (normalized opportunity scores)
    scoring_regions = [r for r in REGIONS if r not in ["England", "Wales"]]
    total_opportunity = sum(risk_results[r]["opportunity_score"] for r in scoring_regions)
    capital_allocation = {}
    for region in scoring_regions:
        capital_allocation[region] = round(
            risk_results[region]["opportunity_score"] / total_opportunity * 100, 2
        )

    # Assemble output
    output = {
        "metadata": {
            "generated_at": datetime.now().isoformat(),
            "data_sources": [
                "UK-HPI-full-file-2025-12.csv",
                "Repossession-2025-12.csv",
                "IoD2025 Local Authority District Summaries",
                "AtomBank_Nationwide_EPC_Risk1.csv",
            ],
            "regions": REGIONS,
            "scoring_regions": scoring_regions,
            "risk_weights": {"repos": 0.40, "hpi": 0.30, "deprivation": 0.30},
        },
        "risk_scores": risk_results,
        "deprivation": deprivation,
        "backtest": backtest,
        "capital_allocation": capital_allocation,
        "time_series": time_series,
        "market_data": market_data,
        "epc": {
            "global": epc_data,
            "by_region": epc_by_region,
        },
    }

    # Write JSON
    output = sanitize_inf_nan(output)
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    file_size = round(len(json.dumps(output, default=str)) / 1024 / 1024, 2)
    print(f"\n{'=' * 60}")
    print(f"Output: {OUTPUT_FILE} ({file_size} MB)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
