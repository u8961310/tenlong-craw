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

  /* 排序工具列 */
  .toolbar {
    margin-bottom: 1.2rem;
  }
  .toolbar-section {
    margin-bottom: 0.8rem;
  }
  .toolbar-section label {
    font-weight: 600;
    margin-right: 0.5rem;
    font-size: 0.9rem;
  }
  .sort-select {
    padding: 0.4rem 0.6rem;
    border-radius: 6px;
    border: 1px solid #ccc;
    font-size: 0.9rem;
    background: #fff;
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
  .card-img-wrapper { position: relative; }
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
  .card-meta {
    font-size: 0.78rem;
    color: #888;
    margin-bottom: 0.4rem;
    display: -webkit-box;
    -webkit-line-clamp: 1;
    -webkit-box-orient: vertical;
    overflow: hidden;
  }
  .card-desc {
    font-size: 0.78rem;
    color: #666;
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
  .badge-new {
    position: absolute;
    top: 8px;
    right: 8px;
    background: #e74c3c;
    color: #fff;
    font-size: 0.75rem;
    font-weight: 700;
    padding: 0.2rem 0.6rem;
    border-radius: 4px;
    z-index: 1;
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
  <p class="stats">共 {{ books | length }} 本書{% if new_count %} ({{ new_count }} 本新書){% endif %}</p>

  <!-- 排序 -->
  <div class="toolbar">
    <div class="toolbar-section">
      <label>排序:</label>
      <select class="sort-select" id="sortSelect" onchange="sortBooks()">
        <option value="default">預設</option>
        <option value="price-asc">價格 低→高</option>
        <option value="price-desc">價格 高→低</option>
        <option value="discount-asc">折扣 低→高</option>
        <option value="date-desc">出版日 新→舊</option>
        <option value="date-asc">出版日 舊→新</option>
      </select>
    </div>
  </div>

  <div class="grid" id="bookGrid">
    {% for book in books %}
    <div class="card"
         data-price="{{ book.sale_price | default('0') }}"
         data-discount="{{ book.discount | default('') }}"
         data-date="{{ book.date_published | default('') }}">
      <a href="{{ book.url }}" target="_blank" rel="noopener">
        <div class="card-img-wrapper">
          <img class="card-img" src="{{ book.image }}" alt="{{ book.title }}" loading="lazy">
          {% if book.is_new %}<span class="badge-new">NEW</span>{% endif %}
        </div>
        <div class="card-body">
          {% if book.discount %}<span class="badge">{{ book.discount }}</span>{% endif %}
          <div class="card-title">{{ book.title }}</div>
          {% if book.author or book.publisher %}
          <div class="card-meta">
            {% if book.author %}{{ book.author }}{% endif %}
            {% if book.author and book.publisher %} / {% endif %}
            {% if book.publisher %}{{ book.publisher }}{% endif %}
          </div>
          {% endif %}
          {% if book.description %}
          <div class="card-desc">{{ book.description }}</div>
          {% endif %}
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

<script>
// === 排序 ===
function sortBooks() {
  var grid = document.getElementById('bookGrid');
  var cards = Array.from(grid.querySelectorAll('.card'));
  var sortVal = document.getElementById('sortSelect').value;

  if (sortVal === 'default') return;

  cards.sort(function(a, b) {
    if (sortVal === 'price-asc' || sortVal === 'price-desc') {
      var pa = parseInt((a.dataset.price || '0').replace(/,/g, ''), 10);
      var pb = parseInt((b.dataset.price || '0').replace(/,/g, ''), 10);
      return sortVal === 'price-asc' ? pa - pb : pb - pa;
    }
    if (sortVal === 'discount-asc') {
      var da = parseInt(((a.dataset.discount || '').match(/(\\d+)/) || [0,0])[1], 10);
      var db = parseInt(((b.dataset.discount || '').match(/(\\d+)/) || [0,0])[1], 10);
      return da - db;
    }
    if (sortVal === 'date-desc' || sortVal === 'date-asc') {
      var ta = a.dataset.date || '';
      var tb = b.dataset.date || '';
      return sortVal === 'date-desc' ? tb.localeCompare(ta) : ta.localeCompare(tb);
    }
    return 0;
  });
  cards.forEach(function(card) { grid.appendChild(card); });
}
</script>
</body>
</html>
"""


def main():
    with open("books.json", "r", encoding="utf-8") as f:
        books = json.load(f)

    tz = timezone(timedelta(hours=8))
    now = datetime.now(tz)
    updated_at = now.strftime("%Y-%m-%d %H:%M (台灣時間)")
    cutoff = (now - timedelta(days=7)).strftime("%Y-%m-%d")

    # 過濾掉出版日期超過 7 天的書（無日期的保留）
    filtered = []
    for book in books:
        dp = book.get("date_published", "")
        if dp and dp < cutoff:
            continue
        filtered.append(book)

    total_before = len(books)
    books = filtered
    print(f"日期篩選: {total_before} → {len(books)} 本 (排除出版日 < {cutoff})")

    # 計算新書數
    new_count = sum(1 for b in books if b.get("is_new"))

    template = Template(TEMPLATE)
    html = template.render(
        books=books,
        updated_at=updated_at,
        new_count=new_count,
    )

    os.makedirs("docs", exist_ok=True)
    with open("docs/index.html", "w", encoding="utf-8") as f:
        f.write(html)

    print(f"已產生 docs/index.html ({len(books)} 本書)")


if __name__ == "__main__":
    main()
