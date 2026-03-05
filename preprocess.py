#!/usr/bin/env python3
"""
UK Lending Risk Dashboard - Data Preprocessing
Aggregates housing data, computes risk scores, and exports JSON for the dashboard.
"""

import csv
import json
import math
from collections import defaultdict
from datetime import datetime

DATA_DIR = "Data"
OUTPUT_FILE = "dashboard_data.json"

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


def load_average_prices():
    """Load and aggregate average prices by region and date."""
    print("Loading average prices...")
    prices = defaultdict(dict)
    filepath = f"{DATA_DIR}/Average-prices-2025-12.csv"

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["Region_Name"]
            if region not in REGIONS:
                continue
            date = row["Date"]
            # Only 2010 onwards for the dashboard
            if date < "2010-01-01":
                continue
            try:
                avg_price = float(row["Average_Price"]) if row["Average_Price"] else None
                annual_change = float(row["Annual_Change"]) if row["Annual_Change"] else None
                monthly_change = float(row["Monthly_Change"]) if row["Monthly_Change"] else None
            except (ValueError, KeyError):
                continue

            prices[region][date] = {
                "price": avg_price,
                "annual_change": annual_change,
                "monthly_change": monthly_change,
            }

    print(f"  Loaded prices for {len(prices)} regions")
    return prices


def load_indices():
    """Load house price indices by region and date."""
    print("Loading price indices...")
    indices = defaultdict(dict)
    filepath = f"{DATA_DIR}/Indices-2025-12.csv"

    with open(filepath, "r") as f:
        reader = csv.DictReader(f)
        for row in reader:
            region = row["Region_Name"]
            if region not in REGIONS:
                continue
            date = row["Date"]
            if date < "2010-01-01":
                continue
            try:
                index_val = float(row["Index"]) if row["Index"] else None
            except (ValueError, KeyError):
                continue
            indices[region][date] = index_val

    print(f"  Loaded indices for {len(indices)} regions")
    return indices


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


def compute_risk_scores(prices, indices, repos, deprivation):
    """Compute lending risk scores per region."""
    print("Computing risk scores...")

    # Get common date range (repos data: 2016-2025)
    all_repo_dates = set()
    for region_dates in repos.values():
        all_repo_dates.update(region_dates.keys())
    repo_date_range = sorted(all_repo_dates)

    # Split for backtest
    train_cutoff = "2023-01-01"
    train_dates = [d for d in repo_date_range if d < train_cutoff]
    test_dates = [d for d in repo_date_range if d >= train_cutoff]

    # Exclude aggregate regions for scoring (England, Wales are aggregates of the sub-regions)
    scoring_regions = [r for r in REGIONS if r not in ["England", "Wales"]]

    risk_results = {}

    for region in scoring_regions:
        # 1. Repo intensity (average monthly repos)
        train_repos = [repos[region].get(d, 0) for d in train_dates if d in repos.get(region, {})]
        test_repos = [repos[region].get(d, 0) for d in test_dates if d in repos.get(region, {})]
        all_repos = [repos[region].get(d, 0) for d in repo_date_range if d in repos.get(region, {})]

        avg_repos_train = sum(train_repos) / max(len(train_repos), 1)
        avg_repos_test = sum(test_repos) / max(len(test_repos), 1)
        avg_repos_all = sum(all_repos) / max(len(all_repos), 1)
        total_repos = sum(all_repos)

        # 2. HPI momentum (average annual change in test period)
        recent_prices = {}
        for d in repo_date_range:
            if d in prices.get(region, {}):
                recent_prices[d] = prices[region][d]

        annual_changes = [v["annual_change"] for v in recent_prices.values()
                         if v["annual_change"] is not None]
        avg_annual_change = sum(annual_changes) / max(len(annual_changes), 1) if annual_changes else 0

        # Recent HPI trend (last 12 months)
        recent_changes = []
        for d in sorted(recent_prices.keys())[-12:]:
            if recent_prices[d]["annual_change"] is not None:
                recent_changes.append(recent_prices[d]["annual_change"])
        recent_hpi_trend = sum(recent_changes) / max(len(recent_changes), 1) if recent_changes else 0

        # 3. Deprivation score
        dep_score = deprivation.get(region, {}).get("deprivation_score", 0.5)

        # 4. Latest price
        latest_dates = sorted(prices.get(region, {}).keys())
        latest_price = prices[region][latest_dates[-1]]["price"] if latest_dates else None

        risk_results[region] = {
            "avg_repos_train": round(avg_repos_train, 2),
            "avg_repos_test": round(avg_repos_test, 2),
            "avg_repos_all": round(avg_repos_all, 2),
            "total_repos": total_repos,
            "avg_annual_hpi_change": round(avg_annual_change, 2),
            "recent_hpi_trend": round(recent_hpi_trend, 2),
            "deprivation_score": dep_score,
            "latest_price": latest_price,
        }

    # Normalize factors across regions
    all_repos_vals = [r["avg_repos_all"] for r in risk_results.values()]
    all_dep_vals = [r["deprivation_score"] for r in risk_results.values()]
    all_hpi_vals = [r["recent_hpi_trend"] for r in risk_results.values()]

    max_repos = max(all_repos_vals) if all_repos_vals else 1
    min_repos = min(all_repos_vals) if all_repos_vals else 0
    max_dep = max(all_dep_vals) if all_dep_vals else 1
    min_dep = min(all_dep_vals) if all_dep_vals else 0
    max_hpi = max(all_hpi_vals) if all_hpi_vals else 1
    min_hpi = min(all_hpi_vals) if all_hpi_vals else 0

    for region, data in risk_results.items():
        # Normalize 0-1
        norm_repos = (data["avg_repos_all"] - min_repos) / max(max_repos - min_repos, 0.001)
        norm_dep = (data["deprivation_score"] - min_dep) / max(max_dep - min_dep, 0.001)
        # HPI: lower trend = higher risk, so invert
        hpi_range = max(max_hpi - min_hpi, 0.001)
        norm_hpi_risk = 1 - ((data["recent_hpi_trend"] - min_hpi) / hpi_range)

        # Weighted risk score (0=safest, 1=riskiest)
        w_repos = 0.40
        w_hpi = 0.30
        w_dep = 0.30
        risk_score = w_repos * norm_repos + w_hpi * norm_hpi_risk + w_dep * norm_dep

        data["norm_repos"] = round(norm_repos, 4)
        data["norm_hpi_risk"] = round(norm_hpi_risk, 4)
        data["norm_deprivation"] = round(norm_dep, 4)
        data["risk_score"] = round(risk_score, 4)

        # Capital allocation (inverse of risk)
        data["opportunity_score"] = round(1 - risk_score, 4)

    # Rank by risk
    sorted_by_risk = sorted(risk_results.items(), key=lambda x: x[1]["risk_score"], reverse=True)
    for rank, (region, data) in enumerate(sorted_by_risk, 1):
        data["risk_rank"] = rank

    print(f"  Computed risk scores for {len(risk_results)} regions")
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


def main():
    print("=" * 60)
    print("UK Lending Risk Dashboard - Data Preprocessing")
    print("=" * 60)

    # Load data
    prices = load_average_prices()
    indices = load_indices()
    repos = load_repossessions()
    deprivation, la_data = load_deprivation()

    # Compute risk scores
    risk_results = compute_risk_scores(prices, indices, repos, deprivation)

    # Backtest
    backtest = compute_backtest(prices, repos, risk_results)

    # Time series for charts
    time_series = build_time_series(prices, indices, repos)

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
                "Average-prices-2025-12.csv",
                "Indices-2025-12.csv",
                "Repossession-2025-12.csv",
                "IoD2025 Local Authority District Summaries",
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
    }

    # Write JSON
    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    file_size = round(len(json.dumps(output, default=str)) / 1024 / 1024, 2)
    print(f"\n{'=' * 60}")
    print(f"Output: {OUTPUT_FILE} ({file_size} MB)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
