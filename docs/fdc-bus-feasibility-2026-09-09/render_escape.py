from pathlib import Path
import re,cairosvg
from PIL import Image,ImageDraw,ImageFont
P=Path(__file__).resolve().parent
font='/System/Library/Fonts/Supplemental/Arial.ttf'
out=Image.new('RGB',(1600,770),'#101923');d=ImageDraw.Draw(out)
d.text((35,20),'Separate FDC bus: validated module escape',font=ImageFont.truetype(font,32),fill='white')
for i,layer in enumerate(['F_Cu','B_Cu']):
 s=(P/'study/layers'/f'nrf-moisture-sensor-{layer}.svg').read_text()
 s=re.sub(r'width="[^"]+" height="[^"]+" viewBox="[^"]+"','width="760" height="550" viewBox="73 52 8 5.8"',s,count=1)
 overlay='<g fill="none" stroke="#9aabba" stroke-width="0.025"><path d="M73 54 H81"/></g>'
 for x,color in [(76.25,'#ffce61'),(77,'#50eed7')]:
  vx=x+.3
  path=f'M{x} 53.5 L{x} 53.95 L{vx} 54.25' if i==0 else f'M{vx} 54.25 L{vx} 56.5'
  overlay+=f'<path d="{path}" fill="none" stroke="{color}" stroke-width="0.13"/><circle cx="{vx}" cy="54.25" r="0.25" fill="none" stroke="{color}" stroke-width="0.065"/>'
 overlay+='<g fill="#ffffff" font-family="Arial" font-size="0.2"><text x="73.15" y="52.4">U1 • BL54L15</text><text x="73.15" y="53.95">Module edge</text></g>'
 if i==0:
  overlay+='<g fill="#ffce61" font-family="Arial" font-size="0.24"><text x="75.9" y="52.95">23</text></g><g fill="#50eed7" font-family="Arial" font-size="0.24"><text x="76.85" y="52.95">22</text></g><g fill="#fff" font-family="Arial" font-size="0.22"><text x="74.65" y="56.75">X1 crystal</text><text x="78" y="56.05">Marker test pads</text></g>'
 else:
  overlay+='<g fill="#fff" font-family="Arial" font-size="0.22"><text x="75.75" y="57.1">Continue toward FDC ↓</text></g>'
 s=s.replace('</svg>',overlay+'</svg>');p=P/f'escape-{layer}.png';cairosvg.svg2png(bytestring=s.encode(),write_to=str(p),background_color='#101923')
 out.paste(Image.open(p).convert('RGB'),(20+i*800,105));d.text((35+i*800,76),'Front copper' if i==0 else 'Back copper · viewed from top',font=ImageFont.truetype(font,24),fill='white')
d.text((35,670),'SCL: pad 23 / P1.04',font=ImageFont.truetype(font,24),fill='#ffce61');d.text((420,670),'SDA: pad 22 / P1.05',font=ImageFont.truetype(font,24),fill='#50eed7')
d.text((35,715),'0.20 mm tracks · 0.50 / 0.30 mm vias · Local breakout only; full FDC route is not yet laid out',font=ImageFont.truetype(font,22),fill='#bfccd9')
out.save(P/'recommended-escape.png')
