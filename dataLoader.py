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

def load_imd(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/lsoa_district_imd_map.csv"):
        #load
        df = pandas.read_csv("File_1_IoD2025 Index of Multiple Deprivation.csv")
        #extract/pre-process
        df = df[["LSOA code (2021)", "Local Authority District code (2024)", "Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)"]]
        #simplify and stash
        df.to_csv("./data/lsoa_district_imd_map.csv", index=False)
    else:
        df= pandas.read_csv("./data/lsoa_district_imd_map.csv")
    return df

if __name__ == "__main__":
    data = link_postcode_district()
    print(data.head())
    data = link_postcode_region()
    print(data.head())
    data = link_district_region()
    print(data.head())
