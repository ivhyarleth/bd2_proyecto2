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

import time
    
ROOT = "./"
EXT = ".json"


nltk.download('stopwords')
nltk.download('punkt')
stoplist = stopwords.words("english")
stoplist += ['?','aqui','.',',','»','«','â','ã','>','<','(',')','º','u']
stemmer = SnowballStemmer('english')


### FOR TESTING set positive
NUMBER_OF_ENTRIES = 1500 #10000


#'''
class InvertedIndex:
    ROOT = "./"
    DATAFOLDER = "./data"

    """
    Class Initialization
    """    
    def __init__(self, data_filename):
        self.data_filename = data_filename
        self.index_filename = "indice_invertido"
        self.index_number = 0
        self.index_extension = ".json"
        self.tmp_filename = "tmpfile"
        self.max_file_size = 4000000 # 4 MB
                             
    
    ###################################################
    #              PATH FUNCTIONS
    ###################################################
    def get_indexfile_path(self, number):
        return self.index_filename+str(number)+self.index_extension

    def get_tmpfile_path(self, number):
        return self.tmp_filename+str(number)+self.index_extension

    def get_datafile_path(self):
        return os.path.join(InvertedIndex.DATAFOLDER, self.data_filename)

    ###################################################
    #              READ INDEXFILE FUNCTIONS
    ###################################################
    def read_indexfile(self, n):
        with open(self.get_indexfile_path(n), 'r') as f:
            for line in f:
                yield line

    def read_jsonblock(self,jsonpaper):
        return json.loads(jsonpaper)

    ###################################################
    #              MANAGEFILES
    ###################################################
    def remove_indexfile(self, n):
        os.remove(self.get_indexfile_path(n))

    def rename_indexfile(self, a, b):
        os.rename(self.get_indexfile_path(a), self.get_indexfile_path(b))

    def rename_tmpfile(self, n):
        os.rename(self.get_tmpfile_path(n), self.get_indexfile_path(n))

    ###################################################
    #              READ DATAFILE FUNCTIONS
    ###################################################
    def read_datafile(self):
        with open(self.get_datafile_path(), 'r') as f:
            for line in f:
                yield line

    def read_jsonpaper(self,jsonpaper):
        return json.loads(jsonpaper)

    def extract_field_paper(self, field, paper):
        if field in paper:
            return paper[field]
        else:
            return " "

    def extract_text_paper(self, paper):
        return " ".join( (self.extract_field_paper('id',paper),
                 self.extract_field_paper('authors',paper),
                 self.extract_field_paper('abstract',paper),
                 self.extract_field_paper('categories',paper),
                 self.extract_field_paper('title',paper) ) )

    def extract_id_paper(self, paper):
        return paper["id"]

    ###################################################
    #                CLEAN TEXT
    ###################################################

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
        #TODO
        text = self.remove_special_character(text)
        text = self.remove_punctuation(text)
        text = self.remove_url(text)
        text = nltk.word_tokenize(text)
        return text


    ###################################################
    #                MEMORY USAGE
    ###################################################
    def memory_usage_block_dict(self, block_dict):
        memory_usage = sys.getsizeof(block_dict)
        memory_usage += sum(map(sys.getsizeof, block_dict.values())) + sum(map(sys.getsizeof, block_dict.keys()))
        for word in block_dict:
            memory_usage += sum(map(sys.getsizeof, block_dict[word].values())) + sum(map(sys.getsizeof, block_dict[word].keys()))
        return memory_usage
    
    ###################################################
    #                INDEX BLOCK
    ###################################################
    def save_block_dict(self, block_dict, indexfile_id):
        indexn_filepath = self.get_indexfile_path(indexfile_id)
        with io.open(indexn_filepath, 'w', encoding='utf8') as outfile:
            for word in sorted(block_dict.keys()):
                jsondata = json.dumps({word:block_dict[word]},
                                ensure_ascii=False) + "\n"
                outfile.write(jsondata)

    ###################################################
    #              WRITE MERGE TMP BLOCK
    ###################################################
    def save_merge_dict(self, tempfile_id, word_dict):
        tmpn_filepath = self.get_tmpfile_path(tempfile_id)
        with io.open(tmpn_filepath, 'a', encoding='utf8') as outfile:
            jsondata = json.dumps(word_dict,
                                  ensure_ascii=False) + "\n"
            outfile.write(jsondata)

    ###################################################
    #              WRITE CALC TMP BLOCK
    ###################################################
    def save_calc_dict(self, word_dict):
        tmpn_filepath = self.get_tmpfile_path(0)
        with io.open(tmpn_filepath, 'a', encoding='utf8') as outfile:
            jsondata = json.dumps(word_dict,
                                  ensure_ascii=False) + "\n"
            outfile.write(jsondata)

    ###################################################
    #                MAIN FUNCTIONS
    ###################################################

    def create_inverted_index(self):
        if os.path.isfile( self.get_indexfile_path(0) ):
            # If index already exists. Skip
            return
        
        datafile = self.read_datafile()
        
        # SPIMI INVERT
        # Init block dict
        block_dict = {}
        indexfile_id = 0
        paper_count = 0
        for jsonpaper in datafile:
            saved = False
            # Parse paper
            paper = self.read_jsonpaper(jsonpaper)
            # Extract paper id
            paper_id = self.extract_id_paper(paper)
            # Extract text from paper
            text = self.extract_text_paper(paper)
            text_tokenized = self.clean_text(text)
            # Tokenize text
            for word in text_tokenized:
                if word not in stoplist:
                    stem_token = stemmer.stem(word)
                    # Insert into posting list
                    if stem_token in block_dict:
                        # Add 1 to count
                        if paper_id in block_dict[stem_token]:
                            block_dict[stem_token][paper_id] += 1
                        else:
                            block_dict[stem_token][paper_id] = 1
                    else:
                        block_dict[stem_token] = {}
                        block_dict[stem_token][paper_id] = 1
            # Check if filesize exceeded
            #print("MEMORY USAGE: {}".format(self.memory_usage_block_dict(block_dict)))
            paper_count += 1
            #############################################################
            #                       FOR TESTING
            #############################################################
            if (paper_count%500) == 0:
                print("PAPER COUNT:", paper_count)
            if paper_count == NUMBER_OF_ENTRIES: 
                break
            #############################################################
            if self.memory_usage_block_dict(block_dict) > self.max_file_size:
                print("MEMORY USAGE EXCEEDED: count {}".format(paper_count))
                # Save block dict
                self.save_block_dict(block_dict, indexfile_id)
                block_dict = {}
                indexfile_id += 1
                saved = True
        # If last block not saved, save
        if not saved:
            self.save_block_dict(block_dict, indexfile_id)
            indexfile_id += 1
        number_indexfiles = indexfile_id-1

        # SPIMI MERGE
        merge_step = 2 #merge_total_levels = math.ceil( (number_indexfiles+1) **(1/2))

        print("ORIGINAL INDEX FILE NUMBER:", number_indexfiles)
        while (number_indexfiles): # While more than 1 file
            tmpfile_id = 0
            for i in range(0,number_indexfiles+1, merge_step):
                print("FILE POINTER:",i)
                if (number_indexfiles >= i+1):
                    block_a = self.read_indexfile(i)
                    block_b = self.read_indexfile(i+1)
                    tmpfile_id = int(i/2) 
                    valid_a = True
                    valid_b = True
                    # Iterate both
                    word_block_a = self.read_jsonblock(next(block_a))
                    word_block_b = self.read_jsonblock(next(block_b))
                    while (True):
                        word_a = list(word_block_a.keys())[0]
                        word_b = list(word_block_b.keys())[0]
                        #print(word_block_a)
                        if word_a == word_b:
                            # If word is the same, merge
                            word_block_next = word_block_a
                            for paper_id in word_block_b[word_a]:
                                t =  word_block_b[word_a][paper_id]
                                if paper_id in word_block_next[word_a]:
                                    word_block_next[word_a][paper_id] += t
                                else:
                                    word_block_next[word_a][paper_id] =  t
                            self.save_merge_dict(tmpfile_id, word_block_next)
                            # Advance to next
                            try:
                                word_block_a = self.read_jsonblock(next(block_a))
                            except:
                                valid_a = False
                                break
                            try:
                                word_block_b = self.read_jsonblock(next(block_b))
                            except:
                                valid_b = False
                                break
                        else:
                            # If different, add in order
                            if word_a < word_b:
                                word_block_next = word_block_a
                                self.save_merge_dict(tmpfile_id, word_block_next)
                                # Advance to next
                                try:
                                    word_block_a = self.read_jsonblock(next(block_a))
                                except:
                                    valid_a = False
                                    break
                            else:
                                word_block_next = word_block_b
                                self.save_merge_dict(tmpfile_id, word_block_next)
                                # Advance to next
                                try:
                                    word_block_b = self.read_jsonblock(next(block_b))
                                except:
                                    valid_b = False
                                    break
                    # Iterate remanining
                    while (valid_a):
                        word_block_next = word_block_a
                        self.save_merge_dict(tmpfile_id, word_block_next)
                        try:
                            word_block_a = read_jsonblock(next(block_a))
                        except:
                            valid_a = False
                            break
                    while (valid_b):
                        word_block_next = word_block_b
                        self.save_merge_dict(tmpfile_id, word_block_next)
                        try:
                            word_block_b = read_jsonblock(next(block_b))
                        except:
                            valid_b = False
                            break

                    # Overwrite old files
                    self.remove_indexfile(i)
                    self.remove_indexfile(i+1)
                    self.rename_tmpfile(tmpfile_id)
                else:
                    tmpfile_id+=1
                    self.rename_indexfile(i, tmpfile_id)

            # Update number of files
            number_indexfiles = tmpfile_id
            print("NUMBER OF INDEX FILES:", number_indexfiles)
        
        # ADD TF.IDF TO INDEX
        base_index = self.read_indexfile(i)
        word_block = self.read_jsonblock(next(base_index))
        while (True):
            word = list(word_block.keys())[0]
            # Calculate IDF
            IDF = math.log(paper_count / len(word_block[word]))
            # Calculate TF*IDF
            norm = 0
            for id_paper in word_block[word]:
                TF = 1+math.log(word_block[word][id_paper])
                word_block[word][id_paper] = TF*IDF
                norm += (TF*IDF) ** 2
            # Norm
            norm = math.sqrt(norm)
            # Total Block
            index_word_block = {word:{"papers":word_block[word],"norm":norm,"IDF":IDF}}
            # Write to temp
            self.save_calc_dict(index_word_block)
            try:
                word_block = self.read_jsonblock(next(base_index))
            except:
                break

        # OVERWRITE INDEX
        self.rename_tmpfile(0)

#'''






"""
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
        print("F:",f)
        if self.dataname in f:
          print("SELECTED:",f)
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

  def colocar(self,variable,paper):
    if paper[variable] is None:
      return " "
    else:
      return paper[variable]

  def create_inverted_index(self):
      # condicional si el txt existe y sino:
      if os.path.isfile('indice_invertido.json'):
          return
      else:
          self.read_files()
          json_file = self.get_metadata()
          print("JSON FILE:{}".format(json_file))
          paper_list = []
          count = 0
          for paper in json_file:
              paperToSave = {}
              for k, v in json.loads(paper).items():
                  paperToSave[k] = v
              paper_list.append(paperToSave)
              count += 1
              if (count == 1000):
                  break     
          # print(paper_list)
          for paper in paper_list:
              t = join(paper['id'], " ", paper['authors'],
                        " ", paper['abstract'], " ", paper['categories'], " ", self.colocar("title",paper))
              t = self.clean_text(t.lower())
              #print(t)
              print(paper["id"])
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

          print(len(paper_list))
          for doc in paper_list:
              
              norma = 0
              for token in self.inverted_index.keys():
                  #print(token)
                  for paper in self.inverted_index[token]['papers']:
                      if doc['id'] == paper['id']:
                          norma += paper['tf_idf']**2
              norma = math.sqrt(norma)
              
              for token in self.inverted_index.keys():
                  for paper in range(len(self.inverted_index[token]['papers'])):
                      if doc['id'] == self.inverted_index[token]['papers'][paper]['id']:
                          self.inverted_index[token]['papers'][paper][
                              'norma'] = self.inverted_index[token]['papers'][paper]["tf_idf"]/norma


          print("DONE")
          with io.open('indice_invertido.json', 'w', encoding='utf8') as outfile:
              str_ = json.dumps(self.inverted_index,
                                indent=4, sort_keys=True,
                                separators=(',', ': '), ensure_ascii=False)
              outfile.write(str_)


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
          outfile.write(str_)

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
"""