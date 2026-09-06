"""Read-only dimensional concept from KiCad outline and current transforms."""
from pathlib import Path
import sys, math
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle,Circle,Polygon
from tools_sexp import parse,find,first
root=Path(__file__).resolve().parents[2]
s=parse((root/'nrf-moisture-sensor.kicad_pcb').read_text())
def xy(n,key):return np.array(list(map(float,first(n,key)[1:3])))
def curve(n):
 a,b,c=xy(n,'start'),xy(n,'mid'),xy(n,'end')
 o=np.linalg.solve(2*np.array([b-a,c-a]),np.array([b@b-a@a,c@c-a@a])); r=np.linalg.norm(a-o)
 ang=[math.atan2(*(p-o)[::-1]) for p in [a,b,c]]
 sweep=(ang[2]-ang[0])%(2*math.pi)
 if (ang[1]-ang[0])%(2*math.pi)>sweep:sweep-=2*math.pi
 t=np.linspace(ang[0],ang[0]+sweep,40)
 return np.array([o[0]+r*np.cos(t),o[1]+r*np.sin(t)]).T
fp={next(x[2] for x in find(f,'property') if x[1]=='Reference'):f for f in find(s,'footprint')}
def transform(f,p):
 tr=first(f,'transform');v=xy(tr,'translate');a=-math.radians(float(first(tr,'rotate')[1]));m=np.array([[math.cos(a),-math.sin(a)],[math.sin(a),math.cos(a)]])
 return p@m.T+v
fig,axs=plt.subplots(1,2,figsize=(12,9),layout='constrained')
for ax,candidate in zip(axs,[False,True]):
 ax.set_aspect('equal');ax.set_xlim(55,108);ax.set_ylim(119,35);ax.set_facecolor('#fafbfc');ax.grid(alpha=.13)
 for n in s:
  if not isinstance(n,list) or first(n,'layer')!=['layer','Edge.Cuts']:continue
  if n[0]=='gr_line':p=np.array([xy(n,'start'),xy(n,'end')]);ax.plot(*p.T,color='#243746',lw=1.6)
  elif n[0]=='gr_arc':ax.plot(*curve(n).T,color='#243746',lw=1.6)
  elif n[0]=='gr_circle':ax.add_patch(Circle(xy(n,'center'),np.linalg.norm(xy(n,'end')-xy(n,'center')),fill=False,color='#243746'))
 for n in find(fp['BT1'],'fp_line'):
  if first(n,'layer')==['layer','F.CrtYd']:
   p=transform(fp['BT1'],np.array([xy(n,'start'),xy(n,'end')]));ax.plot(*p.T,color='#64748b',lw=1)
 ax.add_patch(Circle((77,82.4),10,color='#e2e8f0',ec='#64748b'));ax.text(77,82.4,'CR2032\nØ20 mm',ha='center',va='center',fontsize=9)
 for ref,w,h,col in [('U2',4,4,'#93c5fd'),('U3',3,5,'#c4b5fd'),('J4',7,9,'#fde68a'),('U4',1.5,1.5,'#99f6e4')]:
  p=xy(first(fp[ref],'transform'),'translate');ax.add_patch(Rectangle(p-[w/2,h/2],w,h,color=col,ec='#475569'));ax.text(p[0],p[1],ref,ha='center',va='center',fontsize=8)
 ax.axhline(70,color='#dc2626',ls='--',lw=1.5);ax.text(60,69,'Proposed cut: y = 70 mm',color='#b91c1c',fontsize=9)
 if candidate:
  ax.add_patch(Rectangle((60,40),42,30,color='#fee2e2',alpha=.6));x,y=80,93
  ax.add_patch(Rectangle((89,78),5,23.5,fill=False,hatch='///',edgecolor='#dc2626',lw=1.2))
  ax.add_patch(Rectangle((x,y),14,10,facecolor='#bfdbfe',edgecolor='#1d4ed8',lw=1.8));ax.add_patch(Rectangle((89,y),5,8.5,color='#fdba74',alpha=.8))
  ax.text(85,97.8,'U1\n14 × 10',ha='center',va='center',fontsize=8)
  ax.annotate('Keepout crosses\nholder terminal',xy=(92,82),xytext=(101,75),ha='center',fontsize=8,color='#b91c1c',arrowprops={'arrowstyle':'->','color':'#b91c1c'})
  ax.annotate('Only 0.2 mm to\ndrilled hole edge',xy=(89.5,103.1),xytext=(103,110),ha='center',fontsize=8,color='#b91c1c',arrowprops={'arrowstyle':'->','color':'#b91c1c'})
  ax.annotate('',xy=(57,70),xytext=(57,114),arrowprops={'arrowstyle':'<->'});ax.text(56.4,92,'44 mm head',rotation=90,ha='right',va='center',fontsize=9)
  ax.set_title('Candidate placement exposes conflicts\nConcept only — requires relocation and rerouting',fontsize=12)
 else:
  ax.add_patch(Rectangle((72,40),10,14,facecolor='#bfdbfe',edgecolor='#1d4ed8'));ax.add_patch(Rectangle((72,40),8.5,5,facecolor='#fdba74'));ax.text(77,49,'U1',ha='center',fontsize=9)
  ax.add_patch(Rectangle((57,39),23.5,6,fill=False,hatch='///',edgecolor='#dc2626'))
  ax.annotate('',xy=(57,40),xytext=(57,114),arrowprops={'arrowstyle':'<->'});ax.text(56.4,77,'74 mm head',rotation=90,ha='right',va='center',fontsize=9)
  ax.set_title('Current head: 34 mm wide, 74 mm long\n42 mm total width including SHT tab',fontsize=12)
 ax.set_xlabel('Board X (mm)');ax.set_ylabel('Board Y (mm)')
fig.suptitle('nRF Moisture Sensor • 30 mm trim feasibility\nOverall length 155 → 125 mm (19.4%); probe geometry retained',fontsize=15)
fig.savefig(root/'docs/design-review-2026-09-05/shrink-concept.png',dpi=180)
fig.savefig(root/'docs/design-review-2026-09-05/shrink-concept.svg')
