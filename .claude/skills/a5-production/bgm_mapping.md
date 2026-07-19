# A5 BGM 曲库标签映射表

> 情绪标签 → 曲库检索标签（英文）→ BPM 参考

## 完整映射

| 情绪 | 曲库标签 1 | 曲库标签 2 | BPM 范围 | BPM 中位 |
|------|-----------|-----------|----------|----------|
| 悬疑 | suspense | mystery | 80–100 | 90 |
| 紧张 | tense | dramatic | 110–130 | 120 |
| 激昂 | epic | uplifting | 120–140 | 130 |
| 欢快 | upbeat | happy | 100–120 | 110 |
| 戏谑 | quirky | playful | 95–115 | 105 |
| 温暖 | warm | emotional | 70–90 | 80 |
| 治愈 | healing | gentle | 60–80 | 70 |
| 严肃 | serious | corporate | 90–105 | 97 |

## BPM 对齐规则

- `bpm_hint = "low"` → 取 BPM 范围下限
- `bpm_hint = "mid"` → 取 BPM 中位
- `bpm_hint = "high"` → 取 BPM 范围上限
- 实际选曲允许 ±10 BPM 偏差

## 闪避压缩

- 默认 ducking_db = -12 dB（有人声时 BGM 自动降低 12dB）
