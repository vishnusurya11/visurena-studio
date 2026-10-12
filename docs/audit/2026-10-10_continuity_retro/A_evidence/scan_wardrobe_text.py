import json,sys,re,glob,os,collections
sys.stdout.reconfigure(encoding='utf-8')
B=r"D:/Projects/KingdomOfViSuReNa/alpha/visurena_studio/library/20260827135508_the-war-of-the-worlds"
prof=json.load(open(B+'/analysis/characters/unnamed_first_person_narrator.json',encoding='utf-8'))['profile']
W=prof['wardrobe']
keys={k:v[:45] for k,v in W.items()}
def classify(t):
    hits=[k for k,v in W.items() if v[:40].split(':')[0][:30] in t]
    # distinctive markers
    m=[]
    for k,mark in [('ragged','ash-grey throughout'),('beard','beard'),('flannel','flannel shirt'),('scald','Bare to the waist'),('soaked','soaked to dark charcoal'),('hatless','Bareheaded, dark hair tousled'),('borrowed','Borrowed loose'),('herringbone','herringbone'),('boater','boater'),('second','dry second suit'),('ashgrey_hair','Ash-grey hair parted')]:
        if mark in t: m.append(k)
    return m
for ep in sorted(glob.glob(B+'/episodes/ep*')):
    e=os.path.basename(ep)
    # grids
    gs=sorted(glob.glob(ep+'/storyboard/grids/*.txt'))
    c=collections.Counter(); n=0
    for g in gs:
        t=open(g,encoding='utf-8').read()
        n+=1
        c[tuple(classify(t))]+=1
    # takes
    tk=sorted(glob.glob(ep+'/takes/r2v/T*.graph.json'))
    tc=collections.Counter(); imgs=collections.Counter()
    for g in tk:
        d=json.load(open(g,encoding='utf-8'))
        p=' '.join(n2['inputs'].get('prompt','') for n2 in d.values() if isinstance(n2,dict) and isinstance(n2.get('inputs',{}).get('prompt',''),str))
        tc[tuple(classify(p))]+=1
        for n2 in d.values():
            if isinstance(n2,dict) and n2.get('class_type')=='LoadImage':
                im=n2['inputs']['image']; imgs[re.sub(r'_[0-9a-f]{6,}','',im)]+=1
    print(f'== {e} grids={n} takes={len(tk)}')
    print('  grid wardrobe markers:',dict(c))
    print('  take wardrobe markers:',dict(tc))
    print('  take images:',dict(imgs.most_common(12)))
