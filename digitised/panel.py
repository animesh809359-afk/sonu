import sys, json, numpy as np
from scipy import ndimage as ndi
def runs1d(idx,gap=2):
    g=[]
    for i in idx:
        if g and i-g[-1][1]<=gap: g[-1][1]=i
        else: g.append([int(i),int(i)])
    return g
def digitize(b, ytop, ybot, xlo, xhi, ymax, er=11, debug=False):
    sub=b[ytop-20:ybot+20, xlo:xhi]
    # vertical frame lines: columns with ink over >80% of panel height
    hgt=ybot-ytop
    cs=b[ytop:ybot, xlo:xhi].sum(0)
    vcols=runs1d(np.where(cs>hgt*0.8)[0])
    xl=xlo+vcols[0][0]; xlr=xlo+vcols[0][1]; xr=xlo+vcols[-1][0]
    # ticks left of frame
    tk=[y for y in range(ytop-10,ybot+10) if b[y, xl-14:xl-2].sum()>=8]
    ticks=[ (a+c)/2 for a,c in runs1d(tk)]
    # interior
    inner=b[ytop+8:ybot-5, xlr+3:xr-3].copy()
    yy,xx=np.ogrid[-er:er+1,-er:er+1]; disk=(xx**2+yy**2)<=er**2
    e=ndi.binary_erosion(inner,structure=disk)
    lab,n=ndi.label(e)
    pts=[]
    for i in range(1,n+1):
        ys,xs=np.where(lab==i)
        if len(ys)<15: continue
        pts.append((xs.mean()+xlr+3, ys.mean()+ytop+8, len(ys)))
    pts.sort()
    return dict(xl=int(xl),xr=int(xr),ticks=ticks,pts=pts)
if __name__=='__main__':
    b=np.load(sys.argv[1])
    ytop,ybot,xlo,xhi,ymax=map(int,sys.argv[2:7])
    r=digitize(b,ytop,ybot,xlo,xhi,ymax)
    print('frame x',r['xl'],r['xr'],'ticks',r['ticks'])
    t=r['ticks']; y0=t[-1]; yT=t[0]
    for x,y,s in r['pts']:
        print(round(x),round(y),s, round((y0-y)/(y0-yT)*ymax,2))
