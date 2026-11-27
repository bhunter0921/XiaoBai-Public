#!/usr/bin/env python3
"""Offline integrity check; no third-party Python packages required."""
import argparse, hashlib, json, struct, zlib
from pathlib import Path

def require(condition, message):
    if not condition: raise ValueError(message)
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def apng_info(p):
    b=p.read_bytes(); require(b[:8]==b'\x89PNG\r\n\x1a\n', f'{p}: signature'); pos=8; dims=None; count=0; frames=None; loop=None; total=0; end=False
    while pos+12<=len(b):
        n=struct.unpack_from('>I',b,pos)[0]; k=b[pos+4:pos+8]; v=b[pos+8:pos+8+n]; require(pos+12+n<=len(b),f'{p}: truncated chunk'); require(zlib.crc32(k+v)&0xffffffff==struct.unpack_from('>I',b,pos+8+n)[0],f'{p}: CRC')
        if k==b'IHDR': dims=struct.unpack_from('>II',v)
        elif k==b'acTL': frames,loop=struct.unpack('>II',v)
        elif k==b'fcTL':
            count+=1; num,den=struct.unpack_from('>HH',v,20); total+=1000*num/(den or 100)
        pos+=12+n
        if k==b'IEND': end=True; break
    require(end and pos==len(b) and dims==(384,384) and count==frames and frames>1,f'{p}: invalid APNG structure')
    return frames,loop,total

def refs(o):
    if isinstance(o,dict):
        for k,v in o.items():
            if k.endswith('.apng'): yield k
            yield from refs(v)
    elif isinstance(o,list):
        for v in o: yield from refs(v)
    elif isinstance(o,str) and o.endswith('.apng'): yield o

def main():
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('theme',nargs='?',type=Path,default=Path(__file__).resolve().parent/'xiaobai-bichon'); a=p.parse_args(); root=a.theme
    manifest=json.loads((root/'asset-manifest.json').read_text()); cfg=json.loads((root/'theme.json').read_text()); require(sha(root/'theme.json')==manifest['theme_sha256'],'theme.json checksum mismatch')
    expected={x['file'] for x in manifest['assets']}; actual={x.name for x in (root/'assets').iterdir() if x.is_file()}; require(len(expected)==43 and expected==actual==set(refs(cfg)),'asset set / references mismatch')
    for x in manifest['assets']:
        file=root/'assets'/x['file']; require(sha(file)==x['sha256'],f'{file}: SHA256 mismatch'); frames,loop,total=apng_info(file); require(frames==x['frames'] and loop==x['loop'] and abs(total-x['duration_ms'])<0.1,f'{file}: animation metadata mismatch')
    print('PASS: 43 APNG files, SHA256, CRC, animation metadata, theme references. This is not the official Clawd CLI validation.')
if __name__=='__main__': main()
