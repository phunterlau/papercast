import ChatTTS
import torch
import numpy as np
import os
import soundfile

chat = ChatTTS.Chat()
chat.load_models(compile=False)

# Load pre-trained speaker embeddings
justin_spk = torch.load('seed_1509_restored_emb.pt', map_location=torch.device('cpu'))
emma_spk = torch.load('seed_1742_restored_emb.pt', map_location=torch.device('cpu'))

# Map speaker names to their embeddings
speaker_embedding_map = {
    "Justin": justin_spk,
    "Emma": emma_spk
}

# Core function to produce audio data for a given text
def generate_audio(text, temperature, top_P, top_K, speaker_name, text_seed_input, 
                   refine_text_flag, 
                   speech_speed = '[speed_1]',
                   params_refine_text = {'prompt': '[oral_1][laugh_0][break_5]'}):

    print(f"Generating audio for speaker: {speaker_name}")
    spk_emb = speaker_embedding_map.get(speaker_name, justin_spk)  # Default to Justin if speaker not found
    params_infer_code = {
        'spk_emb': spk_emb, 
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

# Wrapper function to generate audio data for a given text, speaker name and sequence_id
def produce_audio_data(text, speaker_name, sequence_id=1):
    temperature = 0.7
    top_P = 0.3
    top_K = 20
    text_seed_input = 43
    refine_text_flag = True

    (sample_rate, audio), refined_text = generate_audio(text, temperature, top_P, top_K, speaker_name, text_seed_input, refine_text_flag)

    # Calculate the audio duration in seconds 
    audio_duration = len(audio) / sample_rate
    return audio, refined_text, audio_duration

# Given a list of text, speaker names and sequence_id, 
# produce audio files for each speaker and save them to a single audio file
def produce_audio(transcript, audio_filename = 'test.wav', offset=0):
    audio_data = []
    transcript_text = [text for text, _, _ in transcript]
    for text, speaker_name, sequence_id in transcript:
        audio, refined_text, audio_duration = produce_audio_data(text, speaker_name, sequence_id)
        audio_data.append((audio, refined_text, audio_duration))
        print(f"finished producing audio for sequence_id: {sequence_id}, speaker: {speaker_name}")
        print(audio_duration, refined_text)
    
    audio_data_all, refined_text_all, audio_duration_all = zip(*audio_data)
    audio_data_all = np.concatenate(audio_data_all)
    sample_rate = 24000

    # Generate the srt subtitle file with the audio duration from the transcript
    srt_list = []
    if offset > 0: # from zero to offset time, there is music, just show [MUSIC]
        start_time_str = "{:02d}:{:02d}:{:02d},{:03d}".format(0, 0, 0, 0)
        end_time_str = "{:02d}:{:02d}:{:02d},{:03d}".format(int(offset//3600), int((offset//60)%60), int(offset%60), int((offset*1000)%1000))
        time_str = start_time_str + ' --> ' + end_time_str
        srt_list.append((time_str, '[AI GENERATED MUSIC]'))
    start_time = offset
    for text, audio_duration in zip(transcript_text, audio_duration_all):
        print(text, audio_duration)
        end_time = start_time + audio_duration
        # Convert the start and end time to the srt format
        start_time_str = "{:02d}:{:02d}:{:02d},{:03d}".format(int(start_time//3600), int((start_time//60)%60), int(start_time%60), int((start_time*1000)%1000))
        end_time_str = "{:02d}:{:02d}:{:02d},{:03d}".format(int(end_time//3600), int((end_time//60)%60), int(end_time%60), int((end_time*1000)%1000))
        # Output the srt format
        print(start_time_str, '-->', end_time_str)
        time_str = start_time_str + ' --> ' + end_time_str
        srt_list.append((time_str, text))
        start_time = end_time

    if not os.path.exists('audio'):
        os.makedirs('audio')
    
    # Save the srt file
    with open(f'audio/subtitle_{audio_filename}.srt', 'w') as srt_file:
        for i, (time_str, text) in enumerate(srt_list):
            srt_file.write(f"{i+1}\n")
            srt_file.write(f"{time_str}\n")
            srt_file.write(f"{text}\n\n")
        
    # Soundfile is a more friendly lib for concatenated audio in numpy array
    soundfile.write(f"audio/{audio_filename}", audio_data_all, sample_rate)

    with open(f'audio/refined_text_{audio_filename}.txt', 'w') as file:
        for refined_text in refined_text_all:
            file.write(f"{refined_text}\n")

    print(f"Audio file saved to audio/{audio_filename} and refined text saved to audio/refined_text_{audio_filename}.txt")
    return refined_text_all

if __name__ == '__main__':
    test_transcript = [
        ("Reinforcement Learning, or RL, further aligns the model with human preferences by optimizing responses based on reward models.", "Justin", 1),
        ("In DeepSeek-V2, RL is applied in two stages: first focusing on reasoning capabilities and then on general human preference alignment.", "Emma", 2),
        ("This approach ensures the model performs well in both specific tasks like coding and math, and in general conversational contexts.", "Justin", 3)
    ]
    refined_text = produce_audio(test_transcript, "test_output.wav")