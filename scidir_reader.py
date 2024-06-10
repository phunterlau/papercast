import requests
from bs4 import BeautifulSoup
import os
import json
import re

def get_sciencedirect_content(url):
    response = requests.get('https://r.jina.ai/' + url)
    # sanitize the content by removing lines starting with '>'
    sanitized_content = []
    for line in response.text.split('\n'):
        if not line.startswith('>'):
            sanitized_content.append(line)
    return '\n'.join(sanitized_content)

def extract_title_abstract(text):
    # Extract title
    title_match = re.search(r'Title:\s*(.*)', text)
    title = title_match.group(1).strip() if title_match else 'Title not found'
    
    # Extract abstract
    abstract_match = re.search(r'Abstract\s*--------\s*(.*)', text, re.DOTALL)
    abstract = abstract_match.group(1).strip().split("Introduction")[0] if abstract_match else 'Abstract not found'
    
    return title, abstract

def get_sciencedirect(url, use_cache=True):
    folder = 'sciencedirect'
    
    # get the article ID from the URL
    article_id = url.split('/')[-1]

    if os.path.exists(os.path.join(folder, article_id + '.json')) and use_cache:
        with open(os.path.join(folder, article_id+ '.json')) as file:
            return json.load(file)
    else:
        content = get_sciencedirect_content(url)
        title, abstract = extract_title_abstract(content)
        return {
            'article_id': article_id,
            'title': title,
            'abstract': abstract,
            'content': content
        }

def save_article(article_dict):
    import os
    import json
    folder = 'sciencedirect'
    if not os.path.exists(folder):
        os.makedirs(folder)
    with open(os.path.join(folder, article_dict['article_id'] + '.json'), 'w') as file:
        json.dump(article_dict, file)

if __name__ == '__main__':
    url = 'https://www.sciencedirect.com/science/article/abs/pii/S0079742124000033'

    article_dict = get_sciencedirect(url)
    print(article_dict)
    save_article(article_dict)