from flask import Flask
from .services.faiss_retriever import FaissRetriever

def create_app():
    app = Flask(__name__)
    
    app.retriever = FaissRetriever()
    app.retriever.load_index()

    from app.routes import main_bp
    app.register_blueprint(main_bp)

    return app