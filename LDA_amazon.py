import gensim
from gensim import corpora
import pandas as pd
from collections import defaultdict
from pprint import pprint  # pretty-printer
from gensim.models import LdaModel
import logging
import os
from gensim.parsing.preprocessing import STOPWORDS
stopwords = ["1", "2", "3", "4", "5", "star", "stars"]
alphabet = list("abcdefghijklmnopqrstuvwxyz")
stopwords.extend(alphabet)

logging.basicConfig(format='%(asctime)s : %(levelname)s : %(message)s', level=logging.INFO)

## NUMBER OF TOPICS ##

num_topics = 100

chunksize = 4000
passes = 20
iterations = 400

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

lda = LdaModel(mm, num_topics=num_topics, chunksize=chunksize, id2word=dictionary, passes=passes, iterations=iterations, eval_every=eval_every)

pprint(lda.print_topics(num_topics=-1, num_words = 10))

model_name = "LDAs/" + name + "nt" + str(num_topics) + "na" + str(no_above)

ver = 1
while True:
    fname = model_name + "-" + str(ver)
    if not os.path.exists(fname):
        lda.save(fname)
        break
    else:
        ver += 1


