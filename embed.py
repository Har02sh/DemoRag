import json
from sentence_transformers import SentenceTransformer


embd_model = SentenceTransformer("all-mpnet-base-v2")

with open('metadata.json', 'r') as f:
    metadata = json.load(f)

def generate_embeddings_for_section(section):
    # Combine heading and content into a single text block
    text = section["heading"] + "\n" + "\n".join(section.get("content", []))
    # Generate the embedding for the text
    embedding = embd_model.encode(text,show_progress_bar=True, normalize_embeddings=True)
    # Store the embedding (converted to list for JSON serialization)
    section["embedding"] = embedding.tolist()
    
    # Process subsections if they exist
    if "subsections" in section:
        for sub in section["subsections"]:
            generate_embeddings_for_section(sub)

# If metadata is a list of sections (multiple sections in a document)
if isinstance(metadata, list):
    for section in metadata:
        generate_embeddings_for_section(section)
else:
    # If it's a single section or document structure
    generate_embeddings_for_section(metadata)

# Save the updated metadata with embeddings to a new file
with open('metadata_with_embeddings.json', 'w') as f:
    json.dump(metadata, f, indent=2)

print("Embeddings generated and stored in metadata_with_embeddings.json")