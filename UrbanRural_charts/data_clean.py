import pandas as pd
import os

def clean_la_classification_dataset(
    folder_path,
    file_name,
    output_file_name="cleaned_dataset.csv"
):
    """
    Loads an Excel dataset, removes specified columns,
    saves the cleaned dataset as a CSV, and returns the cleaned DataFrame.
    """
    
    # Create full file path
    file_path = os.path.join(folder_path, file_name)

    # Load the dataset
    df = pd.read_excel(file_path, engine="xlrd")

    df.columns = df.columns.str.replace(r"\d+", "", regex=True).str.strip()

    # Columns to remove
    columns_to_remove = [
        "Rural Town Population (including Large Market Town population)",
        "Rural% (including Large Market Town population)"
    ]

    # Create cleaned dataframe
    urdf = df.drop(columns=columns_to_remove, errors='ignore')

    # Save cleaned dataframe
    cleaned_file_path = os.path.join(folder_path, output_file_name)
    urdf.to_csv(cleaned_file_path, index=False)

    return urdf


# Example usage
# folder_path = r"/Users/pavithra_govinda_raj/Git/DataScienceInTheWild/data"
# file_name = "LAClassification-dataset-post0409.xls"

# cleaned_df = clean_la_classification_dataset(folder_path, file_name)

# print(cleaned_df.head())