from flask import Flask, render_template, request, redirect
from config import config
import requests
import json

#rutas
from src.routes import papers_route 

app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.config.from_object(config['development'])
    
    app.register_blueprint(papers_route.main, url_prefix='/api/papers')
    app.run()
