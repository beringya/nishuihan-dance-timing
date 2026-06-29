# Prototype 说明

这里的 Python 原型只用于离线验证视觉阈值、候选框检测和状态机，不发送真实按键。

```bash
pip install -r ../requirements.txt
python vision_timing_prototype.py \
  --video /path/to/video_1782739957535_m_compressed.mp4 \
  --config ../config/default_profile.json \
  --out ../analysis/prototype_events.csv \
  --debug-dir ../analysis/debug_frames
```

正式 Windows 工具建议用 C# / C++ 实现采集与输入，视觉算法仍可复用 OpenCV 逻辑。
