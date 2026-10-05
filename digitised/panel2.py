import numpy as np
from scipy import ndimage as ndi
from panel import runs1d
def digitize2(b, ytop, ybot, xlo, xhi, thr=10):
    hgt=ybot-ytop
    cs=b[ytop:ybot, xlo:xhi].sum(0)
    vcols=runs1d(np.where(cs>hgt*0.8)[0])
    xl=xlo+vcols[0][0]; xlr=xlo+vcols[0][1]; xr=xlo+vcols[-1][0]
    y0=ytop-25; x0=xlr-25
    inner=b[y0:ybot+25, x0:xr+25].copy()
    dt=ndi.distance_transform_edt(inner)
    mx=ndi.maximum_filter(dt,size=25)
    pk=(dt==mx)&(dt>=thr)
    lab,n=ndi.label(pk)
    cents=ndi.center_of_mass(pk,lab,range(1,n+1))
    vals=[dt[int(round(c[0])),int(round(c[1]))] for c in cents]
    pts=[(c[1]+x0,c[0]+y0,v) for c,v in zip(cents,vals)]
    # merge peaks closer than 20 px
    pts.sort(); merged=[]
    for p in pts:
        if merged and abs(p[0]-merged[-1][0])<20 and abs(p[1]-merged[-1][1])<20:
            q=merged[-1]; merged[-1]=((p[0]+q[0])/2,(p[1]+q[1])/2,max(p[2],q[2]))
        else: merged.append(p)
    return dict(xl=int(xl),xr=int(xr),pts=merged)
