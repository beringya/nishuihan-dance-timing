"""
离线视觉原型：从录屏中检测金黄色提示，并输出候选事件日志。

用途：验证 HSV 分割、几何检测、状态机和阈值，不执行真实按键。
运行示例：
    python vision_timing_prototype.py --video ../../video_1782739957535_m_compressed.mp4 --config ../config/default_profile.json --out ../analysis/prototype_events.csv
"""
import argparse
import csv
import json
import math
from pathlib import Path
from typing import Dict, Iterable, List, Tuple

import cv2
import numpy as np

from state_machine import KeySignal, KeyTimingStateMachine, TimingConfig


def load_profile(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def gold_mask(frame: np.ndarray, lower: Iterable[int], upper: Iterable[int]) -> np.ndarray:
    hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
    mask = cv2.inRange(hsv, np.array(list(lower), dtype=np.uint8), np.array(list(upper), dtype=np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, np.ones((3, 3), np.uint8))
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, np.ones((5, 5), np.uint8))
    return mask


def find_gold_components(mask: np.ndarray, min_area: int) -> List[Tuple[int, int, int, int, float]]:
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < min_area:
            continue
        x, y, w, h = cv2.boundingRect(c)
        boxes.append((x, y, w, h, float(area)))
    return boxes


def component_score(mask: np.ndarray, x: int, y: int, w: int, h: int) -> float:
    roi = mask[max(y, 0):max(y + h, 0), max(x, 0):max(x + w, 0)]
    if roi.size == 0:
        return 0.0
    return float((roi > 0).mean())


def classify_candidates(frame: np.ndarray, mask: np.ndarray, profile: dict) -> List[KeySignal]:
    """最小原型：只输出几何候选，不做字母精确识别。
    正式版应在候选圆中心裁剪按钮，再用 letter_gray/edge 模板匹配得到 key。
    """
    v = profile["vision"]
    boxes = find_gold_components(mask, v["circle_min_area_px"])
    signals: List[KeySignal] = []
    for x, y, w, h, area in boxes:
        if w < 18 or h < 18:
            continue
        aspect = h / max(w, 1)
        is_hold_like = aspect >= v.get("hold_bar_aspect_ratio_min", 2.1) or h >= v.get("hold_bar_min_height_px", 45)
        score = component_score(mask, x, y, w, h)
        # 这里只用占位 key，正式版从模板匹配得出 A/S/W/D/Q/E/SPACE。
        key = "UNKNOWN"
        if is_hold_like:
            signals.append(KeySignal(key=key, is_present=True, is_hold=True, hold_start_score=min(1.0, score * 2.2)))
        else:
            # 对 tap，简单用面积/圆度近似重合分数；正式版还要比较外圈半径和圆心距离。
            circularity = min(w, h) / max(w, h)
            tap_score = max(0.0, min(1.0, circularity * score * 2.0))
            signals.append(KeySignal(key=key, is_present=True, is_hold=False, tap_alignment_score=tap_score))
    return signals


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--video", required=True, type=Path)
    parser.add_argument("--config", required=True, type=Path)
    parser.add_argument("--out", required=True, type=Path)
    parser.add_argument("--debug-dir", type=Path, default=None)
    args = parser.parse_args()

    profile = load_profile(args.config)
    cfg = TimingConfig(
        tap_down_duration_ms=profile["timing"]["tap_down_duration_ms"],
        input_advance_ms=profile["timing"]["input_advance_ms_default"],
        debounce_ms=profile["timing"]["debounce_ms"],
        hold_down_score_threshold=profile["timing"]["hold_down_score_threshold"],
        hold_up_tail_score_threshold=profile["timing"]["hold_up_tail_score_threshold"],
        reset_score_threshold=profile["timing"]["reset_score_threshold"],
        consecutive_frames_confirm=profile["vision"]["consecutive_frames_confirm"],
        max_missing_frames_while_holding=profile["timing"]["max_missing_frames_while_holding"],
    )
    machines: Dict[str, KeyTimingStateMachine] = {"UNKNOWN": KeyTimingStateMachine("UNKNOWN", cfg)}

    cap = cv2.VideoCapture(str(args.video))
    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    args.out.parent.mkdir(parents=True, exist_ok=True)
    if args.debug_dir:
        args.debug_dir.mkdir(parents=True, exist_ok=True)

    with args.out.open("w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["frame", "time_ms", "key", "action", "reason", "candidate_count"])
        frame_idx = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            if frame_idx % 2 != 0:  # 原型隔帧处理；正式版按采集帧率处理
                frame_idx += 1
                continue
            now_ms = frame_idx * 1000.0 / fps
            mask = gold_mask(frame, profile["vision"]["gold_hsv_lower"], profile["vision"]["gold_hsv_upper"])
            signals = classify_candidates(frame, mask, profile)
            for sig in signals:
                machine = machines.setdefault(sig.key, KeyTimingStateMachine(sig.key, cfg))
                actions = machine.update(now_ms, sig)
                for a in actions:
                    writer.writerow([frame_idx, f"{a.time_ms:.1f}", a.key, a.action, a.reason, len(signals)])
            if args.debug_dir and frame_idx % int(fps) == 0:
                overlay = frame.copy()
                for x, y, w, h, area in find_gold_components(mask, profile["vision"]["circle_min_area_px"]):
                    cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 255), 2)
                cv2.imwrite(str(args.debug_dir / f"frame_{frame_idx:05d}.jpg"), overlay)
            frame_idx += 1


if __name__ == "__main__":
    main()
