import pdfplumber
from collections import defaultdict
import json
import re

def is_heading(line_chars):
    # Determine if the majority of characters in the line are bold
    if not line_chars:
        return False
    bold_count = sum(1 for c in line_chars if "Bold" in c['fontname'])
    return (bold_count / len(line_chars)) > 0.5

def extract_hierarchy(pdf_path, heading_indent_threshold=20):
    hierarchy = []         # List to hold top-level sections
    current_section = None # Tracks the current section to append text
    last_heading_x = None  # Tracks the x position of the last heading for hierarchy inference
    
    with pdfplumber.open(pdf_path) as pdf:
        for page in pdf.pages:
            # Group characters into lines based on their vertical position (top coordinate)
            lines = defaultdict(list)
            for char in page.chars:
                # Rounding the top coordinate helps group characters into the same line
                key = round(char['top'], 1)
                lines[key].append(char)
            
            # Process each line in reading order
            for top in sorted(lines.keys()):
                line_chars = lines[top]
                text = "".join(c['text'] for c in line_chars).strip()
                if not text:
                    continue

                if "RESTRICTED" in text:
                    continue
                if text.strip() == "NAME OF THE DOCUMENT":
                    continue 

                if re.match(r'^\s*\d+\s*$', text):
                    continue
                # Calculate average x position for the line (for indentation analysis)
                avg_x0 = sum(c['x0'] for c in line_chars) / len(line_chars)
                
                if is_heading(line_chars):
                    # Create a heading node
                    heading_node = {
                        "heading": text,
                        "x0": avg_x0,
                        "content": [],
                        # "subsections": [],
                        "documentName": "Test PDF"
                    }
                    # Use indentation (x0) to decide hierarchy
                    if current_section is None:
                        hierarchy.append(heading_node)
                        current_section = heading_node
                        last_heading_x = avg_x0
                    else:
                        # If this heading is indented significantly more than the last,
                        # treat it as a subheading.
                        if avg_x0 - last_heading_x > heading_indent_threshold:
                            current_section["subsections"].append(heading_node)
                        else:
                            hierarchy.append(heading_node)
                        # Update tracking variables for the current heading
                        current_section = heading_node
                        last_heading_x = avg_x0
                else:
                    # Non-bold lines are normal text; append them to the current section's content.
                    if current_section:
                        current_section["content"].append(text)
                    else:
                        # If no heading has been encountered, optionally store this as introductory text.
                        current_section = {
                            "heading": "Intro",
                            "x0": avg_x0,
                            "content": [text],
                            # "subsections": [],
                            "documentName": "Test PDF"
                        }
                        hierarchy.append(current_section)
    return hierarchy



# Example usage:
pdf_path = "./PDFS/countries.pdf"
hierarchical_structure = extract_hierarchy(pdf_path)
output_file = "metadata.json"
with open(output_file, "w", encoding="utf-8") as file:
    file.write(json.dumps(hierarchical_structure, indent=2))
# print(json.dumps(hierarchical_structure, indent=2))
