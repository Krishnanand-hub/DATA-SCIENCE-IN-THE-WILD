

# main.py
from data_clean import clean_la_classification_dataset
from charts import (
    plot_region_urban_rural_bar,
    plot_region_population_bar
)


def main():
    # File path and name
    folder_path = r"/Users/pavithra_govinda_raj/Git/DataScienceInTheWild/data"
    file_name = "LAClassification-dataset-post0409.xls"

    # Function 0: Clean dataset
    cleaned_df = clean_la_classification_dataset(folder_path, file_name)

    # Function 1: Plot Urban vs Rural by Region
    plot_region_urban_rural_bar(cleaned_df)

    # Function 2: Plot Population by Region
    plot_region_population_bar(cleaned_df)


if __name__ == "__main__":
    main()