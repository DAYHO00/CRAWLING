import re
import os
import sqlite3
import requests
from bs4 import BeautifulSoup
from urllib.parse import urlencode

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

try:
    from dotenv import load_dotenv
    load_dotenv()
except Exception:
    pass

LIST_URL = "https://www.nl.go.kr/kolisnet/notice/noticeList.do"
DETAIL_BASE = "https://www.nl.go.kr/kolisnet/notice/noticeDetail.do"
DB_PATH = "notices.db"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en;q=0.8",
}

# ====== 이메일 설정 (.env 권장) ======
NAVER_EMAIL = os.getenv("NAVER_EMAIL", "").strip()
NAVER_APP_PASSWORD = os.getenv("NAVER_APP_PASSWORD", "").strip()
TO_EMAIL = os.getenv("TO_EMAIL", NAVER_EMAIL).strip()

SMTP_HOST = "smtp.naver.com"
SMTP_PORT_SSL = 465  # SSL


def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS notices (
            no TEXT PRIMARY KEY,
            title TEXT,
            date TEXT,
            link TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_notices_and_collect_new(notices):
    """
    notices: list of (no, title, date, link)
    return: new_items list
    """
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    new_items = []

    for no, title, date, link in notices:
        try:
            cur.execute("""
                INSERT INTO notices (no, title, date, link)
                VALUES (?, ?, ?, ?)
            """, (no, title, date, link))
            new_items.append((no, title, date, link))
        except sqlite3.IntegrityError:
            # 이미 존재하는 글
            pass

    conn.commit()
    conn.close()

    return new_items


def fetch_html(url: str) -> str:
    r = requests.get(url, headers=HEADERS, timeout=10)
    r.raise_for_status()
    return r.text


def parse_top_notices(html: str, limit: int = 5):
    soup = BeautifulSoup(html, "html.parser")
    pattern = re.compile(r"fnDetail\(\s*['\"]?(\d+)['\"]?\s*\)")

    items = []

    for a in soup.select("a[onclick]"):
        onclick = a.get("onclick", "")
        m = pattern.search(onclick)
        if not m:
            continue

        no = m.group(1)
        title = a.get_text(" ", strip=True)
        if not title:
            continue

        link = DETAIL_BASE + "?" + urlencode({"no": no})

        date = ""
        row = a.find_parent("tr")
        if row:
            tds = [td.get_text(" ", strip=True) for td in row.select("td")]
            for t in tds:
                if re.fullmatch(r"\d{4}[./-]\d{2}[./-]\d{2}", t):
                    date = t
                    break

        items.append((no, title, date, link))

    # 중복 제거(공지번호 기준)
    unique = []
    seen = set()
    for no, title, date, link in items:
        if no in seen:
            continue
        seen.add(no)
        unique.append((no, title, date, link))

    return unique[:limit]


def send_email_for_new_items(new_items):
    """
    new_items: list of (no, title, date, link)
    """
    if not new_items:
        return

    if not NAVER_EMAIL or not NAVER_APP_PASSWORD or not TO_EMAIL:
        print("[M5] 이메일 설정이 비어있어서 전송을 건너뜁니다.")
        print("     .env에 NAVER_EMAIL / NAVER_APP_PASSWORD / TO_EMAIL 설정하세요.")
        return

    subject = f"[국회도서관 공지] NEW {len(new_items)}건"
    lines = []
    lines.append(f"새 공지 {len(new_items)}건이 감지되었습니다.\n")
    for i, (_, title, date, link) in enumerate(new_items, 1):
        date_str = date if date else "-"
        lines.append(f"{i}. ({date_str}) {title}")
        lines.append(f"   {link}")
    body = "\n".join(lines)

    msg = MIMEMultipart()
    msg["From"] = NAVER_EMAIL
    msg["To"] = TO_EMAIL
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain", "utf-8"))

    try:
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT_SSL) as smtp:
            smtp.login(NAVER_EMAIL, NAVER_APP_PASSWORD)
            smtp.send_message(msg)
        print(f"[M5] 이메일 전송 완료 → {TO_EMAIL}")
    except Exception as e:
        print("[M5] 이메일 전송 실패:", e)


def main():
    init_db()

    html = fetch_html(LIST_URL)
    notices = parse_top_notices(html, limit=5)

    print("[M1] fetched html length:", len(html))
    print("[M2] parsed notices:", len(notices))

    new_items = save_notices_and_collect_new(notices)
    print("[M4] NEW detected:", len(new_items))

    # 콘솔 NEW 표시
    for (_, title, date, link) in new_items:
        print(f"NEW | {date} | {title} | {link}")

    # M5: 이메일 알림
    send_email_for_new_items(new_items)

    # 참고 출력(현재 파싱된 상위 목록)
    for i, (_, title, date, link) in enumerate(notices, 1):
        print(f"{i}. {title}")
        print(f"   date: {date}")
        print(f"   {link}")


if __name__ == "__main__":
    main()