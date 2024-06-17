from summarizer import generate_summary_arxiv
from tts_gen import produce_audio
from arxiv_reader import get_arxiv_id
from pdf_reader import get_json_id

import json
import os
import yaml
import sys

# magic numbers for some good speaker seeds for podcasting
speaker_seed_map = {"Justin": 2800,
                    "Emma":2400,
                    "Bertie": 4600,
                    'Doudou': 13200}

# generate summary for an arxiv paper and save the transcript in json in 'transcript/' with file name of the arxiv id
def generate_transcript_arxiv(arxiv_url, episode='1', use_cache=False,
                              prompt="dialogue_prompt",
                              background_knowledge="None",
                              additional_research_questions="None"):
    # remove new line characters in the background knowledge
    background_knowledge = background_knowledge.replace('\n', ' ')
    if not os.path.exists('transcript'):
        os.makedirs('transcript')
    if not use_cache:
        arxiv_dict = generate_summary_arxiv(arxiv_url, episode, use_cache, prompt, 
                                            background_knowledge, additional_research_questions)
        transcript = arxiv_dict['summary']
        arxiv_id = arxiv_dict['arxiv_id']
        # save arxiv_dict to a json file in 'transcript' folder
        with open(os.path.join('transcript', arxiv_id + '.json'), 'w') as file:
            json.dump(arxiv_dict, file)
    else: # if use_cache, load the transcript from the json file
        arxiv_id = get_arxiv_id(arxiv_url)
        with open(os.path.join('transcript', arxiv_id + '.json')) as file:
            arxiv_dict = json.load(file)
            transcript = arxiv_dict['summary']

    return transcript

# generate summary of an pdf file and save the transcript in json in 'transcript/' with file name of the pdf id
def generate_transcript_pdf(pdf_path, episode='1', use_cache=False, 
                            prompt='dialogue_prompt', background_knowledge='None',
                            additional_research_questions="None"):
    from summarizer import generate_summary_pdf
    if not os.path.exists('transcript'):
        os.makedirs('transcript')
    if not use_cache:
        pdf_json = generate_summary_pdf(pdf_path, episode, use_cache, prompt, 
                                        background_knowledge, additional_research_questions)
        transcript = pdf_json['summary']
        pdf_id = pdf_json['pdf_id']
        # save pdf_json to a json file in 'transcript' folder
        with open(os.path.join('transcript', pdf_id + '.json'), 'w') as file:
            json.dump(pdf_json, file)
    else: # if use_cache, load the transcript from the json file
        pdf_id = get_json_id(pdf_path)
        with open(os.path.join('transcript', pdf_id + '.json')) as file:
            pdf_json = json.load(file)
            transcript = pdf_json['summary']

    return transcript

# a tool function to sanitize the transcript text by removing special characters
# it is critical to ensure ChatTTS to avoid speaking the break and laugh symbols
# if seeing more invalid characters, add them here
def sanitize_text(text):
    text = text.replace('?', ',')
    text = text.replace('\'', ' ')
    # remove '’' '!' '-' '(' ')'' "'and replace with ','
    text = text.replace('’', ' ')
    text = text.replace('!', ',')
    text = text.replace('-', ' ')
    text = text.replace('(', ' ')
    text = text.replace(')', ' ')
    # remove '"' and replace with ','
    text = text.replace('"', ' ')
    text = text.replace("'", ' ')
    text = text.replace(":", ' ')
    return text

# each line of the transcript starts with the speaker name like 
# **Justin:** Interesting. So, how does sparse computation impact the training costs of DeepSeek-V2?
def parse_transcript(transcript):
    lines = transcript.split('\n')
    sequence_id = 1
    result = []
    for line in lines:
        print(line)
        if line.startswith('**'):
            speaker = line.split('**',2)[1].strip(':')
            # if the speaker is not in the map, ignore this line and continue
            if speaker not in speaker_seed_map:
                continue
            speaker_seed = speaker_seed_map[speaker]
            text = sanitize_text(line.split('**',2)[2].strip())
            result.append((text, speaker_seed, sequence_id))
            sequence_id += 1
    return result

if __name__ == '__main__':
    # load url, episode, use_cache and background knowledge from a yaml file from sys.argv[1]
    with open(sys.argv[1]) as file:
        config = yaml.load(file, Loader=yaml.FullLoader)
    url = config['url']
    episode = str(config['episode'])
    use_cache = config['use_cache']
    prompt = config['prompt']
    background_knowledge = config['background_knowledge']
    additional_research_questions = config.get('additional_questions', ['None'])
    additional_research_questions = '\n'.join(additional_research_questions)
    print('additional_research_questions:', additional_research_questions)
    audio_offset = config.get('audio_offset',0)

    # check the url and see if it is an arxiv url or a local PDF file
    # if it is an arxiv url, get the arxiv id and generate the transcript
    # if it is a local PDF file, load the PDF content and generate the transcript
    if url.startswith('https://arxiv.org/'):
        arxiv_id = get_arxiv_id(url)
        transcript = generate_transcript_arxiv(url, episode, use_cache, prompt, 
                                               background_knowledge=background_knowledge,
                                               additional_research_questions=additional_research_questions)
        #print(transcript)
        parsed_transcript = parse_transcript(transcript)
        produce_audio(parsed_transcript, audio_filename=arxiv_id+'.wav', offset=audio_offset)
    else:
        pdf_id = get_json_id(url)
        transcript = generate_transcript_pdf(url, episode, use_cache, prompt, 
                                            background_knowledge=background_knowledge,
                                            additional_research_questions=additional_research_questions)
        #print(transcript)
        parsed_transcript = parse_transcript(transcript)
        produce_audio(parsed_transcript, audio_filename=pdf_id+'.wav', offset=audio_offset)
