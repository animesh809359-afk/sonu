import sys
from PIL import Image
import numpy as np
fn=sys.argv[1]
im=np.array(Image.open(fn).convert('L')).astype(int)
H,W=im.shape
print(fn,H,W)
ticks=[y for y in range(H) if (im[y,2:22]<100).sum()>=12]
g=[]
for y in ticks:
    if g and y-g[-1][-1]<=2: g[-1].append(y)
    else: g.append([y])
print('left tick rows',[ (gg[0]+gg[-1])/2 for gg in g])
for y in range(4,H-6):
    row=im[y]<90
    runs=[];x=25
    while x<W-25:
        if row[x]:
            s=x
            while x<W and row[x]: x+=1
            if x-s>50: runs.append((s,x))
        x+=1
    if runs: print(y,runs)
