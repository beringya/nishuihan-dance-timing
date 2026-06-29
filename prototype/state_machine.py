from dataclasses import dataclass
from enum import Enum
from typing import Optional, List


class KeyState(str, Enum):
    IDLE = "Idle"
    ARMED = "Armed"
    TAPPING = "Tapping"
    HOLDING = "Holding"
    COOLDOWN = "Cooldown"


@dataclass
class TimingConfig:
    tap_down_duration_ms: int = 35
    input_advance_ms: int = 22
    debounce_ms: int = 120
    hold_down_score_threshold: float = 0.80
    hold_up_tail_score_threshold: float = 0.74
    reset_score_threshold: float = 0.38
    consecutive_frames_confirm: int = 2
    max_missing_frames_while_holding: int = 3


@dataclass
class KeySignal:
    key: str
    is_present: bool
    is_hold: bool
    tap_alignment_score: float = 0.0      # 0..1，外圈/中心越贴合越高
    hold_start_score: float = 0.0         # 0..1，起点按钮高亮程度
    hold_tail_score: float = 0.0          # 0..1，尾端到达释放区域程度
    predicted_ms_to_hit: Optional[float] = None


@dataclass
class KeyAction:
    time_ms: float
    key: str
    action: str                           # "KeyDown", "KeyUp", "Tap"
    reason: str


class KeyTimingStateMachine:
    """单个按键通道的短按/长按状态机。视觉检测层只提供 KeySignal。"""

    def __init__(self, key: str, config: TimingConfig):
        self.key = key
        self.config = config
        self.state = KeyState.IDLE
        self.last_action_ms = -10_000.0
        self.hit_frames = 0
        self.reset_frames = 0
        self.missing_frames = 0
        self.down_at_ms: Optional[float] = None

    def update(self, now_ms: float, signal: KeySignal) -> List[KeyAction]:
        actions: List[KeyAction] = []
        cfg = self.config

        # 允许用预测时间提前触发，抵消采集/处理/输入延迟。
        predicted_ready = (
            signal.predicted_ms_to_hit is not None
            and signal.predicted_ms_to_hit <= cfg.input_advance_ms
        )
        tap_ready = signal.tap_alignment_score >= 0.86 or predicted_ready
        hold_down_ready = signal.hold_start_score >= cfg.hold_down_score_threshold or predicted_ready
        hold_up_ready = signal.hold_tail_score >= cfg.hold_up_tail_score_threshold
        reset_ready = (
            not signal.is_present
            or max(signal.tap_alignment_score, signal.hold_start_score, signal.hold_tail_score) <= cfg.reset_score_threshold
        )

        if signal.is_present:
            self.missing_frames = 0
        else:
            self.missing_frames += 1

        if self.state == KeyState.IDLE:
            if signal.is_hold and hold_down_ready:
                self.hit_frames += 1
                if self.hit_frames >= cfg.consecutive_frames_confirm:
                    actions.append(KeyAction(now_ms, self.key, "KeyDown", "hold_start"))
                    self.state = KeyState.HOLDING
                    self.down_at_ms = now_ms
                    self.last_action_ms = now_ms
                    self.hit_frames = 0
            elif (not signal.is_hold) and tap_ready:
                if now_ms - self.last_action_ms >= cfg.debounce_ms:
                    self.hit_frames += 1
                    if self.hit_frames >= cfg.consecutive_frames_confirm:
                        actions.append(KeyAction(now_ms, self.key, "Tap", "tap_alignment"))
                        self.state = KeyState.COOLDOWN
                        self.last_action_ms = now_ms
                        self.hit_frames = 0
            else:
                self.hit_frames = 0

        elif self.state == KeyState.HOLDING:
            if hold_up_ready or self.missing_frames > cfg.max_missing_frames_while_holding:
                actions.append(KeyAction(now_ms, self.key, "KeyUp", "hold_tail_or_missing"))
                self.state = KeyState.COOLDOWN
                self.down_at_ms = None
                self.last_action_ms = now_ms

        elif self.state == KeyState.COOLDOWN:
            if reset_ready:
                self.reset_frames += 1
                if self.reset_frames >= cfg.consecutive_frames_confirm:
                    self.state = KeyState.IDLE
                    self.reset_frames = 0
            else:
                self.reset_frames = 0

        return actions
