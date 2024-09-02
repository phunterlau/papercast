import yaml
import os
from llm_funcs import gen_gpt_chat_completion

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

def generate_summary_arxiv(url='https://arxiv.org/abs/2405.04434', episode='1', use_cache=False,
                           prompt='dialogue_prompt', background_knowledge='None',
                           additional_research_questions="None"):
    from arxiv_reader import get_arxiv
    arxiv_dict = get_arxiv(url, use_cache=use_cache)
    prompt_dict = load_system_prompt('prompts.yaml')

    generation_prompt = prompt_dict[prompt]
    research_question_prompt = prompt_dict['research_question_prompt']
    topic_prompt = prompt_dict['topic_prompt']
    background_knowledge_prompt = background_knowledge
    title = arxiv_dict['title']
    authors = arxiv_dict['authors']
    abstract = arxiv_dict['abstract']
    content = arxiv_dict['content']
    dummy_content = 'Not available.'

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
    research_question_prompt = research_question_prompt.replace('<TITLE>', title).replace('<ABSTRACT>', abstract).replace('<TOPIC>', generated_topic).replace('<CONTENT>', dummy_content)
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
        'arxiv_id': arxiv_dict['arxiv_id'],
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