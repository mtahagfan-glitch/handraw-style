"""Generate a music cue with Google Lyria 2 through fal.ai (≈30 s clip, 48 kHz WAV), then master it.

  python3 music_gen.py "<prompt>" <out_name> [--neg "vocals, lyrics"] [--seed 7]

Writes output/channel/music/<out_name>_raw.wav and <out_name>_master.wav. Add the result to
output/channel/music/library.json (mood, bpm, best_from) so future episodes can reuse it.
Prompt shape that worked for this channel: genre + instruments + emotion arc + tempo, no artist names, e.g.
  "cinematic orchestral, low strings ostinato and taiko, rising brass, tense then triumphant, 80 bpm, documentary".
For longer pieces or a specific structure, write a prompt for the owner to run in Google Flow Music instead.
"""
import argparse, json, os, subprocess, urllib.request
from pathlib import Path
ap = argparse.ArgumentParser(); ap.add_argument('prompt'); ap.add_argument('name')
ap.add_argument('--neg', default='vocals, singing, lyrics, low quality'); ap.add_argument('--seed', type=int); a = ap.parse_args()
LIB = Path(__file__).resolve().parents[3] / 'output' / 'channel' / 'music'; LIB.mkdir(parents=True, exist_ok=True)
body = {'prompt': a.prompt, 'negative_prompt': a.neg, **({'seed': a.seed} if a.seed is not None else {})}
req = urllib.request.Request('https://fal.run/fal-ai/lyria2', json.dumps(body).encode(),
                             {'Authorization': 'Key ' + os.environ['FAL_KEY'], 'Content-Type': 'application/json'})
r = json.load(urllib.request.urlopen(req, timeout=600))
raw = LIB / f'{a.name}_raw.wav'; raw.write_bytes(urllib.request.urlopen(r['audio']['url']).read())
subprocess.run(['bash', str(Path(__file__).with_name('master_music.sh')), str(raw), str(LIB / f'{a.name}_master.wav')], check=True)
