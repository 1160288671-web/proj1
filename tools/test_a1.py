"""临时脚本：单独运行 A1 查看采集结果"""
import asyncio
import json
from pathlib import Path
from src.agents.a1_collector import A1Collector

async def main():
    collector = A1Collector()
    state = {"workflow_id": "test-a1-20260722", "dry_run": False}
    result = await collector.run(state)

    # 读取落盘文件
    out_path = Path("data/hot_raw.json")
    if out_path.exists():
        print(f"\n{'='*60}")
        print(f"输出文件: {out_path}")

        with open(out_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        print(f"\n[meta] {json.dumps(data.get('meta', {}), ensure_ascii=False)}")
        print(f"[summary] {json.dumps(data.get('summary', {}), ensure_ascii=False)}")
        print(f"\n[source_stats]")
        for sid, s in data.get("source_stats", {}).items():
            print(f"  {sid}: {json.dumps(s, ensure_ascii=False)}")

        items = data.get("items", [])
        print(f"\n[items] 共 {len(items)} 条，以下为每源首 2 条样例：")
        shown_sources = set()
        for item in items:
            sid = item.get("source_id", "")
            if sid in shown_sources:
                continue
            shown_sources.add(sid)
            # 找该源的前 2 条
            same_src = [i for i in items if i.get("source_id") == sid][:2]
            for s in same_src:
                print(f"  [{s['list_type']}] {s['source']} #{s['rank']}")
                print(f"    title     : {s['title'][:60]}")
                print(f"    heat_score: {s['heat_score']}")
                print(f"    domain_tag: {s['domain_tag']}")
                print(f"    trend     : {s.get('trend', '')}")
                print(f"    url       : {s['url'][:80] if s.get('url') else '(无)'}")
            print()

    # 显示错误
    errors = result.get("errors", [])
    if errors:
        print(f"\n[errors] ({len(errors)} 个)")
        for e in errors:
            print(f"  ✗ {e}")

if __name__ == "__main__":
    asyncio.run(main())
