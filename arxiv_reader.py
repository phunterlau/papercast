import requests
from bs4 import BeautifulSoup
import os
import re
import json

import arxiv
import logging

# a tool function to parse arxiv id from a url of either abs or pdf
def get_arxiv_id(url):
    if 'arxiv.org/abs' in url:
        return url.split('arxiv.org/abs/')[-1]
    elif 'arxiv.org/pdf' in url:
        return url.split('arxiv.org/pdf/')[-1].split('.pdf')[0]
    elif "arxiv.org/html" in url:
        return url.split('arxiv.org/html/')[-1].split('v')[0]
    else:
        return None

# get latest version of an arxiv paper so HTML link can be right
def get_latest_version(arxiv_id):
    search = arxiv.Search(id_list=[arxiv_id])
    for result in search.results():
        match = re.search(r'v(\d+)$', result.entry_id)
        if match:
            return match.group(1)
    return None

def construct_html_link(arxiv_id, version_number):
    return f"https://arxiv.org/html/{arxiv_id}v{version_number}"

# Configure logging
logging.basicConfig(level=logging.INFO)

def fetch_html(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except requests.RequestException as e:
        logging.error(f"Error fetching the HTML content: {e}")
        return None

def parse_html(html_content):
    return BeautifulSoup(html_content, 'html.parser') if html_content else None

def extract_title(soup):
    title_tag = soup.title
    return title_tag.string if title_tag else "No Title"

def clean_author_name(name):
    return re.sub(r'\u2020.*', '', name).strip()

def extract_authors(soup):
    authors = []
    author_tags = soup.find_all('span', class_='ltx_personname')
    if author_tags:
        authors = [clean_author_name(author_tag.text) for author_tag in author_tags]
    return authors if authors else ["No Authors"]

def extract_abstract(soup):
    abstract_tag = soup.find('div', class_='ltx_abstract')
    return abstract_tag.text.strip() if abstract_tag else "No Abstract"

def extract_sections(soup):
    sections = {}
    section_tags = soup.find_all('section', class_='ltx_section')
    for section_tag in section_tags:
        section_title_tag = section_tag.find('h2')
        section_title = section_title_tag.text.strip() if section_title_tag else 'No Title'
        section_title = re.sub(r'^\d+\s', '', section_title)  # Remove section numbering
        section_id = section_tag.get('id', 'No ID')
        section_content = ' '.join(p.text.strip() for p in section_tag.find_all('p'))
        sections[section_title] = {
            'content': section_content,
            'id': section_id
        }
    return sections if sections else {"No Sections": {"content": "Content not available", "id": "No ID"}}

def sections_to_markdown(sections):
    markdown_str = ""
    for title, data in sections.items():
        markdown_str += f"## {title}\n\n"
        markdown_str += f"{data['content']}\n\n"
        markdown_str += f"*Section ID: {data['id']}*\n\n"
    return markdown_str

def arxiv_to_json(arxiv_id):
    latest_version = get_latest_version(arxiv_id)
    print(latest_version)
    url = construct_html_link(arxiv_id, latest_version)
    print(url)
    html_content = fetch_html(url)
    if not html_content:
        # TODO: switch to PDF parser
        return {}
    soup = parse_html(html_content)
    if not soup:
        return {}
    
    sections = extract_sections(soup)
    markdown_content = sections_to_markdown(sections)
    data = {
        'arxiv_id': arxiv_id,
        'version': latest_version,
        'title': extract_title(soup),
        'authors': ';'.join(extract_authors(soup)),
        'abstract': extract_abstract(soup),
        'sections': sections,
        'content': markdown_content
    }
    
    return data

# given an arxiv url, get the arxiv id, title, author, abstract and content in a dictionary
def get_arxiv(url, use_cache=True):
    arxiv_id = get_arxiv_id(url)
    print(arxiv_id)
    # check if this id is already saved in the arxiv folder
    # if yes and allow cache, load it and return, otherwise, get the arxiv info and content
    folder = 'arxiv'
    
    if os.path.exists(os.path.join(folder, arxiv_id + '.json')) and use_cache:
        with open(os.path.join(folder, arxiv_id + '.json')) as file:
            return json.load(file)
    else:
        return arxiv_to_json(arxiv_id)

# save the arxiv dictionary to a json file with the file name as the arxiv id in a subfolder named 'arxiv'
# if the subfolder does not exist, create it
def save_arxiv(arxiv_dict):
    import os
    import json
    folder = 'arxiv'
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(os.path.join(folder, arxiv_dict['arxiv_id'] + '.json'), 'w') as file:
        json.dump(arxiv_dict, file)

if __name__ == '__main__':
    url = 'https://arxiv.org/abs/2405.04434'
    arxiv_dict = get_arxiv(url, use_cache=False)
    print(arxiv_dict)
    save_arxiv(arxiv_dict)
