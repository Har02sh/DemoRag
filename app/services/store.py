import json
from faiss_retriever import FaissRetriever  # Assuming you've saved the first file as faiss_retriever.py

# Load the JSON data (from the second file)
metadata = r"D:\Rag\metadata.json"
with open(metadata, 'r') as f:
    country_data = json.load(f)

# Extract text chunks from the JSON structure
text_chunks = []
for entry in country_data:
    # Combine the heading with the content
    heading = entry["heading"]
    # Join the content list into a single string
    content = " ".join(entry["content"])
    # Create a formatted text chunk
    text_chunk = f"{heading}: {content}"
    text_chunks.append(text_chunk)
    
    # Process subsections if they exist
    # if "subsections" in entry and entry["subsections"]:
    #     for subsection in entry["subsections"]:
    #         sub_heading = subsection["heading"]
    #         sub_content = " ".join(subsection["content"])
    #         sub_text = f"{heading} - {sub_heading}: {sub_content}"
    #         text_chunks.append(sub_text)

# Initialize the FAISS retriever
retriever = FaissRetriever(
    model_name='all-mpnet-base-v2',
    index_path="countries_index.index",
    mapping_path="countries_id_to_text.pkl",
    use_cosine=False  # Using L2 distance as per the default
)

# Create the index with the text chunks
retriever.create_index(text_chunks)

# Save the index to disk
retriever.save_index()

# Test the retriever with a sample query
query = "Tell me about European countries"
results = retriever.query(query, k=3)
print("Query Results:")
for result in results:
    print(f"Score: {result['score']:.4f} - Text: {result['text']}")