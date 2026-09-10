"""Compare motion-compensated temporal residuals; this is a flicker proxy, not perceptual proof."""
import json
import sys
from pathlib import Path
import cv2
import numpy as np

reports = {}
for folder_arg in sys.argv[1:]:
    folder = Path(folder_arg)
    frames = []
    for f in range(215, 245):
        im = cv2.imread(str(folder / f'{f:04d}.png'))
        assert im is not None, f'Missing frame {f} in {folder}'
        frames.append(cv2.cvtColor(cv2.resize(im, (1280, 720), interpolation=cv2.INTER_AREA), cv2.COLOR_BGR2GRAY))
    pairs = []
    yy, xx = np.mgrid[:720, :1280].astype(np.float32)
    for i, (a, b) in enumerate(zip(frames, frames[1:])):
        flow = cv2.calcOpticalFlowFarneback(a, b, None, .5, 4, 25, 4, 7, 1.5, 0)
        warped = cv2.remap(b, xx + flow[..., 0], yy + flow[..., 1], cv2.INTER_LINEAR)
        gradient = np.hypot(cv2.Sobel(a, cv2.CV_32F, 1, 0), cv2.Sobel(a, cv2.CV_32F, 0, 1))
        mask = (gradient < 12) & (a > 25) & (a < 245)
        mask[:20] = False
        mask[-20:] = False
        mask[:, :20] = False
        mask[:, -20:] = False
        error = np.abs(a.astype(np.float32) - warped.astype(np.float32))[mask]
        pairs.append({'frame': 215 + i, 'mean_luma_error': float(error.mean()), 'p95_luma_error': float(np.percentile(error, 95))})
    reports[str(folder)] = {'mean_residual': float(np.mean([p['mean_luma_error'] for p in pairs])), 'mean_p95': float(np.mean([p['p95_luma_error'] for p in pairs])), 'pairs': pairs}
print(json.dumps({'description': 'Optical-flow-compensated luma residual in low-gradient regions at 1280x720. Lower suggests less flicker. Geometry, lighting, blur, and codec also influence this metric.', 'results': reports}, indent=2))
