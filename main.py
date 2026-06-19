import requests
import json
from datetime import datetime, timezone, timedelta
import os

# 北京时间
beijing_tz = timezone(timedelta(hours=8))
now = datetime.now(beijing_tz).strftime('%Y-%m-%d %H:%M')

sources = []

# ---------- V2EX 创业节点 ----------
try:
    resp = requests.get("https://www.v2ex.com/api/topics/show.json?node_name=entrepreneur",
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    if resp.status_code == 200:
        topics = resp.json()
        topics_sorted = sorted(topics, key=lambda x: x.get("replies", 0), reverse=True)[:10]
        for t in topics_sorted:
            sources.append({
                "title": t["title"],
                "url": t["url"],
                "heat": t.get("replies", 0),
                "source": "V2EX创业"
            })
except Exception as e:
    print(f"V2EX抓取失败: {e}")

# ---------- Reddit r/sidehustle 热帖 ----------
try:
    resp = requests.get("https://www.reddit.com/r/sidehustle/hot.json?limit=15",
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        for post in data["data"]["children"]:
            pdata = post["data"]
            if not pdata.get("stickied"):
                sources.append({
                    "title": pdata["title"],
                    "url": "https://www.reddit.com" + pdata["permalink"],
                    "heat": pdata.get("score", 0),
                    "source": "Reddit副业"
                })
except Exception as e:
    print(f"Reddit抓取失败: {e}")

# ---------- Hacker News Show HN ----------
try:
    resp = requests.get("https://hn.algolia.com/api/v1/search?tags=show_hn&hitsPerPage=10",
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=15)
    if resp.status_code == 200:
        data = resp.json()
        for hit in data["hits"]:
            sources.append({
                "title": hit.get("title", ""),
                "url": hit.get("url") or f"https://news.ycombinator.com/item?id={hit['objectID']}",
                "heat": hit.get("points", 0),
                "source": "HN Show"
            })
except Exception as e:
    print(f"HN抓取失败: {e}")

# ---------- 如果所有源都失败，添加占位 ----------
if not sources:
    sources.append({
        "title": "暂无热门内容，请稍后再来",
        "url": "#",
        "heat": 0,
        "source": "占位"
    })

# ---------- 去重、排序 ----------
seen = set()
unique = []
for item in sources:
    if item["url"] not in seen:
        seen.add(item["url"])
        unique.append(item)

unique.sort(key=lambda x: x["heat"], reverse=True)

# ---------- 生成 HTML ----------
html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>副业热门日报 · {now}</title>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, sans-serif; max-width: 700px; margin: 40px auto; padding: 0 20px; background: #fafafa; }}
  h1 {{ color: #333; border-bottom: 2px solid #4CAF50; padding-bottom: 10px; }}
  .time {{ color: #888; font-size: 0.9em; margin-top: -10px; }}
  ol {{ padding-left: 20px; }}
  li {{ margin: 12px 0; line-height: 1.5; }}
  a {{ text-decoration: none; color: #1a0dab; font-weight: 500; }}
  a:hover {{ text-decoration: underline; }}
  .source {{ font-size: 0.85em; color: #666; margin-left: 6px; background: #eee; padding: 2px 6px; border-radius: 4px; }}
  .heat {{ color: #e67e22; font-weight: bold; }}
  .footer {{ margin-top: 40px; font-size: 0.8em; color: #aaa; text-align: center; }}
</style>
</head>
<body>
<h1>📌 今日副业热门汇总</h1>
<p class="time">更新时间：{now}（每天自动刷新）</p>
<ol>
"""
for item in unique:
    html += f'<li><a href="{item["url"]}" target="_blank">{item["title"]}</a> <span class="source">{item["source"]}</span> <span class="heat">🔥{item["heat"]}</span></li>\n'

html += """</ol>
<div class="footer">数据来源：V2EX创业节点 · Reddit r/sidehustle · Hacker News Show HN</div>
</body>
</html>"""

os.makedirs("public", exist_ok=True)
with open("public/index.html", "w", encoding="utf-8") as f:
    f.write(html)

print(f"生成完毕，共 {len(unique)} 条")
