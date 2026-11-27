#!/usr/bin/env python3
"""Repair the frozen A09 v0.1 alpha holes, not arbitrary images."""
import argparse, hashlib
from pathlib import Path
import cv2
import numpy as np
from PIL import Image, ImageDraw

SOURCE_SHA = '068386df279008a7a115a25a15b30223b59a3d57d2bdc94bc72046a193e9e1b8'

def repair(src, dst):
    if hashlib.sha256(src.read_bytes()).hexdigest() != SOURCE_SHA:
        raise ValueError('Expected frozen sweeping-v0.1.apng')
    im=Image.open(src); frames=[]; times=[]; masks=[]
    for i in range(im.n_frames):
        im.seek(i); original=np.array(im.convert('RGBA')); a=original[:,:,3]; times.append(im.info['duration'])
        n, labels, stats, _=cv2.connectedComponentsWithStats((a<128).astype('uint8'))
        mask=np.zeros(a.shape,np.uint8)
        for j,(x,y,w,h,area) in enumerate(stats[1:],1):
            if 150<=x<=255 and 90<=y<=215 and w<=30 and h<=30 and area>=7:
                mask[labels==j]=255
        mask=cv2.dilate(mask,np.ones((3,3),np.uint8))
        # Two noses touch the outer silhouette; only restore their traced interior.
        if i in (3,10):
            m=Image.fromarray(mask); d=ImageDraw.Draw(m)
            pts={3:[(220,169),(228,167),(237,169),(241,174),(239,180),(232,186),(226,183),(220,178)],10:[(225,195),(233,193),(241,195),(244,200),(241,206),(235,211),(230,208),(225,203)]}[i]
            d.polygon(pts,fill=255); mask=np.array(m)
        # Composite onto dark brown only within the missing facial regions.
        # Leave the rest of the image and all motion exactly unchanged.
        weight=(mask.astype(np.float32)/255)*(1-a.astype(np.float32)/255)
        rgb=original[:,:,:3].astype(np.float32); alpha=a.astype(np.float32)/255
        newalpha=alpha+weight; numerator=rgb*alpha[:,:,None]+np.array([31,23,22],np.float32)*weight[:,:,None]
        changed=mask>0; out=original.copy(); out[changed,:3]=np.round(numerator[changed]/np.maximum(newalpha[changed,None],1e-8)).astype(np.uint8); out[changed,3]=np.round(newalpha[changed]*255).astype(np.uint8)
        assert np.array_equal(out[~changed],original[~changed]); frames.append(Image.fromarray(out)); masks.append(changed)
    dst.parent.mkdir(parents=True,exist_ok=True)
    frames[0].save(dst,save_all=True,append_images=frames[1:],duration=times,loop=0,disposal=0,blend=0)
    check=Image.open(dst); assert check.n_frames==16 and check.info['loop']==0
    for i,f in enumerate(frames):
        check.seek(i); assert check.info['duration']==times[i] and np.array_equal(np.array(check.convert('RGBA')),np.array(f))
    print('PASS: 16 frames; local alpha repair; original timing preserved; pixels outside mask unchanged')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('source',type=Path);p.add_argument('output',type=Path);args=p.parse_args();repair(args.source,args.output)
