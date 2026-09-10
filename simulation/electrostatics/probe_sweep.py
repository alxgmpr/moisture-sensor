"""Exploratory 2-D cross-section, NOT a soil calibration or whole-probe model.
Actual copper widths; no copper backing beneath electrodes. Each shield layer
is equipotential with sense (ideal driver). Lossless homogeneous exterior with
an explicitly grounded distant boundary. End fringing, conductivity, inter-
electrode coupling, soldermask and copper thickness are omitted.
"""
from pathlib import Path
import csv
import numpy as np
from solver import solve
EPS0=8.8541878128e-12

def case(h,extent,soil,coat):
    x=np.arange(-extent,extent+h/2,h);z=x.copy();X,Z=np.meshgrid(x,z)
    eps=np.full(X.shape,float(soil));fixed=np.full(X.shape,np.nan)
    pcb=(abs(X)<=10)&(Z>=-1.6)&(Z<=0)
    coated=(abs(X)<=10+coat)&(Z>=-1.6-coat)&(Z<=coat)
    eps[coated]=3.;eps[pcb]=4.2
    sense=np.zeros(X.shape,dtype=bool)
    sense[np.argmin(abs(z)),abs(x)<=8]=True
    fixed[sense]=1
    for layer in [0,-.1344,-1.4146,-1.6]:
        fixed[np.argmin(abs(z-layer)),(abs(x)>=8.2)&(abs(x)<=10)]=1
    fixed[[0,-1],:]=0;fixed[:,[0,-1]]=0
    v,q=solve(eps,fixed)
    # 30 mm electrode length: ignores longitudinal end effects.
    sense_pf=q[sense].sum()*EPS0*.03*1e12
    shield_pf=q[(fixed==1)&~sense].sum()*EPS0*.03*1e12
    return sense_pf,shield_pf

out=Path('docs/reliability-2026-09-07');out.mkdir(exist_ok=True)
with (out/'probe-sweep.csv').open('w') as f:
    w=csv.writer(f);w.writerow(['grid_mm','boundary_mm','soil_epsilon','coating_mm','sense_pF_2d','shield_pF_2d'])
    for h,extent in [(.2,30),(.1,30),(.2,50)]:
        for coat in [.2,.6,1.0]:
            for soil in [1,5,20,40]:
                c,s=case(h,extent,soil,coat);w.writerow([h,extent,soil,coat,c,s]);f.flush()
                print(h,extent,soil,coat,round(c,2),round(s,2),flush=True)
