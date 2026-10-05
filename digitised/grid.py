import numpy as np
def gridfit(pts):
    hi=[p for p in pts if p[2]>=13]
    xs=[p[0] for p in hi]
    s=np.median(np.diff(xs))
    x0,x1=xs[0],xs[-1]
    N=int(round((x1-x0)/s))+1
    s=(x1-x0)/(N-1)
    out=[];miss=[]
    for k in range(N):
        xk=x0+k*s
        c=[p for p in pts if abs(p[0]-xk)<s/3 and p[2]>=10.5]
        if not c: miss.append(k); out.append(None); continue
        out.append(max(c,key=lambda p:p[2]))
    return out,miss,s
