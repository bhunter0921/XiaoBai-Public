#!/usr/bin/env python3
"""Inspect animation geometry, alpha and timing; not a visual quality certification."""
import argparse
import json
from pathlib import Path
from PIL import Image, ImageSequence


def inspect(path, expected_size=None, expected_frames=None, expected_loop=None):
    errors = []
    frames = []
    with Image.open(path) as im:
        size, fmt = im.size, im.format
        loop = im.info.get('loop')
        for index, frame in enumerate(ImageSequence.Iterator(im)):
            alpha = frame.convert('RGBA').getchannel('A')
            hist = alpha.histogram()
            bbox = alpha.getbbox()
            duration = round(frame.info.get('duration', 0))
            if not bbox:
                errors.append(f'frame {index}: empty')
            if not hist[0]:
                errors.append(f'frame {index}: no transparent pixels')
            if duration <= 0:
                errors.append(f'frame {index}: nonpositive duration')
            if bbox and (bbox[0] == 0 or bbox[1] == 0 or bbox[2] == size[0] or bbox[3] == size[1]):
                errors.append(f'frame {index}: visible content touches canvas edge')
            frames.append({'index': index, 'duration_ms': duration, 'bbox': bbox,
                           'transparent_ratio': round(hist[0] / (size[0] * size[1]), 4),
                           'partial_alpha_ratio': round(sum(hist[1:255]) / (size[0] * size[1]), 4)})
    if len(frames) < 2:
        errors.append('not animated')
    if expected_size is not None and size != tuple(expected_size):
        errors.append('unexpected canvas size')
    if expected_frames is not None and len(frames) != expected_frames:
        errors.append('unexpected frame count')
    if expected_loop is not None and loop != expected_loop:
        errors.append('unexpected loop setting')
    boxes = [f['bbox'] for f in frames if f['bbox']]
    drift = {key: max(b[i] for b in boxes) - min(b[i] for b in boxes)
             for i, key in enumerate(('left', 'top', 'right', 'bottom'))} if boxes else {}
    return {'file': str(path), 'format': fmt, 'canvas': size, 'frames': len(frames),
            'loop': loop, 'duration_ms': sum(f['duration_ms'] for f in frames),
            'bbox_edge_range_px': drift, 'frame_details': frames, 'errors': errors,
            'visual_review_required': True, 'pass': not errors}


if __name__ == '__main__':
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('path', type=Path)
    p.add_argument('--size', type=int, nargs=2, metavar=('WIDTH', 'HEIGHT'))
    p.add_argument('--frames', type=int)
    p.add_argument('--loop', type=int)
    args = p.parse_args()
    report = inspect(args.path, args.size, args.frames, args.loop)
    print(json.dumps(report, indent=2))
    raise SystemExit(0 if report['pass'] else 1)
