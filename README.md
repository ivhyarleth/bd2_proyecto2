### BD2 - Grupo 4

**_Integrantes:_**

- Salazar Alva, Rodrigo Gabriel
- Sara Junco, Juan Sebastian
- Ponce Contreras, Luis Eduardo
- Lapa Carhuamaca, Arleth Ivhy
---
# Proyecto 2 | Recuperación de Documentos de Texto

  

## Descripción del dominio de datos

  

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
### Manejo de memoria secundaria

### Ejecución óptima de consultas

  

## Frontend

### Diseño del índice con PostgresSQL
La presentación final en video se encuentra en el siguiente [link](url).
### Análisis comparativo con su propia implementación

### GUI


