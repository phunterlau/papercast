import os
import sys
from pydub import AudioSegment
from pydub.effects import compress_dynamic_range

def normalize_audio(audio, target_dBFS):
    change_in_dBFS = target_dBFS - audio.dBFS
    return audio.apply_gain(change_in_dBFS)

def process_audio(input_file, output_file, target_level=-10):
    # Load the audio file
    audio = AudioSegment.from_wav(input_file)

    # Store original parameters
    original_sample_rate = audio.frame_rate
    original_sample_width = audio.sample_width
    original_channels = audio.channels

    # Normalize the audio to a target level (in dBFS)
    normalized_audio = normalize_audio(audio, target_level)

    # Apply compression to reduce dynamic range
    compressed_audio = compress_dynamic_range(normalized_audio,
        threshold=-20,
        ratio=4.0,
        attack=5,
        release=50
    )

    # Export the processed audio, ensuring original parameters are maintained
    compressed_audio.export(
        output_file,
        format="wav",
        parameters=[
            "-ar", str(original_sample_rate),
            "-sample_fmt", {1: "s8", 2: "s16", 3: "s24", 4: "s32"}[original_sample_width],
            "-ac", str(original_channels)
        ]
    )

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python script.py <input_wav_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    
    if not os.path.exists(input_file):
        print(f"Error: The file '{input_file}' does not exist.")
        sys.exit(1)

    if not input_file.lower().endswith('.wav'):
        print("Error: The input file must be a WAV file.")
        sys.exit(1)

    # Create output filename
    base_name = os.path.basename(input_file)
    output_file = f"processed_{base_name}"

    # Process the audio
    process_audio(input_file, output_file)
    print(f"Audio processing complete. Output file: {output_file}")

    # Verify the output file
    output_audio = AudioSegment.from_wav(output_file)
    print(f"Original sample rate: {AudioSegment.from_wav(input_file).frame_rate}")
    print(f"Processed sample rate: {output_audio.frame_rate}")
    print(f"Original sample width: {AudioSegment.from_wav(input_file).sample_width}")
    print(f"Processed sample width: {output_audio.sample_width}")
    print(f"Original channels: {AudioSegment.from_wav(input_file).channels}")
    print(f"Processed channels: {output_audio.channels}")