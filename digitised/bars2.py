import sys
from PIL import Image
import numpy as np
fn=sys.argv[1]; y0,y1=int(sys.argv[2]),int(sys.argv[3]); minrun=int(sys.argv[4]) if len(sys.argv)>4 else 25
im=np.array(Image.open(fn).convert('L')).astype(int)
H,W=im.shape
print(H,W)
# left axis: column with longest dark vertical run
best=max(range(W//4), key=lambda x:(im[y0:y1,x]<120).sum())
print('axis x',best)
# tick marks: short dark horizontal runs just left of axis
ticks=[y for y in range(y0,y1) if (im[y,best-8:best-1]<120).sum()>=5]
g=[]
for y in ticks:
    if g and y-g[-1][-1]<=2: g[-1].append(y)
    else: g.append([y])
print('ticks',[round((a[0]+a[-1])/2,1) for a in g])
prev=None
for y in range(y0,y1):
    row=im[y]<140
    runs=[];x=best+3
    while x<W:
        if row[x]:
            s=x
            while x<W and row[x]: x+=1
            if x-s>=minrun: runs.append((s,x))
        x+=1
    if runs and runs!=prev: print(y,runs)
    prev=runs
