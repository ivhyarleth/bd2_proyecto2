from flask import Flask, render_template, request, redirect, jsonify
from config import config
import requests
import json
from inverted_index import InvertedIndex
from GIN import GIN_index

# rutas
from src.routes import papers_route

app = Flask(__name__)
tables = ['papers_100_v2','papers_1000_v2','papaers_10000_v2']

inverted_index = InvertedIndex("arxiv-metadata-oai-snapshot.json")
indice_GIN = GIN_index("arxiv-metadata-oai-snapshot.json")


@app.route('/')
def index():
    return render_template('index.html')

# @app.route('/<id>', methods['GET'])
# def get_id(_id):
#    id = _id

#    return render_template('index.html',id)


@app.route('/kPrimeros', methods=["POST"])
def kPrimeros():
    consulta = request.form["consulta"]
    k = request.form["topK"]
    cosenos = inverted_index.compare_query(consulta)
    print("cosenos", cosenos[1])
    return jsonify({"data": cosenos[0][:int(k)], "tiempo": cosenos[1]})



if __name__ == '__main__':
    inverted_index.create_inverted_index()
    indice_GIN.create_GIN_index(tables) #Creo el indice GIN a todas las tablas
    #inverted_index.compare_query("solutions")

    #app.config.from_object(config['development'])

    #app.register_blueprint(papers_route.main, url_prefix='/api/papers')
    app.run()