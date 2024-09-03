import yaml
import os
from llm_funcs import gen_gpt_chat_completion
from arxiv_reader import get_arxiv, get_arxiv_id
from pdf_reader import get_pdf
import requests

def load_system_prompt(yaml_file):
    with open(yaml_file) as file:
        prompts_dict = yaml.load(file, Loader=yaml.FullLoader)
    return prompts_dict

def first_pass(content):
    prompt = """
    Perform a first pass read of the following scientific paper. Focus on:
    1. Title, abstract, and introduction
    2. Section and sub-section headings
    3. Conclusions
    4. References (note any you recognize)

    After reading, answer the following questions:
    1. Category: What type of paper is this?
    2. Context: Which other papers is it related to? What theoretical bases were used?
    3. Correctness: Do the assumptions appear to be valid?
    4. Contributions: What are the paper's main contributions?
    5. Clarity: Is the paper well written?

    Paper content:
    {content}

    Analysis:
    """
    return gen_gpt_chat_completion("", prompt.format(content=content), temp=0.7).choices[0].message.content

def second_pass(content, first_pass_summary):
    prompt = """
    You have already performed a first pass on this paper with the following summary:

    {first_pass_summary}

    Now, perform a second pass read of the paper. Focus on:
    1. Carefully examining figures, diagrams, and other illustrations
    2. Marking unread references for further reading

    Provide a summary of the main thrust of the paper with supporting evidence.
    Highlight any parts that were difficult to understand or require background knowledge.

    Paper content:
    {content}

    Analysis:
    """
    return gen_gpt_chat_completion("", prompt.format(content=content, first_pass_summary=first_pass_summary), temp=0.7).choices[0].message.content

def third_pass(content, first_pass_summary, second_pass_summary):
    prompt = """
    You have already performed a first and second pass on this paper with the following summaries:

    First Pass:
    {first_pass_summary}

    Second Pass:
    {second_pass_summary}

    Now, perform a third pass read of the paper. Your goal is to virtually re-implement the paper:
    1. Identify and challenge every assumption in every statement
    2. Think about how you would present each idea
    3. Jot down ideas for future work

    Provide a detailed analysis including:
    1. The entire structure of the paper
    2. Its strong and weak points
    3. Implicit assumptions
    4. Missing citations to relevant work
    5. Potential issues with experimental or analytical techniques

    Paper content:
    {content}

    Analysis:
    """
    return gen_gpt_chat_completion("", prompt.format(content=content, first_pass_summary=first_pass_summary, second_pass_summary=second_pass_summary), temp=0.7).choices[0].message.content

def download_pdf(url, file_path):
    response = requests.get(url)
    if response.status_code == 200:
        with open(file_path, 'wb') as f:
            f.write(response.content)
        return True
    return False

def generate_summary_arxiv(url='https://arxiv.org/abs/2405.04434', episode='1', use_cache=False,
                           prompt='dialogue_prompt', background_knowledge='None',
                           additional_research_questions="None"):
    arxiv_id = get_arxiv_id(url)
    if not arxiv_id:
        print(f"Error: Could not extract arXiv ID from URL: {url}")
        return None

    arxiv_dict = get_arxiv(url, use_cache=use_cache)
    
    # Check if HTML content is available
    if not arxiv_dict or 'content' not in arxiv_dict or not arxiv_dict['content'].strip():
        print(f"HTML content not available for {url}. Attempting to fetch PDF...")
        # Construct PDF URL and local file path
        pdf_url = f"https://arxiv.org/pdf/{arxiv_id}"
        pdf_dir = 'pdfs'
        if not os.path.exists(pdf_dir):
            os.makedirs(pdf_dir)
        pdf_path = os.path.join(pdf_dir, f"{arxiv_id}.pdf")
        
        if use_cache and os.path.exists(pdf_path):
            print(f"Using cached PDF: {pdf_path}")
        else:
            print(f"Downloading PDF from {pdf_url}")
            if not download_pdf(pdf_url, pdf_path):
                print(f"Error: Failed to download PDF from {pdf_url}")
                return None
        
        try:
            arxiv_dict = get_pdf(pdf_path)
        except Exception as e:
            print(f"Error processing PDF: {str(e)}")
            return None
    
    prompt_dict = load_system_prompt('prompts.yaml')

    # Check if arxiv_dict is empty or doesn't contain expected keys
    if not arxiv_dict:
        print(f"Error: Failed to retrieve data for URL: {url}")
        return None

    required_keys = ['title', 'authors', 'abstract', 'content']
    missing_keys = [key for key in required_keys if key not in arxiv_dict]
    if missing_keys:
        print(f"Error: Data is missing the following required keys: {', '.join(missing_keys)}")
        return None

    # let the run YAML file specify the prompt to use
    # so each run can specify dialogue style or monologue style, in English or Chinese
    generation_prompt = prompt_dict[prompt]
    research_question_prompt = prompt_dict['research_question_prompt']
    topic_prompt = prompt_dict['topic_prompt']
    background_knowledge_prompt = background_knowledge
    title = arxiv_dict['title']
    authors = arxiv_dict['authors']
    # Convert authors to string if it's a list
    if isinstance(authors, list):
        authors = ', '.join(authors)
    abstract = arxiv_dict['abstract']
    content = arxiv_dict['content']
    dummy_content = 'Not available.'

    topic_prediction = gen_gpt_chat_completion("", topic_prompt + '\n Title:' + title + '\nAbstract:' + abstract + '\n')
    generated_topic = topic_prediction.choices[-1].message.content.strip()
    print("article topic:", generated_topic)
    research_question_prompt = research_question_prompt.replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<TOPIC>', generated_topic).replace('<CONTENT>', dummy_content)
    # generate the research question using title and abstract
    # TODO: research questions from title and abstract may not be the best choice
    # the full text with selected sections may be better
    research_questions = gen_gpt_chat_completion(research_question_prompt,'', temp=0.5).choices[-1].message.content.strip()
    research_questions += "Additional research questions:\n" + additional_research_questions
    # inject the generated topic, research questions etc
    summarizer_prompt = generation_prompt.replace('<EPISODE_NUMBER>', episode).replace('<BACKGROUND_KNOWLEDGE>',background_knowledge_prompt).replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<AUTHORS>',authors).replace('<TOPIC>', generated_topic).replace('<RESEARCH_QUESTIONS>', research_questions)
    # generate the summary with some high temperature for more creativity
    summary = gen_gpt_chat_completion(summarizer_prompt, content, temp=0.7, max_tokens=4096).choices[-1].message.content.strip()

    return {
        'arxiv_id': arxiv_id,
        'title': title,
        'authors': authors,
        'abstract': abstract,
        'content': content,
        'research_questions': research_questions,
        'summary': summary,
    }

def generate_summary_pdf(pdf_path='pdfs/1-s2.0-S0079742124000033-main.pdf', episode='1', 
                         use_cache=False, prompt='dialogue_prompt', background_knowledge='None',
                         additional_research_questions="None"):
    from pdf_reader import get_pdf
    pdf_json = get_pdf(pdf_path, use_cache=use_cache)
    prompt_dict = load_system_prompt('prompts.yaml')

    generation_prompt = prompt_dict[prompt]
    research_question_prompt = prompt_dict['research_question_prompt']
    topic_prompt = prompt_dict['topic_prompt']
    background_knowledge_prompt = background_knowledge
    title = pdf_json['title']
    authors = pdf_json['authors']
    if isinstance(authors, list):
        authors = ';'.join(authors)
    abstract = pdf_json['abstract']
    content = pdf_json['content']
    selected_content = pdf_json['full_text']
    short_content = ''
    for section, text in selected_content.items():
        short_content += section + ":\n" + text + '\n'

    # Perform three-pass analysis
    first_pass_summary = first_pass(content)
    second_pass_summary = second_pass(content, first_pass_summary)
    third_pass_summary = third_pass(content, first_pass_summary, second_pass_summary)
    
    three_pass_summary = f"""
    First Pass:
    {first_pass_summary}

    Second Pass:
    {second_pass_summary}

    Third Pass:
    {third_pass_summary}
    """

    topic_prediction = gen_gpt_chat_completion("", topic_prompt + '\n Title:' + title + '\nAbstract:' + abstract + '\n')
    generated_topic = topic_prediction.choices[-1].message.content.strip()
    print("article topic:", generated_topic)
    research_question_prompt = research_question_prompt.replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<TOPIC>', generated_topic).replace('<CONTENT>', short_content)
    research_questions = gen_gpt_chat_completion(research_question_prompt,'', temp=0.5).choices[-1].message.content.strip()
    research_questions += "\nAdditional research questions:\n" + additional_research_questions
    
    summarizer_prompt = generation_prompt.replace('<EPISODE_NUMBER>', episode)
    summarizer_prompt = summarizer_prompt.replace('<BACKGROUND_KNOWLEDGE>', background_knowledge_prompt)
    summarizer_prompt = summarizer_prompt.replace('<TITLE>', title)
    summarizer_prompt = summarizer_prompt.replace('<ABSTRACT>', abstract)
    summarizer_prompt = summarizer_prompt.replace('<AUTHORS>', authors)
    summarizer_prompt = summarizer_prompt.replace('<TOPIC>', generated_topic)
    summarizer_prompt = summarizer_prompt.replace('<RESEARCH_QUESTIONS>', research_questions)
    summarizer_prompt = summarizer_prompt.replace('<THREE_PASS_ANALYSIS>', three_pass_summary)
    summarizer_prompt = summarizer_prompt.replace('<ORIGINAL_CONTENT>', content)
    
    summary = gen_gpt_chat_completion(summarizer_prompt, '', temp=0.7, max_tokens=4096).choices[-1].message.content.strip()

    return {
        'pdf_id': pdf_json['pdf_id'],
        'title': title,
        'authors': authors,
        'abstract': abstract,
        'content': content,
        'research_questions': research_questions,
        'summary': summary,
    }

if __name__ == '__main__':
    result = generate_summary_arxiv(url='https://arxiv.org/abs/2405.04434', episode='1', use_cache=False)
    
    # Save the output to temp.md
    with open('temp.md', 'w', encoding='utf-8') as f:
        f.write(f"# {result['title']}\n\n")
        f.write(f"## Authors\n{result['authors']}\n\n")
        f.write(f"## Abstract\n{result['abstract']}\n\n")
        f.write(f"## Research Questions\n{result['research_questions']}\n\n")
        f.write(f"## Summary\n{result['summary']}\n")

    print("Output saved to temp.md")