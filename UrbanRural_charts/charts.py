import matplotlib.pyplot as plt
import numpy as np



def plot_region_population_bar(df,
                               region_column="Region",
                               population_column="Total Population"):
    """
    Creates a bar chart of Region vs Total Population.
    """

    # Group by region and sum population (in case there are multiple rows per region)
    grouped_df = (
        df
        .groupby(region_column)[population_column]
        .sum()
        .reset_index()
    )

    # Create bar chart
    plt.figure(figsize=(10, 6))
    plt.bar(grouped_df[region_column], grouped_df[population_column])

    # Formatting
    plt.xlabel("Region")
    plt.ylabel("Total Population")
    plt.title("Total Population by Region")
    plt.xticks(rotation=45)
    plt.tight_layout()

    plt.show()


def plot_region_urban_rural_bar(
    df,
    region_column="Region",
    urban_column="Total  Urban Population (excluding Large Market Town population)",
    rural_column="Total Rural Population (including Large Market Town population)"
):
    """
    Creates a grouped bar chart of Region vs:
    - Total Urban Population (excluding Large Market Town population)
    - Total Rural Population (including Large Market Town population)
    """

    # Group and sum values by region
    grouped_df = (
        df
        .groupby(region_column)[[urban_column, rural_column]]
        .sum()
        .reset_index()
    )

    regions = grouped_df[region_column]
    urban_values = grouped_df[urban_column]
    rural_values = grouped_df[rural_column]

    x = np.arange(len(regions))  # label locations
    width = 0.35  # width of bars

    plt.figure(figsize=(12, 6))

    plt.bar(x - width/2, urban_values, width, label="Urban Population")
    plt.bar(x + width/2, rural_values, width, label="Rural Population")

    plt.xlabel("Region")
    plt.ylabel("Population")
    plt.title("Urban vs Rural Population by Region")
    plt.xticks(x, regions, rotation=45)
    plt.legend()

    plt.tight_layout()
    plt.show()


# Example usage
#plot_region_urban_rural_bar(cleaned_df)

# Example usage
#plot_region_population_bar(cleaned_df)