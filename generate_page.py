"""從 books.json 產生 GitHub Pages 靜態頁面"""

import json
import os
from datetime import datetime, timezone, timedelta

from jinja2 import Template

TEMPLATE = """\
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>天瓏書店 - 最近新書</title>
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: #f5f5f5;
    color: #333;
    line-height: 1.6;
  }
  header {
    background: #2c3e50;
    color: #fff;
    padding: 1.5rem;
    text-align: center;
  }
  header h1 { font-size: 1.8rem; }
  header p { color: #bdc3c7; margin-top: 0.3rem; font-size: 0.9rem; }
  .container {
    max-width: 1200px;
    margin: 1.5rem auto;
    padding: 0 1rem;
  }
  .stats {
    text-align: center;
    margin-bottom: 1rem;
    color: #666;
  }
  .grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
    gap: 1.2rem;
  }
  .card {
    background: #fff;
    border-radius: 8px;
    overflow: hidden;
    box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    transition: transform 0.2s;
    display: flex;
    flex-direction: column;
  }
  .card:hover { transform: translateY(-4px); }
  .card a { text-decoration: none; color: inherit; }
  .card-img {
    width: 100%;
    height: 280px;
    object-fit: contain;
    background: #fafafa;
    padding: 0.5rem;
  }
  .card-body {
    padding: 0.8rem;
    flex: 1;
    display: flex;
    flex-direction: column;
  }
  .card-title {
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 0.5rem;
    display: -webkit-box;
    -webkit-line-clamp: 2;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .card-price {
    margin-top: auto;
    font-size: 0.9rem;
  }
  .price-original {
    text-decoration: line-through;
    color: #999;
    margin-right: 0.5rem;
  }
  .price-sale {
    color: #e74c3c;
    font-weight: 700;
  }
  .badge {
    display: inline-block;
    background: #3498db;
    color: #fff;
    font-size: 0.75rem;
    padding: 0.15rem 0.5rem;
    border-radius: 4px;
    margin-bottom: 0.4rem;
    align-self: flex-start;
  }
  @media (max-width: 600px) {
    .grid { grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); }
    .card-img { height: 200px; }
  }
</style>
</head>
<body>
<header>
  <h1>天瓏書店 - 最近新書</h1>
  <p>最後更新: {{ updated_at }}</p>
</header>
<div class="container">
  <p class="stats">共 {{ books | length }} 本書</p>
  <div class="grid">
    {% for book in books %}
    <div class="card">
      <a href="{{ book.url }}" target="_blank" rel="noopener">
        <img class="card-img" src="{{ book.image }}" alt="{{ book.title }}" loading="lazy">
        <div class="card-body">
          {% if book.discount %}<span class="badge">{{ book.discount }}</span>{% endif %}
          <div class="card-title">{{ book.title }}</div>
          <div class="card-price">
            {% if book.original_price %}<span class="price-original">NT$ {{ book.original_price }}</span>{% endif %}
            {% if book.sale_price %}<span class="price-sale">NT$ {{ book.sale_price }}</span>{% endif %}
          </div>
        </div>
      </a>
    </div>
    {% endfor %}
  </div>
</div>
</body>
</html>
"""


def main():
    with open("books.json", "r", encoding="utf-8") as f:
        books = json.load(f)

    tz = timezone(timedelta(hours=8))
    updated_at = datetime.now(tz).strftime("%Y-%m-%d %H:%M (台灣時間)")

    template = Template(TEMPLATE)
    html = template.render(books=books, updated_at=updated_at)

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"已產生 docs/index.html ({len(books)} 本書)")


if __name__ == "__main__":
    main()
