# render sequentially through chip-heavy moments so chip placement matches the real render order
import sys, os
sys.argv=["x"]
import render4 as V, subprocess
from PIL import Image
ts=[float(a) for a in os.environ["TS"].split()]
outs=[]
for t in ts:
    raw=subprocess.run(["ffmpeg","-v","error","-ss",f"{t:.3f}","-i",V.SRC,"-frames:v","1","-f","rawvideo","-pix_fmt","rgb24","-"],capture_output=True).stdout
    img=Image.frombytes("RGB",(V.W,V.H),raw)
    # touch every earlier chip moment in order
    for tt in [x/10 for x in range(0,int(t*10)+1,3)]:
        i=V.seg_at(tt)
        if V.TL[i][2]=="sp":
            V.render_seg(i,tt,int(tt*12),img)
    V._cache.clear()
    for cl in V.CLIPS.values(): cl.p=None; cl.idx=-1; cl.img=None
    outs.append(V.render_seg(V.seg_at(t),t,int(t*12),img).resize((640,360)))
sh=Image.new("RGB",(1920,360*((len(outs)+2)//3)))
for i,im in enumerate(outs): sh.paste(im,((i%3)*640,(i//3)*360))
sh.save("v4/snap.jpg",quality=85)
