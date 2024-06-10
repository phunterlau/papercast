import requests
from bs4 import BeautifulSoup
import os
import json

# a tool function to parse arxiv id from a url of either abs or pdf
def get_arxiv_id(url):
    if 'arxiv.org/abs' in url:
        return url.split('arxiv.org/abs/')[-1]
    elif 'arxiv.org/pdf' in url:
        return url.split('arxiv.org/pdf/')[-1].split('.pdf')[0]
    else:
        return None
    
# given an arxiv id, get the abs page, parse the title, author and abstract
def get_arxiv_info(arxiv_id):
    url = 'https://arxiv.org/abs/' + arxiv_id
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    title = soup.find('meta', {'name': 'citation_title'})['content']
    # get all authors from the meta tags
    authors = soup.find_all('meta', {'name': 'citation_author'})
    author_list = '; '.join([a['content'] for a in authors])
    abstract = soup.find('meta', {'name': 'citation_abstract'})['content']
    return title, author_list, abstract

# sanitize the content by removing lines starting with '>'
# remove strings like '\ud835'
# remove continuous spaces 
def sanitize_content(content):
    sanitized_content = []
    cleaned_content = re.sub(r'[^\x00-\x7F]+', '', content)
    cleaned_content = re.sub(r'\s+', ' ', cleaned_content)
    for line in cleaned_content.split('\n'):
        if not line.startswith('>'):
            sanitized_content.append(line)
    
    return '\n'.join(sanitized_content)


# given an arxiv id, construct a jina.ai reader url, for example, 2405.04434
# gives https://r.jina.ai/https://arxiv.org/pdf/2405.04434
# query this url and get its content as Markdown
# sanitize the content by removing lines starting with '>'
def get_arxiv_content(arxiv_id):
    url = 'https://arxiv.org/pdf/' + arxiv_id + '.pdf'
    response = requests.get('https://r.jina.ai/' + url)
    # sanitize the content by removing lines starting with '>'
    sanitized_content = []
    for line in response.text.split('\n'):
        if not line.startswith('>'):
            sanitized_content.append(line)
    return '\n'.join(sanitized_content)

# given an arxiv url, get the arxiv id, title, author, abstract and content in a dictionary
def get_arxiv(url, use_cache=True):
    arxiv_id = get_arxiv_id(url)
    # check if this id is already saved in the arxiv folder
    # if yes and allow cache, load it and return, otherwise, get the arxiv info and content
    folder = 'arxiv'
    
    if os.path.exists(os.path.join(folder, arxiv_id + '.json')) and use_cache:
        with open(os.path.join(folder, arxiv_id + '.json')) as file:
            return json.load(file)
    else:
        title, authors, abstract = get_arxiv_info(arxiv_id)
        content = get_arxiv_content(arxiv_id)
        return {
            'arxiv_id': arxiv_id,
            'title': title,
            'authors': authors,
            'abstract': abstract,
            'content': content
        }

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
