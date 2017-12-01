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
no_above = .1

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
corpora.Dictionary.filter_extremes(dictionary, no_below=no_below, no_above=no_above, keep_tokens=None)

corpus = [dictionary.doc2bow(review) for review in reviews]

corpora.MmCorpus.serialize(name + '.mm', corpus)
mm = corpora.MmCorpus(name + '.mm') # `mm` document stream now has random access

CS = [2000]
PS = [5, 10]
IT = [100, 200]

DS = [.5] # Data set size used
for i in range(len(DS)):
    DS[i] = int(num_reviews * DS[i])

NT = [10] # Number of topics
NA = [.5] # Don't take words that appear in >NA documents

runs = len(CS) * len(PS) * len(IT) * len(DS) * len(NT) * len(NA)

ex_name = "Passes and iterations"
results = "explore/results"

ver = 0
while True:
    fname = results + str(ver) + ".csv"
    if os.path.exists(fname):
        ver += 1
    else:
        break

with open(fname, 'w', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    writer.writerows([["Name", ex_name],["Data sizes", DS], ["Number of topics", NT], ["Not above", NA],
                      ["Chunksize", CS], ["Passes", PS], ["Iterations", IT],[]])

with open(fname, 'a', newline='', encoding='utf-8') as csv_file:
    writer = csv.writer(csv_file)
    run = 0
    for chunksize in CS:
        for passes in PS:
            for iterations in IT:
                for size in DS:
                    mm_used = mm[:size]
                    for num_topics in NT:
                        for no_above in NA:
                            run += 1
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



