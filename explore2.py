from gensim import corpora
import pandas as pd
from collections import defaultdict
from pprint import pprint  # pretty-printer
from gensim.models import LdaModel
import logging
import numpy as np
from gensim.parsing.preprocessing import STOPWORDS
stopwords = ["1", "2", "3", "4", "5", "star", "stars"]
alphabet = list("abcdefghijklmnopqrstuvwxyz")
stopwords.extend(alphabet)
import csv
import os

#logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

## REMOVE DOCUMENTS THAT HAVE LESS THAN x WORDS ##
min_words = 5

## REMOVE WORDS THAT APPEAR IN LESS THAN no_below DOCUMENTS OR MORE THAN no_above % OF THE DOCUMENTS ##
no_below = 20

## SET EVALUATION ##
eval_every = 10

DIR = "data/"
name = "smartplugs1130-merged-lemmatized"
filename = name + ".csv"
file = DIR + filename

df = pd.read_csv(file)
reviews = list(df.Review)
num_reviews = len(reviews)

for document in reviews:
    if type(document) == float:
        reviews.remove(document)

reviews = [[word for word in document.lower().split() if (word not in STOPWORDS and word not in stopwords)] for document in reviews if len(document) > min_words]

frequency = defaultdict(int)
for review in reviews:
    for word in review:
        frequency[word] += 1

reviews = [[token for token in text if frequency[token] > 1] for text in reviews]

dictionary = corpora.Dictionary(reviews)

ex_name = "Passes and iterations"
results = "explore/results"

ver = 1
while True:
    fname = results + str(ver) + ".csv"
    if os.path.exists(fname):
        ver += 1
    else:
        break

DS = [40000]
NT = [30, 100]
NA = [0.1, 0.5, 0.9]
CS = [4000]
PS = [20]
IT = [400]

runs = len(CS) + len(PS) + len(IT) + len(DS) + len(NT) + len(NA)

with open(fname, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerows([["Name", ex_name],["Data sizes", DS], ["Number of topics", NT], ["Not above", NA],
                      ["Chunksize", CS], ["Passes", PS], ["Iterations", IT],[]])

def explore(parameters, run):
    print(parameters)
    no_above = parameters["no_above"]
    chunksize = parameters["chunksize"]
    passes = parameters["passes"]
    iterations = parameters["iterations"]
    size = parameters["size"]
    num_topics = parameters["num_topics"]

    with open(fname, 'a', newline='', encoding='utf-8') as csv_file:
        run += 1
        print("Run " + str(run) + " out of " + str(runs))
        writer = csv.writer(csv_file)
        corpora.Dictionary.filter_extremes(dictionary, no_below=no_below, no_above=no_above, keep_tokens=None)
        corpus = [dictionary.doc2bow(review) for review in reviews]
        corpora.MmCorpus.serialize(name + '.mm', corpus)
        mm = corpora.MmCorpus(name + '.mm')  # `mm` document stream now has random access
        mm_used = mm[:size]
        writer.writerows([["Data size", "Topics", "no_above", "Chunksize", "Passes", "Iteration"],
                          [size, num_topics, no_above, chunksize, passes, iterations],[]])

        lda = LdaModel(mm_used, num_topics=num_topics, chunksize=chunksize, id2word=dictionary, passes=passes,
                       iterations=iterations, eval_every=eval_every)

        lst =[]
        for topic in LdaModel.print_topics(lda, -1, 10):
            terms = [x[0] for x in LdaModel.get_topic_terms(lda, topic[0], topn=10)]
            term_strings = [str(dictionary[term]) for term in terms]
            str_topic = []
            str_topic.append("Topic " + str(topic[0] + 1))
            str_topic.extend(term_strings)
            lst.append(str_topic)

        writer.writerows(zip(*lst))
        writer.writerow([])

        return run

par_default = {"no_above" : 0.9, "chunksize": 2000, "passes" : 5, "iterations" : 200, "size" : 20000, "num_topics" : 50}

if len(NA) == 1:
    par_default["no_above"] = NA[0]
if len(CS) == 1:
    par_default["chunksize"] = CS[0]
if len(PS) == 1:
    par_default["passes"] = PS[0]
if len(IT) == 1:
    par_default["iterations"] = IT[0]
if len(DS) == 1:
    par_default["size"] = DS[0]
if len(NT) == 1:
    par_default["num_topics"] = NT[0]

parameters = par_default.copy()

run = 0

if len(DS) > 1:
    for size in DS:
        parameters["size"] = size
        run = explore(parameters, run)

    parameters = par_default.copy()

if len(NA) > 1:
    for no_above in NA:
        parameters["no_above"] = no_above
        run = explore(parameters, run)

    parameters = par_default.copy()

if len(CS) > 1:
    for chunksize in CS:
        parameters["chunksize"] = chunksize
        run = explore(parameters, run)

    parameters = par_default.copy()

if len(PS) > 1:
    for passes in PS:
        parameters["passes"] = passes
        run = explore(parameters, run)

    parameters = par_default.copy()

if len(IT) > 1:
    for iterations in IT:
        parameters["iterations"] = iterations
        run = explore(parameters, run)

    parameters = par_default.copy()

if len(NT) > 1:
    for num_topics in NT:
        parameters["num_topics"] = num_topics
        run = explore(parameters, run)


