import psycopg2
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

    def create_GIN_index(self,tables):
        for table in tables:
            print("Validating GIN index for table {table}".format(table=table))
            #self.alter_table(table)
            #self.update_table(table)
            self.stored_method_extend_table(table)
            self.create_index(table)