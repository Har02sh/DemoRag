from flask import Blueprint, render_template, jsonify, request, current_app
from .services.faiss_retriever import FaissRetriever

retriever = FaissRetriever()
main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def home():
    return render_template('index.html')

@main_bp.route('/api/chat', methods=["POST"])
def rag():
    data = request.get_json()
    question = data.get("question")
    answer = current_app.retriever.generate_response(query_text=question)
    return jsonify({"message":"success", "answer":answer})