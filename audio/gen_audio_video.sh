#!/bin/bash

# Check if two parameters are passed
if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <arxiv_id> <cover_photo>"
    exit 1
fi

# Assign parameters to variables
arxiv_id=$1
cover_photo=$2

# Define input and output files
audio_file="${arxiv_id}.wav"
output_audio="${arxiv_id}_output.wav"
output_video="${arxiv_id}.mp4"

# Run the first ffmpeg command to concatenate audio files with crossfade
ffmpeg -i head.wav -i "$audio_file" -i tail.wav -filter_complex \
"[0][1]acrossfade=d=1:c1=tri:c2=tri[a1]; [a1][2]acrossfade=d=1:c1=tri:c2=tri[a2]" \
-map "[a2]" "$output_audio"

# Run the second ffmpeg command to create the video with the cover photo and concatenated audio
ffmpeg -loop 1 -i "$cover_photo" -i "$output_audio" -c:v libx264 -c:a aac -b:a 192k -pix_fmt yuv420p -shortest -vf "scale=1792:1024" "$output_video"