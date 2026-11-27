#!/usr/bin/env python3
"""Deterministic XiaoBai APNG -> Codex 8x9 atlas; requires Pillow."""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageOps, ImageFilter, ImageDraw

CELL = (192, 208)
COUNTS = (6, 8, 8, 4, 5, 8, 6, 6, 6)
ROWS = (
    ('idle', 'A01', (0, 1, 3, 5, 6, 8)),
    ('running-right', 'E07', tuple(range(0, 32, 4))),
    ('running-left', 'E07', tuple(range(0, 32, 4))),
    ('waving', 'D05', (0, 3, 9, 13)),
    ('jumping', 'D06', (0, 2, 9, 17, 20)),
    ('failed', 'A10', (0, 2, 3, 4, 5, 6, 8, 11)),
    ('waiting', 'A12', (0, 1, 5, 7, 8, 15)),
    ('running', 'A07', (0, 1, 2, 4, 6, 8)),
    ('review', 'F02', (0, 5, 12, 25, 40, 55)),
)

def require(ok, message):
    if not ok:
        raise ValueError(message)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def clean_alpha(im):
    # Normalize RGB under fully transparent pixels, including after resampling.
    out = im.copy()
    out.paste((0, 0, 0, 0), mask=im.getchannel('A').point(lambda a: 255 if a == 0 else 0))
    return out

def strip_detached(im):
    # Remove isolated marks in the three rows containing notification/error effects.
    # Retain the largest connected silhouette and its antialiased edge.
    a = im.getchannel('A')
    binary = a.point(lambda p: 255 if p >= 16 else 0)
    raw = bytearray(binary.tobytes()); w, h = im.size; best = []
    for start in range(len(raw)):
        if not raw[start]:
            continue
        raw[start] = 0; component = [start]; k = 0
        while k < len(component):
            pos = component[k]; k += 1; x, y = pos % w, pos // w
            for yy in range(max(0, y-1), min(h, y+2)):
                for xx in range(max(0, x-1), min(w, x+2)):
                    q = yy*w+xx
                    if raw[q]:
                        raw[q] = 0; component.append(q)
        if len(component) > len(best):
            best = component
    require(best, 'empty silhouette')
    mask = bytearray(w*h)
    for i in best:
        mask[i] = 255
    keep = Image.frombytes('L', (w,h), bytes(mask)).filter(ImageFilter.MaxFilter(5))
    out = im.copy(); out.paste((0,0,0,0), mask=ImageOps.invert(keep)); return out

def verify(package):
    cfg = json.loads((package/'pet.json').read_text(encoding='utf-8'))
    require(cfg['id'] == package.name == 'xiaobai-bichon', 'pet id/folder mismatch')
    require(cfg['spritesheetPath'] == 'spritesheet.webp', 'unexpected atlas path')
    with Image.open(package/cfg['spritesheetPath']) as im:
        require(im.format == 'WEBP' and im.size == (1536,1872) and im.n_frames == 1, 'invalid atlas')
        atlas = im.convert('RGBA')
    require(atlas.tobytes() == clean_alpha(atlas).tobytes(), 'hidden RGB residue')
    for row,count in enumerate(COUNTS):
        for col in range(8):
            cell=atlas.crop((col*192,row*208,(col+1)*192,(row+1)*208)); box=cell.getchannel('A').getbbox()
            if col>=count:
                require(box is None, f'nonempty unused cell {row}:{col}')
            else:
                require(box and box[0]>0 and box[1]>0 and box[2]<192 and box[3]<208, f'empty/clipped cell {row}:{col}')
    for col in range(8):
        r=atlas.crop((col*192,208,(col+1)*192,416)); l=atlas.crop((col*192,416,(col+1)*192,624))
        require(ImageOps.mirror(r).tobytes()==l.tobytes(), 'walk mirror mismatch')
    print('PASS: 8x9, 57 populated cells, 15 empty cells, alpha and mirror')

def export(theme, package):
    manifest=json.loads((theme/'asset-manifest.json').read_text(encoding='utf-8'))
    assets={x['id']: x for x in manifest['assets']}
    require(not package.exists(), 'output already exists; choose a fresh directory')
    require(package.name=='xiaobai-bichon', 'output folder must be xiaobai-bichon')
    atlas=Image.new('RGBA',(1536,1872)); provenance=[]
    for row,(state,aid,indices) in enumerate(ROWS):
        entry=assets[aid]; path=theme/'assets'/entry['file']; require(sha(path)==entry['sha256'], f'source changed: {aid}')
        with Image.open(path) as im:
            require(im.size==(384,384) and max(indices)<im.n_frames, f'invalid source: {aid}')
            for col,i in enumerate(indices):
                im.seek(i); frame=im.convert('RGBA')
                if state in ('failed','waiting','running'):
                    frame=strip_detached(frame)
                # Common fixed scale, not bbox normalization. Same ground baseline.
                frame=frame.resize((184,184),Image.Resampling.LANCZOS)
                cell=Image.new('RGBA',CELL); cell.paste(frame,(4,20)); cell=clean_alpha(cell)
                if state=='running-left':
                    cell=ImageOps.mirror(cell)
                atlas.paste(cell,(col*192,row*208))
        provenance.append({'state':state,'asset':aid,'file':entry['file'],'sha256':entry['sha256'],'frames':indices})
    package.mkdir(parents=True); atlas.save(package/'spritesheet.webp',lossless=True,quality=100,method=6,exact=True)
    cfg={'id':'xiaobai-bichon','displayName':'小白 · 比熊','description':'一只认真陪伴开发工作的比熊。','spritesheetPath':'spritesheet.webp'}
    (package/'pet.json').write_text(json.dumps(cfg,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    verify(package)
    (package.parent/'export-manifest.json').write_text(json.dumps({'format':'Codex 8x9','rows':provenance,'atlas_sha256':sha(package/'spritesheet.webp')},indent=2)+'\n',encoding='utf-8')
    for label,color in [('light','white'),('dark','#252525')]:
        bg=Image.new('RGBA',atlas.size,color); bg.alpha_composite(atlas); bg.convert('RGB').save(package.parent/f'preview-{label}.png')

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__); p.add_argument('--theme',type=Path,default=Path('themes/xiaobai-bichon')); p.add_argument('--output',type=Path,default=Path('pets/xiaobai-bichon')); p.add_argument('--verify-only',action='store_true'); a=p.parse_args()
    if a.verify_only: verify(a.output)
    else: export(a.theme,a.output)
