"""Turn one key drawing into a real moving shot (image-to-video on fal.ai) for the hook and big moments.

  python3 motion.py <image.png> <out.mp4> "<motion prompt>" [--model kling|veo] [--dur 5]

Default model: Kling (cheap, keeps drawn style well). --model veo uses Google Veo through fal.
Keep the prompt about MOTION only (camera + what moves); the style comes from the picture:
  "slow push-in, the player sprints toward the ball, crowd flags wave, ink-drawn style unchanged"
Then splice it into the scene with xfade (see references/motion-hooks.md). 2-3 such shots per episode, max.
"""
import argparse, base64, json, os, time, urllib.request
ap = argparse.ArgumentParser(); ap.add_argument('img'); ap.add_argument('out'); ap.add_argument('prompt')
ap.add_argument('--model', default='kling'); ap.add_argument('--dur', default='5'); a = ap.parse_args()
M = {'kling': 'fal-ai/kling-video/v2.1/standard/image-to-video', 'veo': 'fal-ai/veo3/fast/image-to-video'}[a.model]
H = {'Authorization': 'Key ' + os.environ['FAL_KEY'], 'Content-Type': 'application/json'}
uri = 'data:image/png;base64,' + base64.b64encode(open(a.img, 'rb').read()).decode()
body = {'image_url': uri, 'prompt': a.prompt, 'duration': a.dur if a.model == 'kling' else f'{int(a.dur)}s'}
if a.model == 'veo': body.update(generate_audio=False, aspect_ratio='16:9')
q = json.load(urllib.request.urlopen(urllib.request.Request(f'https://queue.fal.run/{M}', json.dumps(body).encode(), H)))
while True:
    st = json.load(urllib.request.urlopen(urllib.request.Request(q['status_url'], headers=H)))
    if st['status'] == 'COMPLETED': break
    if st['status'] not in ('IN_QUEUE', 'IN_PROGRESS'): raise SystemExit(st)
    time.sleep(8)
r = json.load(urllib.request.urlopen(urllib.request.Request(q['response_url'], headers=H)))
open(a.out, 'wb').write(urllib.request.urlopen(r['video']['url']).read()); print(a.out)
