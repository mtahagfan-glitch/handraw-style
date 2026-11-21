"""Align the owner's own recording to scenes.json, tighten long pauses without cutting speech.

  python3 align_real.py [--check]       (run from the episode folder)

Inputs : scenes.json, real/raw.m4a (the recording), real/stt.json (word timings: ElevenLabs Scribe
         or any {"words":[{"text","start","end","type":"word"}]}).
Output : parallax_real/voice.wav + parallax_real/align.json  (sentences, cuts in frames @25fps, words)
episode.json "extra_silence": {"<scene number>": seconds} leaves room for inserted audio (e.g. real commentary).
"""
import json, re, difflib, subprocess, wave, sys, os
import numpy as np
EP=json.load(open('episode.json')) if os.path.exists('episode.json') else {}
EXTRA={int(k):v for k,v in EP.get('extra_silence',{}).items()}
SR=48000; GAP=0.3; CUT_AFTER=0.2; MAXPAUSE=0.75; KEEP=0.5; PRE=0.05; POST=0.09
sc=json.load(open('scenes.json')); W=[w for w in json.load(open('real/stt.json'))['words'] if w['type']=='word']
def norm(t):
    t=re.sub(r'[ً-ْـ]','',t); t=re.sub(r'[^\w؀-ۿ]','',t)
    return t.replace('أ','ا').replace('إ','ا').replace('آ','ا').replace('ى','ي').replace('ة','ه').lower()
# script words with (scene, sentence) ids
sw=[]; sents=[]
for i,s in enumerate(sc):
    for sent in re.split(r'(?<=[.!؟?…:])\s+', s['ar'].strip()):
        sid=len(sents); sents.append({'scene':i,'text':sent.strip()})
        for w in sent.split():
            if norm(w): sw.append((norm(w),i,sid))
tw=[norm(w['text']) for w in W]
m=difflib.SequenceMatcher(None,[x[0] for x in sw],tw,autojunk=False)
mp=[None]*len(sw); matched=0
for a,b,n in m.get_matching_blocks():
    for k in range(n): mp[a+k]=b+k; matched+=1
# interpolate unmatched script words between anchors
anch=[(i,j) for i,j in enumerate(mp) if j is not None]
for (i0,j0),(i1,j1) in zip(anch,anch[1:]):
    for i in range(i0+1,i1): mp[i]=min(j1-1 if j1>j0 else j0, j0+round((i-i0)*(j1-j0)/(i1-i0)))
for i in range(anch[0][0]): mp[i]=0
for i in range(anch[-1][0]+1,len(sw)): mp[i]=len(W)-1
print(f'script words {len(sw)}, spoken {len(tw)}, matched {matched} ({matched/len(sw):.0%})')
# big unmatched spoken runs = possible retakes / ad-libs
used=set(j for j in mp)
run=[]; big=[]
for j in range(len(W)):
    if j not in used: run.append(j)
    else:
        if len(run)>=6: big.append((round(W[run[0]]['start'],1),len(run),' '.join(W[k]['text'] for k in run[:10])))
        run=[]
print('unmatched spoken runs >=6 words:',big)
if '--check' in sys.argv: sys.exit()
# scene spans in transcript word indices
first={}; last={}
for (w,i,sid),j in zip(sw,mp):
    first.setdefault(i,j); last[i]=j
for i in range(1,len(sc)):                      # keep spans ordered and non-overlapping
    if first[i]<=last[i-1]: first[i]=last[i-1]+1
# cleaned audio
subprocess.run(['ffmpeg','-v','error','-y','-i','real/raw.m4a','-af',
 'highpass=f=75,afftdn=nr=10:nf=-50,acompressor=threshold=0.06:ratio=3:attack=12:release=180:makeup=2,equalizer=f=3500:t=q:w=1.2:g=2,loudnorm=I=-16:TP=-1.5:LRA=8',
 '-ar',str(SR),'-ac','1','-c:a','pcm_s16le','real/clean.wav'],check=True)
w=wave.open('real/clean.wav'); x=np.frombuffer(w.readframes(w.getnframes()),'<i2').astype(np.float32); w.close()
out=[]; pos=0.0; tmap=[]                         # tmap: (src_start, src_end, dst_start)
def speechy(a,b):                               # a 'pause' that still has voice in it = mistimed words, keep it
    s=x[int((a+0.25)*SR):int((b-0.25)*SR)]/32768
    if len(s)<SR*0.1: return False
    fr=s[:len(s)//960*960].reshape(-1,960); r=20*np.log10(np.sqrt((fr**2).mean(1))+1e-9)
    return (r>-35).mean()>0.3
def add(a,b):
    global pos
    a=max(0,a); seg=x[int(a*SR):int(b*SR)].copy(); f=min(len(seg)//2,int(0.006*SR))
    if f: seg[:f]*=np.linspace(0,1,f); seg[-f:]*=np.linspace(1,0,f)
    tmap.append((a,b,pos)); out.append(seg); pos+=len(seg)/SR
def sil(d):
    global pos
    out.append(np.zeros(int(d*SR),np.float32)); pos+=int(d*SR)/SR
cuts=[0]; sil(0.2); removed=0.0
for i in range(len(sc)):
    js=list(range(first[i],last[i]+1)); a=W[js[0]]['start']-PRE
    for j,k in zip(js,js[1:]):
        g=W[k]['start']-W[j]['end']
        if g>MAXPAUSE and not speechy(W[j]['end'],W[k]['start']):
            add(a,W[j]['end']+KEEP/2); a=W[k]['start']-KEEP/2; removed+=g-KEEP
    add(a,W[js[-1]]['end']+POST)
    if i<len(sc)-1:
        sil(GAP+EXTRA.get(i+1,0.0)); cuts.append(round((pos-GAP-EXTRA.get(i+1,0.0)+CUT_AFTER+EXTRA.get(i+1,0.0))*25))
    else: sil(1.0)
total=pos; cuts.append(round(total*25))
def T(t):
    for a,b,d in tmap:
        if a<=t<=b: return d+(t-a)
    best=min(tmap,key=lambda z:min(abs(t-z[0]),abs(t-z[1]))); return best[2]+min(max(t-best[0],0),best[1]-best[0])
sent_j={}
for (wd,i,sid),j in zip(sw,mp):
    sent_j.setdefault(sid,[j,j]); sent_j[sid][1]=j
S=[{'scene':s['scene'],'text':s['text'],'start':T(W[sent_j[k][0]]['start']),'end':T(W[sent_j[k][1]]['end'])} for k,s in enumerate(sents) if k in sent_j]
for p,q in zip(S,S[1:]):
    if q['start']<p['end']: q['start']=p['end']
    if q['end']<=q['start']: q['end']=q['start']+0.3
import os; os.makedirs('parallax_real',exist_ok=True)
y=np.concatenate(out); y=(np.clip(y,-32768,32767)).astype('<i2')
o=wave.open('parallax_real/voice.wav','wb'); o.setnchannels(2); o.setsampwidth(2); o.setframerate(SR); o.writeframes(np.repeat(y,2).tobytes()); o.close()
WD=[{'text':W[j]['text'],'start':T(W[j]['start']),'end':T(W[j]['end'])} for j in range(first[0],last[len(sc)-1]+1)]
json.dump({'sentences':S,'cuts':cuts,'words':WD,'total':total},open('parallax_real/align.json','w'),ensure_ascii=False,indent=1)
print(f'total {total/60:.2f} min (raw {len(x)/SR/60:.2f}), pauses removed {removed:.0f}s')
