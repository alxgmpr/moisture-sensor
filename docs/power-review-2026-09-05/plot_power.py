#!/usr/bin/env python3
"""Plot measured copper and screening curves after running analyze_power.py."""
import json, pathlib, math
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.patches import Polygon, Circle
P=pathlib.Path(__file__).resolve().parent
j=json.loads((P/'copper-inventory.json').read_text())
colors={'+3V3':'#d34b22','+3V3_FDC_SW':'#d68f00','VBAT':'#286eb7','/VBAT_RAW':'#925ac1','/VINT':'#22917c','/SW':'#333333'}
fig,ax=plt.subplots(figsize=(8,10))
for z in j['zones']:
 if z['net'] in colors:
  for p in z['fills']:
   ax.add_patch(Polygon(p['points'],color=colors[z['net']],alpha=.28))
for s in j['segments']:
 if s['net'] in colors:
  ax.plot([s['start'][0],s['end'][0]],[s['start'][1],s['end'][1]],color=colors[s['net']],linewidth=2.2,linestyle='--' if s['layer']=='B.Cu' else '-')
for v in j['vias']:
 if v['net'] in colors: ax.add_patch(Circle(v['at'],v['diameter_mm']/2,fill=False,color=colors[v['net']]))
for ref in ['U1','U2','U3','U4','J4','BT1']:
 ps=[p for p in j['pads'] if p['ref']==ref and p['net'] in colors]
 if ps:
  p=ps[0];ax.annotate(ref,p['at'],xytext=(6,-12),textcoords='offset points',fontsize=11,fontweight='bold')
for net,color in colors.items(): ax.plot([],[],color=color,label=net,linewidth=3)
ax.legend(loc='lower right'); ax.set(xlim=(59,104),ylim=(105,47),aspect='equal',xlabel='Board X (mm)',ylabel='Board Y (mm)',title='Actual power copper: solid top / dashed bottom\nFilled polygons shown; other copper omitted')
ax.grid(alpha=.15);fig.tight_layout();fig.savefig(P/'power-copper.png',dpi=180);plt.close(fig)
fig,axs=plt.subplots(1,2,figsize=(11,4.5))
amps=[i/1000 for i in range(1,251)]
for w in [.2,.38,.4,.5]:
 t=.035*.8;wd=w*.8
 rises=[(i/(.048*(wd*t/.0254**2)**.725))**(1/.44) for i in amps]
 drops=[i*.01724*(1+.00393*40)*.01/(wd*t)*1000 for i in amps]
 axs[0].plot([i*1000 for i in amps],rises,label=f'{w:g} mm nominal')
 axs[1].plot([i*1000 for i in amps],drops,label=f'{w:g} mm nominal')
for ax in axs:
 ax.axvline(450/3.3,color='#777',linestyle=':',label='136 mA boost power limit')
 ax.set_xlabel('Current (mA)');ax.grid(alpha=.2)
axs[0].set_ylabel('IPC-2221 screening rise (°C)');axs[1].set_ylabel('Drop per 10 mm at 60°C copper (mV)');axs[0].legend(fontsize=8)
fig.suptitle('Sensitivity: outer copper and width each reduced 20%\nModel only; not measured temperature or board-level voltage drop')
fig.tight_layout();fig.savefig(P/'current-sweep.png',dpi=180)
