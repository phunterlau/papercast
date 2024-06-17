import yaml
import os

from llm_funcs import gen_gpt_chat_completion

def load_system_prompt(yaml_file):
    with open(yaml_file) as file:
        prompts_dict = yaml.load(file, Loader=yaml.FullLoader)
    return prompts_dict

# the wrapper function to generate the summary from an arxiv url
# url, episode, use_cache, prompt, background_knowledge are loaded from the driver's YAML file
def generate_summary_arxiv(url='https://arxiv.org/abs/2405.04434', episode='1', use_cache=False,
                           prompt='dialogue_prompt', background_knowledge='None',
                           additional_research_questions="None"):
    from arxiv_reader import get_arxiv
    arxiv_dict = get_arxiv(url, use_cache=use_cache)
    prompt_dict = load_system_prompt('prompts.yaml')

    # let the run YAML file specify the prompt to use
    # so each run can specify dialogue style or monologue style, in English or Chinese
    generation_prompt = prompt_dict[prompt]
    research_question_prompt = prompt_dict['research_question_prompt']
    topic_prompt = prompt_dict['topic_prompt']
    background_knowledge_prompt = background_knowledge
    title = arxiv_dict['title']
    #authors = ';'.join(arxiv_dict['authors'].split(';')[:3])
    authors = arxiv_dict['authors']
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
        'arxiv_id': arxiv_dict['arxiv_id'],
        'title': title,
        'authors': authors,
        'abstract': abstract,
        'content': content,
        'research_questions': research_questions,
        'summary': summary,
    }

# the wrapper function to generate the summary from a pdf file
# pdf_path, use_cache, prompt are loaded from the driver's YAML file
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
    # if authors is a list, convert it to a string
    if isinstance(authors, list):
        authors = ';'.join(authors)
    abstract = pdf_json['abstract']
    content = pdf_json['content']
    selected_content = pdf_json['full_text'] # LLM extracted selected content in dictionary format
    short_content = ''
    for section, text in selected_content.items():
        short_content += section + ":\n" + text + '\n'

    topic_prediction = gen_gpt_chat_completion("", topic_prompt + '\n Title:' + title + '\nAbstract:' + abstract + '\n')
    generated_topic = topic_prediction.choices[-1].message.content.strip()
    print("article topic:", generated_topic)
    research_question_prompt = research_question_prompt.replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<TOPIC>', generated_topic).replace('<CONTENT>', short_content)
    # generate the research question using title and abstract and short content
    research_questions = gen_gpt_chat_completion(research_question_prompt,'', temp=0.5).choices[-1].message.content.strip()
    research_questions += "Additional research questions:\n" + additional_research_questions
    summarizer_prompt = generation_prompt.replace('<EPISODE_NUMBER>', episode).replace('<BACKGROUND_KNOWLEDGE>',short_content).replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<AUTHORS>',authors).replace('<TOPIC>', generated_topic).replace('<RESEARCH_QUESTIONS>', research_questions)
    # generate the summary with some high temperature for more creativity
    summary = gen_gpt_chat_completion(summarizer_prompt, content, temp=0.7, max_tokens=4096).choices[-1].message.content.strip()

    return {
        'pdf_id': pdf_json['pdf_id'],
        'title': title,
        'authors': authors,
        'abstract': abstract,
        'content': content,
        'research_questions': research_questions,
        'summary': summary,
    }

# not yet finished
# TODO: get a good crawler function and fix the sciencedirect summarizer later
def generate_summary_sciencedirect():
    from scidir_reader import get_sciencedirect
    url = 'https://www.sciencedirect.com/science/article/abs/pii/S0079742124000033'
    episode = '1'
    article_dict = get_sciencedirect(url, use_cache=True)
    dialogue_prompt, monologue_prompt, research_question_prompt, topic_prompt = load_system_prompt('prompts.yaml')
    title = article_dict['title']
    abstract = article_dict['abstract']
    content = article_dict['content']
    topic_prediction = gen_gpt_chat_completion("", topic_prompt + '\n Title:' + title + '\nAbstract:' + abstract + '\n')
    generated_topic = topic_prediction.choices[-1].message.content.strip()
    print(generated_topic)
    # replace research_question_prompt with title, abstract and generated topics by changing the <TITLE>, <ABSTRACT> and <TOPIC> placeholders
    research_question_prompt = research_question_prompt.replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<TOPIC>', generated_topic)
    #print(research_question_prompt)
    # generate the research question
    research_questions = gen_gpt_chat_completion(research_question_prompt,'').choices[-1].message.content.strip()
    # replace summarizer_prompt with the generated topic by changing the "<TOPIC>" placeholder
    summarizer_prompt = dialogue_prompt.replace('<EPISODE_NUMBER>', episode).replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<TOPIC>', generated_topic).replace('<RESEARCH_QUESTIONS>', research_questions)
    print(summarizer_prompt)
    # generate the summary
    summary = gen_gpt_chat_completion(summarizer_prompt, content, temp=0.5, max_tokens=4096).choices[-1].message.content.strip()
    print(summary)

if __name__ == '__main__':
    generate_summary_arxiv(url='https://arxiv.org/abs/2405.04434', episode='1', use_cache=False)
    #generate_summary_sciencedirect()