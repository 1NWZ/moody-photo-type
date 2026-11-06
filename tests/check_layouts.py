from pathlib import Path
import sys,json,tempfile
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'scripts'))
from PIL import Image,ImageDraw
from render_batch import render
from layout_engine import render_blocks
font=sys.argv[1]  # Supply a local font; no font binaries are distributed.
root=Path(tempfile.mkdtemp(prefix='layout-test-')).resolve()
Image.new('RGB',(1080,1440),'#47606c').save(root/'photo.png')
m=Image.new('L',(1080,1440));ImageDraw.Draw(m).ellipse((400,600,680,1150),fill=255);m.save(root/'mask.png')
variants={
 'vertical':[{'role':'main','lines':['A moment','to pause','and breathe','in the','quiet light']}],
 'split':[{'role':'title','lines':['Slow days']},{'role':'body','lines':['A quiet moment','to pause']},{'role':'top_left','lines':['DAILY NOTES']}],
 'micro':[{'role':'left','lines':['PAUSE','BREATHE']},{'role':'main','lines':['A QUIET MOMENT','Room to pause.']},{'role':'right','lines':['SLOW','DAYS']}]}
base={'font':font,'width':1080,'grade':{'mode':'none'},'layout_seed':42}
def run(name,items):
 data={**base,'items':items}; mf=root/(name+'.json');mf.write_text(json.dumps(data));render(mf,root/name);return json.loads((root/name/'layout.json').read_text())
def item(id,layouts,mask=True):
 d={'id':id,'image':'photo.png','layouts':layouts}
 if mask:d['foreground_mask']='mask.png'
 return d
r=run('all',[item(k,{k:v}) for k,v in variants.items()])
assert {i['layout_id'] for i in r['items']}==set(variants)
assert all(i['foreground_mask_applied'] for i in r['items'])
assert any(i['occluded_text_pixels']>0 for i in r['items'])
a=run('random_a',[item(str(i),variants) for i in range(8)])
b=run('random_b',[item(str(i),variants) for i in range(8)])
assert a==b
ids=[i['layout_id'] for i in a['items']];assert all(x!=y for x,y in zip(ids,ids[1:]))
for k,v in variants.items():
 ink,records=render_blocks((1080,1440),font,k,v)
 for rec in records:
  l,t,r,b=rec['text_bounds_before_occlusion'];x,y,w,h=rec['box']
  assert l>=x*1080-1 and t>=y*1440-1 and r<=(x+w)*1080+1 and b<=(y+h)*1440+1
try:run('missing_mask',[item('x',{'micro':variants['micro']},False)])
except ValueError: assert not (root/'missing_mask').exists()
else:raise AssertionError('Missing mask accepted')
try:run('overflow',[item('x',{'split':[{'role':'title','lines':['W'*100]},{'role':'body','lines':['Hello']} ]})])
except ValueError: assert not (root/'overflow').exists()
else:raise AssertionError('Overflow accepted')
# Full foreground coverage must leave every photo pixel untouched before JPEG encoding.
Image.new('L',(1080,1440),255).save(root/'mask.png')
run('covered',[item('x',{'vertical':variants['vertical']})])
Image.open(root/'photo.png').save(root/'baseline.jpg',quality=95,subsampling=0)
assert (root/'covered/x.jpg').read_bytes()==(root/'baseline.jpg').read_bytes()
run('legacy',[{'id':'legacy','image':'photo.png','lines':['A quiet day']}])
run('no_text',[{'id':'none','image':'photo.png','lines':[]}])
print('PASS: three layouts, bounds, seeded randomization, no adjacent repetition, foreground occlusion, missing-mask/overflow rejection, legacy and no-text paths')
print(root/'all/contact-sheet.jpg')
