from src.database.db import get_connection
from .entities.paper_class import Paper

class PaperModel():
    
    @classmethod
    def get_all(self):
        try:
            connection=get_connection()
            papers=[]
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, submitter, authors, title, comments, journalref, doi, abstract, categories, versions FROM papers ORDER BY title ASC")
                resultset = cursor.fetchall()
                
                for row in resultset:
                    paper = Paper(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
                    papers.append(paper.to_JSON())
                connection.close()
            return papers      
        except Exception as ex:
            raise Exception(ex)
    
    @classmethod
    def get_paper(self,id):
        try:
            connection = get_connection()
            
            with connection.cursor() as cursor:
                cursor.execute("SELECT id, submitter, authors, title, comments, journalref, doi, abstract, categories, versions FROM papers WHERE id = %s",(id,))
                row = cursor.fetchone()
                paper=None
                if row != None:
                    paper = Paper(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8], row[9])
                    paper = paper.to_JSON()
              
                connection.close()
            return paper      
        except Exception as ex:
            raise Exception(ex)