import cv2,json,sys
import numpy as np
from pathlib import Path
root=Path(__file__).resolve().parent.parent
points=json.loads((root/'qa/board-plane.json').read_text())
stacks=[]
masks=[]
clean_folder=Path(sys.argv[1]) if len(sys.argv)>1 else root/'frames'
report_path=Path(sys.argv[2]) if len(sys.argv)>2 else root/'qa/board-flicker.json'
for folder in [root/'qa/baseline',clean_folder]:
 stack=[]
 mask=np.ones((720,1280),bool)
 for f in range(215,245):
  im=cv2.imread(str(folder/f'{f:04d}.png'))
  hom=cv2.getPerspectiveTransform(np.float32(points[str(f)]),np.float32(points['215']))
  hom=np.diag([.5,.5,1])@hom
  aligned=cv2.warpPerspective(im,hom,(1280,720),flags=cv2.INTER_LINEAR).astype(np.float32)
  b,g,r=cv2.split(aligned)
  gray=cv2.cvtColor(aligned,cv2.COLOR_BGR2GRAY)
  gradient=np.hypot(cv2.Sobel(gray,cv2.CV_32F,1,0),cv2.Sobel(gray,cv2.CV_32F,0,1))
  mask&=(g>r*1.10)&(g>b*1.02)&(gradient<18)&(gray>40)
  stack.append(gray)
 masks.append(mask)
 stacks.append(np.array(stack))
mask=cv2.erode((masks[0]&masks[1]).astype(np.uint8),np.ones((5,5),np.uint8)).astype(bool)
assert mask.sum()>1000
report={'method':'Ground-truth board-plane homography, shared green PCB low-gradient mask; RMS temporal second difference divided by sqrt(6), in 8-bit luma units. A local temporal-noise proxy; real shading changes can contribute.','clean_frames':str(clean_folder),'pixels':int(mask.sum())}
for name,stack in zip(['previous','clean'],stacks):
 second=np.diff(stack[:,mask],n=2,axis=0)
 report[name]={'temporal_noise_rms':float(np.sqrt(np.mean(second**2)/6))}
report['reduction_percent']=100*(1-report['clean']['temporal_noise_rms']/report['previous']['temporal_noise_rms'])
report_path.write_text(json.dumps(report,indent=2))
cv2.imwrite(str(report_path.with_suffix('.mask.png')),mask.astype(np.uint8)*255)
print(json.dumps(report,indent=2))
