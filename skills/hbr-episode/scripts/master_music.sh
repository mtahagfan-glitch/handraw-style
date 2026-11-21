#!/usr/bin/env bash
# Polish a generated track (Flow Music / Lyria / any AI track) to channel standard: 48 kHz 24-bit, -14 LUFS.
#   bash master_music.sh <in.(mp3|m4a|wav)> <out_master.wav>
# Tames mud and boom, adds air and width, gentle glue. Download WAV from the generator when it offers it:
# Flow's m4a is ~106 kbps AAC with nothing above 16 kHz, and no mastering brings that back.
set -e
ffmpeg -v error -y -i "$1" -af "highpass=f=28,equalizer=f=60:t=q:w=1:g=-1.5,equalizer=f=280:t=q:w=1.2:g=-2.5,\
equalizer=f=3500:t=q:w=1.5:g=1.5,aexciter=amount=2:drive=6:freq=6500:blend=0,highshelf=f=11000:g=2.5,extrastereo=m=1.35,\
aecho=0.85:0.5:45|75:0.12|0.08,acompressor=threshold=-20dB:ratio=2:attack=30:release=300:makeup=1,loudnorm=I=-14:TP=-1.2:LRA=14" \
  -ar 48000 -c:a pcm_s24le "$2"
echo "$2"
