from pypdf import PdfReader
from llm_funcs import gen_gpt_chat_json
import json
import os

# tool function to generate json file name from pdf path 
def get_json_id(pdf_path):
    # get the file name without extension
    # for example, '1-s2.0-S0079742124000033-main.pdf' gives '1-s2.0-S0079742124000033-main'
    return os.path.splitext(os.path.basename(pdf_path))[0]

# load PDF raw content
def load_pdf_content(pdf_path = "pdfs/1-s2.0-S0079742124000033-main.pdf"):
    reader = PdfReader(pdf_path)
    number_of_pages = len(reader.pages)
    text = ""
    for page in reader.pages:
        text += page.extract_text()
    return text

# call a GPT-4o json mode and extract pdf text for title, abstract, authors, 
# and full text by each section
def extract_pdf_info(pdf_path):
    """
    Extract title, abstract, author names, and full text from a given PDF file.
    """
    pdf_text = load_pdf_content(pdf_path)
    sys_prompt = '''
    You are a helpful PDF reader bot designed to output JSON for scientific articles. By given the following text extract by pyPDF,
    extract the title as "title", abstract as "abstract", authors as "authors" in a list,
    and full text as "full_text" as a dictionary from provided content and return a JSON object.
    The full text should be include introduction, methods, results, and conclusion sections. You must limit the JSON to 4096 tokens.
    '''

    response = gen_gpt_chat_json(sys_prompt, pdf_text, temp=0.1, max_tokens=2048)
    json_str = response.choices[-1].message.content.strip()
    json_obj = json.loads(json_str)

    # add raw text and other metadata
    json_obj['pdf_id'] = get_json_id(pdf_path)
    json_obj['content'] = pdf_text
    return json_obj

# save the json object to a file in "json" folder
def save_json(json_obj, file_name):
    # if 'json' folder does not exist, create it
    if not os.path.exists('json'):
        os.makedirs('json')

    with open('json/' + file_name + '.json', 'w') as file:
        json.dump(json_obj, file)

    return

# since the PDF extractor and data generation is time-consuming, use_cache is set to True by default
def get_pdf(pdf_path, use_cache=True):
    json_id = get_json_id(pdf_path)
    # check if the json file already exists
    if os.path.exists('json/' + json_id + '.json') and use_cache:
        with open('json/' + json_id + '.json') as file:
            pdf_json = json.load(file)
            return pdf_json
    # if not, extract the pdf info and save it to a json file
    pdf_json = extract_pdf_info(pdf_path)
    return pdf_json

if __name__ == '__main__':
    pdf_path = "pdfs/1-s2.0-S0079742124000033-main.pdf"
    pdf_json = get_pdf(pdf_path, use_cache=False)
    print(pdf_json)
    save_json(pdf_json, pdf_json['pdf_id'])
    print("JSON file saved successfully!")