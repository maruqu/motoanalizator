import json
import pandas as pd
import concurrent.futures
import geocoder
from requests.exceptions import ReadTimeout




def remove_outliers(df):
    """Remove records with price and milage outside 3 std deviation"""

    df = df[((df.price - df.price.mean()) / df.price.std()).abs() < 3]
    df = df[((df.milage - df.milage.mean()) / df.milage.std()).abs() < 3]

    return df


def prepare_year_pice_data(year_grouped_df):
    """Return dict with years and price means"""

    years = []
    price_means = []
    for (year, group) in year_grouped_df:
        years.append(int(year))
        price_means.append(int(group['price'].mean()))

    return serialize_chart_data(years, price_means)


def prepare_year_milage_data(year_grouped_df):
    """Return dict with years and milage means"""

    years = []
    milage_means = []
    for (year, group) in year_grouped_df:
        years.append(int(year))
        milage_means.append(int(group['milage'].mean()))

    return serialize_chart_data(years, milage_means)


def prepare_year_quantity_data(fuel_grouped_df, year_grouped_df, df):
    """Return dict with years and quantities"""

    years = [int(year) for (year, group) in year_grouped_df]
    quantities = []
    for (fuel, fuel_group) in fuel_grouped_df:
        fuel_data = []
        for (year, year_group) in year_grouped_df:
            fuel_data.append(len(year_group.loc[df['fuelType'] == fuel]))

        quantities.append(fuel_data)

    data = {}
    data["labels"] = years
    data["series"] = quantities

    return data


def prepare_location_data(location_grouped_df):
    """Return dict with cords of cities and quantities od offers"""

    locations = []
    quantities = []
    for (location, group) in location_grouped_df:
        locations.append(location)
        quantities.append(len(group))

    with concurrent.futures.ThreadPoolExecutor(max_workers=len(locations)) as executor:
        geocoded_locations = list(executor.map(geocode, locations))

    data = {}
    data["labels"] = geocoded_locations
    data["series"] = quantities

    return data


def geocode(location):
    """Return lat, lng dict of location"""
    while True: #in case of fail try untill success
        try:
            g = geocoder.arcgis(location)
        except ReadTimeout:
            continue
        break

    data = {}
    if g.latlng != []:
        data["lat"] = g.latlng[0]
        data["lng"] = g.latlng[1]
    else:
        data["lat"] = 0
        data["lng"] = 0

    return data


def prepare_fuel_pie_chart_data(fuel_grouped_df):
    """Return dict with quantity of fuel group"""
    labels = []
    quantities = []
    for (fuel, group) in fuel_grouped_df:
        labels.append(fuel)
        quantities.append(len(group))

    data = {}
    data["labels"] = labels
    data["series"] = quantities

    return data


def serialize_chart_data(labels, series):
    """Return dict with data for single chart"""

    data = {}
    data["labels"] = labels
    data["series"] = list([series])

    return data


def prepare_full_data(data):

    df = pd.DataFrame(
        data,
        columns=[
            "price",
            "year",
            "milage",
            "capacity",
            "fuelType",
            "location"
        ]
    )

    df = remove_outliers(df)

    year_grouped_df = df.groupby(['year'])
    fuel_grouped_df = df.groupby(['fuelType'])
    location_grouped_df = df.groupby(['location'])

    data = {}
    data["yearPrice"] = prepare_year_pice_data(year_grouped_df)
    data["yearMilage"] = prepare_year_milage_data(year_grouped_df)
    data["yearQuantity"] = prepare_year_quantity_data(fuel_grouped_df, year_grouped_df, df)
    data["fuelType"] = prepare_fuel_pie_chart_data(fuel_grouped_df)
    data["locationData"] = prepare_location_data(location_grouped_df)

    return json.dumps(data, separators=(',',': '))

