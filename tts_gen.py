import ChatTTS
import torch
import numpy as np
import os
import soundfile

chat = ChatTTS.Chat()
chat.load_models(compile=False) 

def generate_seed(new_seed):
    return {
        "__type__": "update",
        "value": new_seed
        }

# core function to produce audio data for a given text
# use the audio_seed_input to generate the speaker seed
# use speech_speed to control the speed of the speech
# use params_refine_text to make the text more podcast friendly
def generate_audio(text, temperature, top_P, top_K, audio_seed_input, text_seed_input, 
                   refine_text_flag, 
                   speech_speed = '[speed_1]',
                   params_refine_text = {'prompt': '[oral_3][laugh_0][break_5]'}):

    torch.manual_seed(audio_seed_input)
    rand_spk = chat.sample_random_speaker()
    params_infer_code = {
        'spk_emb': rand_spk, 
        'temperature': temperature,
        'prompt': speech_speed,
        'top_P': top_P,
        'top_K': top_K,
        }
    
    torch.manual_seed(text_seed_input)

    if refine_text_flag:
        text = chat.infer(text, 
                          skip_refine_text=False,
                          refine_text_only=True,
                          params_refine_text=params_refine_text,
                          params_infer_code=params_infer_code
                          )
    
    wav = chat.infer(text, 
                     skip_refine_text=True, 
                     params_refine_text=params_refine_text, 
                     params_infer_code=params_infer_code
                     )
    
    audio_data = np.array(wav[0]).flatten()
    sample_rate = 24000
    text_data = text[0] if isinstance(text, list) else text

    return [(sample_rate, audio_data), text_data]

# wrapper function to generate audio data for a given text, speaker_seed and sequence_id
def produce_audio_data(text, speaker_seed, sequence_id=1):
    temperature = 0.7
    top_P = 0.3
    top_K = 20
    audio_seed_input = speaker_seed
    text_seed_input = 42
    refine_text_flag = True

    (sample_rate,audio), refined_text = generate_audio(text, temperature, top_P, top_K, audio_seed_input, text_seed_input, refine_text_flag)

    print(text, refined_text)
    return audio, refined_text

# given a list of text, speaker_seed and sequence_id, 
# produce audio files for each speaker and save them to a single audio file
def produce_audio(transcript, audio_filename = 'test.wav'):
    audio_data = []
    for text, speaker_seed, sequence_id in transcript:
        audio, refined_text = produce_audio_data(text, speaker_seed, sequence_id)
        audio_data.append((audio, refined_text))
        print("finished producing audio for sequence_id:", sequence_id)
        print(refined_text)
    audio_data_all = [audio for audio, _ in audio_data]
    refined_text_all = [refined_text for _, refined_text in audio_data]
    audio_data_all = np.concatenate(audio_data_all)
    sample_rate = 24000

    if not os.path.exists('audio'):
        os.makedirs('audio')
    
    # soundfile is a more friendly lib for concatenated audio in numpy array
    # ChatTTS's torch audio example was not working for me
    soundfile.write("audio/"+audio_filename, audio_data_all, sample_rate)

    with open('audio/refined_text_'+audio_filename+'.txt', 'w') as file:
        for refined_text in refined_text_all:
            file.write(refined_text + '\n')

    print("audio file saved to audio/" + audio_filename
          + " and refined text saved to audio/refined_text_"+audio_filename+".txt")
    return refined_text_all

if __name__ == '__main__':
    text = ("Reinforcement Learning (RL) further aligns the model with human preferences by optimizing responses based on reward models."
            "In DeepSeek-V2, RL is applied in two stages: first focusing on reasoning capabilities and then on general human preference alignment."
            "This approach ensures the model performs well in both specific tasks like coding and math, and in general conversational contexts.")
    speaker_seed = 2400
    refined_text = produce_audio(text, speaker_seed)