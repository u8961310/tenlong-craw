"""天瓏書店中文最近新書爬蟲"""

import argparse
import json
import os
import re
import shutil
import time

import httpx
from bs4 import BeautifulSoup

BASE_URL = "https://www.tenlong.com.tw"
START_URL = f"{BASE_URL}/zh_tw/recent"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
}

BOOKS_FILE = "books.json"
BOOKS_PREV_FILE = "books_previous.json"


def parse_price(text: str) -> str | None:
    """從文字中提取價格數字"""
    if not text:
        return None
    match = re.search(r"[\d,]+", text.strip())
    if match:
        return match.group(0)
    return None


def scrape_page(client: httpx.Client, url: str) -> tuple[list[dict], str | None]:
    """爬取單頁書籍資料，回傳 (書籍列表, 下一頁URL或None)"""
    resp = client.get(url)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    books = []
    for li in soup.select("li.single-book"):
        # 書名與連結
        title_a = li.select_one("strong.title > a")
        if not title_a:
            continue
        title = title_a.get("title") or title_a.get_text(strip=True)
        href = title_a.get("href", "")
        book_url = BASE_URL + href if href.startswith("/") else href

        # 封面圖
        img = li.select_one("a.cover > img")
        image = img.get("src", "") if img else ""

        # 折扣標籤
        discount_span = li.select_one("a.cover > span.label-blue")
        discount = discount_span.get_text(strip=True) if discount_span else ""

        # 價格
        pricing_div = li.select_one("div.pricing")
        original_price = ""
        sale_price = ""
        if pricing_div:
            del_tag = pricing_div.select_one("del")
            if del_tag:
                original_price = parse_price(del_tag.get_text()) or ""
            # 折扣價在 pricing div 的直接文字節點中
            pricing_text = pricing_div.get_text(strip=True)
            # 移除 del 標籤的文字後，剩餘的就是折扣價
            if del_tag:
                del_text = del_tag.get_text(strip=True)
                pricing_text = pricing_text.replace(del_text, "")
            sale_price = parse_price(pricing_text) or ""

        books.append(
            {
                "title": title,
                "url": book_url,
                "image": image,
                "original_price": original_price,
                "sale_price": sale_price,
                "discount": discount,
            }
        )

    # 偵測下一頁
    next_link = soup.select_one("a.next_page")
    next_url = None
    if next_link:
        next_href = next_link.get("href", "")
        if next_href:
            # 頁面連結可能是 /tw/recent?page=N，統一轉為 /zh_tw/recent?page=N
            next_href = next_href.replace("/tw/recent", "/zh_tw/recent")
            next_url = BASE_URL + next_href if next_href.startswith("/") else next_href

    return books, next_url


def scrape_detail(client: httpx.Client, book_url: str) -> dict:
    """抓取書籍詳情頁，回傳 author/publisher/date_published/description/categories"""
    detail = {}
    try:
        resp = client.get(book_url)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "lxml")

        # JSON-LD：author, publisher, date_published
        ld_script = soup.select_one("script[type='application/ld+json']")
        if ld_script:
            try:
                ld = json.loads(ld_script.string)
                # author 可能是 list 或 dict
                author_raw = ld.get("author")
                if isinstance(author_raw, list):
                    detail["author"] = ", ".join(
                        a.get("name", "") for a in author_raw if isinstance(a, dict)
                    )
                elif isinstance(author_raw, dict):
                    detail["author"] = author_raw.get("name", "")

                pub_raw = ld.get("publisher")
                if isinstance(pub_raw, dict):
                    detail["publisher"] = pub_raw.get("name", "")

                detail["date_published"] = ld.get("datePublished", "")
            except (json.JSONDecodeError, TypeError):
                pass

        # description：從 og:description meta 取 | 前的部分
        og_desc = soup.select_one("meta[property='og:description']")
        if og_desc:
            desc_text = og_desc.get("content", "")
            if "|" in desc_text:
                desc_text = desc_text.split("|")[0].strip()
            detail["description"] = desc_text

        # categories：從 keywords meta + category links
        categories = set()
        kw_meta = soup.select_one("meta[name='keywords']")
        if kw_meta:
            kw_text = kw_meta.get("content", "")
            for kw in kw_text.split(","):
                kw = kw.strip()
                if kw:
                    categories.add(kw)

        for cat_a in soup.select("a[href^='/categories/']"):
            cat_text = cat_a.get_text(strip=True)
            if cat_text:
                categories.add(cat_text)

        detail["categories"] = sorted(categories)

    except Exception as e:
        print(f"  ⚠ 抓取詳情失敗: {book_url} ({e})")

    return detail


def scrape_all() -> list[dict]:
    """爬取所有頁面的書籍資料"""
    all_books = []
    url = START_URL
    page = 1

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        while url:
            print(f"正在爬取第 {page} 頁: {url}")
            books, next_url = scrape_page(client, url)
            all_books.extend(books)
            print(f"  取得 {len(books)} 本書")

            url = next_url
            page += 1
            if url:
                time.sleep(1)  # 禮貌性延遲

    print(f"\n共取得 {len(all_books)} 本書")
    return all_books


def load_old_books() -> dict[str, dict]:
    """讀取舊的 books.json，以 URL 為 key 建立索引"""
    if not os.path.exists(BOOKS_FILE):
        return {}
    try:
        with open(BOOKS_FILE, "r", encoding="utf-8") as f:
            old_books = json.load(f)
        return {b["url"]: b for b in old_books if "url" in b}
    except (json.JSONDecodeError, KeyError):
        return {}


def backup_old_books():
    """備份舊的 books.json 為 books_previous.json"""
    if os.path.exists(BOOKS_FILE):
        shutil.copy2(BOOKS_FILE, BOOKS_PREV_FILE)
        print(f"已備份 {BOOKS_FILE} → {BOOKS_PREV_FILE}")


def mark_new_books(books: list[dict], old_index: dict[str, dict]):
    """標記每本書是否為新書"""
    for book in books:
        book["is_new"] = book["url"] not in old_index


def enrich_details(books: list[dict], old_index: dict[str, dict]):
    """對每本書抓取詳情，已有詳情的書直接沿用快取"""
    detail_fields = ("author", "publisher", "date_published", "description", "categories")
    to_fetch = []

    for book in books:
        old = old_index.get(book["url"])
        if old and old.get("author"):
            # 沿用舊資料的詳情欄位
            for field in detail_fields:
                if field in old:
                    book[field] = old[field]
        else:
            to_fetch.append(book)

    if not to_fetch:
        print("所有書籍詳情皆已快取，無需額外請求")
        return

    print(f"\n需抓取 {len(to_fetch)} 本書的詳情（{len(books) - len(to_fetch)} 本已快取）")

    with httpx.Client(headers=HEADERS, follow_redirects=True, timeout=30) as client:
        for i, book in enumerate(to_fetch, 1):
            print(f"  [{i}/{len(to_fetch)}] 抓取詳情: {book['title'][:40]}...")
            detail = scrape_detail(client, book["url"])
            book.update(detail)
            if i < len(to_fetch):
                time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="天瓏書店新書爬蟲")
    parser.add_argument(
        "--skip-details",
        action="store_true",
        help="跳過詳情頁抓取（本地開發用）",
    )
    args = parser.parse_args()

    # 讀取舊資料 & 備份
    old_index = load_old_books()
    backup_old_books()

    # 爬取列表頁
    books = scrape_all()

    # 標記新書
    mark_new_books(books, old_index)
    new_count = sum(1 for b in books if b.get("is_new"))
    print(f"其中 {new_count} 本為新書")

    # 抓取詳情（可跳過）
    if args.skip_details:
        print("已跳過詳情抓取 (--skip-details)")
        # 即使跳過，也沿用舊資料的詳情
        detail_fields = ("author", "publisher", "date_published", "description", "categories")
        for book in books:
            old = old_index.get(book["url"])
            if old:
                for field in detail_fields:
                    if field in old:
                        book[field] = old[field]
    else:
        enrich_details(books, old_index)

    # 寫入 JSON
    with open(BOOKS_FILE, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print(f"已儲存至 {BOOKS_FILE}")


if __name__ == "__main__":
    main()
