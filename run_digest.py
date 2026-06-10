"""GitHub Actions 일일 자동 실행 스크립트 (평일 + 공휴일 제외)"""
import os
import sys
from datetime import date

# Google 서비스 계정 JSON을 환경변수에서 파일로 저장
google_creds = os.getenv("GOOGLE_CREDENTIALS_JSON", "")
if google_creds:
    with open("google_credentials.json", "w", encoding="utf-8") as f:
        f.write(google_creds)

# .env 없이 환경변수 직접 사용 (GitHub Actions에서는 Secrets로 주입)
import database, scraper, ai_guide, notifier, sheets

def is_workday() -> bool:
    import holidays
    today = date.today()
    if today.weekday() >= 5:
        print(f"[skip] 주말 ({today})")
        return False
    kr_holidays = holidays.SouthKorea(years=today.year)
    if today in kr_holidays:
        print(f"[skip] 공휴일 ({today}: {kr_holidays[today]})")
        return False
    return True

def main():
    if not is_workday():
        sys.exit(0)

    today_str = date.today().strftime("%Y-%m-%d")
    print(f"[start] {today_str} 다이제스트 실행")

    # DB 및 Sheets 초기화
    database.init_db()
    sheets.init_sheets()

    # 키워드 수집
    keywords = sheets.get_all_active_keywords()
    print(f"[collect] 키워드 {len(keywords)}개 검색 시작")
    results = scraper.search_all_keywords(keywords)

    # 중복 방지: 이전에 수집된 URL 제외
    seen_urls = sheets.get_seen_urls()
    new_results = [item for item in results if item["url"] not in seen_urls]
    print(f"[collect] 전체 {len(results)}개 중 신규 {len(new_results)}개 (중복 {len(results) - len(new_results)}개 제외)")

    saved = sum(
        1 for item in new_results
        if database.save_question(item["url"], item["title"], item["description"], item["keyword"])
    )
    sheets.save_seen_urls(new_results)
    print(f"[collect] 신규 질문 {saved}개 저장")

    # 완성 답변 생성 (오늘 신규 수집분만)
    grouped = database.get_questions_for_digest(today_str)
    all_q = [q for qs in grouped.values() for q in qs]
    print(f"[ai] 완성 답변 생성 중 ({len(all_q)}개)...")
    answers = ai_guide.generate_all_answers(all_q) if all_q else []
    print(f"[ai] 씨드 질문 생성 중...")
    seeds = ai_guide.generate_daily_seed_questions()

    # 이메일 발송
    ok = notifier.send_daily_digest(grouped, today_str, answers=answers, seeds=seeds)
    print(f"[email] 발송 {'성공' if ok else '실패'}")

if __name__ == "__main__":
    main()
