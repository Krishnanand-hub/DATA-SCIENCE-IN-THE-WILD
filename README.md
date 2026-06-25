# UK Lending Risk Dashboard

An interactive analytics dashboard that estimates **regional mortgage-lending risk** across England and Wales by combining house-price, repossession, deprivation, energy-efficiency (EPC) and market data into a single risk view — including a live **Expected Credit Loss (ECL = PD × EAD × LGD)** calculator driven by UK postcodes.

> **Architecture in one line:** a Python batch pipeline pre-computes all metrics into a single JSON file, which a static, framework-free JavaScript front-end loads and visualises. There is no live application server or database — the dashboard is served as static files.

---

## Table of Contents
- [What It Does](#what-it-does)
- [How It Works (Architecture)](#how-it-works-architecture)
- [Tech Stack](#tech-stack)
- [Data Sources](#data-sources)
- [Repository Structure](#repository-structure)
- [Prerequisites](#prerequisites)
- [Installation & Running](#installation--running)
- [Crucial Notes (Read Before Running)](#crucial-notes-read-before-running)
- [The Risk Model](#the-risk-model)
- [The ECL Calculator](#the-ecl-calculator)
- [Known Limitations](#known-limitations)
- [Contributors](#contributors)
- [License](#license)

---

## What It Does

- Aggregates five+ UK datasets to **regional level** (9 English regions + England + Wales).
- Fits a **logistic regression** that maps regional features (recent house-price momentum, deprivation, price level) onto historical repossession tiers, producing a per-region **risk score**.
- Runs a **time-split backtest** (train period vs. post-2023 test period) and reports a Spearman rank correlation as a directional sanity check.
- Derives a **capital-allocation** split from inverse risk scores.
- Renders interactive charts (price trends, repossession trends, global market trends, EPC distribution, risk-factor breakdown) using Chart.js.
- Provides an **Expected Credit Loss calculator**: enter a UK postcode, property value, loan amount and term, and it computes PD, EAD, LGD and the resulting ECL client-side.

---

## How It Works (Architecture)

This is a **two-stage batch pipeline**, not a request/response web app:

```
                 ┌─────────────────────────┐
   CSV files ──► │   preprocess.py (Python) │  ETL + logistic model + backtest
   (Data/)       │  - load & clean CSVs     │
                 │  - fit risk model        │
                 │  - run backtest          │
                 │  - build chart series    │
                 └────────────┬─────────────┘
                              │ writes once
                              ▼
                   dashboard_data.json   ◄── single pre-computed artifact
                              │
                              │ fetched once at page load
                              ▼
                 ┌─────────────────────────┐
   Browser ◄──── │  index.html + app.js     │  static front-end (vanilla JS + Chart.js)
                 │  - renders all charts    │
                 │  - ECL calculator (in JS)│
                 └─────────────────────────┘
```

1. **Build step (offline):** `preprocess.py` reads every CSV in `Data/`, computes all metrics and the risk model, and writes a single `dashboard_data.json`.
2. **Serve step:** a static file server (`python3 -m http.server`) serves the HTML, CSS, JS and the JSON.
3. **Runtime (browser):** `app.js` fetches `dashboard_data.json` **once** into memory and renders everything. The ECL calculator runs entirely in JavaScript against that in-memory data — no further server calls.

---

## Tech Stack

**Data / Modelling (Python)**
- `csv`, `collections`, `datetime`, `math` — manual ETL (no pandas)
- `scikit-learn` — `LogisticRegression`, `StandardScaler`
- `numpy`

**Front-end**
- Vanilla JavaScript (no framework, no build step)
- [Chart.js 4.4.1](https://www.chartjs.org/) (loaded via CDN)
- HTML5 / CSS3 (Inter font via Google Fonts)

**Serving**
- Python's built-in `http.server` (static files only)

---

## Data Sources

| File (in `Data/`) | Source | Used for |
|---|---|---|
| `UK-HPI-full-file-2025-12.csv` | HM Land Registry — UK House Price Index | Regional prices, indices, HPI momentum |
| `Repossession-2025-12.csv` | HM Land Registry | Repossession volumes (model target) |
| `IoD2025 Local Authority District Summaries ... .csv` | Ministry of Housing — Indices of Deprivation 2025 | Regional deprivation scores |
| `AtomBank_Nationwide_EPC_Risk1.csv` | EPC / energy data | Energy-efficiency ratings by region |
| `S&P_20-26.csv` | Market data | Global trends chart |
| `Euro Stoxx 50 Historical Results Price Data.csv` | Market data | Global trends chart |
| `GBP to USD Historical Exchage Rates.csv` | Market data | Global trends chart |

> **Note:** Some of these files are large (one EPC CSV is ~90+ MB). See [Crucial Notes](#crucial-notes-read-before-running).

---

## Repository Structure

```
.
├── Data/                       # All input CSV datasets
├── preprocess.py               # ETL + risk model + backtest → dashboard_data.json
├── dashboard_data.json         # Pre-computed output (regenerated by preprocess.py)
├── index.html                  # Dashboard markup
├── app.js                      # Front-end logic, charts, ECL calculator
├── styles.css                  # Styling
├── image.png                   # Header logo
├── start.sh                    # Convenience script: preprocess + serve
└── README.md
```

---

## Prerequisites

- **Python 3.10+** (the code uses `int | None` style type hints)
- **pip** to install Python dependencies
- A modern web browser
- All CSV files present in `Data/` (the pipeline will fail without them)

Install Python dependencies:

```bash
pip install scikit-learn numpy
```

---

## Installation & Running

### Option A — One command (recommended)

```bash
git clone https://github.com/JosephHall978/DataScienceInTheWild.git
cd DataScienceInTheWild

# install dependencies
pip install scikit-learn numpy

# run preprocessing + start the server
chmod +x start.sh
./start.sh
```

Then open **http://localhost:8000** in your browser.

### Option B — Manual steps

```bash
git clone https://github.com/JosephHall978/DataScienceInTheWild.git
cd DataScienceInTheWild

pip install scikit-learn numpy

# 1) Build the data artifact
python3 preprocess.py        # creates dashboard_data.json

# 2) Serve the static files
python3 -m http.server 8000

# 3) Open the dashboard
#    http://localhost:8000
```

---

## Crucial Notes (Read Before Running)

These are the things most likely to trip you (or anyone cloning the repo) up:

1. **The data folder must be named `Data` (capital D).**
   The housing/EPC loaders read from `Data/`, while the market-data loaders read from `data/`. On macOS (case-insensitive filesystem) this works; on **Linux** it will fail with `FileNotFoundError`. If you hit this, make the folder name consistent in `preprocess.py`. 

2. **You must open the dashboard via the local server, not by double-clicking `index.html`.**
   The front-end uses `fetch('dashboard_data.json')`, which browsers block under the `file://` protocol (CORS). Always use `http://localhost:8000`.

3. **`dashboard_data.json` must exist before the dashboard will load.**
   It is produced by `preprocess.py`. If the page shows an error, run the preprocessing step first.

4. **The input CSVs are large.**
   The pipeline streams them with the standard `csv` module, but the first run can take a little time. Ensure all files in `Data/` are present and uncorrupted.

5. **Port 8000 must be free.**
   If it's in use, run `python3 -m http.server 8080` and open `http://localhost:8080` instead.

---

## The Risk Model

`preprocess.py` fits a **logistic regression** (`scikit-learn`) at the regional level:

- **Features:** recent HPI trend, deprivation score, latest average price (standardised).
- **Target:** a binary label of *above-median repossession rate* across regions during the training window.
- **Output:** each region receives a `risk_score` (probability of being in the higher-repossession tier) and an `opportunity_score` (`1 − risk_score`).

A separate **backtest** trains on data before 2023 and compares the rank ordering against the post-2023 period using a Spearman rank correlation, as a directional check on stability.

> **Honest framing:** the model is fit across a small number of regional observations and is intended as an interpretable, directional risk indicator — not a production-grade default-prediction model. See [Known Limitations](#known-limitations).

---

## The ECL Calculator

Implemented client-side in `app.js`, using the standard credit-risk decomposition:

```
ECL = PD × EAD × LGD
```

- **PD (Probability of Default):** derived from the region's risk score, then adjusted by a banded **LTV** multiplier (higher LTV → higher PD), capped at 10%.
- **EAD (Exposure at Default):** the entered loan amount.
- **LGD (Loss Given Default):** based on a forced-sale recovery discount on the property value, adjusted for HPI trend and regional deprivation, floored at 5% and capped at 70%.

Enter a UK postcode, property value, loan amount and term, and the calculator returns the ECL in pounds plus a PD/EAD/LGD breakdown and a risk gauge.

---

## Known Limitations

- **No back-end / database.** The app is static files plus a pre-computed JSON; it does not serve dynamic requests.
- **Small modelling sample.** The risk model is fit at the regional level on a limited number of observations; treat scores as directional.
- **Postcode → region mapping is prefix-based** and contains overlapping prefixes that can mis-classify some postcodes. It is a heuristic, not an authoritative ONS lookup. 
- **Coverage** is limited to the 9 English regions plus England and Wales; Scotland and Northern Ireland are out of scope.

---

## Contributors

| Name | GitHub |
|---|---|
| Joseph Hall | [@JosephHall978](https://github.com/JosephHall978) |
| Omar Alsubaihi | [@omaralsubaihi](https://github.com/omaralsubaihi) |
| Pavithra Govinda Raj | [@Pavi1hra](https://github.com/Pavi1hra) |
| Abdulqudus Abiri | [@abiriabdul](https://github.com/abiriabdul) |
| Krishnanand Sagar | [@Krishnanand-hub](https://github.com/Krishnanand-hub) |

> The Git history was squashed into a single commit, so the other two contributors listed on the GitHub repository page could not be recovered automatically. **Fill in their names, contributions and GitHub handles above.**

---

