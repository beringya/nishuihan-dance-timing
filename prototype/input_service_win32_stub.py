"""
Win32 输入服务接口草稿。

默认不会发送真实按键；开发时应先在测试窗口中验证，再启用真实输入。
不要用于绕过平台规则、反作弊或任何未获授权的自动化场景。
"""
import os
from dataclasses import dataclass


@dataclass
class InputEvent:
    key: str
    action: str  # KeyDown / KeyUp / Tap


class InputService:
    def __init__(self) -> None:
        self.real_input_enabled = os.environ.get("ENABLE_REAL_INPUT") == "1"

    def key_down(self, key: str) -> None:
        if not self.real_input_enabled:
            print(f"[DRY-RUN] KeyDown {key}")
            return
        # TODO: 使用 Win32 SendInput 实现。注意权限完整性级别和前台窗口校验。
        raise NotImplementedError("SendInput implementation should be added in Windows build.")

    def key_up(self, key: str) -> None:
        if not self.real_input_enabled:
            print(f"[DRY-RUN] KeyUp {key}")
            return
        raise NotImplementedError("SendInput implementation should be added in Windows build.")

    def tap(self, key: str, down_ms: int = 35) -> None:
        if not self.real_input_enabled:
            print(f"[DRY-RUN] Tap {key} {down_ms}ms")
            return
        raise NotImplementedError("SendInput implementation should be added in Windows build.")
