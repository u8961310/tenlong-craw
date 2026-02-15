"""寄送新書通知 email (透過 Gmail SMTP)"""

import json
import os
import smtplib
from datetime import datetime, timezone, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_html(books: list[dict]) -> str:
    """產生 HTML 格式的 email 內容，風格與網頁一致"""

    # 過濾 7 日內的書
    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")
    books = [b for b in books if not b.get("date_published") or b["date_published"] >= cutoff]

    new_count = sum(1 for b in books if b.get("is_new"))

    rows = ""
    for book in books:
        # NEW badge
        new_badge = ""
        if book.get("is_new"):
            new_badge = (
                '<span style="background:#e74c3c;color:#fff;padding:2px 8px;'
                'border-radius:4px;font-size:11px;font-weight:700;margin-right:6px'
                '">NEW</span>'
            )

        # 折扣 badge
        discount_badge = ""
        if book.get("discount"):
            discount_badge = (
                f'<span style="background:#3498db;color:#fff;padding:2px 8px;'
                f'border-radius:4px;font-size:11px">{book["discount"]}</span>'
            )

        # 價格
        price_html = ""
        if book.get("original_price"):
            price_html += f'<del style="color:#999;font-size:13px">NT$ {book["original_price"]}</del> '
        if book.get("sale_price"):
            price_html += f'<b style="color:#e74c3c;font-size:15px">NT$ {book["sale_price"]}</b>'

        # 作者 / 出版社 / 出版日
        meta_parts = []
        if book.get("author"):
            meta_parts.append(book["author"])
        if book.get("publisher"):
            meta_parts.append(book["publisher"])
        if book.get("date_published"):
            meta_parts.append(book["date_published"])
        meta_html = ""
        if meta_parts:
            meta_text = " / ".join(meta_parts)
            meta_html = f'<div style="font-size:12px;color:#888;margin-top:4px">{meta_text}</div>'

        # 簡介
        desc_html = ""
        if book.get("description"):
            desc = book["description"][:80]
            if len(book["description"]) > 80:
                desc += "..."
            desc_html = f'<div style="font-size:12px;color:#666;margin-top:4px">{desc}</div>'

        # badges 行
        badges = f"{new_badge}{discount_badge}"
        badges_html = f'<div style="margin-bottom:4px">{badges}</div>' if badges else ""

        rows += f"""\
<tr style="border-bottom:1px solid #eee">
  <td style="padding:12px;width:80px;vertical-align:top">
    <img src="{book.get('image', '')}" width="70" style="display:block;border-radius:4px">
  </td>
  <td style="padding:12px;vertical-align:top">
    {badges_html}
    <a href="{book['url']}" style="color:#2c3e50;text-decoration:none;font-weight:600;font-size:14px">
      {book['title']}
    </a>
    {meta_html}
    {desc_html}
    <div style="margin-top:6px">{price_html}</div>
  </td>
</tr>
"""

    stats = f"共 {len(books)} 本書"
    if new_count:
        stats += f" ({new_count} 本新書)"

    return f"""\
<html><body style="font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;color:#333;margin:0;padding:0;background:#f5f5f5">
<div style="background:#2c3e50;color:#fff;padding:20px;text-align:center">
  <h1 style="margin:0;font-size:22px">天瓏書店 - 最近新書通知</h1>
  <p style="margin:6px 0 0;color:#bdc3c7;font-size:13px">
    {now.strftime("%Y-%m-%d %H:%M")} (台灣時間)
  </p>
</div>
<div style="max-width:600px;margin:16px auto;padding:0 12px">
  <p style="text-align:center;color:#666;margin-bottom:12px">{stats}</p>
  <table style="border-collapse:collapse;width:100%;background:#fff;border-radius:8px;overflow:hidden;box-shadow:0 2px 8px rgba(0,0,0,0.1)">
{rows}
  </table>
  <p style="margin-top:16px;font-size:12px;color:#999;text-align:center">
    此信件由 GitHub Actions 自動寄出
  </p>
</div>
</body></html>
"""


def main():
    email_to = os.environ.get("EMAIL_TO")
    email_from = os.environ.get("EMAIL_FROM")
    email_password = os.environ.get("EMAIL_PASSWORD")

    if not all([email_to, email_from, email_password]):
        print("缺少 EMAIL_TO, EMAIL_FROM 或 EMAIL_PASSWORD 環境變數，跳過寄信")
        return

    with open("books.json", "r", encoding="utf-8") as f:
        books = json.load(f)

    html_content = build_html(books)

    # 計算過濾後數量（與 build_html 相同邏輯）
    tz = timezone(timedelta(hours=8))
    cutoff = (datetime.now(tz) - timedelta(days=7)).strftime("%Y-%m-%d")
    filtered = [b for b in books if not b.get("date_published") or b["date_published"] >= cutoff]

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"天瓏書店新書通知 ({len(filtered)} 本)"
    msg["From"] = email_from
    msg["To"] = email_to

    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_from, email_password)
        server.sendmail(email_from, email_to.split(","), msg.as_string())

    print(f"已寄送通知至 {email_to}")


if __name__ == "__main__":
    main()
