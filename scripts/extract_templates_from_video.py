"""
从录屏中抽取金黄色候选模板，生成候选图和 contact sheet。

运行示例：
    python extract_templates_from_video.py --video input.mp4 --out ./template_candidates --step-frames 15

生成结果需要人工筛选：
- 圆形按钮模板：用于字母/图标匹配
- 纵向长按模板：用于长按起点/尾端识别
- 误检项：背景金色 UI、文字、道具，需要剔除
"""
import argparse
import math
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("--video", required=True, type=Path)
    p.add_argument("--out", required=True, type=Path)
    p.add_argument("--step-frames", type=int, default=15)
    p.add_argument("--max-candidates", type=int, default=220)
    p.add_argument("--hsv-lower", default="13,50,70")
    p.add_argument("--hsv-upper", default="45,255,255")
    return p.parse_args()


def parse_triplet(s: str):
    return np.array([int(v.strip()) for v in s.split(",")], dtype=np.uint8)


def main():
    args = parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    lower = parse_triplet(args.hsv_lower)
    upper = parse_triplet(args.hsv_upper)

    cap = cv2.VideoCapture(str(args.video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    selected = []
    crops = []
    seen = set()
    idx = 0

    while len(selected) < args.max_candidates:
        ok, frame = cap.read()
        if not ok:
            break
        if idx % args.step_frames != 0:
            idx += 1
            continue

        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, lower, upper)
        mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
        mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        candidates = []

        for c in contours:
            area = cv2.contourArea(c)
            if area < 250 or area > 6000:
                continue
            x, y, w, h = cv2.boundingRect(c)
            if not (18 <= w <= 120 and 18 <= h <= 130):
                continue
            ar = w / max(h, 1)
            if not (0.35 <= ar <= 2.5):
                continue
            cx, cy = x + w / 2, y + h / 2
            if y < 30 and x < 300:
                continue
            size = max(72, int(max(w, h) * 1.8))
            size = min(size, 140)
            x0 = int(max(0, cx - size / 2))
            y0 = int(max(0, cy - size / 2))
            x1 = int(min(frame.shape[1], cx + size / 2))
            y1 = int(min(frame.shape[0], cy + size / 2))
            crop = frame[y0:y1, x0:x1]
            if crop.size == 0:
                continue
            candidate_key = (idx // 30, int(cx) // 45, int(cy) // 45)
            if candidate_key in seen:
                continue
            candidate_hsv = cv2.cvtColor(crop, cv2.COLOR_BGR2HSV)
            candidate_mask = cv2.inRange(candidate_hsv, lower, upper)
            gold_ratio = float((candidate_mask > 0).mean())
            if gold_ratio < 0.08:
                continue
            candidates.append((gold_ratio, idx, idx / fps, x0, y0, x1, y1, crop.copy()))

        for item in sorted(candidates, reverse=True)[:5]:
            _, frame_idx, t, x0, y0, x1, y1, crop = item
            key = (frame_idx // 30, int((x0 + x1) / 2) // 45, int((y0 + y1) / 2) // 45)
            if key in seen:
                continue
            seen.add(key)
            selected.append((frame_idx, t, x0, y0, x1, y1))
            crops.append(crop)
        idx += 1

    thumbs = []
    for i, ((frame_idx, t, x0, y0, x1, y1), crop) in enumerate(zip(selected, crops)):
        name = f"cand_{i:03d}_f{frame_idx}_t{t:.2f}_x{x0}_y{y0}.png"
        cv2.imwrite(str(args.out / name), crop)
        im = Image.fromarray(cv2.cvtColor(crop, cv2.COLOR_BGR2RGB))
        im.thumbnail((96, 96))
        canvas = Image.new("RGB", (112, 126), "white")
        canvas.paste(im, ((112 - im.width) // 2, 0))
        d = ImageDraw.Draw(canvas)
        d.text((3, 99), f"{i:03d} t{t:.1f}", fill=(0, 0, 0))
        thumbs.append(canvas)

    cols = 10
    rows = max(1, math.ceil(len(thumbs) / cols))
    sheet = Image.new("RGB", (cols * 112, rows * 126), "white")
    for i, im in enumerate(thumbs):
        sheet.paste(im, ((i % cols) * 112, (i // cols) * 126))
    sheet.save(args.out / "candidate_sheet.jpg", quality=92)
    print(f"saved {len(thumbs)} candidates to {args.out}")


if __name__ == "__main__":
    main()
