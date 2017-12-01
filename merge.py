import pandas as pd
import csv

DIR = "data/"
filenames = ["smartplugs1130", "smartplugs1130-2", "smartplugs1130-3", "smartplugs1130-4", "smartplugs1130-5"]

headers = []
ratings = []
reviews = []
products = []
asins = []
for filename in filenames:
    print("Merging " + filename)
    file = DIR + filename + ".csv"
    df = pd.read_csv(file)
    headers.extend(list(df.Header))
    ratings.extend(list(df.Rating))
    reviews.extend(list(df.Review))
    products.extend(list(df.Product))
    asins.extend(list(df.asin))

    assert len(headers) == len(ratings) == len(reviews) == len(products) == len(asins)

new_name = "smartplugs1130-merged"
file = DIR + new_name + ".csv"

with open(file, 'w', newline='', encoding="utf-8") as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(["Header", "Rating", "Review", "Product", "asin"])
    writer.writerows(zip(*[headers, ratings, reviews, products, asins]))
