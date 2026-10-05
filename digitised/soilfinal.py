import numpy as np, json
from PIL import Image
from panel import runs1d
cfg={
 8:dict(name='OC',starts=[396,1286,2196,3088,3983,4885,5794],sites=['Ludhiana','Pantnagar','Kanpur','Faizabad','Sabour','Kalyani','Jabalpur'],offs=[30,119,168,218,267,317,366],tick0=2079,tickTop=299,valTop=14),
 9:dict(name='N',starts=[457,1946,3426,4901],sites=['Ludhiana','Faizabad','Kalyani','Jabalpur'],offs=[45,195,274,353,432,511,590],tick0=3441,tickTop=54,valTop=300),
 10:dict(name='P',starts=[471,1345,2235,3121,4007,4890,5773],sites=['Ludhiana','Pantnagar','Kanpur','Faizabad','Sabour','Kalyani','Jabalpur'],offs=[30,119,168,218,267,317,366],tick0=2520,tickTop=52,valTop=14),
 11:dict(name='K',starts=[443,1330,2219,3126,4007,4898,5784],sites=['Ludhiana','Pantnagar','Kanpur','Faizabad','Sabour','Kalyani','Jabalpur'],offs=[30,119,168,218,267,317,366],tick0=1867,tickTop=67,valTop=450),
}
trt=['Initial','Control','50F','100F','50F+FYM','50F+CR','50F+GM']
out={}
for k,c in cfg.items():
    b=np.array(Image.open(f'p-{k:03d}.png')).astype(bool)
    H,W=b.shape
    rs=b.sum(1)
    def top(x):
        idx=np.where(b[0:c['tick0']-6,x])[0]
        return idx[0] if len(idx) else c['tick0']
    scale=c['valTop']/(c['tick0']-c['tickTop'])
    out[c['name']]={}
    print('==',c['name'])
    for g,site in zip(c['starts'],c['sites']):
        v=[]
        for o in c['offs']:
            ts=[top(x) for x in range(g+o-12,g+o+12)]
            v.append(round((c['tick0']-np.median(ts))*scale,2))
        out[c['name']][site]=dict(zip(trt,v))
        print(f'{site:10s}',v)
json.dump(out,open('yadav_soil.json','w'),indent=1)
