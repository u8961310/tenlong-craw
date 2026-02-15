"""天瓏書店中文最近新書爬蟲"""

import json
import re
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


def main():
    books = scrape_all()
    with open("books.json", "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
    print("已儲存至 books.json")


if __name__ == "__main__":
    main()
