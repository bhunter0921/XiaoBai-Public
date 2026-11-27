#!/usr/bin/env python3
"""Offline body/tail compositor: independent rotation about a moving anchor."""
import argparse
import json
import math
from pathlib import Path
from PIL import Image


def compose(timeline: Path, output: Path):
    cfg = json.loads(timeline.read_text())
    root = timeline.parent
    canvas = tuple(cfg['canvas'])
    fps = cfg['fps']
    hold = cfg['poseFrames']
    tail = cfg['tail']
    if fps <= 0 or hold < 1 or not cfg['poses']:
        raise ValueError('invalid timeline')
    if tail['frequencyHz'] <= 0 or fps < 8 * tail['frequencyHz']:
        raise ValueError('insufficient temporal sampling')
    source = Image.open(root / tail['file']).convert('RGBA')
    px, py = tail['pivot']
    frames = []
    for pose in cfg['poses']:
        body = Image.open(root / pose['file']).convert('RGBA')
        if body.size != canvas:
            raise ValueError('body canvas mismatch')
        ax, ay = pose['anchor']
        for _ in range(hold):
            t = len(frames) / fps
            angle = tail['amplitudeDegrees'] * math.sin(2 * math.pi * tail['frequencyHz'] * t)
            # Inverse affine: output anchor maps to original tail pivot. No scale.
            c, s = math.cos(math.radians(angle)), math.sin(math.radians(angle))
            transform = (c, -s, px - c*ax + s*ay, s, c, py - s*ax - c*ay)
            layer = source.transform(canvas, Image.Transform.AFFINE, transform,
                                     resample=Image.Resampling.BICUBIC)
            layer.alpha_composite(body)
            frames.append(layer)
    durations = [round((i+1)*1000/fps)-round(i*1000/fps) for i in range(len(frames))]
    output.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(output, format='PNG', save_all=True, append_images=frames[1:],
                   duration=durations, loop=1, disposal=0, blend=0)
    return frames, durations


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('timeline', type=Path)
    p.add_argument('output', type=Path)
    a = p.parse_args()
    frames, durations = compose(a.timeline, a.output)
    print(f'{len(frames)} frames, {sum(durations)} ms')
