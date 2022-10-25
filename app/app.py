from flask import Flask, render_template, request, redirect
from config import config
import requests
import json
from inverted_index import InvertedIndex

#rutas
from src.routes import papers_route 

app = Flask(__name__)

inverted_index = InvertedIndex("arxiv-metadata-oai-snapshot.json")


@app.route('/')
def index():
    return render_template('index.html')

#@app.route('/<id>', methods['GET'])
#def get_id(_id):
#    id = _id
    
#    return render_template('index.html',id)



if __name__ == '__main__':
    inverted_index.create_inverted_index()
    
    app.config.from_object(config['development'])
    
    app.register_blueprint(papers_route.main, url_prefix='/api/papers')
    app.run()
