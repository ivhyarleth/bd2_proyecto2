import psycopg2
from src.database.db import get_connection
from .src.models.entities.paper_class import Paper

class GIN_index():
    dataname = ""
    
    def __init__(self,dfname):
        self.dataname=dfname
    
    @classmethod
    def alter_table(self,table):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_alter = "ALTER TABLE %s ADD COLUMN search_txt tsvector;"
                par = (table,)
                cursor.execute(consulta_alter,par)
                connection.commit()
        except Exception as e:
            raise Exception(e)
        
    @classmethod
    def update_table(self,table):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_update = "UPDATE %s SET search_txt = setweight(to_tsvector('english', id), 'A') || setweight(to_tsvector('english', title), 'B') || setweight(to_tsvector('english', categories), 'C');"
                par = (table,)
                cursor.execute(consulta_update,par)
                connection.commit()
        except Exception as e:
            raise Exception(e)
        
    @classmethod    
    def create_index(self,table):
        try:
            connection = get_connection()
            with connection.cursor() as cursor:
                consulta_create = "CREATE INDEX paper_search ON %s USING GIN (search_txt);"
                par = (table,)
                cursor.execute(consulta_create,par)
                connection.commit()
        except Exception as e:
            raise Exception(e)

    def create_GIN_index(self,tables):
        for table in tables:
            self.alter_table(table)
            self.update_table(table)
            self.create_index(table)