from cgitb import handler
from genericpath import isfile
import nltk
from nltk.corpus import stopwords
from nltk.stem import SnowballStemmer
import re, string
import os
import sys
from os.path import join
import json
import math
import pickle as serializer
import io
import time
from itertools import islice

try:
    to_unicode = unicode
except NameError:
    to_unicode = str
    
ROOT = "./"
EXT = ".json"


nltk.download('stopwords')
nltk.download('punkt')
stoplist = stopwords.words("english")
stoplist += ['?','aqui','.',',','»','«','â','ã','>','<','(',')','º','u']
stemmer = SnowballStemmer('english')

class InvertedIndex:
  inverted_index = { }
  papers_files = ""
  dataname = ""
  
  def __init__(self,dfname):
      self.dataname=dfname
    
  def get_metadata(self):
    with open(self.papers_files, 'r') as f:
        for line in f:
            yield line
              
  def read_files(self):
    for base, dirs, files in os.walk(ROOT):
      for file in files:
        f = join(base,file)
        if self.dataname in f:
          self.papers_files=f
  
  def remove_punctuation(self, text):
    return re.sub('[%s]' % re.escape(string.punctuation), ' ', text)

  def remove_url(self, text):
    t = text.find('https://t.co/')
    if t != -1:
      text = re.sub('https://t.co/\w{10}', '', text)
    return text

  def remove_special_character(self, text):
    characters = ('\"','\'','º','&','¿','?','¡','!',' “','…','👏',
								'-','—','‘','•','›','‼','€','£','↑','→','↓','↔',
								'↘','↪','√','∧','⊃','⌒','⌛','⏬','⏯','⏰','⏹')
    for char in characters:
      text = text.replace(char, "")
    return text

  def clean_text(self, text):
    text = self.remove_special_character(text)
    text = self.remove_punctuation(text)
    text = self.remove_url(text)
    text = nltk.word_tokenize(text)
    return text

  def create_inverted_index(self):
      # condicional si el txt existe y sino:
      if os.path.isfile('..\indice_invertido.json'):
          return
      else:
          self.read_files()
          json_file = self.get_metadata()
          paper_list = []
          count = 0
          for paper in json_file:
              paperToSave = {}
              for k, v in json.loads(paper).items():
                  paperToSave[k] = v
              paper_list.append(paperToSave)
              count += 1
              if (count == 100):
                  break     
          # print(paper_list)
          for paper in paper_list:
              t = join(paper['id'], " ", paper['authors'],
                        " ", paper['abstract'])
              t = self.clean_text(t.lower())
              # print(t)
              # print(paper["id"])
              for word in t:
                  if word not in stoplist:
                      token = stemmer.stem(word)
                  if token not in self.inverted_index.keys():
                      # df = un solo archivo
                      self.inverted_index[token] = {
                          "df": 0, "tf": 0, 'papers': []}
                      # print(self.inverted_index[token]['papers'])
                  found = False
                  for x in self.inverted_index[token]['papers']:
                      if x['id'] == paper['id']:
                          found = True
                          x['freq'] += 1
                          break
                  if not found:
                      self.inverted_index[token]['papers'].append(
                          {"id": paper['id'], "freq": 1})
                      self.inverted_index[token]['df'] += 1
                  self.inverted_index[token]['tf'] += 1
                  #print(token," - ",self.inverted_index[token])
          # print(len(paper_list))
          # for val in self.inverted_index.keys():
          #  print(self.inverted_index[val])
          for token in self.inverted_index.keys():
              self.inverted_index[token]['idf'] = math.log(
                  len(paper_list)/self.inverted_index[token]["df"], 10)
              self.inverted_index[token]['score'] = 0
              for index in range(len(self.inverted_index[token]['papers'])):
                  #print(index,end=" - ")
                  tf = self.inverted_index[token]['papers'][index]['freq']
                  idf = self.inverted_index[token]["idf"]
                  tf_idf = (1 + math.log(tf)) * idf
                  self.inverted_index[token]['papers'][index]['tf_idf'] = tf_idf
                  self.inverted_index[token]['score'] += tf_idf
                  #print(self.inverted_index[token]['score'],end=" - ")
              # print()
          # for val in self.inverted_index:
                  #print(val," - ",self.inverted_index[val])
          print(len(paper_list))
          for doc in paper_list:
              norma = 0
              for token in self.inverted_index.keys():
                  for paper in self.inverted_index[token]['papers']:
                      if doc['id'] == paper['id']:
                          norma += paper['tf_idf']**2
              norma = math.sqrt(norma)
              for token in self.inverted_index.keys():
                  for paper in range(len(self.inverted_index[token]['papers'])):
                      if doc['id'] == self.inverted_index[token]['papers'][paper]['id']:
                          self.inverted_index[token]['papers'][paper][
                              'norma'] = self.inverted_index[token]['papers'][paper]["tf_idf"]/norma

          with io.open('indice_invertido.json', 'w', encoding='utf8') as outfile:
              str_ = json.dumps(self.inverted_index,
                                indent=4, sort_keys=True,
                                separators=(',', ': '), ensure_ascii=False)
              outfile.write(to_unicode(str_))
          # indice en binario
          # with open('indice_invertidos.txt', 'wb') as f:
          #     serializer.dump(self.inverted_index,f,protocol = serializer.HIGHEST_PROTOCOL)

  def get_data_index(self, cosenos):
      data_index = []
      with open('./data/arxiv-metadata-oai-snapshot.json') as f:
          for line in f:
              paper = json.loads(str(line))
              for i in range(len(cosenos)):
                  if (cosenos[i]["paper"] == paper["id"]):
                      data_index.append(
                          {"val": str(cosenos[i]["similarity"]), "info": paper})
                      del cosenos[i]
                      break
              if (len(cosenos) == 0):
                  break
      return data_index

  def compare_query(self, query):
      start_time = time.time()
      query = self.clean_text(query)
      index_query = {}
      for word in query:
          word = word.lower()
          if word not in stoplist:
              tokenq = stemmer.stem(word)
          if tokenq not in index_query.keys():
              index_query[tokenq] = {'tf': 0}
          index_query[tokenq]['tf'] += 1
      norma = 0

      for tokenq in index_query.keys():
          if tokenq in self.inverted_index.keys():
              index_query[tokenq]['tf_idf'] = (
                  1+math.log10(index_query[tokenq]['tf'])) * self.inverted_index[tokenq]['idf']
              norma += index_query[tokenq]['tf_idf']**2
      norma = math.sqrt(norma)

      for tokenq in index_query.keys():
          if 'tf_idf' in index_query[tokenq].keys():
              index_query[tokenq]['norma'] = index_query[tokenq]['tf_idf'] / \
                  norma if norma != 0 else 0
              #self.inverted_index['norma'] = self.inverted_index['tf_idf']/norma if norma != 0 else 0
      cosenos = []
      # print(index_query)
      # print(self.inverted_index["data"])

      #print("esto es tokenq: ", tokenq)

      similarity = 0
      papers = []
      matrix = {}
      for tokenq in index_query.keys():
          print(tokenq)
          # print(self.inverted_index[tokenq])
          for val in self.inverted_index[tokenq]['papers']:
              if val["id"] not in matrix:
                  # matrix[val["id"]]=[]
                  matrix[val["id"]] = [[tokenq, val['norma']]]
              else:
                  matrix[val["id"]].append([tokenq, val['norma']])

      for papers in matrix:
          similarity = 0
          for words in matrix[papers]:
              similarity += index_query[words[0]]['norma']*words[1]
          cosenos.append({"paper": papers, "similarity": similarity})
      cosenos = sorted(cosenos, key=lambda v: v['similarity'], reverse=True)

      '''
    if "norma" in index_query[tokenq].keys():
      papers_by_word = sorted(self.inverted_index[tokenq]['papers'], key = lambda v: v['freq'], reverse=True)
      papers.append({"word": tokenq, "papers": papers_by_word})
      similarity += index_query[tokenq]['norma']
    cosenos.append({"papers":self.inverted_index[tokenq]['papers'],"coseno": similarity})
  cosenos = sorted(cosenos, key = lambda v: v['coseno'], reverse=True)
  '''
      # print(matrix)

      for val in matrix:
          print(val, "-", matrix[val])

      print(index_query)
      with io.open('cosenos.json', 'w', encoding='utf8') as outfile:
          str_ = json.dumps(cosenos,
                            indent=4, sort_keys=True,
                            separators=(',', ': '), ensure_ascii=False)
          outfile.write(to_unicode(str_))

          #print(index_query[tokenq].keys()," - ",index_query[tokenq])
          # print(self.inverted_index[tokenq].keys())
          # print(self.inverted_index[tokenq])

      '''      
  for paper in self.inverted_index[tokenq]['papers']: #error
  #print(file)
    similarity = 0
    papers = []
    #print(self.inverted_index[tokenq]['papers'].keys())
    #print(index_query[tokenq].keys())
    for tokenq in index_query.keys():
      #print("holaaaaasassaasas")
      if 'norma' in index_query[tokenq].keys():
        #print("holaaaa")
        papers_by_word = sorted(self.inverted_index[tokenq]['papers'], key = lambda v: v['freq'], reverse=True)
        papers.append({"word": tokenq, "papers": papers_by_word})
        similarity += index_query[tokenq]['norma'] * paper['norma']
      cosenos.append({"paper": paper, "coseno": similarity})
    cosenos = sorted(cosenos, key = lambda v: v['coseno'], reverse=True)
  
  
  '''
      return [sorted(self.get_data_index(cosenos), key=lambda v: v['val'], reverse=True), round((time.time()-start_time)*1000, 4)]