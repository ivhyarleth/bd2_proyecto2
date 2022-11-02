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
import heapq
import struct
import time
    
ROOT = "./"
EXT = ".json"


nltk.download('stopwords')
nltk.download('punkt')
stoplist = stopwords.words("english")
stoplist += ['?','aqui','.',',','»','«','â','ã','>','<','(',')','º','u']
stemmer = SnowballStemmer('english')


### FOR TESTING set positive
#NUMBER_OF_ENTRIES = 10000 #10000


class InvertedIndex:
    ROOT = "./"
    DATAFOLDER = "./data"

    """
    Class Initialization
    """    
    def __init__(self, data_filename , number_entries):
        # Origin File
        self.data_filename = data_filename
        # Binary Files
        self.database_data_filename = "database_data"
        self.database_head_filename = "database_head"
        self.tmp_head_filename = "tmpfile_head"
        self.database_extension = ".bin"
        # Index Files
        self.index_filename = "indice_invertido"
        self.index_extension = ".json"
        # Temporary Files
        self.tmp_filename = "tmpfile"
        # Properties/Config
        self.max_memory_usage = 4000000 # 4 MB
        self.HEADER_STRUCT = '32sIId'
        # Calculate header struct size in bytes
        entry = ("sample".ljust(32).encode('ascii'),1,1,0.0)
        self.HEADER_LEN = len(struct.pack(self.HEADER_STRUCT, *entry))
        self.NUMBER_OF_ENTRIES = number_entries

    
    ###################################################
    #              UTILITY FUNCTIONS
    ###################################################
    def get_file_size(self, file):
        return os.stat(file).st_size
    ###################################################
    #              PATH FUNCTIONS
    ###################################################
    def get_indexfile_path(self, number):
        return self.index_filename+str(number)+self.index_extension

    def get_tmpfile_path(self, number):
        return self.tmp_filename+str(number)+self.index_extension

    def get_database_datafile_path(self):
        return self.database_data_filename+self.database_extension

    def get_database_headfile_path(self, number):
        return self.database_head_filename+str(number)+self.database_extension

    def get_database_tmpheadfile_path(self, number):
        return self.tmp_head_filename+str(number)+self.database_extension

    def get_datafile_path(self):
        return os.path.join(InvertedIndex.DATAFOLDER, self.data_filename)
    
    ###################################################
    #              DATABASE FUNCTIONS
    ###################################################
    def save_paper_database(self, paper_entry):
        with io.open(self.get_database_datafile_path(), 'a', encoding='utf8') as outfile:
            data_pos = outfile.tell()
            jsondata = json.dumps(paper_entry,
                                ensure_ascii=False) + "\n"
            data_len = len(jsondata)
            outfile.write(jsondata)
            #print(data_pos, data_len)
            return data_pos, data_len
    
    def save_header_database(self, block_header, headerfile_id):
        with io.open(self.get_database_headfile_path(headerfile_id), 'wb') as outfile:
            block_header = sorted(block_header)
            for entry in block_header:
                data = struct.pack(self.HEADER_STRUCT, *entry)
                outfile.write(data)

    def read_headerfile(self, n):
        with open(self.get_database_headfile_path(n), 'rb') as f:
            chunk = f.read(self.HEADER_LEN)
            while chunk:
                data = struct.unpack(self.HEADER_STRUCT, chunk)
                yield data
                chunk = f.read(self.HEADER_LEN)

    def extract_paper_database(self, data_pos, data_len):
        with io.open(self.get_database_datafile_path(), 'r', encoding='utf8') as f:
            f.seek(data_pos)
            paper_entry = f.read(data_len)
            jsondata = json.loads(paper_entry)
            return jsondata


    def save_merge_header(self, tempfile_id, entry):
        tmpn_filepathn = self.get_database_tmpheadfile_path(tempfile_id)
        with io.open(tmpn_filepathn, 'ab') as outfile:
            data = struct.pack(self.HEADER_STRUCT, *entry)
            outfile.write(data)


    def update_header_database(self, entry, data_pos):
        with io.open(self.get_database_headfile_path(0), 'r+b') as outfile:
            outfile.seek(data_pos)
            data = struct.pack(self.HEADER_STRUCT, *entry)
            outfile.write(data)

    def extract_header_database(self, data_pos):
        with io.open(self.get_database_headfile_path(0), 'rb') as f:
            f.seek(data_pos)
            entry = f.read(self.HEADER_LEN)
            return struct.unpack(self.HEADER_STRUCT, entry)


    def search_header_database(self, paper_id):
        hfile = self.get_database_headfile_path(0)
        filesize = self.get_file_size(hfile)
        number_entries = int(filesize/self.HEADER_LEN)
        low = 0
        high = number_entries-1
        while low<=high:
            mid = (high + low) // 2
            data = self.extract_header_database(mid*self.HEADER_LEN)
            data_id = data[0]
            if data_id < paper_id:
                low = mid+1
            elif data_id > paper_id:
                high = mid-1
            else:
                return mid*self.HEADER_LEN
        return -1 # If not found

    def sqrt_header_norm_database(self):
        hfile = self.get_database_headfile_path(0)
        filesize = self.get_file_size(hfile)
        number_entries = int(filesize/self.HEADER_LEN)
        for i in range(number_entries):
            data = self.extract_header_database(i*self.HEADER_LEN)
            updated_norm = math.sqrt(data[3])
            modified_data = (data[0],data[1],data[2],updated_norm)
            self.update_header_database(modified_data, i*self.HEADER_LEN)

    ###################################################
    #              READ INDEXFILE FUNCTIONS
    ###################################################
    def read_indexfile(self, n):
        with open(self.get_indexfile_path(n), 'r') as f:
            for line in f:
                yield line

    def read_jsonblock(self,jsonpaper):
        return json.loads(jsonpaper)

    def find_entry(self, word):
        fileread = self.read_indexfile(0)
        for jsondata in fileread:
            entry = self.read_jsonblock(jsondata)
            entryword = list(entry.keys())[0]
            if (entryword == word):
                return entry[word]
        return None

    ###################################################
    #              MANAGEFILES
    ###################################################
    def remove_headerfile(self, n):
        os.remove(self.get_database_headfile_path(n))

    def rename_headerfile(self, a, b):
        os.rename(self.get_database_headfile_path(a), self.get_database_headfile_path(b))

    def rename_headertmpfile(self, n):
        os.rename(self.get_database_tmpheadfile_path(n), self.get_database_headfile_path(n))

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

    def extract_text_paper(self, paper_id, paper):
        return " ".join( (paper_id,
                 self.extract_field_paper('authors',paper),
                 self.extract_field_paper('abstract',paper),
                 self.extract_field_paper('categories',paper),
                 self.extract_field_paper('title',paper) ) )

    def extract_id_paper(self, paper):
        return paper["id"].ljust(32) # STRING OF SIZE 32

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
    
    def memory_usage_block_list_header(self, block_list_header):
        memory_usage = sys.getsizeof(block_list_header)
        for entry in block_list_header:
            memory_usage += sys.getsizeof(entry)
            for element in entry:
                memory_usage += sys.getsizeof(element)
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

    def clean_inverted_index(self):
        files = [self.get_database_datafile_path(), self.get_database_headfile_path(0), self.get_indexfile_path(0)]
        for f in files:
            if os.path.exists(f):
                os.remove(f)

    def create_inverted_index(self):
        
        #if os.path.isfile( self.get_indexfile_path(0) ):
        #    # If index already exists. Skip
        #    return
        self.clean_inverted_index()

        ## ------------------------- BUILD DATABASE ------------------------
        print(">>> BUILD DATABASE <<<")
        # Load JSON data file to database
        datastream = self.read_datafile()
        paper_count = 0
        headerfile_id = 0
        block_header = []
        for jsonpaper in datastream:
            saved = False
            paper = self.read_jsonpaper(jsonpaper)
            paper_id = self.extract_id_paper(paper)
            paper_data_entry = {
                'id':self.extract_field_paper('id',paper),
                'authors':self.extract_field_paper('authors',paper),
                'abstract':self.extract_field_paper('abstract',paper),
                'categories':self.extract_field_paper('categories',paper),
                'title':self.extract_field_paper('title',paper),
                'submitter':self.extract_field_paper('submitter',paper),
                'comments':self.extract_field_paper('comments',paper),
                'journal-ref':self.extract_field_paper('journal-ref',paper),
                'doi':self.extract_field_paper('doi',paper),
                'versions':self.extract_field_paper('versions',paper),
            }
            data_pos, data_len = self.save_paper_database(paper_data_entry)
            paper_head_entry = (paper_id.encode('ascii'), data_pos, data_len, 0.0)
            block_header.append(paper_head_entry)

            if self.memory_usage_block_list_header(block_header) > self.max_memory_usage:
                print("INFO: Memory usage exceeded at count {}. Creating new batch.".format(paper_count))
                # Save block list
                self.save_header_database(block_header, headerfile_id)
                block_header = []
                headerfile_id += 1
                saved = True
            
            paper_count += 1
            if (paper_count%500) == 0:
                print("INFO: Paper count:", paper_count)
            ########################## DEBUG ##########################
            # Limit number of entries for testing                     #
            ###########################################################
            if paper_count == self.NUMBER_OF_ENTRIES: 
                break
            ###########################################################
            

        if not saved:
            print("INFO: Saving last block")
            self.save_header_database(block_header, headerfile_id)
            headerfile_id += 1
        
        # Merge Headers in sorted form
        print(">>> MERGE HEADERS DATABASE <<<")
        number_headerfiles = headerfile_id-1
        merge_step = 2
        print("INFO: Original HeaderFile Number ", number_headerfiles)
        while (number_headerfiles): # While more than 1 header
            tmpfile_id = 0
            for i in range(0,number_headerfiles+1, merge_step):
                if (number_headerfiles >= i+1):
                    print("INFO: HeaderFiles Merged:",i," <> ",i+1)
                    block_a = self.read_headerfile(i)
                    block_b = self.read_headerfile(i+1)
                    valid_a = True
                    valid_b = True
                    tmpfile_id = int(i/2) 
                    entry_a = next(block_a)
                    entry_b = next(block_b)
                    # Select in order
                    while True:
                        if entry_a[0] < entry_b[0]:
                            self.save_merge_header(tmpfile_id, entry_a)
                            try:
                                entry_a = next(block_a)
                            except:
                                valid_a = False
                                break
                        else:
                            self.save_merge_header(tmpfile_id, entry_b)
                            try:
                                entry_b = next(block_b)
                            except:
                                valid_b = False
                                break
                    # Iterate remanining
                    print(valid_a, valid_b)
                    while (valid_a):
                        self.save_merge_header(tmpfile_id, entry_a)
                        try:
                            entry_a = next(block_a)
                        except:
                            valid_a = False
                            break
                    while (valid_b):
                        self.save_merge_header(tmpfile_id, entry_b)
                        try:
                            entry_b = next(block_b)
                        except:
                            valid_b = False
                            break
                    print(valid_a, valid_b)
                    # Overwrite old files
                    self.remove_headerfile(i)
                    self.remove_headerfile(i+1)
                    self.rename_headertmpfile(tmpfile_id)
                else:
                    print("INFO: Single Header File Skipped:",i)
                    tmpfile_id+=1
                    self.rename_headerfile(i, tmpfile_id)

            # Update number of files
            number_headerfiles = tmpfile_id
            print("INFO: Current Number of HeaderFiles:", number_headerfiles)
            
        ## ------------------------- CREATE INDEX ------------------------
        print(">>> BUILD INDEX <<<")
        headerfile = self.read_headerfile(0)

        # SPIMI INVERT
        # Init block dict
        block_dict = {}
        indexfile_id = 0
        paper_count = 0
        for header_entry in headerfile:
            saved = False
            # Extract paper id
            paper_id = header_entry[0].decode('ascii')
            data_pos = header_entry[1]
            data_len = header_entry[2]
            # Extract paper data
            paper = self.extract_paper_database(data_pos, data_len)
            # Extract text from paper
            text = self.extract_text_paper(paper_id,paper)
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
            paper_count += 1
            if (paper_count%500) == 0:
                print("INFO: Paper count:", paper_count)
            # Check if filesize exceeded
            if self.memory_usage_block_dict(block_dict) > self.max_memory_usage:
                print("INFO: Memory usage exceeded at count {}. Creating new batch.".format(paper_count))
                # Save block dict
                self.save_block_dict(block_dict, indexfile_id)
                block_dict = {}
                indexfile_id += 1
                saved = True
        # If last block not saved, save
        if not saved:
            print("INFO: Saving last block")
            self.save_block_dict(block_dict, indexfile_id)
            indexfile_id += 1
        number_indexfiles = indexfile_id-1

        # SPIMI MERGE
        print(">>> MERGE INDEX <<<")
        merge_step = 2 #merge_total_levels = math.ceil( (number_indexfiles+1) **(1/2))

        print("INFO: Original IndexFile Number ", number_indexfiles)
        while (number_indexfiles): # While more than 1 file
            tmpfile_id = 0
            for i in range(0,number_indexfiles+1, merge_step):
                print("INFO: IndexFile Pointer ",i)
                if (number_indexfiles >= i+1):
                    print("INFO: IndexFiles Merged:",i," <> ",i+1)
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
            print("INFO: Current Number of IndexFiles:", number_indexfiles)
        
        # ADD TF.IDF TO INDEX
        print(">>> CALCULATING TFIDF <<<")
        base_index = self.read_indexfile(0)
        word_block = self.read_jsonblock(next(base_index))
        while (True):
            word = list(word_block.keys())[0]
            # Calculate IDF
            IDF = math.log(paper_count / len(word_block[word]))
            # Calculate TF*IDF
            for id_paper in word_block[word]:
                TF = 1+math.log(word_block[word][id_paper])
                word_block[word][id_paper] = TF*IDF
                # Update norm in header
                data_pos = self.search_header_database(id_paper.encode('ascii'))
                data = self.extract_header_database(data_pos)
                #norm += (TF*IDF) ** 2
                updated_norm = data[3] + (TF*IDF)**2
                modified_data = (data[0],data[1],data[2],updated_norm)
                self.update_header_database(modified_data, data_pos)
            # Total Block
            index_word_block = {word:{"papers":word_block[word],"IDF":IDF}} # NOTE: norm inecesario?
            # Write to temp
            self.save_calc_dict(index_word_block)
            try:
                word_block = self.read_jsonblock(next(base_index))
            except:
                break
        # UPDATE NORM TO SQRT
        print(">>> UPDATE NORM <<<")
        self.sqrt_header_norm_database()
        # OVERWRITE INDEX
        self.rename_tmpfile(0)

        print(">>> --- END --- <<<")


    def compare_query(self, query, k):
        start_time = time.time()
        
        query = self.clean_text(query)
        
        # Init query dict
        index_query = {}
        
        # CONTEO DE TOKENS
        for word in query:
            word = word.lower()
            if word not in stoplist:
                tokenq = stemmer.stem(word)
                if tokenq not in index_query:
                    index_query[tokenq] = 1
                index_query[tokenq] += 1
        
        # CALCULO DE TF.IDF de la QUERY y PROD COSENO
        norma_query = 0
        papers_data = {}
        for tokenq in index_query.keys():
            entry = self.find_entry(tokenq)
            if entry:
                TF = 1+math.log(index_query[tokenq])
                IDF = entry["IDF"]
                TFIDF = TF*IDF
                norma_query += (TFIDF) ** 2
                for paper_id in entry["papers"]:
                    cosine_pq = TFIDF * entry["papers"][paper_id]
                    if paper_id in papers_data:
                        papers_data[paper_id]["cos"] += cosine_pq
                    else:
                        papers_data[paper_id] = {}
                        papers_data[paper_id]["cos"] = cosine_pq
        norma_query = math.sqrt(norma_query)

        # Normalizar
        similarity = []
        for paper_id in papers_data:
            # Calculate Cosine Norm
            data_pos = self.search_header_database(paper_id.encode('ascii'))
            data = self.extract_header_database(data_pos)
            papers_data[paper_id]["norm"] = data[3]
            papers_data[paper_id]["cos"] = papers_data[paper_id]["cos"] / (norma_query * papers_data[paper_id]["norm"])
            sim = papers_data[paper_id]["cos"]
            # KNN with heap
            if len(similarity) < k:
                heapq.heappush(similarity, (sim, paper_id))
            else:
                current_max = similarity[0]
                if current_max[0] < sim:
                    heapq.heappop(similarity)
                    heapq.heappush(similarity, (sim, paper_id))

        # Transform similarity to expected output by frontend
        data_index = []
        for sim, paper_id in similarity:
            header_data_pos = self.search_header_database(paper_id.encode('ascii'))
            header_data = self.extract_header_database(header_data_pos)
            info = self.extract_paper_database(header_data[1],header_data[2])

            data_index.append(
                    {"val": str(sim), "info": info}
            )

        #print(similarity)
        #with io.open('cosenos.json', 'w', encoding='utf8') as outfile:
        #    str_ = json.dumps(similarity,
        #                        indent=4, sort_keys=True,
        #                        separators=(',', ': '), ensure_ascii=False)
        #    outfile.write(str_)

        return [sorted(data_index, key=lambda v: v['val'], reverse=True), round((time.time()-start_time)*1000, 4)]

