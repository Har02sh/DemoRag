import faiss
import numpy as np
import pickle
from sentence_transformers import SentenceTransformer
import ollama
import os

class FaissRetriever:
    def __init__(self, 
                 model_name='all-mpnet-base-v2', 
                 index_path=r"D:\Rag\app\services\countries_index.index", 
                 mapping_path= r"D:\Rag\app\services\countries_id_to_text.pkl",
                 use_cosine=False):
        """
        :param model_name: Name of the Sentence Transformer model.
        :param index_path: File path to persist the FAISS index.
        :param mapping_path: File path to persist the mapping (index to original text).
        :param use_cosine: If True, uses cosine similarity (requires normalization) with inner product.
                           Otherwise, uses L2 distance (native).
        """
        self.model = SentenceTransformer(model_name)
        self.index = None
        self.id_to_text = {}
        self.index_path = index_path
        self.mapping_path = mapping_path
        self.use_cosine = use_cosine  # For now, keep this False for L2 distance
        self.embedding_dim = None

    def create_index(self, text_chunks):
        """
        Generate embeddings for the provided text chunks and create a FAISS index.
        :param text_chunks: List of text strings.
        """
        # Generate embeddings using the Sentence Transformer model
        embeddings = self.model.encode(text_chunks, convert_to_numpy=True)
        # If using cosine similarity, normalize the embeddings. For L2, skip normalization.
        if self.use_cosine:
            embeddings = embeddings / np.linalg.norm(embeddings, axis=1, keepdims=True)
        self.embedding_dim = embeddings.shape[1]
        # Create a FAISS index based on the similarity measure
        if self.use_cosine:
            self.index = faiss.IndexFlatIP(self.embedding_dim)
        else:
            self.index = faiss.IndexFlatL2(self.embedding_dim)
        # Add embeddings to the index
        self.index.add(embeddings)
        # Build a mapping from index id to the original text chunk
        self.id_to_text = {i: text for i, text in enumerate(text_chunks)}

    def add_texts(self, text_chunks):
        """
        Add new text chunks to an existing index.
        :param text_chunks: List of new text strings to be added.
        """
        if self.index is None:
            raise ValueError("Index not created yet. Call create_index() first.")
        new_embeddings = self.model.encode(text_chunks, convert_to_numpy=True)
        if self.use_cosine:
            new_embeddings = new_embeddings / np.linalg.norm(new_embeddings, axis=1, keepdims=True)
        start_idx = len(self.id_to_text)
        self.index.add(new_embeddings)
        for i, text in enumerate(text_chunks):
            self.id_to_text[start_idx + i] = text

    def save_index(self):
        """
        Persist the FAISS index and mapping to disk.
        """
        if self.index is not None:
            faiss.write_index(self.index, self.index_path)
            with open(self.mapping_path, "wb") as f:
                pickle.dump(self.id_to_text, f)
        else:
            print("No index available to save.")

    def load_index(self):
        """
        Load a persisted FAISS index and its mapping from disk.
        """
        if not os.path.exists(self.index_path):
            raise FileNotFoundError(f"FAISS index file not found: {self.index_path}")
        self.index = faiss.read_index(self.index_path)
        with open(self.mapping_path, "rb") as f:
            self.id_to_text = pickle.load(f)
        print("Index loaded properly.")

    def query(self, query_text, k=3):
        """
        Query the FAISS index to find the top-k most similar text chunks.
        :param query_text: The query string.
        :param k: Number of nearest neighbors to retrieve.
        :return: A list of dictionaries containing the text and its similarity score.
        """
        query_embedding = self.model.encode([query_text], convert_to_numpy=True)

        # Check if FAISS index is initialized
        if self.index is None:
            raise ValueError("FAISS index is not initialized.")

        # Check if FAISS index has any documents
        if self.index.ntotal == 0:
            raise ValueError("FAISS index is empty. Add documents before searching.")

        # Ensure query vector dimension matches FAISS index dimension
        if query_embedding.shape[1] != self.index.d:
            raise ValueError(f"Query dimension {query_embedding.shape[1]} does not match FAISS index dimension {self.index.d}.")
        if self.use_cosine:
            query_embedding = query_embedding / np.linalg.norm(query_embedding, axis=1, keepdims=True)
        distances, indices = self.index.search(query_embedding, k)
        results = []
        for idx, score in zip(indices[0], distances[0]):
            text = self.id_to_text.get(idx, "Text not found")
            results.append({"text": text, "score": score})
        return results
    
    def generate_response(self, query_text, model="mistral:7b"):
        """
        Generate a response using Ollama by providing context retrieved from FAISS.
        :param query_text: User's input query.
        :param model: Ollama model to use (default: mistral).
        :return: The generated response from Ollama.
        """
        # Retrieve relevant documents
        top_docs = self.query(query_text, k=3)
        if not top_docs:
            return "I couldn't find relevant information. Could you clarify your question?"
        
        # Construct the prompt using retrieved context
        context = "\n\n".join([doc["text"] for doc in top_docs])
        prompt = f"""You must answer the question **only using the provided context**. 
        Do not add any external knowledge, opinions, or extra details.

        If the answer is not in the context, reply with:
        "The information is not available in the provided context."

        Strictly base your response on the context below:

        Context:
        {context}

        Question: {query_text}
        Answer:"""

        # Query Ollama for response
        response = ollama.chat(model=model, 
                               messages=[{"role": "user", "content": prompt}],
                               options={"temperature": 0.0},
                               stream=False
                               )
        return response['message']['content']

# Example usage:
if __name__ == "__main__":
    # Sample text chunks (replace with your actual data)
    # text_chunks = [
    #     "India is a diverse and populous country in South Asia, known for its rich history and economic growth.",
    #     "China is the world's most populous country with rapid technological advancements.",
    #     "The United States is a global superpower known for its innovation and diverse culture."
    # ]

    # Initialize the retriever with native L2 distance (use_cosine=False)
    retriever = FaissRetriever(use_cosine=False)

    # Create the FAISS index from the text chunks
    # retriever.create_index(text_chunks)
    
    # Save the index and mapping to disk
    # retriever.save_index()

    # Later you can load the index back (e.g., in another session)
    retriever.load_index()

    # Perform a similarity query
    query = "Tell me about India"
    results = retriever.query(query, k=3)
    print("Query Results:")
    for result in results:
        print(f"Score: {result['score']:.4f} - Text: {result['text']}")

    print("---------------------------")
    query = "Tell me about India"
    response = retriever.generate_response(query)
    print(response)
