import re
from collections import Counter
import json
import fitz  # PyMuPDF


from http.server import HTTPServer, SimpleHTTPRequestHandler, BaseHTTPRequestHandler
import json
import sys
from urllib.parse import urlparse, parse_qs



def extract_all_text(pdf_path):
    """Extracts all text from a PDF file using PyMuPDF (fitz)."""
    doc = fitz.open(pdf_path)
    text = ""

    for page in doc:
        text += page.get_text("text") + "\n"  # Extract text from each page

    return text

# Function to split the input text based on specific delimiters: ", and", "and", or ","
def custom_split(text):
    # Regular expression to split by ", and", "and", or ","
    split_text = re.split(r'\s*,\s*and\s*|\s* and \s*|\s*,\s*', text)
    return split_text

# Function to split the paper text into blocks, each separated by a delimiter line (e.g., ". . . x")
def split_papers(text):
    # Regular expression to detect delimiter lines (lines with ". . . x" where x is an integer)
    delimiter_pattern = r"^.*\.\s+\.\s+\.\s+\d+$"

    # Split the input text into lines
    lines = text.split("\n")
    blocks = []  # List to hold the blocks of text
    current_block = []  # Temporary list to store lines for the current block

    for line in lines:
        # If a delimiter line is found, start a new block
        if re.match(delimiter_pattern, line):
            if current_block:
                blocks.append("\n".join(current_block))  # Save the previous block
            current_block = [line]  # Start a new block with the delimiter line
        else:
            current_block.append(line)  # Add line to the current block

    # Append the last block if exists
    if current_block:
        blocks.append("\n".join(current_block))

    return blocks
def display_stats(total_authors, total_universities):

  # Create frequency dictionaries for authors and universities
  author_frequency = dict(Counter(total_authors))
  university_frequency = dict(Counter(total_universities))

  # Print the sorted frequency dictionaries from greatest to least
  print("Author Frequency (sorted):")
  print(dict(sorted(author_frequency.items(), key=lambda item: item[1], reverse=True)))

  print("University Frequency (sorted):")
  print(dict(sorted(university_frequency.items(), key=lambda item: item[1], reverse=True)))


def parse_blocks(blocks, total_authors, total_universities):
  # Loop through each block of paper text
  for i, block in enumerate(blocks, 1):
      # print(f"Block {i}:\n{block}\n")

      # Extract the title (first sentence before a period)
      title = block.split('\n')[0].split('.')[0]

      # Join the rest of the block content (credentials) into a single string
      credentials = ''.join(block.split('\n')[1:])

      # Split the credentials into groups based on the semicolon delimiter
      university_groups = credentials.split(';')

      # Initialize empty lists to hold authors and universities
      author_list = []
      university_list = []

      # Loop through each university group and extract authors and universities
      for university_group in university_groups:
          university_group = university_group.split(',')

          # if len(university_group) == 2:
          #     # If exactly two parts, assume first is the author and second is the university
          #     author_list.append(university_group[0])
          #     university_list.append(university_group[1])
          # elif len(university_group) > 2:
          # If more than two parts, look for "and" to separate authors
          if "and" not in ''.join(university_group):
              # If no "and" found, assume first part is the author
              author_list.append(university_group[0])
              university_list.append(','.join(university_group[1:]))
          else:
              # Split the authors and universities at "and"
              i = 0
              while 'and' not in university_group[i]:
                  author_list.append(university_group[i])
                  i += 1
              author_list += university_group[i].split(' and ')
              university_list.append(','.join(university_group[i+1:]))

      # Clean up the author and university lists by removing leading/trailing spaces and duplicates
      author_list = [s.strip() for s in author_list if s.strip()]
      author_list = list(dict.fromkeys(author_list))  # Remove duplicates while preserving order
      university_list = [s.strip() for s in university_list if s.strip()]
      university_list = list(dict.fromkeys(university_list))  # Remove duplicates while preserving order

      # Add the authors and universities to the totals
      total_authors += author_list
      total_universities += university_list

      # Print extracted data for the current block
      # print(title)
      # print(university_list)
      # print(author_list)
      # print('-' * 40)


#   display_stats(total_authors, total_universities)
  return total_authors, total_universities


# Function to process each PDF and return universities
def process_pdfs(pdf_paths):
    # Initialize lists to store authors and universities across all blocks
    total_authors = []
    total_universities = []
    university_frequency = {}
    for pdf_path in pdf_paths:
        extracted_text = extract_all_text(pdf_path)
        blocks = split_papers(extracted_text)
        parse_blocks(blocks, total_authors, total_universities)

    university_frequency = dict(Counter(total_universities))
    return dict(sorted(university_frequency.items(), key=lambda item: item[1], reverse=True))
        
pdf_paths = {
    "2015": "../data/usenix/sec15_contents.pdf",
    "2016": "../data/usenix/sec16_contents.pdf",
    "2017": "../data/usenix/sec17_contents.pdf",
    "2018": "../data/usenix/sec18_contents.pdf",
    "2019": "../data/usenix/sec19_contents.pdf",
    "2020": "../data/usenix/sec20_contents.pdf",
    "2021": "../data/usenix/sec21_contents.pdf",
    "2022": "../data/usenix/sec22_contents.pdf",
    "2023": "../data/usenix/sec23_contents.pdf",
    "2024": "../data/usenix/sec24_contents.pdf"
}


class handler(BaseHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')  # Allow CORS
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')  # Allow methods
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')  # Allow headers
        super().end_headers()

    def do_OPTIONS(self):
        # Handle CORS preflight request
        self.send_response(204)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        self.end_headers()

    def do_GET(self):
        # Parse query parameters
        parsed_url = urlparse(self.path)
        query_params = parse_qs(parsed_url.query)
        year_start = query_params.get('year_start', [None])[0]
        year_end = query_params.get('year_end', [None])[0]

        try:
            year_start = int(year_start) if year_start is not None else None
            year_end = int(year_end) if year_end is not None else None
        except ValueError:
            self.send_response(400)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"error": "Invalid year_start or year_end"}).encode('utf-8'))
            return

        # Filter valid years within the range
        selected_pdfs = []
        if year_start and year_end:
            for year in range(year_start, year_end+1):
                key = str(year)
                if key in pdf_paths:  # Assuming pdf_paths is defined elsewhere
                    selected_pdfs.append(pdf_paths[key])

        # Call process_pdfs only if there's something to process
        print(selected_pdfs)
        if selected_pdfs:
            data = process_pdfs(selected_pdfs)  # Assuming process_pdfs is defined elsewhere
        else:
            data = {"message": "No data for the given year range"}

        # Respond with JSON data
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        response = json.dumps({"data": data}).encode("utf-8")
        self.wfile.write(response)


# def handler(request):
#     # Handle CORS preflight
#     if request["method"] == "OPTIONS":
#         return {
#             "statusCode": 204,
#             "headers": {
#                 "Access-Control-Allow-Origin": "*",
#                 "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
#                 "Access-Control-Allow-Headers": "*"
#             },
#             "body": ""
#         }

#     # Parse query parameters
#     parsed_url = urlparse(request["url"])
#     query_params = parse_qs(parsed_url.query)
#     year_start = query_params.get("year_start", [None])[0]
#     year_end = query_params.get("year_end", [None])[0]

#     try:
#         year_start = int(year_start) if year_start is not None else None
#         year_end = int(year_end) if year_end is not None else None
#     except ValueError:
#         return {
#             "statusCode": 400,
#             "headers": {
#                 "Content-Type": "application/json",
#                 "Access-Control-Allow-Origin": "*"
#             },
#             "body": json.dumps({"error": "Invalid year_start or year_end"})
#         }

#     # Filter PDF paths
#     selected_pdfs = []
#     if year_start is not None and year_end is not None:
#         for year in range(year_start, year_end + 1):
#             key = str(year)
#             if key in pdf_paths:
#                 selected_pdfs.append(pdf_paths[key])

#     # Process PDFs if available
#     if selected_pdfs:
#         data = process_pdfs(selected_pdfs)
#     else:
#         data = {"message": "No data for the given year range"}

#     # Return JSON response
#     return {
#         "statusCode": 200,
#         "headers": {
#             "Content-Type": "application/json",
#             "Access-Control-Allow-Origin": "*"
#         },
#         "body": json.dumps({"data": data})
#     }

if __name__ == "__main__":
    server_address = ('', 8000)
    httpd = HTTPServer(server_address, handler)
    print("Server running on http://localhost:8000")
    httpd.serve_forever()
