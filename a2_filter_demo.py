# -*- coding: utf-8 -*-
"""
A2 领域过滤 + 敏感词过滤 · 冷启动演示
直接解析 skill 目录下的 whitelist.md / sensitive_words.md，
用 12 条模拟热榜条目跑一遍过滤，打印每条处置结果。
"""
import re
from pathlib import Path

SKILL_DIR = Path(__file__).parent / ".claude" / "skills" / "a2-topic-select"


def parse_whitelist(md_path):
    """解析白名单表格：返回 {领域: [关键词...]} 与排除领域表。"""
    text = md_path.read_text(encoding="utf-8")
    whitelist, exclude = {}, {}
    # 按表格分段：白名单表、排除领域表
    sections = re.split(r"^## ", text, flags=re.M)
    for sec in sections:
        target = None
        if sec.startswith("泛娱乐领域白名单"):
            target = whitelist
        elif sec.startswith("排除领域参考"):
            target = exclude
        if target is None:
            continue
        for line in sec.splitlines():
            cells = [c.strip() for c in line.split("|")[1:-1]]
            # 白名单表为 3 列（关键词在第 3 列），排除领域表为 2 列（关键词在最后一列）
            if len(cells) < 2 or "领域" in cells[0] or cells[0].startswith("---"):
                continue
            domain = cells[0]
            kws = [k.strip() for k in re.split(r"[、,，]", cells[-1]) if k.strip()]
            target[domain] = kws
    return whitelist, exclude


def parse_sensitive(md_path):
    """解析敏感词代码块：一级词（淘汰）、二级词（降分）。"""
    text = md_path.read_text(encoding="utf-8")
    level1, level2 = [], []
    # 一级词库与二级词库之间的内容为一级
    parts = re.split(r"^## ", text, flags=re.M)
    for sec in parts:
        if sec.startswith("一级词库"):
            bucket = level1
        elif sec.startswith("二级词库"):
            bucket = level2
        else:
            continue
        for block in re.findall(r"```\n(.*?)```", sec, flags=re.S):
            for w in block.splitlines():
                w = w.strip()
                if w and not w.startswith("#"):
                    bucket.append(w)
    return level1, level2


def match_domains(title, table):
    return [d for d, kws in table.items() if any(k.lower() in title.lower() for k in kws)]


def hit_word(title, words):
    for w in words:
        if w.lower() in title.lower():
            return w
    return None


def filter_entry(title, whitelist, exclude, level1, level2):
    """返回 (处置, 原因)"""
    w = hit_word(title, level1)
    if w:
        return "淘汰", f"命中一级敏感词「{w}」"
    domains = match_domains(title, whitelist)
    excluded = match_domains(title, exclude)
    flag = hit_word(title, level2)
    if not domains:
        reason = f"未命中白名单（命中排除领域：{'、'.join(excluded)}）" if excluded else "未命中白名单"
        return "丢弃", reason
    notes = []
    if flag:
        notes.append(f"命中二级词「{flag}」→ 安全性上限2分")
    if excluded:
        notes.append(f"同时命中排除领域「{'、'.join(excluded)}」→ 安全性-1分")
    suffix = "；" + "；".join(notes) if notes else ""
    return "保留", f"领域：{'、'.join(domains)}{suffix}"


SAMPLES = [
    "某顶流明星演唱会门票秒罄，黄牛溢价三倍",
    "央行宣布降准0.5个百分点，释放长期资金约1万亿",
    "新片《星河入梦》首映口碑爆棚，票房破10亿",
    "某网红裸聊视频泄露，平台紧急下架",
    "LOL全球总决赛中国战队夺冠，选手爆头操作封神",
    "某地发生分尸案，警方深夜通报",
    "盲盒隐藏款被炒到上千元，年轻人排队抢购",
    "AI芯片发布会召开，大模型参数再升级",
    "美食博主探店排队3小时，网红店打卡攻略走红",
    "某平台赌球直播间被查封，主播被警方带走",
    "高考分数线公布，各地招生政策解读",
    "某偶像官宣恋情，粉丝破防热搜刷屏",
]

def main():
    whitelist, exclude = parse_whitelist(SKILL_DIR / "whitelist.md")
    level1, level2 = parse_sensitive(SKILL_DIR / "sensitive_words.md")
    print(f"词表加载：白名单 {sum(len(v) for v in whitelist.values())} 词 / "
          f"排除领域 {sum(len(v) for v in exclude.values())} 词 / "
          f"一级敏感词 {len(level1)} / 二级敏感词 {len(level2)}\n")
    kept = 0
    for i, title in enumerate(SAMPLES, 1):
        action, reason = filter_entry(title, whitelist, exclude, level1, level2)
        mark = {"保留": "✅", "淘汰": "🚫", "丢弃": "⛔"}[action]
        if action == "保留":
            kept += 1
        print(f"{mark} [{i:02d}] {title}\n      → {action}｜{reason}\n")
    print(f"结果：12 条进 → {kept} 条保留进入打分阶段")


if __name__ == "__main__":
    main()
