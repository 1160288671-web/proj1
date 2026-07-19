"""A4 编剧（判断型）：读素材 → 定体验定位 → 写口播稿 → 拆分镜"""
import json

from src.agents.base import JudgementAgent
from src.utils.id_gen import generate_script_id


# 受控情绪词表
EMOTION_LABELS = ["悬疑", "紧张", "激昂", "欢快", "戏谑", "温暖", "治愈", "严肃"]
# 六体验
EXPERIENCES = ["掌控感", "爽感", "共鸣感", "优越感", "成长感", "参与感"]
# 转场类型
TRANSITIONS = ["cut", "fade", "slide"]
# BPM 提示
BPM_HINTS = ["low", "mid", "high"]


class A4ScriptWriter(JudgementAgent):
    """A4：编剧"""

    DEFAULT_DURATION = 75  # 秒
    WORDS_PER_SEC = 4.5    # 中文 TTS 约 4-5 字/秒

    def __init__(self, llm):
        super().__init__(name="A4_ScriptWriter", llm=llm)

    async def run(self, state: dict) -> dict:
        self.log("开始编剧...")

        topics = state.get("topics", [])
        materials = state.get("materials", {})
        scripts = []

        for topic in topics:
            topic_id = topic.get("topic_id", "")
            topic_materials = materials.get(topic_id, [])

            if len(topic_materials) < 3:
                self.log(f"  选题 {topic_id} 素材不足（{len(topic_materials)} 条），跳过")
                state.setdefault("errors", []).append(
                    f"A4: 选题 {topic_id} 素材不足，已跳过"
                )
                continue

            self.log(f"  创作选题 {topic_id}: {topic.get('title_candidate', '')[:40]}...")
            try:
                script = await self._write_script(topic, topic_materials)
                if script:
                    scripts.append(script)
                    # 生成人读报告
                    self._generate_report(script, topic)
            except Exception as e:
                self.log(f"  ERROR 选题 {topic_id}: {e}")
                state.setdefault("errors", []).append(
                    f"A4: 选题 {topic_id} 编剧失败: {e}"
                )

        state["scripts"] = scripts
        state["stage"] = "A4_script"
        self.log(f"编剧完成，生成了 {len(scripts)} 个脚本")
        return state

    async def _write_script(self, topic: dict, materials: list[dict]) -> dict | None:
        """调用 LLM 生成完整脚本"""
        # 加载所有 skill
        emotion_table = self._load_skill("a4-scriptwriting/emotion_table.md")
        experience_map = self._load_skill("a4-scriptwriting/experience_map.md")
        storyboard_schema = self._load_skill("a4-scriptwriting/storyboard_schema.md")
        hook_guide = self._load_skill("a4-scriptwriting/hook_guide.md")

        # 计算字数预算
        target_sec = self.DEFAULT_DURATION
        target_chars = int(target_sec * self.WORDS_PER_SEC)

        # 准备素材摘要（限制长度）
        materials_summary = self._summarize_materials(materials)

        # 构建 prompt
        system_prompt = f"""你是短视频编剧专家，为「棒读」风格的口播视频撰写脚本。

## 核心理念：棒读风格
- 语言口语化、短句、不用复杂从句
- 像朋友聊天一样自然，不要播音腔
- 每句话不超过 20 个字

## 情绪词表
{emotion_table}

## 六体验映射表
{experience_map}

## 分镜 Schema
{storyboard_schema}

## 钩子写法
{hook_guide}

## 关键约束
1. 口播稿总字数控制在 {target_chars} 字左右（目标时长 {target_sec} 秒，按 {self.WORDS_PER_SEC} 字/秒换算）
2. 情绪标签只能从 {json.dumps(EMOTION_LABELS, ensure_ascii=False)} 中选择
3. 一条视频的情绪标签不超过 3 种
4. 分镜数量：{target_sec} 秒视频建议 7-10 个分镜
5. 每个分镜的 duration_sec 总和 ≈ {target_sec} 秒

## 输出格式（纯 JSON）
{{
  "experience": {{ "primary": "主攻体验", "secondary": "辅攻体验", "reason": "选择理由" }},
  "duration_target_sec": {target_sec},
  "title_options": ["候选标题1", "候选标题2", "候选标题3"],
  "hook": "前3秒钩子（≤15字）",
  "full_text": "完整口播稿（约{target_chars}字）",
  "storyboard": [
    {{
      "seq": 1,
      "duration_sec": 5.0,
      "voice_text": "配音文本",
      "subtitle_text": "字幕文本",
      "visual_prompt": "English visual prompt for AI image generation",
      "emotion": "悬疑",
      "transition": "cut",
      "bpm_hint": "mid"
    }}
  ]
}}

注意：visual_prompt 用英文写，描述画面内容，系统会自动追加风格后缀。"""

        user_prompt = f"""选题信息：
- 候选标题：{topic.get('title_candidate', '')}
- 领域：{topic.get('domains', [])}
- 关键词：{topic.get('keywords', [])}
- A2 建议体验：{topic.get('experience_hint', '未指定')}
- 关联假设：{topic.get('combo_hypotheses', [])}

素材内容（共 {len(materials)} 条）：
{materials_summary}

请根据以上素材创作脚本。A2 建议的体验定位是「{topic.get('experience_hint', '未指定')}」，你可以改变，但必须在 reason 中说明。"""

        raw = await self.llm.chat_with_json(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.5,
        )

        # 校验与补全
        script = self._validate_and_fix(raw, topic)

        return script

    def _summarize_materials(self, materials: list[dict], max_chars: int = 3000) -> str:
        """将素材列表压缩为 LLM 可读的摘要"""
        lines = []
        total = 0
        for i, m in enumerate(materials[:8]):
            title = m.get("title", "")[:80]
            text = m.get("text", "")[:400]
            density = m.get("info_density", {}).get("score", 0)
            entry = f"[素材{i+1}] (密度{density}分) {title}\n{text}"
            if total + len(entry) > max_chars:
                lines.append(f"[素材{i+1}] (省略，已达长度限制)...")
                break
            lines.append(entry)
            total += len(entry)
        return "\n\n".join(lines)

    def _validate_and_fix(self, raw: dict, topic: dict) -> dict:
        """校验 LLM 输出并修复常见问题"""
        topic_id = topic.get("topic_id", "")

        script = {
            "script_id": generate_script_id(),
            "topic_id": topic_id,
        }

        # experience
        exp = raw.get("experience", {})
        primary = exp.get("primary", topic.get("experience_hint", "共鸣感"))
        secondary = exp.get("secondary", "爽感")
        reason = exp.get("reason", "")
        # 如果推翻了 A2 hint，确保 reason 不为空
        if primary != topic.get("experience_hint", "") and not reason:
            reason = f"A4 将体验从「{topic.get('experience_hint', '')}」调整为「{primary}」，基于素材特征判断"

        script["experience"] = {
            "primary": primary if primary in EXPERIENCES else "共鸣感",
            "secondary": secondary if secondary in EXPERIENCES else "爽感",
            "reason": reason,
        }

        # 时长
        script["duration_target_sec"] = raw.get("duration_target_sec", self.DEFAULT_DURATION)
        if not (60 <= script["duration_target_sec"] <= 90):
            script["duration_target_sec"] = self.DEFAULT_DURATION

        # 标题
        titles = raw.get("title_options", [])
        if not titles:
            titles = [topic.get("title_candidate", "无标题")]
        script["title_options"] = titles[:5]

        # 钩子
        script["hook"] = raw.get("hook", topic.get("title_candidate", ""))[:20]

        # 口播稿
        script["full_text"] = raw.get("full_text", "")

        # 分镜
        storyboard = raw.get("storyboard", [])
        if not storyboard:
            storyboard = self._fallback_storyboard(raw.get("full_text", ""), script["duration_target_sec"])

        fixed_storyboard = []
        for sb in storyboard:
            if not isinstance(sb, dict):
                continue
            emotion = sb.get("emotion", "严肃")
            fixed_storyboard.append({
                "seq": sb.get("seq", len(fixed_storyboard) + 1),
                "duration_sec": max(2.0, min(float(sb.get("duration_sec", 5)), 30.0)),
                "voice_text": sb.get("voice_text", ""),
                "subtitle_text": sb.get("subtitle_text", sb.get("voice_text", "")),
                "visual_prompt": sb.get("visual_prompt", "abstract background"),
                "emotion": emotion if emotion in EMOTION_LABELS else "严肃",
                "transition": sb.get("transition", "cut") if sb.get("transition") in TRANSITIONS else "cut",
                "bpm_hint": sb.get("bpm_hint", "mid") if sb.get("bpm_hint") in BPM_HINTS else "mid",
            })

        # 情绪标签种类检查
        used_emotions = set(s["emotion"] for s in fixed_storyboard)
        if len(used_emotions) > 3:
            # 合并为最接近的 3 种
            dominant = list(used_emotions)[:3]
            for s in fixed_storyboard:
                if s["emotion"] not in dominant:
                    s["emotion"] = dominant[0]

        script["storyboard"] = fixed_storyboard

        return script

    def _fallback_storyboard(self, full_text: str, total_duration: float) -> list[dict]:
        """LLM 未返回分镜时的降级拆分"""
        if not full_text:
            return []
        segments = full_text.split("。")
        segments = [s.strip() + "。" for s in segments if s.strip()]
        if not segments:
            return []

        n = len(segments)
        per_dur = total_duration / n
        return [
            {
                "seq": i + 1,
                "duration_sec": round(per_dur, 1),
                "voice_text": segments[i],
                "subtitle_text": segments[i],
                "visual_prompt": "abstract background",
                "emotion": "严肃",
                "transition": "cut",
                "bpm_hint": "mid",
            }
            for i in range(min(n, 12))
        ]

    def _generate_report(self, script: dict, topic: dict):
        """生成人读报告（脚本报告.md）"""
        exp = script.get("experience", {})
        scenes = script.get("storyboard", [])

        report = f"""# 脚本报告

## 基本信息
- **脚本 ID**：{script['script_id']}
- **选题 ID**：{script['topic_id']}
- **候选标题**：{', '.join(script.get('title_options', []))}
- **目标时长**：{script['duration_target_sec']} 秒

## 体验定位
- **主攻**：{exp.get('primary', '')}
- **辅攻**：{exp.get('secondary', '')}
- **理由**：{exp.get('reason', '')}

## 前 3 秒钩子
> {script.get('hook', '')}

## 完整口播稿
{script.get('full_text', '')}

## 分镜概览
| # | 时长 | 情绪 | 转场 | BPM |
|---|------|------|------|-----|
"""
        for s in scenes:
            report += f"| {s['seq']} | {s['duration_sec']}s | {s['emotion']} | {s['transition']} | {s['bpm_hint']} |\n"

        import os
        report_dir = "data/reports"
        os.makedirs(report_dir, exist_ok=True)
        path = os.path.join(report_dir, f"{script['script_id']}_report.md")
        with open(path, "w", encoding="utf-8") as f:
            f.write(report)
        self.log(f"  报告已保存: {path}")
