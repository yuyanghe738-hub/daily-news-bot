#!/usr/bin/env python3
"""
每日新闻机器人 - 自动抓取、分类、发送邮件
支持 RSS 抓取，按关键词分类，生成 HTML 邮件并通过 SendGrid/SMTP 发送。
"""

import asyncio
import hashlib
import html
import json
import os
import re
import smtplib
import sys
import time
import traceback
from datetime import datetime, timedelta, timezone
from email.header import Header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formataddr
from typing import Optional
from urllib.parse import urlparse

import aiohttp
import feedparser

import config

# 可选翻译库，不存在时跳过翻译
try:
    from deep_translator import GoogleTranslator
    HAS_TRANSLATOR = True
except ImportError:
    HAS_TRANSLATOR = False

# 北京时区
BJT = timezone(timedelta(hours=8))


# ==================== 工具函数 ====================

def bj_now() -> datetime:
    """返回当前北京时间"""
    return datetime.now(BJT)


def bj_date_str(days_ago: int = 0) -> str:
    """返回北京时间日期字符串 YYYY-MM-DD"""
    return (bj_now() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def strip_html(text: str) -> str:
    """去除 HTML 标签"""
    clean = re.compile(r"<[^>]+>")
    return clean.sub("", text).strip()


def truncate(text: str, max_len: int = 150) -> str:
    """截断文本"""
    if len(text) <= max_len:
        return text
    return text[:max_len].rstrip() + "..."


def dedup(articles: list, key: str = "url") -> list:
    """根据 key 去重"""
    seen = set()
    result = []
    for a in articles:
        k = a.get(key, "")
        if k and k not in seen:
            seen.add(k)
            result.append(a)
    return result


def classify_article(title: str, summary: str) -> list[str]:
    """根据关键词对文章分类，返回分类列表"""
    text = f"{title} {summary}".lower()
    matched = []
    for cat_name, cat_cfg in config.CATEGORIES.items():
        for kw in cat_cfg["keywords"]:
            if kw.lower() in text:
                matched.append(cat_name)
                break
    return matched


def is_english(text: str) -> bool:
    """判断文本是否主要为英文"""
    if not text:
        return False
    # 统计英文字母占比
    letters = sum(1 for c in text if c.isalpha())
    eng = sum(1 for c in text if c.isascii() and c.isalpha())
    return letters > 0 and (eng / letters) > 0.7


def translate_batch(texts: list[str], max_retries: int = 2) -> dict[int, str]:
    """批量翻译英文文本为中文，返回 {index: translated_text} 映射"""
    if not config.TRANSLATE_TO_CN or not HAS_TRANSLATOR:
        return {}

    # 只翻译英文内容
    to_translate = {i: t for i, t in enumerate(texts) if t and is_english(t)}
    if not to_translate:
        return {}

    translator = GoogleTranslator(source="en", target="zh-CN")
    results = {}

    # 分批翻译，每批10条避免限流
    batch_size = 10
    indices = list(to_translate.keys())

    for batch_start in range(0, len(indices), batch_size):
        batch_idx = indices[batch_start : batch_start + batch_size]
        batch_texts = [to_translate[i] for i in batch_idx]

        for attempt in range(max_retries):
            try:
                translated = translator.translate_batch(batch_texts)
                for i, t in zip(batch_idx, translated):
                    if t and t != to_translate[i]:
                        results[i] = t
                break
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(2)
                else:
                    print(f"  ⚠ 翻译失败 (第{batch_start//batch_size+1}批): {e}")

        # 批次间等待，减缓请求频率
        time.sleep(1)

    return results


# ==================== RSS 新闻抓取 ====================

async def fetch_feed(
    session: aiohttp.ClientSession, name: str, url: str
) -> list[dict]:
    """异步抓取单个 RSS feed"""
    articles = []
    try:
        headers = {"User-Agent": config.USER_AGENT}
        async with session.get(url, timeout=aiohttp.ClientTimeout(total=config.TIMEOUT), headers=headers) as resp:
            if resp.status != 200:
                print(f"  ⚠ {name}: HTTP {resp.status}")
                return articles
            text = await resp.text()

        feed = feedparser.parse(text)
        cutoff = bj_now() - timedelta(days=config.DAYS_BACK)

        for entry in feed.entries[: config.MAX_PER_SOURCE]:
            pub = entry.get("published_parsed") or entry.get("updated_parsed")
            if pub:
                try:
                    pub_dt = datetime(*pub[:6], tzinfo=timezone.utc)
                    if pub_dt < cutoff.replace(tzinfo=timezone.utc):
                        continue
                except Exception:
                    pass

            link = entry.get("link", "")
            title = strip_html(entry.get("title", ""))
            summary = strip_html(
                entry.get("summary", entry.get("description", ""))
            )

            if not title:
                continue

            articles.append({
                "title": title,
                "url": link,
                "summary": truncate(summary, 250),
                "source": name,
                "published": str(pub[:3]) if pub else "",
            })

        print(f"  ✅ {name}: {len(articles)} 条")
    except asyncio.TimeoutError:
        print(f"  ⏰ {name}: 超时")
    except Exception as e:
        print(f"  ❌ {name}: {e}")

    return articles


async def fetch_all_news() -> list[dict]:
    """并行抓取所有 RSS 源"""
    all_articles = []
    connector = aiohttp.TCPConnector(limit=10)

    async with aiohttp.ClientSession(connector=connector) as session:
        tasks = []
        for name, url in config.RSS_SOURCES.items():
            if url:
                tasks.append(fetch_feed(session, name, url))
        results = await asyncio.gather(*tasks)

    for articles in results:
        all_articles.extend(articles)

    # 全局去重
    all_articles = dedup(all_articles, "url")

    # 按分类
    for article in all_articles:
        cats = classify_article(article["title"], article["summary"])
        article["categories"] = cats if cats else ["uncategorized"]

    return all_articles


# ==================== 生成 HTML 邮件 ====================

def build_html_email(articles: list[dict], date_range: str, trans_map: dict[int, dict] = None) -> str:
    """生成格式化的 HTML 邮件正文"""
    today = bj_now().strftime("%Y年%m月%d日")
    trans_map = trans_map or {}

    # 统计
    cat_counts = {}
    for a in articles:
        for c in a.get("categories", ["uncategorized"]):
            cat_counts[c] = cat_counts.get(c, 0) + 1

    sections_html = ""
    for cat_name, cat_cfg in config.CATEGORIES.items():
        cat_articles = [
            a for a in articles if cat_name in a.get("categories", [])
        ][: cat_cfg["max_articles"]]

        if not cat_articles:
            continue

        articles_html = ""
        for i, a in enumerate(cat_articles, 1):
            aid = id(a)
            tmap = trans_map.get(aid, {})
            title = html.escape(tmap.get("title", a["title"]))
            url = html.escape(a.get("url", ""))
            summary = html.escape(tmap.get("summary", a.get("summary", "")))
            source = html.escape(a.get("source", ""))
            articles_html += f"""
            <tr>
                <td style="padding: 10px 16px; border-bottom: 1px solid #eee;">
                    <div style="font-size: 13px; color: #999; margin-bottom: 2px;">
                        <span style="background: #e8f4fd; padding: 1px 6px; border-radius: 3px; font-size: 11px;">{source}</span>
                    </div>
                    <a href="{url}" style="font-size: 15px; color: #1a73e8; text-decoration: none; font-weight: 500; line-height: 1.4;" target="_blank">{title}</a>
                    <div style="font-size: 13px; color: #555; margin-top: 4px; line-height: 1.4;">{summary}</div>
                </td>
            </tr>"""

        sections_html += f"""
        <tr>
            <td style="padding: 16px 0 8px 0;">
                <table width="100%" cellpadding="0" cellspacing="0" border="0">
                    <tr>
                        <td style="border-bottom: 2px solid #1a73e8; padding-bottom: 6px;">
                            <span style="font-size: 18px; font-weight: bold; color: #333;">{cat_cfg['title']}</span>
                            <span style="font-size: 12px; color: #999; margin-left: 8px;">共 {len(cat_articles)} 条</span>
                        </td>
                    </tr>
                </table>
            </td>
        </tr>
        {articles_html}"""

    html_content = f"""<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin: 0; padding: 0; background: #f5f5f5; font-family: -apple-system, 'Helvetica Neue', Arial, sans-serif;">
<table width="100%" cellpadding="0" cellspacing="0" border="0" style="background: #f5f5f5;">
<tr><td align="center" style="padding: 20px 10px;">
<table width="640" cellpadding="0" cellspacing="0" border="0" style="background: #fff; border-radius: 8px; overflow: hidden; box-shadow: 0 1px 3px rgba(0,0,0,0.08);">

<!-- 头部 -->
<tr>
    <td style="background: linear-gradient(135deg, #1a73e8, #0d47a1); padding: 28px 24px; text-align: center;">
        <div style="font-size: 26px; font-weight: bold; color: #fff; margin-bottom: 4px;">📰 每日国际新闻摘要</div>
        <div style="font-size: 14px; color: rgba(255,255,255,0.85);">{date_range}</div>
        <div style="font-size: 12px; color: rgba(255,255,255,0.65); margin-top: 6px;">{today} · 自动抓取 | 共 {len(articles)} 条</div>
    </td>
</tr>

<!-- 内容 -->
<tr><td style="padding: 0 20px 20px 20px;">
    <table width="100%" cellpadding="0" cellspacing="0" border="0">
        {sections_html}
    </table>
</td></tr>

<!-- 页脚 -->
<tr>
    <td style="background: #fafafa; padding: 16px 24px; text-align: center; border-top: 1px solid #eee;">
        <div style="font-size: 12px; color: #999; line-height: 1.6;">
            本邮件由 <strong>AI 新闻机器人</strong> 自动生成 · 每天早上 7:30 发送<br>
            数据来源：BBC、CNN、Reuters、Al Jazeera、Nature、Science 等<br>
            <a href="https://github.com/yuyanghe738/daily-news-bot" style="color: #1a73e8; text-decoration: none;">GitHub 项目地址</a>
        </div>
    </td>
</tr>
</table>
</td></tr>
</table>
</body>
</html>"""

    return html_content


def build_text_email(articles: list[dict], trans_map: dict[int, dict] = None) -> str:
    """生成纯文本备用邮件"""
    trans_map = trans_map or {}
    lines = ["📰 每日国际新闻摘要", "=" * 40, f"日期范围：{get_date_range()}", ""]
    for cat_name, cat_cfg in config.CATEGORIES.items():
        cat_articles = [a for a in articles if cat_name in a.get("categories", [])][: cat_cfg["max_articles"]]
        if not cat_articles:
            continue
        lines.append(f"\n{cat_cfg['title']}")
        lines.append("-" * 30)
        for a in cat_articles:
            aid = id(a)
            tmap = trans_map.get(aid, {})
            title = tmap.get("title", a["title"])
            lines.append(f"\n• {title}")
            lines.append(f"  {a.get('url', '')}")
            summary = tmap.get("summary", a.get("summary", ""))
            if summary:
                lines.append(f"  {summary}")
    lines.append("\n" + "=" * 40)
    lines.append("由 AI 新闻机器人自动生成")
    return "\n".join(lines)


def get_date_range() -> str:
    """获取日期范围字符串"""
    if config.DAYS_BACK <= 1:
        return f"{bj_date_str(0)}"
    return f"{bj_date_str(config.DAYS_BACK - 1)} ~ {bj_date_str(0)}"


# ==================== 邮件发送 ====================

def send_email_via_sendgrid(html_body: str, text_body: str, subject: str):
    """通过 SendGrid API 发送"""
    if not config.SENDGRID_API_KEY:
        raise ValueError("SENDGRID_API_KEY 未设置")

    import http.client
    import json

    data = {
        "personalizations": [{"to": [{"email": config.TO_EMAIL}]}],
        "from": {"email": config.FROM_EMAIL or "news-bot@example.com"},
        "subject": subject,
        "content": [
            {"type": "text/plain", "value": text_body},
            {"type": "text/html", "value": html_body},
        ],
    }

    conn = http.client.HTTPSConnection("api.sendgrid.com")
    conn.request(
        "POST",
        "/v3/mail/send",
        body=json.dumps(data),
        headers={
            "Authorization": f"Bearer {config.SENDGRID_API_KEY}",
            "Content-Type": "application/json",
        },
    )
    resp = conn.getresponse()
    if resp.status not in (200, 201, 202):
        raise RuntimeError(
            f"SendGrid 发送失败: HTTP {resp.status} - {resp.read().decode()}"
        )
    print(f"✅ SendGrid 邮件发送成功（{resp.status}）")


def send_email_via_smtp(html_body: str, text_body: str, subject: str):
    """通过 SMTP 发送"""
    if not config.SMTP_USER or not config.SMTP_PASS:
        raise ValueError("SMTP 账户未配置")

    msg = MIMEMultipart("alternative")
    msg["From"] = formataddr(("每日新闻摘要", config.FROM_EMAIL or config.SMTP_USER))
    msg["To"] = config.TO_EMAIL
    msg["Subject"] = Header(subject, "utf-8")

    msg.attach(MIMEText(text_body, "plain", "utf-8"))
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
        server.starttls()
        server.login(config.SMTP_USER, config.SMTP_PASS)
        server.send_message(msg)

    print(f"✅ SMTP 邮件发送成功 → {config.TO_EMAIL}")


def send_email(html_body: str, text_body: str, subject: str):
    """自动选择发送方式"""
    if config.SENDGRID_API_KEY:
        send_email_via_sendgrid(html_body, text_body, subject)
    elif config.SMTP_USER and config.SMTP_PASS:
        send_email_via_smtp(html_body, text_body, subject)
    else:
        print("\n⚠️  未配置邮件发送方式！请设置以下环境变量之一：")
        print("  方式一（推荐）：SENDGRID_API_KEY")
        print("  方式二：SMTP_USER + SMTP_PASS（Gmail 应用专用密码）")
        print()
        print("📧 以下为邮件预览（将保存到 HTML 文件）：")
        preview_path = os.path.expanduser("~/daily-news-bot/preview.html")
        with open(preview_path, "w", encoding="utf-8") as f:
            f.write(html_body)
        print(f"  → 已保存到 {preview_path}")
        return False
    return True


# ==================== 主流程 ====================

async def main():
    """主流程"""
    start = time.time()
    date_range = get_date_range()

    print(f"\n{'='*50}")
    print(f"📰 每日新闻抓取 - {date_range}")
    print(f"{'='*50}\n")

    # 1. 抓取新闻
    print("📡 正在抓取 RSS 新闻源...")
    articles = await fetch_all_news()
    print(f"\n📊 共抓取 {len(articles)} 条去重新闻")

    if not articles:
        print("⚠️  未抓取到任何新闻，请检查网络或 RSS 源")
        sys.exit(1)

    # 2. 分类统计
    print("\n📊 分类统计：")
    for cat_name, cat_cfg in config.CATEGORIES.items():
        count = sum(1 for a in articles if cat_name in a.get("categories", []))
        print(f"  {cat_cfg['title']}: {count} 条")

    uncat = sum(1 for a in articles if "uncategorized" in a.get("categories", []))
    print(f"  未分类: {uncat} 条")

    # 3. 翻译英文标题和摘要为中文
    if config.TRANSLATE_TO_CN:
        print("\n🌐 正在翻译为中文...")
        # 收集所有需要翻译的文本
        all_titles = []
        all_summaries = []
        for a in articles:
            all_titles.append(a["title"])
            all_summaries.append(a.get("summary", ""))

        # 批量翻译
        title_trans = translate_batch(all_titles)
        summary_trans = translate_batch(all_summaries)

        # 构建翻译映射
        trans_map = {}
        for i, a in enumerate(articles):
            aid = id(a)
            tmap = {}
            if i in title_trans:
                tmap["title"] = title_trans[i]
            if i in summary_trans:
                tmap["summary"] = summary_trans[i]
            if tmap:
                trans_map[aid] = tmap

        translated_count = len(title_trans) + len(summary_trans)
        print(f"  ✅ 翻译完成: {len(title_trans)} 个标题 + {len(summary_trans)} 条摘要")
    else:
        trans_map = {}

    # 4. 生成邮件
    print("\n📝 正在生成邮件...")
    subject = f"📰 每日国际新闻摘要 - {date_range}"
    html_body = build_html_email(articles, date_range, trans_map)
    text_body = build_text_email(articles, trans_map)

    # 5. 发送邮件
    print("📧 正在发送邮件...")
    send_email(html_body, text_body, subject)

    elapsed = time.time() - start
    print(f"\n⏱ 总耗时: {elapsed:.1f} 秒")


if __name__ == "__main__":
    asyncio.run(main())
