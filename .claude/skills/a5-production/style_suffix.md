# A5 画面风格后缀

> 所有背景图生图时，系统自动在用户 prompt 末尾追加风格后缀。
> 同一视频只选一种风格，保证画风一致。

## 可选风格后缀

| 风格名称 | 后缀文本 |
|----------|---------|
| 电影感写实 | cinematic lighting, photorealistic, 9:16 aspect ratio, high detail |
| 扁平插画 | flat vector illustration, clean lines, vibrant colors, 9:16 aspect ratio |
| 3D 渲染 | 3D render, octane render, soft lighting, 9:16 aspect ratio |
| 极简信息图 | minimalist infographic style, clean layout, bold typography, 9:16 |
| 暗调氛围 | moody atmosphere, dramatic shadows, cinematic, 9:16 aspect ratio |
| 明亮清新 | bright and airy, soft pastel colors, clean aesthetic, 9:16 aspect ratio |

## 默认风格

```
cinematic lighting, photorealistic, 9:16 aspect ratio, high detail
```

> 如分镜的 `visual_prompt` 已包含风格描述，系统不重复追加。
