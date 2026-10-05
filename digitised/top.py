import sys,json
from PIL import Image
import numpy as np
fn=sys.argv[1]; bars=json.loads(sys.argv[2]); ystart=int(sys.argv[3]); yend=int(sys.argv[4])
im=np.array(Image.open(fn).convert('L')).astype(int)
for (a,b) in bars:
    w=b-a
    for y in range(ystart,yend):
        seg=im[y,a+2:b-1]<150
        if seg.mean()>0.8:
            print((a,b),'top',y); break
