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

def load_repossession_data(FORCE_PROCESSING=False):
    if FORCE_PROCESSING or not os.path.exists("./data/district_repossesssion_map.csv"):
        # Load 
        df = pd.read_csv("Repossession-2025-12.csv")
	#pre-process/extract
        df = df.rename(columns={'AreaCode': 'districtCode'})
        # Convert the string dates into proper datetime objects for time-series analysis
        df['date'] = pd.to_datetime(df['date'], dayfirst=True)
        #Simplify and Stash
        df.to_csv("./data/district_repossesssion_map.csv", index=False)
          
    else:
        df = pd.read_csv("./data/district_repossesssion_map.csv")
    return df


if __name__ == "__main__":
    data = link_postcode_district()
    print(data.head())
    data = link_postcode_region()
    print(data.head())
    data = link_district_region()
    print(data.head())

