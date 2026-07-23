# -*- coding: utf-8 -*-
"""探测各平台热榜接口的可用性，保存原始响应样本

输出目录：data/a1_data/probe/
"""
import json
import sys
import time
from pathlib import Path

import requests

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUT = PROJECT_ROOT / "data" / "a1_data" / "probe"
UA = ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36")

# (id, 说明, url, extra_headers)
ENDPOINTS = [
    # ---- 官方/半官方直连 ----
    ("bilibili_popular", "B站热门视频(官方)", "https://api.bilibili.com/x/web-interface/popular?ps=20&pn=1", {}),
    ("bilibili_search_square", "B站热搜(官方)", "https://api.bilibili.com/x/web-interface/search/square?limit=10", {}),
    ("toutiao_hot_board", "头条热榜(半官方)", "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc", {}),
    ("weibo_hot_search", "微博热搜(半官方)", "https://weibo.com/ajax/side/hotSearch", {"Referer": "https://weibo.com/"}),
    ("baidu_board", "百度热搜(半官方)", "https://top.baidu.com/api/board?platform=wise&tab=realtime", {"Referer": "https://top.baidu.com/board"}),
    # ---- 第三方聚合(免key) ----
    ("vvhan_weibo", "韩小韩-微博", "https://api.vvhan.com/api/hotlist/wbHot", {}),
    ("vvhan_bili", "韩小韩-B站", "https://api.vvhan.com/api/hotlist/bili", {}),
    ("vvhan_baidu", "韩小韩-百度", "https://api.vvhan.com/api/hotlist/baiduRD", {}),
    ("vvhan_toutiao", "韩小韩-头条", "https://api.vvhan.com/api/hotlist/toutiao", {}),
    ("vvhan_xhs", "韩小韩-小红书", "https://api.vvhan.com/api/hotlist/xhs", {}),
    ("60s_weibo", "60s-微博", "https://60s-api.viki.moe/v2/weibo", {}),
    ("60s_toutiao", "60s-头条", "https://60s-api.viki.moe/v2/toutiao", {}),
    ("60s_bili", "60s-B站", "https://60s-api.viki.moe/v2/bili", {}),
    ("dailyhot_weibo", "DailyHot公共实例-微博", "https://api-hot.imsyy.top/weibo", {}),
    ("dailyhot_xhs", "DailyHot公共实例-小红书", "https://api-hot.imsyy.top/xiaohongshu", {}),
]


def probe(eid, desc, url, extra_headers):
    headers = {"User-Agent": UA, "Accept": "application/json, text/plain, */*"}
    headers.update(extra_headers)
    result = {"id": eid, "desc": desc, "url": url, "ok": False, "status": None,
              "ms": None, "error": None, "top_keys": None, "item_count": None}
    t0 = time.time()
    try:
        resp = requests.get(url, headers=headers, timeout=15, allow_redirects=True)
        result["ms"] = int((time.time() - t0) * 1000)
        result["status"] = resp.status_code
        if resp.status_code != 200:
            result["error"] = f"HTTP {resp.status_code}"
            return result
        text = resp.text
        try:
            data = resp.json()
            result["top_keys"] = list(data.keys())[:10] if isinstance(data, dict) else f"list[{len(data)}]"
            # 保存完整样本（截断到前 60KB 防爆）
            (OUT / f"{eid}.json").write_text(
                json.dumps(data, ensure_ascii=False, indent=2)[:60000], encoding="utf-8")
            result["ok"] = True
        except json.JSONDecodeError:
            result["error"] = f"非JSON响应({len(text)}字符): {text[:120]!r}"
            (OUT / f"{eid}.txt").write_text(text[:20000], encoding="utf-8")
    except Exception as e:
        result["ms"] = int((time.time() - t0) * 1000)
        result["error"] = f"{type(e).__name__}: {e}"
    return result


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = []
    for eid, desc, url, hdrs in ENDPOINTS:
        r = probe(eid, desc, url, hdrs)
        results.append(r)
        mark = "✅" if r["ok"] else "❌"
        print(f"{mark} {r['id']:<26} {r['status'] or '-':<4} {r['ms']:>6}ms  "
              f"{r['error'] or ('keys=' + str(r['top_keys']))}")
    (OUT / "probe_summary.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    ok = sum(1 for r in results if r["ok"])
    print(f"\n可用 {ok}/{len(results)}，样本已保存到 {OUT}")


if __name__ == "__main__":
    sys.exit(main())
