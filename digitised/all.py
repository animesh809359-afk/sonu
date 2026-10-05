import numpy as np, json, sys
from PIL import Image
sys.path.insert(0,'.')
from panel import runs1d
from panel2 import digitize2 as digitize
from grid import gridfit
sites=['Ludhiana','Pantnagar','Kanpur','Faizabad','Sabour','Kalyani','Jabalpur']
T3={'Ludhiana':(6083,5059,4459,4400),'Pantnagar':(4564,3841,3753,3449),'Kanpur':(4470,3658,4532,4384),
'Faizabad':(4205,3780,3449,3310),'Sabour':(4111,3873,3128,3154),'Kalyani':(3328,3467,2671,3093),'Jabalpur':(5094,4371,2553,2483)}
res={}
for k,site in enumerate(sites):
    fn=f'p-{k:03d}.png'
    im=np.array(Image.open(fn)).astype(np.uint8)
    H,W=im.shape; im=im[:H//2*2,:W//2*2]
    b=im.reshape(H//2,2,W//2,2).max(axis=(1,3)).astype(bool)
    H,W=b.shape
    res[site]={}
    YM={'Ludhiana':(8,6),'Pantnagar':(6,6),'Kanpur':(6,6),'Faizabad':(6,5),'Sabour':(6,5),'Kalyani':(6,4),'Jabalpur':(10,4)}[site]
    for side,(x0,x1,ymax,crop) in {'L':(0,W//2,YM[0],'rice'),'R':(W//2,W,YM[1],'wheat')}.items():
        sub=b[:,x0:x1]
        hl=[]
        for y in range(H):
            r=sub[y]
            if r.sum()<(x1-x0)*0.5: continue
            d=np.diff(np.concatenate([[0],r.astype(int),[0]]))
            st=np.where(d==1)[0]; en=np.where(d==-1)[0]
            if (en-st).max()>(x1-x0)*0.6: hl.append(y)
        lines=[((a+c)/2,a,c) for a,c in runs1d(hl,3)]
        panels=[];i=0
        while i<len(lines)-1:
            j=i+1
            while j<len(lines) and lines[j][0]-lines[i][0]<400: j+=1
            if j<len(lines) and lines[j][0]-lines[i][0]<540:
                panels.append((lines[i],lines[j])); i=j+1
            else: i+=1
        if len(panels)!=6: print(site,side,'PANELS',len(panels),[ (round(p[0][0]),round(p[1][0])) for p in panels]); 
        out={}
        for pi,name in [(2,'100F'),(4,'CR')]:
            (tc,ta,tb),(bc,ba,bb)=panels[pi]
            r=digitize(b,int(tb),int(ba),x0,x1)
            g,miss,sp=gridfit(r['pts'])
            if miss: print('  MISSING slots',site,crop,name,miss)
            vals=[None if p is None else round((bc-p[1])/(bc-tc)*ymax,2) for p in g]
            r['pts']=[p for p in g if p is not None]
            out[name]=vals
            out[name+'_x']=[round(x) for x,y,s in r['pts']]
            out[name+'_sz']=[s for x,y,s in r['pts']]
        res[site][crop]=out
        m100=np.mean([v for v in out['100F'] if v is not None]); mcr=np.mean([v for v in out['CR'] if v is not None])
        t=T3[site]; i0=0 if crop=='rice' else 2
        print(f"{site:10s} {crop:5s} n={len(out['100F'])},{len(out['CR'])}  100F dig {m100:.3f} vs T3 {t[i0]/1000:.3f} | CR dig {mcr:.3f} vs T3 {t[i0+1]/1000:.3f}")
json.dump(res,open('yadav_yields.json','w'),indent=1)
