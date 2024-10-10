import openai
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

# json mode
def gen_gpt_chat_json(system_prompt, user_prompt, temp=0.1, engine="gpt-4o", max_tokens=2048,
                            top_p=1, frequency_penalty=0, presence_penalty=0,):
    
    response = client.chat.completions.create(
                    model="gpt-4o",
                    response_format={ "type": "json_object" },
                    messages=[{"role":"system", "content":system_prompt},
                            {"role":"user", "content":user_prompt}],
                    temperature=temp,
                    max_tokens=max_tokens,
                    top_p=1,
                    frequency_penalty=0,
                    presence_penalty=0)
    return response