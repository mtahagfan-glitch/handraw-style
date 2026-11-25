#!/usr/bin/env bash
# Final long video: hook + channel intro + story, upscaled to 1440p for YouTube, plus a <400 MB HEVC copy for delivery.
#   [GAIN=1.5] bash final.sh <work> <name> [intro_after_scene=2]        (run from the episode folder)
# Needs <work>_25d.mp4 (pipeline.py assemble with the final audio) and <work>/align.json.
set -e
WK=${1:?work dir}; NAME=${2:?output name}; AFTER=${3:-2}
CH="$(cd "$(dirname "$0")/../../.." && pwd)/output/channel"
mkdir -p final_hd
C=$(python3 -c "import json;print(json.load(open('$WK/align.json'))['cuts'][$AFTER]/25)")
G=${GAIN:+volume=${GAIN}dB,alimiter=limit=0.84:level=false,}   # GAIN=1.5 lifts a quiet mix toward -14 LUFS
V="scale=2560:1440:flags=lanczos,unsharp=5:5:0.35:5:5:0,format=yuv420p"
E="-c:v libx264 -preset medium -crf 21 -maxrate 7M -bufsize 14M -r 25 -g 50 -c:a aac -b:a 192k -ar 48000 -ac 2"
[ -s final_hd/p1.mp4 ] || ffmpeg -y -v error -i ${WK}_25d.mp4 -t $C -vf "$V" -af "${G}afade=t=out:st=$(python3 -c "print($C-0.5)"):d=0.5" $E final_hd/p1.mp4
[ -s final_hd/p2.mp4 ] || ffmpeg -y -v error -i "$CH/intro/intro_final.mp4" -vf "$V" $E final_hd/p2.mp4
[ -s final_hd/p3.mp4 ] || ffmpeg -y -v error -ss $C -i ${WK}_25d.mp4 -vf "$V" -af "${G}afade=t=in:d=0.8" $E final_hd/p3.mp4
printf "file 'p1.mp4'\nfile 'p2.mp4'\nfile 'p3.mp4'\n" > final_hd/list.txt
ffmpeg -y -v error -f concat -safe 0 -i final_hd/list.txt -c copy -movflags +faststart ${NAME}_1440p.mp4
rm -f final_hd/p3.mp4                                   # biggest part; keep disk free
# subtitles + chapter times shifted by the intro
python3 - "$WK" "$NAME" "$AFTER" <<'PY'
import json,re,subprocess,sys
wk,name,after=sys.argv[1],sys.argv[2],int(sys.argv[3])
d=lambda f:float(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','csv=p=0',f]))
c=[x/25 for x in json.load(open(f'{wk}/align.json'))['cuts']]; p2=d('final_hd/p2.mp4')
sh=lambda t:t+(p2 if t>=c[after]-0.01 else 0)
ts=lambda t:f"{int(t//3600):02d}:{int(t%3600//60):02d}:{int(t%60):02d},{int(round(t%1*1000))%1000:03d}"
P=lambda s:int(s[:2])*3600+int(s[3:5])*60+float(s[6:].replace(',','.'))
out=[]
for b in open(f'{wk}_25d.srt').read().strip().split('\n\n'):
    L=b.split('\n'); m=re.match(r'(\S+) --> (\S+)',L[1]); out.append(f"{L[0]}\n{ts(sh(P(m[1])))} --> {ts(sh(P(m[2])))}\n"+'\n'.join(L[2:]))
open(f'{name}_1440p.srt','w').write('\n\n'.join(out)+'\n')
json.dump({'intro_len':p2,'scene_start':[round(sh(x),2) for x in c]},open(f'{name}_times.json','w'))
print('chapter time of scene index k = scene_start[k] in', f'{name}_times.json')
PY
# delivery copy that fits the 400 MB upload limit (YouTube accepts HEVC; it re-encodes anyway)
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 ${NAME}_1440p.mp4)
VB=$(python3 -c "print(int(380*8*1024/$DUR - 170))")
ffmpeg -y -v error -i ${NAME}_1440p.mp4 -c:v libx265 -preset fast -b:v ${VB}k -maxrate $((VB*14/10))k -bufsize $((VB*28/10))k \
  -x265-params log-level=error -tag:v hvc1 -pix_fmt yuv420p -c:a aac -b:a 160k -movflags +faststart ${NAME}_1440p_hevc.mp4
ls -la ${NAME}_1440p*.mp4
