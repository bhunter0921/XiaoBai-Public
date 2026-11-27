#!/usr/bin/env python3
"""Convert an animated GIF/WebP/PNG to APNG without changing frame geometry."""
import argparse
from pathlib import Path
from PIL import Image, ImageSequence


def convert(source: Path, target: Path, *, loop: int = 0) -> dict:
    if source.resolve() == target.resolve():
        raise ValueError("source and target must differ")
    if target.suffix.lower() not in {".png", ".apng"}:
        raise ValueError("target must end in .png or .apng")
    with Image.open(source) as image:
        frames, durations = [], []
        for frame in ImageSequence.Iterator(image):
            rgba = frame.convert("RGBA")
            duration = round(frame.info.get("duration", 0))
            if duration <= 0:
                raise ValueError("every frame must have a positive duration")
            frames.append(rgba)
            durations.append(duration)
    if len(frames) < 2:
        raise ValueError("source must be animated")
    if any(frame.size != frames[0].size for frame in frames):
        raise ValueError("inconsistent canvas size")
    if not all(frame.getchannel("A").getextrema()[0] == 0 for frame in frames):
        raise ValueError("each frame must contain fully transparent pixels")
    target.parent.mkdir(parents=True, exist_ok=True)
    frames[0].save(target, format="PNG", save_all=True, append_images=frames[1:],
                   duration=durations, loop=loop, disposal=0, blend=0)
    with Image.open(target) as check:
        if check.n_frames != len(frames) or check.info.get("loop") != loop:
            raise RuntimeError("APNG frame count or loop changed")
        for index, frame in enumerate(ImageSequence.Iterator(check)):
            if frame.convert("RGBA").tobytes() != frames[index].tobytes():
                raise RuntimeError(f"APNG frame {index} differs from source")
            if round(frame.info.get("duration", 0)) != durations[index]:
                raise RuntimeError(f"APNG frame {index} timing changed")
    return {"frames": len(frames), "size": frames[0].size,
            "duration_ms": sum(durations), "loop": loop, "bytes": target.stat().st_size}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("target", type=Path)
    parser.add_argument("--loop", type=int, default=0, help="0=infinite, 1=play once")
    args = parser.parse_args()
    if args.loop < 0:
        parser.error("--loop must be nonnegative")
    print(convert(args.source, args.target, loop=args.loop))
