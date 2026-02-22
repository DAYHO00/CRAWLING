# KOLIS-NET Notice Crawler

- 국회도서관 KOLIS-NET 공지사항을 크롤링하여 SQLite에 저장하고 신규 공지를 감지해 알림하는 Python 프로젝트
- https://www.nl.go.kr/kolisnet/notice/noticeList.do
---

### 🎯 Overview
- 공지 목록에서 제목 / 링크 / 작성일 추출
- SQLite 저장 및 중복 방지
- 신규 공지 감지 (Diff)
- 신규 공지 이메일 알림 (SMTP 기반)

---

### ⚙️ Tech Stack
- Python 3.11+
- requests
- beautifulsoup4
- sqlite3
- python-dotenv (optional)
- smtplib (email)

---

### 📂 Project Structure
- `src/main.py` : 크롤링 + 저장 + 알림 로직
- `notices.db` : SQLite DB (Git 제외)
- `.env` : 이메일 환경변수 (Git 제외)

---

### 🚀 Run

```bash
# 가상환경 (선택)
python -m venv .venv
.\.venv\Scripts\activate

# 패키지 설치
pip install -r requirements.txt

# 실행
python src/main.py
