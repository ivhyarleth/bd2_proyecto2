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
try:
    to_unicode = unicode
except NameError:
    to_unicode = str
    
ROOT = "./"
EXT = ".json"


nltk.download('stopwords')
nltk.download('punkt')
stoplist = stopwords.words("spanish")
stoplist += ['?','aqui','.',',','»','«','â','ã','>','<','(',')','º','u']
stemmer = SnowballStemmer('spanish')

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
    #condicional si el txt existe y sino:
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
    
        for paper in paper_list:
            t = join(paper['id'], " ", paper['authors'], " ", paper['abstract'])
            t = self.clean_text(t.lower())
            for word in t:
                if word not in stoplist:
                    token = stemmer.stem(word)
                if token not in self.inverted_index.keys():
                    #df = un solo archivo
                    self.inverted_index[token] = {"df":0,"tf":0,'papers':[]} 
                found = False
                for x in self.inverted_index[token]['papers']:
                    if x['id'] == paper['id']:
                        found = True
                        x['freq'] += 1
                        break
                if not found:
                    self.inverted_index[token]['papers'].append({"id":paper['id'], "freq":1})
                    self.inverted_index[token]['df'] += 1
                self.inverted_index[token]['tf'] += 1

        for token in self.inverted_index.keys():
            self.inverted_index[token]['idf'] = math.log(len(paper_list)/self.inverted_index[token]["df"], 10)
            self.inverted_index[token]['score'] = 0
            for index in range(len(self.inverted_index[token]['papers'])):
                tf = self.inverted_index[token]['papers'][index]['freq']
                idf = self.inverted_index[token]["idf"]
                tf_idf = (1 + math.log(tf)) * idf
                self.inverted_index[token]['papers'][index]['tf_idf'] = tf_idf
                self.inverted_index[token]['score'] += tf_idf
        
        for doc in paper_list:
            norma = 0
            for token in self.inverted_index.keys():
                for paper in self.inverted_index[token]['papers']:
                    if doc['id'] == paper['id']:
                        norma += paper['tf_idf']**2
            norma = math.sqrt(norma)
            for token in self.inverted_index.keys():
                for paper in range(len(self.inverted_index[token]['papers'])):
                    if doc['id'] == self.inverted_index[token]['papers'][paper]:
                        self.inverted_index[token]['papers'][paper]['norma'] = self.inverted_index[token]['papers'][paper]["tf_idf"]/norma
    
        with io.open('indice_invertido.json', 'w', encoding='utf8') as outfile:
            str_ = json.dumps(self.inverted_index,
                      indent=4, sort_keys=True,
                      separators=(',', ': '), ensure_ascii=False)
            outfile.write(to_unicode(str_))
        # indice en binario     
        # with open('indice_invertidos.txt', 'wb') as f:
        #     serializer.dump(self.inverted_index,f,protocol = serializer.HIGHEST_PROTOCOL)
    
    
  def compare_query(self, query):
    query = self.clean_text(query)
    index_query = {}
    for word in query:
        word=word.lower()
        if word not in stoplist:
            tokenq = stemmer.stem(word)
        if tokenq not in index_query.keys():
            index_query[tokenq] = { 'tf' : 0 }
        index_query[tokenq]['tf'] += 1
    norma = 0
    
    for tokenq in index_query.keys():
      if tokenq in self.inverted_index.keys():
        index_query[tokenq]['tf_idf'] = (1+math.log10(index_query[tokenq]['tf'])) * self.inverted_index[tokenq]['idf']
        norma += index_query[tokenq]['tf_idf']**2
    norma = math.sqrt(norma)
    
    for tokenq in index_query.keys():
      if 'tf_idf' in index_query[tokenq].keys():
        index_query[tokenq]['norma'] = index_query[tokenq]['tf_idf']/norma if norma != 0 else 0
        self.inverted_index['norma'] = self.inverted_index['tf_idf']/norma if norma != 0 else 0
    cosenos = []
    
    #for file in range(len(self.inverted_index[tokenq]['papers'])): #error
    #print(file)
    similarity = 0
    papers = []
    print(self.inverted_index[tokenq].keys())
    print(index_query[tokenq].keys())
    for tokenq in index_query.keys():
      if 'norma' in index_query[tokenq].keys() and self.inverted_index[tokenq].keys():
        papers_by_word = sorted(self.inverted_index[tokenq]['papers'], key = lambda v: v['freq'], reverse=True)
        papers.append({"word": tokenq, "papers": papers_by_word})
        similarity += index_query[tokenq]['norma'] * self.inverted_index['norma']
      cosenos.append({"id": papers['id'], "coseno": similarity, "results": papers})
    cosenos = sorted(cosenos, key = lambda v: v['coseno'], reverse=True)
    
    with io.open('cosenos.json', 'w', encoding='utf8') as outfile:
        str_ = json.dumps(cosenos,
                  indent=4, sort_keys=True,
                  separators=(',', ': '), ensure_ascii=False)
        outfile.write(to_unicode(str_))
    return cosenos
    

