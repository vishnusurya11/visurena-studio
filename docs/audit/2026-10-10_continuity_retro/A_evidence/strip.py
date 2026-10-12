import json,glob,sys,subprocess,os
from PIL import Image,ImageDraw
B="D:/Projects/KingdomOfViSuReNa/alpha/visurena_studio/library/20260827135508_the-war-of-the-worlds/episodes"
S=sys.argv[1]; ep=sys.argv[2]; takes=sys.argv[3].split(',')
rows=[]
for t in takes:
    mp=f"{B}/{ep}/takes/r2v/T{int(t):02d}.mp4"
    panel=f"{B}/{ep}/storyboard/shot_{int(t):02d}.png"
    ims=[]
    if os.path.exists(panel): ims.append(Image.open(panel).convert('RGB'))
    for ss in ('2','-0.2'):
        out=f"{S}/{ep}_T{t}_{ss}.png"
        args=['ffmpeg','-y','-loglevel','error']+(['-sseof','-0.3'] if ss.startswith('-') else ['-ss',ss])+['-i',mp,'-frames:v','1',out]
        subprocess.run(args)
        if os.path.exists(out): ims.append(Image.open(out).convert('RGB'))
    ims=[i.resize((360,int(360*i.height/i.width))) for i in ims]
    h=max(i.height for i in ims); row=Image.new('RGB',(360*len(ims),h+20),'black')
    for k,i in enumerate(ims): row.paste(i,(360*k,20))
    ImageDraw.Draw(row).text((4,4),f"{ep} T{t}: panel | 2s | last",fill='white')
    rows.append(row)
W=max(r.width for r in rows); H=sum(r.height for r in rows)
c=Image.new('RGB',(W,H)); y=0
for r in rows: c.paste(r,(0,y)); y+=r.height
c.save(f"{S}/strip_{ep}.png"); print(f"{S}/strip_{ep}.png")
