# 按键时机识别工具交付包

本交付包基于用户提供的 `1280×694 / 30 FPS / 约107.7秒` 屏幕录制生成，目标是给开发团队提供一套可落地的本地 Windows 小工具设计资料：识别模板、技术方案、系统架构、UI 交互、开发计划和最小原型。

> 说明：录屏为 30 FPS，因此视频内样例的时机分析精度约为 ±33ms。正式工具建议使用 60/120 FPS 屏幕采集，并通过标定向导测量本机延迟。

## 目录结构

```text
key_timing_delivery/
├─ README.md
├─ docs/
│  ├─ 01_开发设计说明.md
│  ├─ 02_开发计划.md
│  ├─ 03_模板资产说明与标定指南.md
│  ├─ 04_算法伪代码与事件协议.md
│  └─ 05_UI与交互说明.md
├─ config/
│  ├─ default_profile.json
│  └─ calibration_profile.schema.json
├─ templates/
│  ├─ full_prompt/              # 长按整体提示模板
│  ├─ key_button_raw/           # 字母/图标按钮原始模板
│  ├─ letter_gray/              # 字母灰度模板，建议用于小范围匹配
│  ├─ letter_edge/              # 字母边缘模板
│  ├─ letter_binary/            # 二值字母模板，作为参考
│  ├─ masks/                    # 圆形/文字/长条ROI掩码
│  ├─ examples/                 # HSV分割示例
│  └─ templates_manifest.json
├─ prototype/
│  ├─ vision_timing_prototype.py
│  ├─ state_machine.py
│  ├─ input_service_win32_stub.py
│  └─ README.md
├─ scripts/
│  └─ extract_templates_from_video.py
├─ ui/wireframes/
│  ├─ main_dashboard_wireframe.png
│  ├─ calibration_wizard_wireframe.png
│  └─ debug_overlay_wireframe.png
├─ diagrams/
│  ├─ architecture.mmd
│  ├─ capture_pipeline.mmd
│  └─ state_machine.mmd
├─ assets/contact_sheets/
│  ├─ initial_prompt_sequence.jpg
│  ├─ multi_prompt_15_17.jpg
│  ├─ A_hold_first_metrics_plot.png
│  └─ candidate_sheet.jpg
└─ requirements.txt
```

## 推荐打开顺序

1. `docs/01_开发设计说明.md`：技术选型、架构、算法和性能目标。
2. `docs/05_UI与交互说明.md`：主界面、标定向导、调试浮层和交互状态。
3. `docs/03_模板资产说明与标定指南.md`：模板文件含义、如何复采集、如何调阈值。
4. `config/default_profile.json`：初始配置样例。
5. `prototype/README.md`：离线原型运行方法。

## 合规边界

本资料按“自有软件、训练工具、辅助功能、自动化测试”的合法授权场景设计，不包含绕过平台限制、反作弊、风控或权限隔离的方案。正式产品应提供明显的启停开关、目标窗口校验和操作日志。
