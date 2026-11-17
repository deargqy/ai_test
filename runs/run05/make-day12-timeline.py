from PIL import Image,ImageDraw
from pathlib import Path
r=Path(__file__).resolve().parents[2]
a=sorted((r/'docs/playtest-2026-11-16-run05').glob('day12-fight-*.jpg'))
s=Image.new('RGB',(960,len(a)*100),'white');d=ImageDraw.Draw(s)
for i,p in enumerate(a):
 im=Image.open(p).crop((0,0,1920,170));im.thumbnail((960,85));s.paste(im,(0,i*100+15));d.text((0,i*100),p.stem,fill='black')
s.save(r/'runs/run05/day12-timeline.jpg')
