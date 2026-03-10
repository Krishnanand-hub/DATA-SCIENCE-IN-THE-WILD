/**
 * UK Lending Risk Dashboard - Frontend Application
 */

// Color palette for regions
const REGION_COLORS = {
    'North West': 'rgba(239, 68, 68, 0.8)',
    'Yorkshire and The Humber': 'rgba(249, 115, 22, 0.8)',
    'North East': 'rgba(245, 158, 11, 0.8)',
    'West Midlands Region': 'rgba(234, 179, 8, 0.8)',
    'East Midlands': 'rgba(132, 204, 22, 0.8)',
    'South West': 'rgba(16, 185, 129, 0.8)',
    'London': 'rgba(6, 182, 212, 0.8)',
    'East of England': 'rgba(99, 102, 241, 0.8)',
    'South East': 'rgba(139, 92, 246, 0.8)',
    'England': 'rgba(148, 163, 184, 0.5)',
    'Wales': 'rgba(100, 116, 139, 0.5)',
};

const REGION_COLORS_SOLID = {
    'North West': '#ef4444',
    'Yorkshire and The Humber': '#f97316',
    'North East': '#f59e0b',
    'West Midlands Region': '#eab308',
    'East Midlands': '#84cc16',
    'South West': '#10b981',
    'London': '#06b6d4',
    'East of England': '#6366f1',
    'South East': '#8b5cf6',
    'England': '#94a3b8',
    'Wales': '#64748b',
};

// Chart.js global defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";
Chart.defaults.font.size = 11;
Chart.defaults.plugins.legend.labels.usePointStyle = true;
Chart.defaults.plugins.legend.labels.pointStyleWidth = 10;

let dashboardData = null;
let charts = {};

async function init() {
    try {
        const res = await fetch('dashboard_data.json');
        if (!res.ok) {
            throw new Error(`HTTP ${res.status}: ${res.statusText}`);
        }
        dashboardData = await res.json();
        renderAll();
    } catch (err) {
        console.error('Failed to load data:', err);
        const errorMsg = `Failed to load dashboard_data.json: ${err.message}. 
        Ensure you are in the Dashboard directory and run: 
        1) python3 preprocess.py 
        2) python3 -m http.server 8000`;
        document.body.innerHTML = `<div style="color:#ef4444;text-align:center;padding:60px;font-size:1rem;white-space:pre-wrap;font-family:monospace;">${errorMsg}</div>`;
    }
}

function renderAll() {
    renderHeader();
    renderRiskCards();
    renderPriceChart();
    renderRepoChart();
    renderGlobalTrend();
    renderValidation();
    renderCapitalChart();
    renderFactorChart();
    renderTable();
    setupControls();
}

// ─── Header ───
function renderHeader() {
    const genDate = new Date(dashboardData.metadata.generated_at);
    const now = new Date();
    const daysAgo = Math.floor((now - genDate) / (1000 * 60 * 60 * 24));

    let dateStr;
    if (daysAgo === 0) {
        const hoursAgo = Math.floor((now - genDate) / (1000 * 60 * 60));
        dateStr = hoursAgo === 0 ? 'Updated now' : `Updated ${hoursAgo}h ago`;
    } else {
        dateStr = `Updated ${daysAgo}d ago`;
    }

    const genDateElement = document.getElementById('gen-date');
    if (genDateElement) genDateElement.textContent = dateStr;
}

// Helper: Calculate 12-month trend for a region
function computeRegionTrend(region) {
    const repoTs = dashboardData.time_series.repos[region] || [];
    const priceTs = dashboardData.time_series.prices[region] || [];

    // Repo trend: compare recent 3 months to prior 3 months
    let repoTrend = 0;
    if (repoTs.length > 6) {
        const recent = repoTs.slice(-3).reduce((sum, d) => sum + (d.volume || 0), 0) / 3;
        const prior = repoTs.slice(-6, -3).reduce((sum, d) => sum + (d.volume || 0), 0) / 3;
        repoTrend = prior > 0 ? ((recent - prior) / prior) * 100 : 0;
    }

    // HPI trend: 12-month price change
    let hpiTrend = 0;
    if (priceTs.length > 12) {
        const recent = priceTs[priceTs.length - 1].price;
        const yearAgo = priceTs[priceTs.length - 12].price;
        hpiTrend = yearAgo > 0 ? ((recent - yearAgo) / yearAgo) * 100 : 0;
    }

    return { repos: repoTrend, hpi: hpiTrend };
}

// ─── Risk Cards ───
function renderRiskCards() {
    const container = document.getElementById('risk-cards-container');
    if (!container) return;

    const scores = dashboardData.risk_scores;
    const regions = Object.keys(scores).sort((a, b) => scores[a].risk_rank - scores[b].risk_rank);

    container.innerHTML = regions.map(region => {
        const d = scores[region];
        const score = d.risk_score;
        const riskClass = score > 0.6 ? 'risk-high' : score > 0.35 ? 'risk-medium' : 'risk-low';
        const price = d.latest_price ? `£${Math.round(d.latest_price).toLocaleString()}` : '—';

        // Get trend indicators
        const trend = computeRegionTrend(region);
        const repoArrow = trend.repos > 1 ? '↑' : trend.repos < -1 ? '↓' : '→';
        const repoArrowClass = trend.repos > 1 ? 'trend-up' : trend.repos < -1 ? 'trend-down' : 'trend-stable';
        const hpiArrow = trend.hpi > 1 ? '↑' : trend.hpi < -1 ? '↓' : '→';
        const hpiArrowClass = trend.hpi > 1 ? 'trend-up' : trend.hpi < -1 ? 'trend-down' : 'trend-stable';

        return `
            <div class="risk-card ${riskClass}">
                <div class="risk-card-timestamp">Data: <span class="timestamp-dot"></span></div>
                <div class="risk-card-rank">#${d.risk_rank} Risk</div>
                <div class="risk-card-region">${region}</div>
                <div class="risk-card-score">${(score * 100).toFixed(0)}</div>
                <div class="risk-card-detail">
                    <span class="metric-item">
                        Repos: ${d.avg_repos_all.toFixed(0)}/mo
                        <span class="trend-arrow ${repoArrowClass}">${repoArrow}</span>
                    </span>
                    •
                    <span class="metric-item">
                        HPI: ${d.recent_hpi_trend > 0 ? '+' : ''}${d.recent_hpi_trend.toFixed(1)}%
                        <span class="trend-arrow ${hpiArrowClass}">${hpiArrow}</span>
                    </span>
                </div>
                <div class="risk-card-price">Avg Price: ${price}</div>
            </div>
        `;
    }).join('');
}

// ─── House Price Chart ───
function renderPriceChart(selectedRegion = 'all') {
    const canvas = document.getElementById('price-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (charts.price) charts.price.destroy();

    const ts = dashboardData.time_series.prices;
    const allDates = dashboardData.time_series.price_dates;

    const regionsToShow = selectedRegion === 'all'
        ? dashboardData.metadata.scoring_regions
        : [selectedRegion];

    // Build central labels array to match chart ticks
    const labels = selectedRegion === 'all'
        ? allDates.filter((_, i) => i % 3 === 0)
        : allDates;

    // Downsample: take every 3rd data point for performance when showing all
    const datasets = regionsToShow.map(region => {
        const data = ts[region] || [];
        const sampled = selectedRegion === 'all'
            ? data.filter((_, i) => i % 3 === 0)
            : data;

        return {
            label: region,
            data: sampled.map(d => d.price),
            borderColor: REGION_COLORS_SOLID[region],
            backgroundColor: REGION_COLORS[region],
            borderWidth: selectedRegion === 'all' ? 1.5 : 2.5,
            pointRadius: 0,
            tension: 0.3,
            fill: selectedRegion !== 'all',
        };
    });

    charts.price = new Chart(ctx, {
        type: 'line',
        data: { labels, datasets },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    display: regionsToShow.length <= 9,
                    position: 'top',
                    labels: { boxWidth: 12, padding: 10, font: { size: 10 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    borderColor: 'rgba(100, 120, 180, 0.3)',
                    borderWidth: 1,
                    titleFont: { weight: '600' },
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: £${Math.round(ctx.parsed.y).toLocaleString()}`
                    }
                }
            },
            scales: {
                x: {
                    type: 'category',
                    grid: { color: 'rgba(100, 120, 180, 0.08)' },
                    ticks: {
                        maxTicksLimit: 12,
                        callback: function (val) {
                            const label = this.getLabelForValue(val);
                            return label ? label.substring(0, 7) : '';
                        }
                    }
                },
                y: {
                    grid: { color: 'rgba(100, 120, 180, 0.08)' },
                    ticks: {
                        callback: val => '£' + (val >= 1000 ? Math.round(val / 1000) + 'k' : val)
                    }
                }
            }
        }
    });
}


function renderGlobalTrend() {
    const canvas = document.getElementById('global-trend');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');

    // Destroy existing chart instance to prevent overlaying
    if (charts.globalTrend) charts.globalTrend.destroy();

    // ─── 1. Data Processing ──────────────────────────────────────────────────
    const md = dashboardData?.market_data;
    if (!md) return;

    function toISO(dateStr) {
        if (!dateStr) return null;
        if (/^\d{4}-\d{2}-\d{2}$/.test(dateStr)) return dateStr;
        const [d, m, y] = dateStr.split("/");
        return `${y}-${m.padStart(2, "0")}-${d.padStart(2, "0")}`;
    }

    function toChangePctMap(records) {
        const map = new Map();
        for (const r of records) {
            const iso = toISO(r.date);
            if (iso && r.change_pct != null) map.set(iso, r.change_pct);
        }
        return map;
    }

    function cumulativeIndex(dates, changePctMap) {
        let level = 100;
        return dates.map(d => {
            const pct = changePctMap.get(d);
            if (pct != null) level = level * (1 + pct / 100);
            return level;
        });
    }

    const sp500Map = toChangePctMap(md.sp500 || []);
    const stoxxMap = toChangePctMap(md.euro_stoxx_50 || []);
    const gbpMap = toChangePctMap(md.gbp_usd || []);

    const allDates = [...new Set([
        ...sp500Map.keys(),
        ...stoxxMap.keys(),
        ...gbpMap.keys(),
    ])].sort();

    // ─── 2. Chart.js Implementation ──────────────────────────────────────────
    charts.globalTrend = new Chart(ctx, {
        type: 'line',
        data: {
            labels: allDates,
            datasets: [
                {
                    label: 'S&P 500',
                    data: cumulativeIndex(allDates, sp500Map),
                    borderColor: '#4fffb0',
                    backgroundColor: 'rgba(79, 255, 176, 0.1)',
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3
                },
                {
                    label: 'Euro Stoxx 50',
                    data: cumulativeIndex(allDates, stoxxMap),
                    borderColor: '#ff6b6b',
                    borderDash: [6, 3],
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3
                },
                {
                    label: 'GBP / USD',
                    data: cumulativeIndex(allDates, gbpMap),
                    borderColor: '#4db8ff',
                    borderDash: [2, 4],
                    borderWidth: 2,
                    pointRadius: 0,
                    tension: 0.3
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: { mode: 'index', intersect: false },
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 15, padding: 15, font: { size: 11 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    borderColor: 'rgba(100, 120, 180, 0.3)',
                    borderWidth: 1,
                    callbacks: {
                        label: (ctx) => `${ctx.dataset.label}: ${(ctx.parsed.y - 100).toFixed(2)}%`
                    }
                }
            },
            scales: {
                x: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    ticks: {
                        maxTicksLimit: 8,
                        callback: function(val) {
                            const date = this.getLabelForValue(val);
                            return date ? date.substring(2, 7) : ''; // Returns YY-MM
                        }
                    }
                },
                y: {
                    grid: { color: 'rgba(255, 255, 255, 0.05)' },
                    title: { display: true, text: 'Cumulative % Return', color: '#5a6070' },
                    ticks: {
                        callback: (val) => `${(val - 100).toFixed(0)}%`
                    }
                }
            }
        }
    });
}

// ─── Repossession Chart ───
function renderRepoChart(selectedRegion = 'all') {
    const canvas = document.getElementById('repo-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (charts.repo) charts.repo.destroy();

    const ts = dashboardData.time_series.repos;
    const regionsToShow = selectedRegion === 'all'
        ? dashboardData.metadata.scoring_regions.filter(r => r !== 'England' && r !== 'Wales')
        : [selectedRegion];

    if (selectedRegion === 'all') {
        // Stacked area chart
        const allDates = [...new Set(
            regionsToShow.flatMap(r => (ts[r] || []).map(d => d.date))
        )].sort();

        const datasets = regionsToShow.map(region => {
            const dataMap = {};
            (ts[region] || []).forEach(d => dataMap[d.date] = d.volume);

            return {
                label: region,
                data: allDates.map(d => dataMap[d] || 0),
                borderColor: REGION_COLORS_SOLID[region],
                backgroundColor: REGION_COLORS[region],
                borderWidth: 1,
                pointRadius: 0,
                tension: 0.3,
                fill: true,
            };
        });

        charts.repo = new Chart(ctx, {
            type: 'line',
            data: { labels: allDates, datasets },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                interaction: { mode: 'index', intersect: false },
                plugins: {
                    legend: {
                        position: 'top',
                        labels: { boxWidth: 12, padding: 10, font: { size: 10 } }
                    },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        borderColor: 'rgba(100, 120, 180, 0.3)',
                        borderWidth: 1,
                    }
                },
                scales: {
                    x: {
                        grid: { color: 'rgba(100, 120, 180, 0.08)' },
                        ticks: {
                            maxTicksLimit: 12,
                            callback: function (val) {
                                const label = this.getLabelForValue(val);
                                return label ? label.substring(0, 7) : '';
                            }
                        }
                    },
                    y: {
                        stacked: true,
                        grid: { color: 'rgba(100, 120, 180, 0.08)' },
                        title: { display: true, text: 'Repossessions', color: '#64748b' }
                    }
                }
            }
        });
    } else {
        // Single region bar chart
        const data = ts[selectedRegion] || [];
        charts.repo = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.date),
                datasets: [{
                    label: selectedRegion,
                    data: data.map(d => d.volume),
                    backgroundColor: REGION_COLORS[selectedRegion],
                    borderColor: REGION_COLORS_SOLID[selectedRegion],
                    borderWidth: 1,
                    borderRadius: 3,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        backgroundColor: 'rgba(15, 23, 42, 0.95)',
                        borderColor: 'rgba(100, 120, 180, 0.3)',
                        borderWidth: 1,
                    }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: {
                            maxTicksLimit: 12,
                            callback: function (val) {
                                const label = this.getLabelForValue(val);
                                return label ? label.substring(0, 7) : '';
                            }
                        }
                    },
                    y: {
                        grid: { color: 'rgba(100, 120, 180, 0.08)' },
                        title: { display: true, text: 'Repossessions', color: '#64748b' }
                    }
                }
            }
        });
    }
}

// ─── Validation Panel ───
function renderValidation() {
    const canvas = document.getElementById('validation-chart');
    const metricsContainer = document.getElementById('validation-metrics');
    if (!canvas || !metricsContainer) return;

    const ctx = canvas.getContext('2d');
    const bt = dashboardData.backtest;

    const spearmanPct1 = (bt.spearman_train_vs_test * 100).toFixed(0);
    const spearmanPct2 = (bt.spearman_risk_vs_test * 100).toFixed(0);

    metricsContainer.innerHTML = `
        <div class="metric-card">
            <div class="metric-label">Repo Rank Consistency</div>
            <div class="metric-value positive">${spearmanPct1}%</div>
            <div class="metric-sub">Spearman ρ (train → test)</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Risk Model Accuracy</div>
            <div class="metric-value ${parseFloat(spearmanPct2) >= 60 ? 'positive' : 'neutral'}">${spearmanPct2}%</div>
            <div class="metric-sub">Spearman ρ (model → actual)</div>
        </div>
    `;

    if (charts.validation) charts.validation.destroy();

    const regions = Object.keys(bt.regions);
    const scatterData = regions.map(r => ({
        x: bt.regions[r].risk_rank,
        y: bt.regions[r].test_rank,
        label: r,
    }));

    charts.validation = new Chart(ctx, {
        type: 'scatter',
        data: {
            datasets: [
                {
                    label: 'Risk Rank vs Actual Repo Rank',
                    data: scatterData,
                    backgroundColor: regions.map(r => REGION_COLORS_SOLID[r] || '#6366f1'),
                    pointRadius: 8,
                    pointHoverRadius: 12,
                },
                {
                    label: 'Perfect Prediction',
                    data: [{ x: 1, y: 1 }, { x: 9, y: 9 }],
                    type: 'line',
                    borderColor: 'rgba(100, 120, 180, 0.3)',
                    borderDash: [5, 5],
                    borderWidth: 1,
                    pointRadius: 0,
                    fill: false,
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    borderColor: 'rgba(100, 120, 180, 0.3)',
                    borderWidth: 1,
                    callbacks: {
                        label: ctx => {
                            if (ctx.raw.label) {
                                return `${ctx.raw.label}: Risk Rank ${ctx.raw.x}, Actual ${ctx.raw.y}`;
                            }
                            return '';
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: { display: true, text: 'Model Risk Rank', color: '#64748b' },
                    grid: { color: 'rgba(100, 120, 180, 0.08)' },
                    min: 0.5, max: 9.5,
                    ticks: { stepSize: 1 }
                },
                y: {
                    title: { display: true, text: 'Actual Repo Rank (2023–25)', color: '#64748b' },
                    grid: { color: 'rgba(100, 120, 180, 0.08)' },
                    min: 0.5, max: 9.5,
                    reverse: false,
                    ticks: { stepSize: 1 }
                }
            }
        }
    });
}

// ─── Capital Allocation ───
function renderCapitalChart() {
    const canvas = document.getElementById('capital-chart');
    if (!canvas) return;

    const ctx = canvas.getContext('2d');
    if (charts.capital) charts.capital.destroy();

    const alloc = dashboardData.capital_allocation;
    const sorted = Object.entries(alloc).sort((a, b) => b[1] - a[1]);
    const labels = sorted.map(([r]) => r);
    const data = sorted.map(([, v]) => v);

    charts.capital = new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels,
            datasets: [{
                data,
                backgroundColor: labels.map(r => REGION_COLORS_SOLID[r] || '#6366f1'),
                borderColor: 'rgba(10, 14, 26, 0.8)',
                borderWidth: 2,
                hoverBorderColor: '#e2e8f0',
                hoverOffset: 8,
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            cutout: '55%',
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12,
                        padding: 12,
                        font: { size: 11 },
                        generateLabels: chart => {
                            const data = chart.data;
                            return data.labels.map((label, i) => ({
                                text: `${label} (${data.datasets[0].data[i].toFixed(1)}%)`,
                                fillStyle: data.datasets[0].backgroundColor[i],
                                strokeStyle: data.datasets[0].backgroundColor[i],
                                lineWidth: 0,
                                pointStyle: 'circle',
                                index: i,
                            }));
                        }
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    borderColor: 'rgba(100, 120, 180, 0.3)',
                    borderWidth: 1,
                    callbacks: {
                        label: ctx => `${ctx.label}: ${ctx.parsed.toFixed(1)}% of capital`
                    }
                }
            }
        }
    });
}

// ─── Factor Chart ───
function renderFactorChart() {
    const canvas = document.getElementById('factor-chart');
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (charts.factor) charts.factor.destroy();

    // Convert object → array of [regionName, regionData]
    const entries = Object.entries(dashboardData.risk_scores);

    // Sort by risk_rank
    const sorted = entries.sort((a, b) => a[1].risk_rank - b[1].risk_rank);

    const regions = sorted.map(([name]) => name);
    const scores = sorted.map(([_, data]) => data);

    // Compute relative factor contributions normalized to 100%
    // Since original specific 'contrib_pct' keys don't exist in json
    const maxRepo = Math.max(...scores.map(s => s.avg_repos_all));
    const maxDep = Math.max(...scores.map(s => s.deprivation_score));

    const factorData = scores.map(s => {
        const hpiRisk = Math.max(0, 10 - (s.recent_hpi_trend || 0)); // Inverse trend = higher risk
        const depRisk = ((s.deprivation_score || 0) / maxDep) * 10;
        const repoRisk = ((s.avg_repos_all || 0) / maxRepo) * 10;
        const totalRiskSum = hpiRisk + depRisk + repoRisk || 1;

        return {
            hpiPct: (hpiRisk / totalRiskSum) * 100,
            depPct: (depRisk / totalRiskSum) * 100,
            repoPct: (repoRisk / totalRiskSum) * 100
        };
    });

    charts.factor = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: regions,
            datasets: [
                {
                    label: 'HPI Trend Risk',
                    data: factorData.map(f => f.hpiPct.toFixed(1)),
                    backgroundColor: 'rgba(245, 158, 11, 0.7)',
                    borderColor: '#f59e0b',
                    borderWidth: 1,
                    borderRadius: 2,
                },
                {
                    label: 'Deprivation Risk',
                    data: factorData.map(f => f.depPct.toFixed(1)),
                    backgroundColor: 'rgba(139, 92, 246, 0.7)',
                    borderColor: '#8b5cf6',
                    borderWidth: 1,
                    borderRadius: 2,
                },
                {
                    label: 'Repossession Risk',
                    data: factorData.map(f => f.repoPct.toFixed(1)),
                    backgroundColor: 'rgba(6, 182, 212, 0.7)',
                    borderColor: '#06b6d4',
                    borderWidth: 1,
                    borderRadius: 2,
                },
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                    labels: { boxWidth: 12, padding: 14, font: { size: 11 } }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.95)',
                    borderColor: 'rgba(100, 120, 180, 0.3)',
                    borderWidth: 1,
                    callbacks: {
                        label: ctx => `${ctx.dataset.label}: ${ctx.parsed.y.toFixed(1)}%`
                    }
                }
            },
            scales: {
                x: {
                    stacked: true,
                    grid:  { display: false },
                    ticks: { font: { size: 10 } }
                },
                y: {
                    stacked: true,
                    max: 100,
                    grid:  { color: 'rgba(100, 120, 180, 0.08)' },
                    title: { display: true, text: 'Relative Risk Contribution %', color: '#64748b' },
                }
            }
        }
    });
}

// ─── Summary Table ───
function renderTable() {
    const tbody = document.getElementById('table-body');
    if (!tbody) return;

    const scores = dashboardData.risk_scores;
    const alloc = dashboardData.capital_allocation;
    const regions = Object.keys(scores).sort((a, b) => scores[a].risk_rank - scores[b].risk_rank);

    tbody.innerHTML = regions.map(region => {
        const d = scores[region];
        const score = d.risk_score;
        const badgeClass = score > 0.6 ? 'high' : score > 0.35 ? 'medium' : 'low';
        const price = d.latest_price ? `£${Math.round(d.latest_price).toLocaleString()}` : '—';
        const capitalPct = alloc[region] ? alloc[region].toFixed(1) + '%' : '—';

        return `
            <tr>
                <td>${d.risk_rank}</td>
                <td>${region}</td>
                <td><span class="risk-badge ${badgeClass}">${(score * 100).toFixed(0)}</span></td>
                <td>${d.avg_repos_all.toFixed(1)}</td>
                <td>${d.recent_hpi_trend > 0 ? '+' : ''}${d.recent_hpi_trend.toFixed(1)}%</td>
                <td>${(d.deprivation_score * 100).toFixed(0)}</td>
                <td>${price}</td>
                <td>${capitalPct}</td>
            </tr>
        `;
    }).join('');
}

// ─── Controls ───
function setupControls() {
    const repoSelect = document.getElementById('repo-region-select');
    if (repoSelect) {
        // Populate repo select
        const regions = dashboardData.metadata.scoring_regions;
        regions.forEach(r => {
            repoSelect.innerHTML += `<option value="${r}">${r}</option>`;
        });
        // Add England and Wales
        ['England', 'Wales'].forEach(r => {
            repoSelect.innerHTML += `<option value="${r}">${r}</option>`;
        });

        repoSelect.addEventListener('change', e => renderRepoChart(e.target.value));
    }

    // ECL Calculator: live LTV update
    const propInput = document.getElementById('calc-property-value');
    const loanInput = document.getElementById('calc-loan-amount');
    const postcodeInput = document.getElementById('calc-postcode');
    const ltvValue = document.getElementById('calc-ltv-value');

    function updateLTV() {
        const pv = parseFloat(propInput.value) || 0;
        const la = parseFloat(loanInput.value) || 0;
        const ltv = pv > 0 ? (la / pv * 100) : 0;
        if (ltvValue) ltvValue.textContent = ltv.toFixed(1) + '%';
    }

    if (propInput) propInput.addEventListener('input', updateLTV);
    if (loanInput) loanInput.addEventListener('input', updateLTV);

    // Show region on postcode input
    if (postcodeInput) {
        postcodeInput.addEventListener('input', () => {
            const region = postcodeToRegion(postcodeInput.value);
            const badge = document.getElementById('calc-region-badge');
            if (badge) badge.textContent = region ? `📍 ${region}` : '';
        });

        // Allow Enter key to calculate
        [postcodeInput, propInput, loanInput, document.getElementById('calc-loan-term')].forEach(el => {
            if (el) {
                el.addEventListener('keydown', e => { if (e.key === 'Enter') calculateECL(); });
            }
        });
    }
}

// ─── Postcode → Region Mapping ───
const POSTCODE_TO_REGION = {
    // North East
    'DH': 'North East', 'DL': 'North East', 'NE': 'North East',
    'SR': 'North East', 'TS': 'North East',
    // North West
    'BB': 'North West', 'BL': 'North West', 'CA': 'North West',
    'CH': 'North West', 'CW': 'North West', 'FY': 'North West',
    'L': 'North West', 'LA': 'North West', 'M': 'North West',
    'OL': 'North West', 'PR': 'North West', 'SK': 'North West',
    'WA': 'North West', 'WN': 'North West',
    // Yorkshire and The Humber
    'BD': 'Yorkshire and The Humber', 'DN': 'Yorkshire and The Humber',
    'HD': 'Yorkshire and The Humber', 'HG': 'Yorkshire and The Humber',
    'HU': 'Yorkshire and The Humber', 'HX': 'Yorkshire and The Humber',
    'LS': 'Yorkshire and The Humber', 'S': 'Yorkshire and The Humber',
    'WF': 'Yorkshire and The Humber', 'YO': 'Yorkshire and The Humber',
    // East Midlands
    'DE': 'East Midlands', 'LE': 'East Midlands', 'LN': 'East Midlands',
    'NG': 'East Midlands', 'PE': 'East Midlands',
    // West Midlands
    'B': 'West Midlands Region', 'CV': 'West Midlands Region',
    'DY': 'West Midlands Region', 'HR': 'West Midlands Region',
    'ST': 'West Midlands Region', 'TF': 'West Midlands Region',
    'WR': 'West Midlands Region', 'WS': 'West Midlands Region',
    'WV': 'West Midlands Region',
    // East of England
    'AL': 'East of England', 'CB': 'East of England', 'CM': 'East of England',
    'CO': 'East of England', 'EN': 'East of England', 'HP': 'East of England',
    'IP': 'East of England', 'LU': 'East of England', 'NR': 'East of England',
    'SG': 'East of England', 'SS': 'East of England', 'WD': 'East of England',
    // London
    'E': 'London', 'EC': 'London', 'N': 'London', 'NW': 'London',
    'SE': 'London', 'SW': 'London', 'W': 'London', 'WC': 'London',
    'BR': 'London', 'CR': 'London', 'DA': 'London', 'HA': 'London',
    'IG': 'London', 'KT': 'London', 'RM': 'London', 'SM': 'London',
    'TW': 'London', 'UB': 'London',
    // South East
    'BN': 'South East', 'CT': 'South East', 'GU': 'South East',
    'ME': 'South East', 'MK': 'South East', 'OX': 'South East',
    'PO': 'South East', 'RG': 'South East', 'RH': 'South East',
    'SL': 'South East', 'SO': 'South East', 'TN': 'South East',
    // South West
    'BA': 'South West', 'BH': 'South West', 'BS': 'South West',
    'DT': 'South West', 'EX': 'South West', 'GL': 'South West',
    'PL': 'South West', 'SN': 'South West', 'SP': 'South West',
    'TA': 'South West', 'TQ': 'South West', 'TR': 'South West',
    // Wales
    'CF': 'Wales', 'LL': 'Wales', 'LD': 'Wales', 'NP': 'Wales',
    'SA': 'Wales', 'SY': 'Wales',
    // Additional common codes
    'NN': 'East Midlands'
};

function postcodeToRegion(postcode) {
    if (!postcode) return null;
    const cleaned = postcode.toUpperCase().replace(/\s+/g, '');
    // Try 2-letter area first, then 1-letter
    const area2 = cleaned.substring(0, 2).replace(/[0-9]/g, '');
    const area1 = cleaned.substring(0, 1);

    return POSTCODE_TO_REGION[area2] || POSTCODE_TO_REGION[area1] || null;
}

// ─── ECL Calculator ───
function calculateECL() {
    const postcode = document.getElementById('calc-postcode').value.trim();
    const propertyValue = parseFloat(document.getElementById('calc-property-value').value);
    const loanAmount = parseFloat(document.getElementById('calc-loan-amount').value);
    const loanTerm = parseFloat(document.getElementById('calc-loan-term').value);
    const resultsDiv = document.getElementById('calc-results');

    // Validate postcode
    const region = postcodeToRegion(postcode);
    if (!region) {
        resultsDiv.innerHTML = `
            <div class="calc-placeholder">
                <span class="calc-placeholder-icon">⚠️</span>
                <p>Could not identify region for postcode "<strong>${postcode}</strong>". Please enter a valid UK postcode (e.g. M1 1AA, LS1 1UR, SW1A 1AA).</p>
            </div>`;
        return;
    }

    // Validate inputs
    if (!propertyValue || !loanAmount || !loanTerm) {
        resultsDiv.innerHTML = `
            <div class="calc-placeholder">
                <span class="calc-placeholder-icon">⚠️</span>
                <p>Please fill in all fields: property value, loan amount, and loan term.</p>
            </div>`;
        return;
    }

    // Get regional risk data
    const riskData = dashboardData.risk_scores[region];
    if (!riskData) {
        resultsDiv.innerHTML = `
            <div class="calc-placeholder">
                <span class="calc-placeholder-icon">⚠️</span>
                <p>No risk data available for region: ${region}. Try a postcode in England.</p>
            </div>`;
        return;
    }

    // ── Compute PD (Probability of Default) ──
    // Base PD from regional risk score, scaled to realistic UK mortgage PD range (0.3% – 4%)
    const basePD = 0.003 + riskData.risk_score * 0.037; // 0.3% to 4.0%

    // LTV adjustment: higher LTV → higher PD
    const ltv = loanAmount / propertyValue;
    const ltvMultiplier = ltv <= 0.6 ? 0.7 : ltv <= 0.75 ? 0.85 : ltv <= 0.85 ? 1.0 : ltv <= 0.9 ? 1.3 : ltv <= 0.95 ? 1.6 : 2.0;

    const PD = Math.min(basePD * ltvMultiplier, 0.10); // Cap at 10%

    // ── EAD (Exposure at Default) ──
    // EAD = loan amount (simplified; in practice includes undrawn commitments)
    const EAD = loanAmount;

    // ── Compute LGD (Loss Given Default) ──
    // Conservative approach: use current property value with forced-sale discount
    // Don't assume future price growth (prudent credit risk practice)
    const hpiTrend = riskData.recent_hpi_trend || 0;

    // Forced sale discount: 20-30% below market value (legal costs, estate agents, delays, void period)
    const forcedSaleDiscount = 0.25;
    const recoveryAmount = propertyValue * (1 - forcedSaleDiscount);
    const recoveryRate = Math.min(recoveryAmount / loanAmount, 1.0);
    const baseLGD = Math.max(1 - recoveryRate, 0);

    // HPI adjustment: falling prices increase LGD further, rising prices reduce slightly
    const hpiAdjust = hpiTrend < 0 ? (1 + Math.abs(hpiTrend) / 100 * 2) : (1 - hpiTrend / 100 * 0.3);

    // Deprivation adjustment (harder to sell in deprived areas, longer void period)
    const depAdjust = 1 + riskData.deprivation_score * 0.3;
    const LGD = Math.min(Math.max(baseLGD * hpiAdjust * depAdjust + 0.03, 0.05), 0.70); // Floor 5%, cap 70%

    // ── ECL = PD × EAD × LGD ──
    const ECL = PD * EAD * LGD;
    const ECL_pct = (ECL / EAD) * 100;

    // ── Render Results ──
    const eclClass = ECL_pct < 0.3 ? 'ecl-low' : ECL_pct < 1.0 ? 'ecl-medium' : '';
    const riskLevel = ECL_pct < 0.3 ? 'Low Risk' : ECL_pct < 1.0 ? 'Medium Risk' : 'High Risk';
    const gaugeColor = ECL_pct < 0.3 ? 'linear-gradient(90deg, #10b981, #06b6d4)' :
        ECL_pct < 1.0 ? 'linear-gradient(90deg, #f59e0b, #eab308)' :
            'linear-gradient(90deg, #ef4444, #f59e0b)';
    const gaugePct = Math.min(ECL_pct / 2 * 100, 100); // Scale: 2% ECL = full bar

    resultsDiv.innerHTML = `
        <div class="ecl-result-header">
            <div class="ecl-big-number ${eclClass}">£${Math.round(ECL).toLocaleString()}</div>
            <div class="ecl-subtitle">Expected Credit Loss • ${riskLevel} • ${region}</div>
        </div>

        <div class="ecl-breakdown">
            <div class="ecl-factor">
                <div class="ecl-factor-label">PD</div>
                <div class="ecl-factor-value" style="color: #ef4444;">${(PD * 100).toFixed(2)}%</div>
                <div class="ecl-factor-desc">Prob. of Default</div>
            </div>
            <div class="ecl-factor">
                <div class="ecl-factor-label">EAD</div>
                <div class="ecl-factor-value" style="color: #f59e0b;">£${Math.round(EAD).toLocaleString()}</div>
                <div class="ecl-factor-desc">Exposure at Default</div>
            </div>
            <div class="ecl-factor">
                <div class="ecl-factor-label">LGD</div>
                <div class="ecl-factor-value" style="color: #8b5cf6;">${(LGD * 100).toFixed(1)}%</div>
                <div class="ecl-factor-desc">Loss Given Default</div>
            </div>
        </div>

        <div class="ecl-gauge">
            <div class="ecl-gauge-label">
                <span>Low Risk</span>
                <span>ECL: ${ECL_pct.toFixed(3)}% of loan</span>
                <span>High Risk</span>
            </div>
            <div class="ecl-gauge-bar">
                <div class="ecl-gauge-fill" style="width: ${gaugePct}%; background: ${gaugeColor};"></div>
            </div>
        </div>

        <div class="ecl-details">
            <div class="ecl-detail-row"><span class="label">Region</span><span class="value">${region}</span></div>
            <div class="ecl-detail-row"><span class="label">Regional Risk Score</span><span class="value">${(riskData.risk_score * 100).toFixed(0)} / 100</span></div>
            <div class="ecl-detail-row"><span class="label">LTV Ratio</span><span class="value">${(ltv * 100).toFixed(1)}%</span></div>
            <div class="ecl-detail-row"><span class="label">HPI Annual Trend</span><span class="value">${hpiTrend > 0 ? '+' : ''}${hpiTrend.toFixed(1)}%</span></div>
            <div class="ecl-detail-row"><span class="label">Deprivation Score</span><span class="value">${(riskData.deprivation_score * 100).toFixed(0)}%</span></div>
            <div class="ecl-detail-row"><span class="label">Avg Regional Price</span><span class="value">£${riskData.latest_price ? Math.round(riskData.latest_price).toLocaleString() : '—'}</span></div>
            <div class="ecl-detail-row"><span class="label">Monthly Repos (avg)</span><span class="value">${riskData.avg_repos_all.toFixed(1)}</span></div>
        </div>

        <div class="ecl-formula-display">
            ECL = ${(PD * 100).toFixed(2)}% × £${Math.round(EAD).toLocaleString()} × ${(LGD * 100).toFixed(1)}% = <strong>£${Math.round(ECL).toLocaleString()}</strong>
        </div>
    `;
}

// ─── Start ───
document.addEventListener('DOMContentLoaded', init);