import psycopg2
import re
import time
from src.database.db import get_connection
from src.models.entities.paper_class import Paper

class GIN_index():
    dataname = ""
    
    def __init__(self,dfname):
        self.dataname=dfname
    
    @classmethod
    def alter_table(self,table):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_alter = "ALTER TABLE {table} ADD COLUMN IF NOT EXISTS search_txt tsvector;".format(table=table)
                cursor.execute(consulta_alter)
                connection.commit()
        except Exception as e:
            raise Exception(e)
        
    @classmethod
    def update_table(self,table):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_update = "UPDATE {table} SET search_txt = setweight(to_tsvector('english', id), 'A') || setweight(to_tsvector('english', title), 'B') || setweight(to_tsvector('english', categories), 'C');".format(table=table)
                cursor.execute(consulta_update)
                connection.commit()
        except Exception as e:
            raise Exception(e)
        
    @classmethod    
    def create_index(self,table):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_create = "CREATE INDEX IF NOT EXISTS paper_search_{table} ON {table} USING GIN (search_txt);".format(table=table)
                cursor.execute(consulta_create)
                connection.commit()
        except Exception as e:
            raise Exception(e)

    @classmethod
    def stored_method_extend_table(self,table):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_alter = """DO $$
                    BEGIN
                    IF NOT EXISTS (SELECT column_name
                                   FROM information_schema.columns
                                   WHERE  table_schema = 'public' 
                                   AND  table_name = '{table}' 
                                   AND  column_name = 'search_txt') THEN
                        ALTER TABLE {table} ADD COLUMN search_txt tsvector;
                        UPDATE {table} SET search_txt = setweight(to_tsvector('english', id), 'A') || setweight(to_tsvector('english', title), 'B') || setweight(to_tsvector('english', categories), 'C');
                    END IF;
                    END
                    $$
                    """.format(table=table)
                cursor.execute(consulta_alter)
                connection.commit()
        except Exception as e:
            raise Exception(e)

    @classmethod
    def query_knn_table(self,table, input_query, k):
        start_time = time.time()
        input_query = re.sub(r'[^A-Za-z0-9 ]+', ' ', input_query) # Only alphanumeric
        query= " | ".join(input_query.split())
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_get = """
                SELECT id, authors, abstract, categories, title, ts_rank_cd(search_txt, query) AS similarity
                FROM {table}, to_tsquery('english', '{query}') query
                where query @@ search_txt
                order by similarity desc
                limit {k};
                    """.format(table=table, query=query, k=k)
                consulta_analyze = "EXPLAIN ANALYZE " + consulta_get
                cursor.execute(consulta_analyze)
                explain_analyze = cursor.fetchall()
                planning_time = float(re.search("\d+\.\d+",explain_analyze[-2][0])[0])
                execution_time = float(re.search("\d+\.\d+",explain_analyze[-1][0])[0])
                total_time = planning_time+execution_time
                print("GIN Query:", query)
                print("GIN Pgtime:", total_time)
                cursor.execute(consulta_get)
                results = cursor.fetchall()
                connection.commit()
            
            
            data_index = []
            for paper_tuple in results:
                sim = paper_tuple[5]
                paper_id = paper_tuple[0]
                paper_authors = paper_tuple[1]
                paper_abstract = paper_tuple[2]
                paper_categories = paper_tuple[3]
                paper_title = paper_tuple[4]
                info = {
                    "id":paper_id,
                    "submitter": "-",
                    "authors": paper_authors,
                    "title": paper_title,
                    "comments": "-",
                    "journal-ref":"-",
                    "doi" :"-",
                    "abstract" :paper_abstract,
                    "categories" : paper_categories,
                    "versions" : "-",
                }

                data_index.append({"val": str(sim), "info": info})

            return [sorted(data_index, key=lambda v: v['val'], reverse=True), total_time]#round((time.time()-start_time)*1000, 4)]

        except Exception as e:
            raise Exception(e)

    def create_GIN_index(self,tables):
        for table in tables:
            print("Validating GIN index for table {table}".format(table=table))
            #self.alter_table(table)
            #self.update_table(table)
            self.stored_method_extend_table(table)
            self.create_index(table)