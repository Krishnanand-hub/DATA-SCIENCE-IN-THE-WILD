import pandas
import os
import numpy
import matplotlib.pyplot as plt

def link_postcode_district(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/postcode_district_map.csv"):
        #load
        df = pandas.read_excel("./data/ONSPD_NOV_2025_UK_-4615871342515732933.xlsx")
        #extract/pre-process
        df = df[["Postcode (7 char)", "Local Authority District Code (2025)"]]
        #simplify and stash
        df.to_csv("./data/postcode_district_map.csv", index=False)

    else:  df = pandas.read_csv("./data/postcode_district_map.csv") # read simplified

    return df  # return pandas dataframe

def link_postcode_region(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/postcode_region_map.csv"):
        df = pandas.read_excel("./data/ONSPD_NOV_2025_UK_-4615871342515732933.xlsx")
        df = df[["Postcode (7 char)", "Region Code (2025)"]]
        df.to_csv("./data/postcode_region_map.csv", index=False)

    else: df = pandas.read_csv("./data/postcode_region_map.csv")

    return df

def link_district_region(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/district_region_map.csv"):
        df = pandas.read_excel("./data/ONSPD_NOV_2025_UK_-4615871342515732933.xlsx")
        df = df[["Local Authority District Code (2025)", "Region Code (2025)"]]
        df.to_csv("./data/district_region_map.csv", index=False)

    else: df = pandas.read_csv("./data/district_region_map.csv")

    return df

def read_ons_pd(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/read_ons_pd.csv"):
        df = pandas.read_excel("./data/ONSPD_NOV_2025_UK_-4615871342515732933.xlsx")
        df.to_csv("./data/read_ons_pd.csv", index=False)
    else: df = pandas.read_csv("./data/read_ons_pd.csv")
    return df

def hpi_2025_data(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/hpi_2025_data.csv"):
        df_englad = pandas.read_excel("./data/ukhousepriceindexmonthlypricestatistics.xlsx", sheet_name="8", skiprows=2)
        df_wales = pandas.read_excel("./data/ukhousepriceindexmonthlypricestatistics.xlsx", sheet_name="9", skiprows=2)
        df_scotland = pandas.read_excel("./data/ukhousepriceindexmonthlypricestatistics.xlsx", sheet_name="10", skiprows=2)
        df_north_ireland = pandas.read_excel("./data/ukhousepriceindexmonthlypricestatistics.xlsx", sheet_name="11", skiprows=2)
        df = pandas.concat([df_englad, df_wales, df_scotland, df_north_ireland])
        df.to_csv("./data/hpi_2025_data.csv", index=False)

    else: df = pandas.read_excel("./data/hpi_2025_data.csv")

    return df

def historical_price_data(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/historical_price_data.csv"):
        rename_column = pandas.read_csv("./data/region_country_code.csv")
        rename_column = dict(zip(rename_column["Region"], rename_column["Code"]))
        df = pandas.read_excel("./data/ukhousepriceindexmonthlypricestatistics.xlsx", sheet_name="2", skiprows=2)
        df.to_csv("./data/historical_price_data.csv", index=False)
        df = df.rename(columns=rename_column)
    else: df = pandas.read_excel("./data/historical_price_data.csv")

    return df

def historical_hpi_data(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/historical_data.csv"):
        rename_column = pandas.read_csv("./data/region_country_code.csv")
        rename_column = dict(zip(rename_column["Region"], rename_column["Code"]))

        df = pandas.read_excel("./data/ukhousepriceindexmonthlypricestatistics.xlsx", sheet_name="3", skiprows=2)
        df = df.rename(columns=rename_column)
        df.to_csv("./data/historical_data.csv", index=False)


    else: df = pandas.read_excel("./data/historical_data.csv")

    return df

if __name__ == "__main__":
    data = historical_price_data(FORCE_PROCESSING=True)
    print(data.head())