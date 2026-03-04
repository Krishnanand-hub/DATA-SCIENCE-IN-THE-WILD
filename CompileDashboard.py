import altair as alt
import pandas as pd
import json

COLORS = [
    "#FA0014", "#FB9824", "#C8C900", "#784315", "#FC65FA",
    "#29D23C", "#33D5FC", "#666666", "#2800CC", "#A800F9",
]

def load_data() -> pd.DataFrame:
    df = pd.read_csv("./data/historical_data.csv")
    return df


def load_long(df: pd.DataFrame) -> pd.DataFrame:
    return df.melt(id_vars="Time period", var_name="Region", value_name="value")


def make_selection_and_color(df_long: pd.DataFrame):
    regions = df_long["Region"].unique().tolist()
    selection = alt.selection_point(fields=["Region"], on="mouseover", toggle=True)
    color = alt.Color("Region:N", legend=None, scale=alt.Scale(domain=regions, range=COLORS))
    cond_color = alt.condition(selection, color, alt.value("lightgray"))
    return selection, color, cond_color

def chart_normalised(df: pd.DataFrame, selection, cond_color) -> alt.Chart:
    region_cols = df.columns[1:]
    df_norm = df.copy()
    df_norm[region_cols] = df_norm[region_cols].div(df_norm[region_cols].iloc[0])
    long = df_norm.melt(id_vars="Time period", var_name="Region", value_name="value")

    return (
        alt.Chart(long)
        .mark_line(point=False)
        .encode(
            x=alt.X("Time period:O", axis=alt.Axis(labelAngle=-45, title="Time")),
            y=alt.Y("value:Q", title="Index (first period = 1.0)"),
            color=cond_color,
            opacity=alt.condition(selection, alt.value(1.0), alt.value(0.15)),
            tooltip=["Region:N", "Time period:O", alt.Tooltip("value:Q", format=".3f")],
        )
        .properties(title="Normalised Regional Trends", width=400, height=300)
    )

def chart_raw(df_long: pd.DataFrame, selection, cond_color) -> alt.Chart:
    return (
        alt.Chart(df_long)
        .mark_line(point=False)
        .encode(
            x=alt.X("Time period:O", axis=alt.Axis(labelAngle=-45, title="Time")),
            y=alt.Y("value:Q", title="Value"),
            color=cond_color,
            opacity=alt.condition(selection, alt.value(1.0), alt.value(0.15)),
            tooltip=["Region:N", "Time period:O", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(title="Regional Comparison – Raw Values", width=400, height=300)
    )

def chart_area(df_long: pd.DataFrame, selection, cond_color) -> alt.Chart:
    return (
        alt.Chart(df_long)
        .mark_area(opacity=0.4)
        .encode(
            x=alt.X("Time period:O", axis=alt.Axis(labelAngle=-45, title="Time")),
            y=alt.Y("value:Q", stack=None, title="Value"),
            color=cond_color,
            opacity=alt.condition(selection, alt.value(0.5), alt.value(0.08)),
            tooltip=["Region:N", "Time period:O", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(title="Regional Trends – Area View", width=400, height=300)
    )

def chart_latest_bar(df_long: pd.DataFrame, selection, cond_color) -> alt.Chart:
    latest_period = df_long["Time period"].iloc[-1]
    latest = df_long[df_long["Time period"] == latest_period]

    return (
        alt.Chart(latest)
        .mark_bar()
        .encode(
            x=alt.X("value:Q", title="Value"),
            y=alt.Y("Region:N", sort="-x", title=None),
            color=cond_color,
            opacity=alt.condition(selection, alt.value(1.0), alt.value(0.3)),
            tooltip=["Region:N", alt.Tooltip("value:Q", format=".2f")],
        )
        .properties(title=f"Latest Snapshot – {latest_period}", width=400, height=300)
    )

def chart_legend(df_long: pd.DataFrame, selection, cond_color) -> alt.Chart:
    return (
        alt.Chart(df_long)
        .mark_point(size=120, filled=True)
        .encode(
            y=alt.Y("Region:N", axis=alt.Axis(title="Region")),
            color=cond_color,
            tooltip=["Region:N"],
        )
        .properties(title="Legend (hover to highlight)", height=800)
        .add_params(selection)
    )

def chart_map(df_long: pd.DataFrame, month: str = "Jan 2024") -> alt.Chart:
    with open("./data/Regions_December_2024_Boundaries_EN_BUC_-3712119485630821125.geojson") as f:
        regions = json.load(f)
    with open("./data/Countries_December_2024_Boundaries_UK_BGC_-611145351699583027.geojson") as f:
        countries = json.load(f)

    for feat in countries["features"]:
        props = feat["properties"]
        props["GEO_CODE"] = props["CTRY24CD"]
        props["GEO_NAME"] = props["CTRY24NM"]
    for feat in regions["features"]:
        props = feat["properties"]
        props["GEO_CODE"] = props["RGN24CD"]
        props["GEO_NAME"] = props["RGN24NM"]

    merged = {
        "type": "FeatureCollection",
        "features": countries["features"] + regions["features"],
    }

    lookup = {
        feat["properties"]["GEO_NAME"]: feat["properties"]["GEO_CODE"]
        for feat in merged["features"]
    }
    content = df_long[df_long["Time period"] == month].copy()
    content["geo_code"] = content["Region"]
    geo_data = alt.Data(values=merged["features"])

    return (
        alt.Chart(geo_data)
        .mark_geoshape(stroke="white", strokeWidth=0.5)
        .transform_lookup(
            lookup="properties.GEO_CODE",
            from_=alt.LookupData(
                data=alt.InlineData(values=content[["geo_code", "value", "Region"]].to_dict("records")),
                key="geo_code",
                fields=["value", "Region"],
            ),
        )
        .encode(
            color=alt.Color(
                "value:Q",
                scale=alt.Scale(scheme="redyellowblue", reverse=True),
                legend=alt.Legend(title=f"Value ({month})"),
            ),
            tooltip=[
                alt.Tooltip("properties.GEO_NAME:N", title="Region"),
                alt.Tooltip("value:Q", format=".2f", title="Value"),
            ],
        )
        .project(type="mercator")
        .properties(title=f"Regional Map – {month}", width=400, height=800)
    )

def build_dashboard(output_path: str = "./static/figures/centralisedView.html", month: str = "Jan 2024") -> None:
    df = load_data()
    df_long = load_long(df)

    selection, color, cond_color = make_selection_and_color(df_long)

    legend = chart_legend(df_long, selection, cond_color)

    c1 = chart_normalised(df, selection, cond_color)
    c2 = chart_raw(df_long, selection, cond_color)
    c3 = chart_area(df_long, selection, cond_color)
    c4 = chart_latest_bar(df_long, selection, cond_color)

    cmap = chart_map(df_long, month=month)

    dashboard = (legend | cmap) | ((c1 | c2) & (c3 | c4))
    dashboard.save(output_path)
    print(f"Dashboard saved to {output_path}")


if __name__ == "__main__":
    build_dashboard()