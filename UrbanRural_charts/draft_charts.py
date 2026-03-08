import os
from pathlib import Path

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.ticker import MaxNLocator

# ─────────────────────────────────────────────
# GLOBAL STYLE
# ─────────────────────────────────────────────

BACKGROUND = "#f7f9fc"

CLASSIFICATION_COLOURS = {
    "MU": "#1a3a5c",
    "LU": "#1e6fa5",
    "OU": "#4aa3d9",
    "ST": "#6dbf82",
    "RT": "#a8d08d",
    "SR": "#e0b96e",
    "PR": "#d96c3c",
}

URBAN_STACK_COLOURS = {
    "Major Urban": "#1a3a5c",
    "Large Urban": "#1e6fa5",
    "Other Urban": "#4aa3d9",
    "Large Market Town": "#6dbf82",
    "Rural Town": "#a8d08d",
    "Village": "#e0b96e",
    "Dispersed": "#d96c3c",
}

CHART_DIR = Path("/Users/pavithra_govinda_raj/Git/DataScienceInTheWild/UrbanRural_charts")
CHART_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# DATA LOADING
# ─────────────────────────────────────────────

def load_data(dataset1: str, dataset2: str) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Load dataset1 (Excel) and dataset2 (CSV) and clean numeric columns."""
    data_path = Path("/Users/pavithra_govinda_raj/Git/DataScienceInTheWild/data")
    
    df1 = pd.read_excel(data_path / dataset1, engine="xlrd")
    df2 = pd.read_csv(data_path / dataset2)
    
    # Clean column names
    df1.columns = (
        df1.columns.str.replace(r"\d+$", "", regex=True)
        .str.replace("\n", " ")
        .str.replace(r"\s+", " ", regex=True)
        .str.strip()
    )
    
    # Ensure numeric columns
    numeric_cols = df1.select_dtypes(include=np.number).columns
    df1[numeric_cols] = df1[numeric_cols].apply(pd.to_numeric, errors="coerce")
    
    # Calculate urban/rural percentages
    df1["Urban%"] = np.where(
        df1["Total Population"] > 0,
        df1["Total Urban Population (excluding Large Market Town population)"] / df1["Total Population"] * 100,
        np.nan
    )
    
    df1["Rural%"] = np.where(
        df1["Total Population"] > 0,
        df1["Total Rural Population (including Large Market Town population)"] / df1["Total Population"] * 100,
        np.nan
    )
    
    return df1, df2


# ─────────────────────────────────────────────
# PLOTTING UTILITIES
# ─────────────────────────────────────────────

def save_fig(fig: plt.Figure, filename: str) -> Path:
    """Save a figure to the CHART_DIR and return the path."""
    path = CHART_DIR / filename
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    return path


# ─────────────────────────────────────────────
# RISK SCATTER
# ─────────────────────────────────────────────

def draw_risk_scatter(df: pd.DataFrame) -> Path:
    """Scatter plot of numerical risk by region."""
    df = df.dropna(subset=["Total Population", "Region", "Numerical classification"])
    
    fig, ax = plt.subplots(figsize=(12, 7), facecolor=BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.grid(True, linestyle="--", alpha=0.5)
    
    regions = df["Region"].astype("category")
    y_pos = regions.cat.codes
    
    norm = plt.Normalize(df["Numerical classification"].min(), df["Numerical classification"].max())
    cmap = plt.get_cmap("RdYlBu_r")
    ax.scatter(df["Total Population"], y_pos, c=cmap(norm(df["Numerical classification"])), s=80, alpha=0.8, edgecolors="white")
    
    ax.set_yticks(range(len(regions.cat.categories)))
    ax.set_yticklabels(regions.cat.categories)
    ax.set_xlabel("Total Population")
    ax.set_ylabel("Region")
    ax.set_title("Numerical Risk by Region", fontsize=12, fontweight="bold")
    
    cbar = fig.colorbar(plt.cm.ScalarMappable(norm=norm, cmap=cmap), ax=ax)
    cbar.set_label("Numerical Classification (Risk)")
    
    return save_fig(fig, "risk_scatter_numerical.png")


# ─────────────────────────────────────────────
# URBAN STACKED BAR
# ─────────────────────────────────────────────

def draw_stacked_bar(df: pd.DataFrame) -> Path:
    """Stacked horizontal bar chart of urban composition by region."""
    fig, ax = plt.subplots(figsize=(12, 8), facecolor=BACKGROUND)
    
    region_df = df.groupby("Region").sum(numeric_only=True)
    totals = region_df["Total Population"].replace({0: np.nan})
    prop_df = pd.DataFrame({label: region_df.get(col, 0) / totals * 100 for label, col in [
        ("Major Urban","Major Urban Population"),
        ("Large Urban","Large Urban Population"),
        ("Other Urban","Other Urban Population"),
        ("Large Market Town","Large Market Town Population"),
        ("Rural Town","Rural Town Population"),
        ("Village","Village Population"),
        ("Dispersed","Dispersed Population"),
    ]}).fillna(0)
    
    y_pos = np.arange(len(prop_df))
    left = np.zeros(len(prop_df))
    
    for label in prop_df.columns:
        ax.barh(y_pos, prop_df[label], left=left, color=URBAN_STACK_COLOURS[label], edgecolor="white", label=label)
        left += prop_df[label]
    
    ax.set_yticks(y_pos)
    ax.set_yticklabels(prop_df.index)
    ax.set_xlim(0, 100)
    ax.set_xlabel("Population Share (%)")
    ax.set_ylabel("Region")
    ax.set_title("Urban Composition by Region", fontsize=12, fontweight="bold")
    ax.legend(title="Urban Type", bbox_to_anchor=(1.02,1), loc="upper left")
    
    return save_fig(fig, "urban_composition.png")


# ─────────────────────────────────────────────
# DATASET 2 CHART
# ─────────────────────────────────────────────

def draw_dataset2_chart(df2: pd.DataFrame, df1: pd.DataFrame) -> Path:
    """Bar chart of educational institutions by region."""
    df2 = df2.rename(columns={df2.columns[0]: "Count of Educational institutions in the region"})
    df2["Count of Educational institutions in the region"] = pd.to_numeric(df2.iloc[:, 0], errors="coerce")
    
    df2 = df2.merge(df1[["Name", "Region"]], left_on=df2.columns[1], right_on="Name", how="left")
    grouped = df2.groupby("Region")["Count of Educational institutions in the region"].sum().sort_values().reset_index()
    
    fig, ax = plt.subplots(figsize=(10, 7), facecolor=BACKGROUND)
    ax.set_facecolor(BACKGROUND)
    ax.grid(True, linestyle="--", alpha=0.5)
    
    ax.barh(grouped["Region"], grouped["Count of Educational institutions in the region"], color="#4aa3d9", alpha=0.8)
    ax.xaxis.set_major_locator(MaxNLocator(integer=True))
    
    for i, v in enumerate(grouped["Count of Educational institutions in the region"]):
        ax.text(v + 0.5, i, str(int(v)), va="center", fontsize=9)
    
    ax.set_xlabel("Count of Educational institutions in the region")
    ax.set_ylabel("Region")
    ax.set_title("Educational Institutions by Region", fontsize=12, fontweight="bold")
    
    return save_fig(fig, "dataset2_bar_chart_by_region.png")


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────

def main():
    dataset1 = "LAClassification-dataset-post0409.xls"
    dataset2 = "LEA_and_ELB_names_and_codes_UK_as_at_04_09.csv"
    
    df1, df2 = load_data(dataset1, dataset2)
    
    files = [
        draw_risk_scatter(df1),
        draw_stacked_bar(df1),
        draw_dataset2_chart(df2, df1)
    ]
    
    print(f"Charts saved in: {CHART_DIR}")
    print("Saved files:")
    for f in files:
        print(f)


if __name__ == "__main__":
    main()