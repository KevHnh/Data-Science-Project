# Name: Kevin Hinh
# Email: Kevin.Hinh78@myhunter.cuny.edu
# Resources: 1. Motor-Vehicle-Collisions-Crashes (2019)
#            https://data.cityofnewyork.us/Public-Safety/Motor-Vehicle-Collisions-Crashes/h9gi-nx95/data
#            2. Median Income by zip code (2019)
#            https://data.cccnewyork.org/data/map/66/median-incomes#66/39/6/107/62/a/4
#            3. Pothole Map
#            https://data.cityofnewyork.us/Social-Services/Pothole-Map/wr97-8arm
# Title: Motor Vehicle Collisions - Whose Fault Is It?
# Theme: Vehicles, Collisions, Causes
# Abstract: My project's focus is on the cause of motor vehicle collisions and heavily relies on the location at
# which they occurred. More specifically, I strived to find a correlation between low-income zip codes and collisions
# by using fairly basic data processing methods. In the end, my ultimate goal is to identify two things, the causes
# of motor vehicle collisions in New York City and possible solutions.
# Relevance to NYC: New York City is the home of millions of drivers, after all, driving is one of the most reliable
# modes of transportation. However, many would argue that driving, especially in New York City, is not the safest,
# hence the hundreds of thousands of motor vehicle collisions that occur each year. As a result, it is relevant to
# New York City because I am confident that most, if not all, drivers of New York City want to feel safe while driving.
# URL: https://kevinhinh9.wixsite.com/motorvc

import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
import pandasql as psql
import json
import folium
from folium.plugins import HeatMap

# Focus Questions:
# 1) Is there a correlation between low-income zip codes and motor vehicle collisions?
# 2) What is the most common collision factor? 
# 3) Is there a consistency in where it happens?
# 4) What or who else is at fault for all the collisions?

# CSV FILES
mvc = pd.read_csv('Motor_Vehicle_Collisions_2019_Crashes.csv')
mi = pd.read_csv('Median Incomes.csv')
phm = pd.read_csv('Potholes.csv')

# MVC DATA FILTERING
mvc = mvc.fillna("Invalid")
mvc = mvc[~mvc["CONTRIBUTING FACTOR VEHICLE 1"].str.contains('Unspecified')]
mvc = mvc[~mvc["CONTRIBUTING FACTOR VEHICLE 1"].str.contains('Invalid')]
mvc["LATITUDE"] = mvc["LATITUDE"].astype(str)
mvc["LONGITUDE"] = mvc["LONGITUDE"].astype(str)
mvc = mvc[~mvc["LATITUDE"].str.contains('Invalid')]
mvc = mvc[~mvc["LONGITUDE"].str.contains('Invalid')]
mvc = mvc[~mvc["LOCATION"].str.contains('Invalid')]
mvc["ZIP CODE"] = mvc["ZIP CODE"].astype(str)
mvc = mvc[~mvc["ZIP CODE"].str.contains('Invalid')]
mvc["ZIP CODE"] = mvc["ZIP CODE"].str.strip(".0")
mvc = mvc.drop(columns=["ON STREET NAME", "CROSS STREET NAME", "OFF STREET NAME",
                        "CONTRIBUTING FACTOR VEHICLE 2", "CONTRIBUTING FACTOR VEHICLE 3",
                        "CONTRIBUTING FACTOR VEHICLE 4", "CONTRIBUTING FACTOR VEHICLE 5",
                        "VEHICLE TYPE CODE 1", "VEHICLE TYPE CODE 2", "VEHICLE TYPE CODE 3", "VEHICLE TYPE CODE 4",
                        "VEHICLE TYPE CODE 5"])

# NEDIAN INCOME DATA FILTERING
mi = mi[mi['Location'].notna()]
mi = mi.drop(columns=['Fips', 'DataFormat'])
mi = mi[mi.Location.str.contains('Zip')]
mi = mi[mi["Household Type"].str.contains('All')]
mi['Location'] = mi.Location.str.replace(r"[a-zA-Z]", '')
mi['TimeFrame'] = mi['TimeFrame'].astype(str)
mi = mi[mi.TimeFrame.str.contains('2019')].reset_index(drop=True)
mi['Data'] = mi['Data'].astype(int)

# TOP 5 ZIP CODES WITH HIGHEST COLLISIONS
mvc_cnt = 'select "ZIP CODE", count("ZIP CODE") as cnt from mvc group by "ZIP CODE" order by cnt desc limit 5'
mvc_cnt = psql.sqldf(mvc_cnt)
print(mvc_cnt)

# COUNT OF COLLISIONS PER MONTH
mon = mvc
mon["CRASH DATE"] = mon["CRASH DATE"].str.split('/')
mon["CRASH DATE"] = mon["CRASH DATE"].str[0]
mon["CRASH DATE"] = mon["CRASH DATE"].astype(int)
c_mon = 'select "CRASH DATE" as month, count("CRASH DATE") as cnt from mon group by "CRASH DATE" order by "CRASH DATE" asc'
c_mon = psql.sqldf(c_mon)
print(c_mon)

# COUNT OF ACCIDENTS RESULTING IN DEATH
death = mvc["NUMBER OF PERSONS KILLED"].sum()
injured = mvc["NUMBER OF PERSONS INJURED"].sum()
print(death)
print(injured)

# TOP 5 ZIP CODES WITH LOWEST MEDIAN INCOME (ALL HOUSEHOLDS)
mi['Location'] = mi['Location'].astype(int)
mi['Data'] = mi['Data'].astype(int)
mi_cnt = 'select "Location", "Data" from mi group by "Location" order by "Data" asc limit 5'
mi_cnt = psql.sqldf(mi_cnt)
print(mi_cnt)

# MEDIAN INCOME OF TOP 5 ZIP CODES WITH MOST COLLISIONS
mvc_df = pd.DataFrame(mvc_cnt)
mvc_df['ZIP CODE'] = mvc_df['ZIP CODE'].astype(int)
mvc_list = mvc_df['ZIP CODE'].tolist()
mi['Location'] = mi['Location'].astype(int)

ans = mi.loc[mi['Location'].isin(mvc_list)]
print(ans)

# COLLISION FACTORS
cf = mvc["CONTRIBUTING FACTOR VEHICLE 1"].unique()
print(cf)

# COLLISION FACTORS (COUNT)
cf_cnt = mvc["CONTRIBUTING FACTOR VEHICLE 1"].value_counts()
print(cf_cnt)

# PIE CHART OF TOP 10 FACTORS
cftop10 = cf_cnt.nlargest(10)
cf_pie = cftop10.plot(kind='pie')
plt.show()

# COLLISION COUNT PER ZIPCODE
mvc_cnt = 'select "ZIP CODE", count("ZIP CODE") as cnt from mvc group by "ZIP CODE"'
mvc_cnt = psql.sqldf(mvc_cnt)
zip_df = pd.DataFrame(mvc_cnt)
zip_df = zip_df.iloc[1:, :]
print(zip_df)

# HEAT MAP OF COLLISIONS
mvc["LATITUDE"] = mvc["LATITUDE"].astype(float)
mvc["LONGITUDE"] = mvc["LONGITUDE"].astype(float)
mvc["coord"] = list(zip(mvc['LATITUDE'], mvc['LONGITUDE']))

geojson = json.load(open("zipcode_map.geojson"))
map = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
data = np.asarray(mvc["coord"])
folium.GeoJson(geojson).add_to(map)
HeatMap(data).add_to(map)
folium.GeoJson(geojson).add_child(folium.features.GeoJsonTooltip(['ZIPCODE'])).add_to(map)

map.save("output1.html")

# CHOROPLETH MAP OF COLLISIONS
map2 = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
choropleth1 = folium.Choropleth(geo_data=geojson,
                                name="choropleth",
                                data=zip_df,
                                columns=["ZIP CODE", "cnt"],
                                key_on="feature.properties.ZIPCODE",
                                fill_color="Reds",
                                fill_opacity=0.75,
                                line_opacity=0.75,
                                threshold_scale=[0, 300, 600, 900, 1200, 1500, 1800, 2100],
                                highlight=True).add_to(map2)

choropleth1.geojson.add_child(
    folium.features.GeoJsonTooltip(['ZIPCODE'])
)

map2.save("output2.html")

# POTHOLE DATA PROCESSING
phm = phm.fillna("Invalid")
phm['Year'] = phm['Created Date'].str[6:10]
phm = (phm.loc[phm['Year'].isin(['2019'])])
phm["Latitude"] = phm["Latitude"].astype(str)
phm["Longitude"] = phm["Longitude"].astype(str)
phm = phm[~phm["Latitude"].str.contains('Invalid')]
phm = phm[~phm["Longitude"].str.contains('Longitude')]
phm["Latitude"] = phm["Latitude"].astype(float)
phm["Longitude"] = phm["Longitude"].astype(float)
phm["coord"] = list(zip(phm['Latitude'], phm['Longitude']))

data2 = np.asarray(phm["coord"])
phm_map = folium.Map(location=[40.7128, -74.0060], zoom_start=12)
folium.GeoJson(geojson).add_to(phm_map)
HeatMap(data2).add_to(phm_map)
folium.GeoJson(geojson).add_child(folium.features.GeoJsonTooltip(['ZIPCODE'])).add_to(phm_map)

phm_map.save("output4.html")