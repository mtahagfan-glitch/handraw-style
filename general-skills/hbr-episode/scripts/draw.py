"""Draw every scene of an episode (gpt-image-2 on fal), one request per scene.

  python3 draw.py prompts.txt imgs/ [--size 1920x1088] [--workers 3]      (FAL_KEY in the env)

prompts.txt: one full prompt per line, line N -> imgs/NN.png. Finished scenes are skipped, so it can be rerun.
A refused prompt (fal content checker, 422) does not stop the batch: it is reported as FAILED with the reason, so
it can be rephrased (no gore, no weapon details, no bodies; show the reaction, not the harm) and the script rerun.
"""
import argparse, glob, os, subprocess, tempfile, shutil
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
GEN = next(iter(glob.glob('/root/.claude/skills/**/gpt-image-2/scripts/generate.py', recursive=True)), None)
ap = argparse.ArgumentParser(); ap.add_argument('prompts'); ap.add_argument('out')
ap.add_argument('--size', default='1920x1088'); ap.add_argument('--workers', type=int, default=3); ap.add_argument('--quality', default='high')
a = ap.parse_args(); out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
lines = [l.strip() for l in open(a.prompts) if l.strip()]
def one(k):
    dst = out / f'{k + 1:02d}.png'
    if dst.exists(): return
    for attempt in range(2):
        tmp = tempfile.mkdtemp()
        r = subprocess.run(['python3', GEN, '--prompt', lines[k], '--size', a.size, '--quality', a.quality, '--out', tmp],
                           capture_output=True, text=True)
        png = glob.glob(f'{tmp}/*.png')
        if png: shutil.move(png[0], dst); shutil.rmtree(tmp); print('ok', dst.name, flush=True); return
        shutil.rmtree(tmp); err = (r.stdout + r.stderr).strip().splitlines()
        reason = next((x for x in err if 'HTTP' in x), err[-1] if err else '?')
        if '422' in reason or 'content' in reason: break           # a refusal will not pass on retry
    print('FAILED', dst.name, reason[:200], flush=True)
with ThreadPoolExecutor(a.workers) as ex: list(ex.map(one, range(len(lines))))
print('have', len(list(out.glob('*.png'))), 'of', len(lines))
