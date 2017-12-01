import numpy as np
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import RegexpTokenizer
import csv
import re
import pandas as pd
import os
import tensorflow as tf

tokenizer = RegexpTokenizer(r'\w+')

glove = "wordvectors/GloVe/glove.6B.100d.txt"
model = {}

DIR = "data/"
name = "smartplugs1130-merged"
filename = name + ".csv"
file = DIR + filename

lmtzr = WordNetLemmatizer()

df = pd.read_csv(file)
ratings = df.Rating
headers = df.Header
reviews = df.Review
products = df.Product

new_headers = list()
new_reviews = list()

print("Checking headers")
for header in headers:
    if type(header) != float:
        new_header = list()
        words = tokenizer.tokenize(header)
        for word in words:
            lemma = lmtzr.lemmatize(word.lower())
            new_header.append(lemma)
        new_headers.append(' '.join(new_header))
    else:
        new_headers.append('')

print("Checking reviews")
for review in reviews:
    if type(review) != float:
        new_review = list()
        words = tokenizer.tokenize(review)
        for word in words:
            lemma = lmtzr.lemmatize(word.lower())
            new_review.append(lemma)
        new_reviews.append(' '.join(new_review))
    else:
        new_reviews.append('')

assert len(new_headers) == len(new_reviews)

filename = name + "-tokenized-lemmatized.csv"
file = DIR + filename

with open(file, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerow(['Header', 'Rating', 'Review', 'Product'])
    for i in range(len(new_headers)):
        writer.writerow([new_headers[i], ratings[i], new_reviews[i], products[i]])
