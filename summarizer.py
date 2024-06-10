import openai
import yaml
import os

client = openai.OpenAI(api_key=os.environ['OPENAI_API_KEY'])

def gen_gpt_chat_completion(system_prompt, user_prompt, temp=0.1, engine="gpt-4o", max_tokens=2048,
                            top_p=1, frequency_penalty=0, presence_penalty=0,):
    
    response = client.chat.completions.create(
                    model="gpt-4o",
                    messages=[{"role":"system", "content":system_prompt},
                            {"role":"user", "content":user_prompt}],
                    temperature=temp,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0)
    return response

def load_system_prompt(yaml_file):
    with open(yaml_file) as file:
        prompts_dict = yaml.load(file, Loader=yaml.FullLoader)
    return prompts_dict

# the wrapper function to generate the summary from an arxiv url
# url, episode, use_cache, prompt, background_knowledge are loaded from the driver's YAML file
def generate_summary_arxiv(url='https://arxiv.org/abs/2405.04434', episode='1', use_cache=False,
                           prompt='dialogue_prompt',
                           background_knowledge='None'):
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

    topic_prediction = gen_gpt_chat_completion("", topic_prompt + '\n Title:' + title + '\nAbstract:' + abstract + '\n')
    generated_topic = topic_prediction.choices[-1].message.content.strip()
    print("article topic:", generated_topic)
    research_question_prompt = research_question_prompt.replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<TOPIC>', generated_topic)
    # generate the research question using title and abstract
    # TODO: research questions from title and abstract may not be the best choice
    # the full text with selected sections may be better
    research_questions = gen_gpt_chat_completion(research_question_prompt,'', temp=0.5).choices[-1].message.content.strip()
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