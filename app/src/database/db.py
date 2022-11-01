import psycopg2
from psycopg2 import DatabaseError
from decouple import config

def get_connection():
    try:
        #print("Connecting to database ...")
        return psycopg2.connect(
            host=config('PGSQL_HOST'),
            user=config('PGSQL_USER'),
            password=config('PGSQL_PASSWORD'),
            database=config('PGSQL_DATABASE')
        )
        #print("coneccion exitosa")
    except DatabaseError as ex:
        raise ex

