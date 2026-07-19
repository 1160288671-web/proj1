# A5 ffmpeg 渲染参数模板

## 默认参数

```json
{
  "resolution": "1080x1920",
  "fps": 30,
  "format": "mp4",
  "video_codec": "libx264",
  "pixel_format": "yuv420p",
  "crf": 23,
  "preset": "medium",
  "audio_codec": "aac",
  "audio_bitrate": "192k",
  "sample_rate": 44100
}
```

## 分辨率选项

| 平台 | 推荐分辨率 | 宽高比 |
|------|-----------|--------|
| 抖音 / 快手 | 1080x1920 | 9:16 |
| B 站横屏 | 1920x1080 | 16:9 |
| 通用竖屏 | 1080x1920 | 9:16 |

## 字幕参数

```
fontfile=/path/to/font.ttf
fontsize=48
fontcolor=white
outlinecolor=black
outline=2
shadow=1
marginv=80
alignment=2 (底部居中)
```

> TODO: 中文字体路径需按操作系统配置。
