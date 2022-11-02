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
> remove_punctuation -> Remueve la puntuacion
> remove_url -> Remueve las URL's
>  remove_special_character -> Remueve caracteres especiales
>  clean_text -> Se encarga de tokenizar las palabras del texto
> 
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

Para la construcción del índice invertido se tiene como base principal una clase a la cual denominaremos "InvertedIndex". En dicha clase, se ha distribuido en distintas funciones los pasos para la construcción de este índice.  La función "create_inverted_index" contiene la estructura del índice invertido para guardar los pesos TF-IDF, además que esta función incluye la construcción del índice en memoria secundaria el cual utiliza el algoritmo de Single-pass in-memory indexing (SPIMI). A continuación, se mencionan las funciones que son parte de la implementación del algoritmo:

>SPIMI

Este genera diccionarios (Hash) separados para cada bloque, sin necesidad de mantener el mapeo <termino - IdTermino> entre los bloques, además, esta no se debe de ordenar, sino acumular en el hash las publicaciones en listas a medida que van ocurriendo y al final se debe de ejecutar un merge en un "Big Index". Las funciones que contienen estos pasos son:
- save_block_dict
- save_merge_dict
- save_calc_dict
- memory_usage_block_dict
- memory_usage_block_list_header


#### Consulta

### Manejo de memoria secundaria

### Ejecución óptima de consultas

  

## Frontend

### Diseño del índice con PostgresSQL
La presentación final en video se encuentra en el siguiente [link](url).
### Análisis comparativo con su propia implementación

### GUI


