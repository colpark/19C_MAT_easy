import sys, os, io, base64, warnings; warnings.filterwarnings("ignore")
sys.path.insert(0, os.path.expanduser("~/mcp/vision"))
import numpy as np
from PIL import Image
from worker import Req, run_tool
A=384; yy,xx=np.mgrid[0:A,0:A]; rng=np.random.default_rng(0)
for a in [6,9,12,20,30]:
    sig=a*0.15; img=np.zeros((A,A),np.float32); n=0
    for i in range(-2,90):
        for j in range(-2,90):
            x=i*a+(j%2)*a/2; y=j*a*np.sqrt(3)/2
            if 0<=x<A and 0<=y<A: img+=np.exp(-((xx-x)**2+(yy-y)**2)/(2*sig**2)); n+=1
    img=np.clip(img/img.max()+rng.normal(0,0.05,img.shape),0,1)
    buf=io.BytesIO(); Image.fromarray(np.uint8(img*255)).save(buf,format="PNG")
    for m in ["G_MD","BFO"]:
        o=run_tool("find_atoms",Req(image_b64=base64.b64encode(buf.getvalue()).decode(),args={"model":m},seed=0))
        v=o["values"]; nn=v["nn_distance_px"]
        print(f"a={a} true_n={n} {m}: count={v['atom_count']} est_spacing={v['estimated_spacing_px']} scale={v['rescale_factor']:.2f} nn_median={nn and round(nn['median'],2)} t={o['provenance']['duration_s']}")
