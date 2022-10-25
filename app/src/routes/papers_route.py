from flask import Blueprint, jsonify
from src.models.paper_model import PaperModel
main=Blueprint('papers_blueprint', __name__)

@main.route('/')
def get_papers():
    try:
        papers=PaperModel.get_all()
        return jsonify(papers)
    except Exception as ex:
        return jsonify({'message': str(ex)}),500

@main.route('/<id>')
def get_paper(id):
    try:
        paper=PaperModel.get_paper(id)
        if paper != None:
            return jsonify(paper)
        else:
            return jsonify({}),404

    except Exception as ex:
        return jsonify({'message': str(ex)}),500