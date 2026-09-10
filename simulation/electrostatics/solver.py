"""2-D square-cell finite-volume electrostatics; charge is Q/length/epsilon0.
Harmonic face permittivity; unspecified exterior edges have zero normal flux.
Dirichlet nodes use finite values in `fixed`, free nodes use NaN.
"""
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.linalg import spsolve

def solve(eps, fixed):
    shape=eps.shape; n=eps.size; idx=np.arange(n).reshape(shape)
    rows=[]; cols=[]; data=[]
    for axis in (0,1):
        left=[slice(None)]*2; right=left.copy()
        left[axis]=slice(None,-1); right[axis]=slice(1,None)
        a=tuple(left); b=tuple(right)
        i=idx[a].ravel(); j=idx[b].ravel()
        g=(2*eps[a]*eps[b]/(eps[a]+eps[b])).ravel()
        for r,c,v in [(i,i,g),(j,j,g),(i,j,-g),(j,i,-g)]:
            rows.extend(r);cols.extend(c);data.extend(v)
    lap=coo_matrix((data,(rows,cols)),shape=(n,n)).tocsr()
    known=np.isfinite(fixed.ravel()); free=~known
    v=np.nan_to_num(fixed.ravel())
    v[free]=spsolve(lap[free][:,free],-lap[free][:,known]@v[known])
    return v.reshape(shape),(lap@v).reshape(shape)
