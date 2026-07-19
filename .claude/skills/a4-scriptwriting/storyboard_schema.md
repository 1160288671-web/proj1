# A4 分镜 Schema 规范

## 必填字段

| 字段 | 类型 | 说明 | 约束 |
|------|------|------|------|
| `seq` | int | 分镜序号 | 从 1 开始递增 |
| `duration_sec` | float | 该分镜时长（秒） | > 0 |
| `voice_text` | str | 该镜头配音文本 | 与 TTS 合成一致 |
| `subtitle_text` | str | 字幕文本 | 可与配音略有出入（精简） |
| `visual_prompt` | str | 背景图提示词 | 系统统一追加风格后缀 |
| `emotion` | str | 情绪标签 | 必须来自受控词表 |
| `transition` | str | 转场类型 | `cut` / `fade` / `slide` |
| `bpm_hint` | str | BPM 节奏提示 | `low` / `mid` / `high` |

## 硬性约束

- Σ `duration_sec` ≈ `duration_target_sec`（允许 ±5 秒误差）
- `emotion` 取值必须 ∈ `["悬疑","紧张","激昂","欢快","戏谑","温暖","治愈","严肃"]`
- 一条视频内 `emotion` 种类 ≤ 3

## 分镜数量建议

- 60 秒视频：6–8 个分镜
- 75 秒视频：7–10 个分镜
- 90 秒视频：9–12 个分镜
