"""寄送新書通知 email (透過 Gmail SMTP)"""

import json
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText


def build_html(books: list[dict]) -> str:
    """產生 HTML 格式的 email 內容"""
    rows = ""
    for book in books:
        price_html = ""
        if book.get("original_price"):
            price_html += f'<del style="color:#999">NT$ {book["original_price"]}</del> '
        if book.get("sale_price"):
            price_html += f'<b style="color:#e74c3c">NT$ {book["sale_price"]}</b>'
        discount_html = ""
        if book.get("discount"):
            discount_html = (
                f'<span style="background:#3498db;color:#fff;padding:2px 6px;'
                f'border-radius:3px;font-size:12px">{book["discount"]}</span> '
            )

        rows += f"""\
<tr style="border-bottom:1px solid #eee">
  <td style="padding:8px;width:80px">
    <img src="{book.get('image', '')}" width="70" style="display:block">
  </td>
  <td style="padding:8px">
    {discount_html}
    <a href="{book['url']}" style="color:#2c3e50;text-decoration:none;font-weight:600">
      {book['title']}
    </a><br>
    <span style="font-size:14px">{price_html}</span>
  </td>
</tr>
"""

    return f"""\
<html><body style="font-family:sans-serif;color:#333">
<h2 style="color:#2c3e50">天瓏書店 - 最近新書通知</h2>
<p>共 {len(books)} 本新書：</p>
<table style="border-collapse:collapse;width:100%;max-width:600px">
{rows}
</table>
<p style="margin-top:16px;font-size:13px;color:#999">
  此信件由 GitHub Actions 自動寄出
</p>
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

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"天瓏書店新書通知 ({len(books)} 本)"
    msg["From"] = email_from
    msg["To"] = email_to

    html_content = build_html(books)
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(email_from, email_password)
        server.sendmail(email_from, email_to.split(","), msg.as_string())

    print(f"已寄送通知至 {email_to}")


if __name__ == "__main__":
    main()
