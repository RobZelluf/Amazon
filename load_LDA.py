from gensim.models import LdaModel
from gensim import corpora
from pprint import pprint
import pandas as pd

DIR = "LDAs/"
data_set = "smartplugs1130-merged-lemmatized"
model_type = "nt100na0.1-1"
model = data_set + model_type
lda = LdaModel.load(DIR + model)

mm_file = data_set + '.mm'
mm = corpora.MmCorpus(mm_file)

DIR = "data/"
filename = data_set + ".csv"
file = DIR + filename

df = pd.read_csv(file)
reviews = df.Review

r = 3
review = mm[r]

topic_dist = LdaModel.get_document_topics(lda, review)
topics = [x[0] for x in topic_dist]
print(topics)

pprint(LdaModel.print_topics(lda, -1, 10))
