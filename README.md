### BD2 - Grupo 4

**_Integrantes:_**

- Salazar Alva, Rodrigo Gabriel
- Sara Junco, Juan Sebastian
- Ponce Contreras, Luis Eduardo
- Lapa Carhuamaca, Arleth Ivhy
---
# Proyecto 2 | Recuperación de Documentos de Texto

## Descripción del dominio de datos
## Introducción


La recuperación de documentos de texto basadas en el contenido es uno de los campos más estudiados en el área de base de datos, por ende, en el presente trabajo se tiene como objetivo entender y aplicar los algoritmos de búsqueda y recuperación, por lo que, este proyecto está enfocado en la construcción de un índice invertido para la realización de este tipo de tareas. Asimismo, se desarrollará una interfaz gráfica para poder comparar dichos resultados de Python con PostgreSQL y analizar los tiempos de recuperación. Cabe resaltar, que la data que se usará será de un repositorio de la página Kagle que tiene como temática los papers.

El siguiente informe se basará en dos aspectos. En primer lugar, se implementará el Índice Invertido utilizando un modelo de recuperación basado en ranking para consultas de texto libre. En adición, el scoring se debe de aplicar todo en memoria secundaria, por ende se usará el algoritmo de Single-pass in-memory indexing (SPIMI) para el cálculo de la similitud de coseno. En segundo lugar, se utilizará el índice GIN para poder ejecutar las consultas en PostgreSQL y de esa forma poder realizar un análisis, discusión y comparación de los resultados.

## Backend
Se ha construido un índice invertido óptimo para la busqueda y recuperación de _papers_  por ranking (top k) para consultas de texto libre.
### Construcción del índice invertido
#### Preprocesamiento
*Filtrado de stopwords*
La librería _nltk_ crea los _stopwords_ en inglés, debido a la data se encuentra en ese idioma.
```
nltk.download('stopwords')
nltk.download('punkt')
stoplist = stopwords.words("english")
stoplist += ['?','.',',','»','«','â','ã','>','<','(',')','º','u']
```
*Reducción de palabras (Stemming)*
La librería _SnowballStemmer_ obtiene las raíces de las palabras de nuestra _data_, las cuales se usan para el proceso de tokenización.
```
stemmer = SnowballStemmer('english')
stem_token = stemmer.stem(word)
```
*Toquenizacion*
Se implementó una función que realiza la limpieza del texto, la cual removerá caracteres principales y urls.
```
def  clean_text(self, text):
	text = self.remove_special_character(text)
	text = self.remove_punctuation(text)
	text = self.remove_url(text)
	text = nltk.word_tokenize(text)
	return  text
```
- remove_punctuation -> Remueve la puntuacion
- remove_url -> Remueve las URL's
-  remove_special_character -> Remueve caracteres especiales
-  clean_text -> Se encarga de tokenizar las palabras del texto

El proceso para la obtención de los tokens es aplicar la función de limpieza y guardar el texto en *text_tokenized*, luego recorrer todas las palabras del texto de los _papers_ y obtener sus raíces, finalmente insertarlos en la lista *block_dict[]*.
```
# Extract text from paper
text = self.extract_text_paper(paper_id,paper)
text_tokenized = self.clean_text(text)

# Tokenize text
for  word  in  text_tokenized:
	if  word  not  in  stoplist:
		stem_token = stemmer.stem(word)
		# Insert into posting list
		if  stem_token  in  block_dict:
			# Add 1 to count
			if  paper_id  in  block_dict[stem_token]:
				block_dict[stem_token][paper_id] += 1
			else:
				block_dict[stem_token][paper_id] = 1
		else:
			block_dict[stem_token] = {}
			block_dict[stem_token][paper_id] = 1
```

#### Construcción del índice

Para la construcción del índice invertido se tiene como base principal una clase a la cual denominaremos "InvertedIndex". En dicha clase, se ha distribuido en distintas funciones los pasos para la construcción de este índice.  

La función "create_inverted_index" contiene la estructura del índice invertido para guardar los pesos TF-IDF, además que esta función incluye la construcción del índice en memoria secundaria el cual utiliza el algoritmo de *Single-pass in-memory indexing (SPIMI)*. Este algoritmo realiza la construcción del índice en memoria secundaria, debido a que este algoritmo es óptimo para el manejo de una gran colección de datos que contiene nuestra _data_. Este genera diccionarios (Hash) separados para cada bloque, sin necesidad de mantener el mapeo *<termino - IdTermino>* entre los bloques, además, esta no se debe de ordenar, sino acumular en el hash las publicaciones en listas a medida que van ocurriendo y al final se debe de ejecutar un merge en un "Big Index".A continuación, se mencionan las funciones que son parte de la implementación del algoritmo:
- save_block_dict
- save_merge_dict
- save_calc_dict
- memory_usage_block_dict
- memory_usage_block_list_header

#### Consulta
Se recibe una consulta ingresada por el usuario, esta es una frase en lenguaje natural, para obtener los resultados de dicha consulta se implementó la función *compare_query(query)*, la cual realiza el siguiente procedimiento:
-   Limpia la _query_ en lenguaje natural
-   Calcula el _td_ e _idf_
-   Halla la frecuencia de cada palabra en el _query_
-   Si la palabra esta en un indice invertido, se calcula el indice invertido
-   Obtiene el *tf-idf* del _query_
- 
Al final, se ordena la lista de cosenos obtenidos, donde se guarda el *paper_id** del documento, la similitud respectiva y su lista de _papers_ de mayor a menor por el que tenga mayor similitud .
```
similarity = []
for  paper_id  in  papers_data:
	data_pos = self.search_header_database(paper_id.encode('ascii'))
	data = self.extract_header_database(data_pos)
	papers_data[paper_id]["norm"] = data[3]
	papers_data[paper_id]["cos"] = papers_data[paper_id]["cos"] / (norma_query * papers_data[paper_id]["norm"])
	similarity.append( {"paper":paper_id,"similarity":papers_data[paper_id]["cos"]} )
```
### Manejo de memoria secundaria
Para poder garantizar la escalabilidad de la base de datos indexada, se ha unido el algoritmo mencionado en la seccion previa con el algoritmo de SPIMI.
Para ello, se maneja con tres archivos principales:

- database_data.bin  : Archivo de texto de longitud variable. Contiene la data de cada paper
- database_head0.bin : Archivo binario de texto que sirve como cabecera para database_data.bin, garantizando acceso en O(1) y busqueda en O(log n)
- indice_invertido0.json : Indice invertido

Entonces, primero construimos nuestros archivos database utilizando usando buckets de head y un mergesort. Cada entrada en el archivo header contiene (paper_id, pos_data, pos_len, norm). Donde norm es inicializado en 0.0 y sera usado como el valor sobre el cual debemos dividir el coseno calculado con dicho documento para normalizarlo.

Se presenta el algoritmo simplificado para crear la database:
```
# CREATE DATABASE
block_header = []
headerfile_id = 0
for jsonpaper in datastream:
    saved = False
    paper = read_jsonpaper(jsonpaper)
    data_pos, data_len = save_paper_database(paper_data_entry)
    block_header.append( (paper.id, data_pos, data_len, 0.0) )

    if memory_usage > max_memory_usage:
        save_header_database(block_header, headerfile_id)
        block_header = []
        headerfile_id += 1
        saved = True
    
    paper_count += 1
if not saved:
    print("INFO: Saving last block")
    save_header_database(block_header, headerfile_id)
    headerfile_id += 1

# MERGE HEADERS
number_headerfiles = headerfile_id-1
while (number_headerfiles != 0):    # While more than 1 header
    tmpfile_id = 0
    for i in range(0,number_headerfiles+1, 2):
        if (number_headerfiles >= i+1):
            # Merge and & i+1
            block_a = read_headerfile(i)
            block_b = read_headerfile(i+1)
            tmpfile_id = int(i/2) 
            # Select in order
            while (block_a && block_b)):
                if entry_a[0] < entry_b[0]:
                    save_merge_header(tmpfile_id, block_a.entry)
                    block_a.next_entry()
                else:
                    save_merge_header(tmpfile_id, block_b.entry)
                    block_b.next_entry()
            # Iterate remanining
            while (block_a):
                save_merge_header(tmpfile_id, block_a.entry)
                block_a.next_entry()
            while (valid_b):
                save_merge_header(tmpfile_id, block_b.entry)
                block_b.next_entry()
            remove_headerfile(i)
            remove_headerfile(i+1)
            rename_headertmpfile(tmpfile_id)
        else:
            # Skip lonely file
            tmpfile_id+=1
            rename_headerfile(i, tmpfile_id)
    # Update number of files
    number_headerfiles = tmpfile_id
```

Posteriormente, con la database creamos el indice usando el algoritmo de la seccion previa. Este a sido fusionado con SPIMI. De esta forma, en vez de guardar una diccionario de listas {word:docID_list}, se guarda un diccionario de diccionario de repeticiones {word:{docID:count}}. El algoritmo simplicado para realizar esta operacion se muestra a continuacion.
```
# CREAR INDICE PRELIMINAR

# SPIMI INVERT
# Init block dict
block_dict = {}
indexfile_id = 0
for paper in database:
    saved = False
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
    if memory_usage > max_memory_usage:
        # Save block dict
        save_block_dict(block_dict, indexfile_id)
        block_dict = {}
        indexfile_id += 1
        saved = True
# If last block not saved, save
if not saved:
    save_block_dict(block_dict, indexfile_id)
    indexfile_id += 1


# SPIMI MERGE
number_indexfiles = indexfile_id-1
merge_step = 2

while (number_indexfiles!=0): # While more than 1 file
    tmpfile_id = 0
    for i in range(0,number_indexfiles+1, merge_step):
        if (number_indexfiles >= i+1):
            block_a = self.read_indexfile(i)
            block_b = self.read_indexfile(i+1)
            tmpfile_id = int(i/2) 
            while (True):
                word_a = block_a.word
                word_b = block_a.word
                if word_a == word_b:
                    # If word is the same, merge
                    word_block_next = block_a
                    for paper_id in block_a[word_a]:
                        t =  block_a[word_a][paper_id]
                        if paper_id in word_block_next[word_a]:
                            word_block_next[word_a][paper_id] += t
                        else:
                            word_block_next[word_a][paper_id] =  t
                    save_merge_dict(tmpfile_id, word_block_next)
                    word_a.next_entry()
                    word_b.next_entry()
                else:
                    # If different, add in order
                    if word_a < word_b:
                        save_merge_dict(tmpfile_id, block_a)
                        block_a.next_entry()
                    else:
                        self.save_merge_dict(tmpfile_id, block_b)
                        block_b.next_entry()
            # Iterate remanining
            while (block_a):
                save_merge_dict(tmpfile_id, block_a)
                block_a.next_entry()
            while (valid_b):
                self.save_merge_dict(tmpfile_id, block_b)
                block_b.next_entry()

            # Overwrite old files
            remove_indexfile(i)
            remove_indexfile(i+1)
            rename_tmpfile(tmpfile_id)
        else:
            # Skip lonely file
            tmpfile_id+=1
            rename_indexfile(i, tmpfile_id)

    # Update number of files
    number_indexfiles = tmpfile_id
```

El archivo preliminar obtenido de hacer el InvertSPIMI y MergeSPIMI luego se itera sequencialmente para convertir los diccionarios {word:{docID:count}} en diccionarios de {word:{docID:TF-IDF}} y calcular la norma de los documentos (actualizando en el header). El algoritmo simplicado para realizar esta operacion se muestra a continuacion.

```
base_index = read_indexfile(0)
word_block = base_index.entry
while (base_index):
    word = word_block.word
    # Calculate IDF
    IDF = math.log( paper_count / len(word_block.papers))
    # Calculate TF*IDF
    for id_paper in word_block.papers:
        TF = 1+math.log(word_block.papers[id_paper])
        word_block.papers[id_paper] = TF*IDF
        # Update norm in header
        data_pos = search_header_database(id_paper)
        data = extract_header_database(data_pos)
        data.norm += data.norm + (TF*IDF)**2
        update_header_database(data, data_pos)
    # Total Block
    index_word_block = {word:{"papers":word_block[word],"IDF":IDF}}
    # Write to temp
    save_calc_dict(index_word_block)
    #Next
    base_index.next_entry()
# UPDATE NORM TO SQRT
sqrt_header_norm_database()
# OVERWRITE INDEX
rename_tmpfile(0)
```

### Ejecuccion Optima de consultas
Las consultas se ejecutan de forma optima utilizando el indice invertido construido con los pasos previamente explicados. 

Para ello, primero se constuye un diccionario de conteo de palabras de la query dada como entrada. Con dicho diccionario se itera sobre cada una de sus palabras: se busca en el indice invertido. Si esta existe, se extrae el IDF para calcular el TFIDF del termino para la query, y para cada documento que aparece en el indice con ese termino, se calcula su producto, agregandolos a un diccionario de papers (agregando el paper si no esta, o sumando el valor calculado si ya existe). En paralelo, se obtiene la norm de la query.

Con el diccionario de producto coseno por paper, este se normaliza usando la norm de la query calculada y la norm del paper, extraido de database_head0.bin en O(log n) por busqueda binaria. El valor normalizado se inserta a un heap de los k mas similares. El resultado es un arreglo con los k papers mas similares.
```
index_query = {}

# CONTEO DE TOKENS
for word in query:
    word = clean(word)
    if word not in stoplist:
        tokenq = stemmer.stem(word)
        if tokenq not in index_query:
            index_query[tokenq] = 1
        else:
            index_query[tokenq] += 1

# CALCULO DE TF.IDF de la QUERY y PROD COSENO
norma_query = 0
papers_data = {}
for tokenq in index_query:
    entry = find_entry_in_index(tokenq)
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

# Normalizar con filtro de KNN
similarity = []
for paper_id in papers_data:
    # Calculate Cosine Norm
    data_pos = search_header_database(paper_id.encode('ascii'))
    data = extract_header_database(data_pos)
    papers_data[paper_id]["norm"] = data.norm
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
```


## Frontend

### Diseño del índice con PostgresSQL
La presentación final en video se encuentra en el siguiente [link](url).
### Análisis comparativo con su propia implementación

### GUI


