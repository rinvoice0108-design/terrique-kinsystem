"""
Google Sheets 연동 - 키워드 관리 대시보드

시트 구조:
  탭1 "내 키워드"       - 직접 입력/수정
  탭2 "AI 추천 키워드"  - Claude가 매주 자동 기록
"""
import os
from datetime import date
import gspread
from google.oauth2.service_account import Credentials
import config

SCOPES = ["https://www.googleapis.com/auth/spreadsheets"]

_gc = None


def _is_configured() -> bool:
    return bool(config.GOOGLE_SHEET_ID and os.path.exists(config.GOOGLE_CREDENTIALS_PATH))


def _get_gc():
    global _gc
    if _gc is None:
        creds = Credentials.from_service_account_file(
            config.GOOGLE_CREDENTIALS_PATH, scopes=SCOPES
        )
        _gc = gspread.authorize(creds)
    return _gc


def _get_ss():
    return _get_gc().open_by_key(config.GOOGLE_SHEET_ID)


# ── 초기화 ────────────────────────────────────────────────────────────────────

def init_sheets() -> bool:
    """
    최초 실행 시 탭 구조 + 헤더 + 기본 키워드 생성.
    이미 존재하면 건너뜀. 성공 여부 반환.
    """
    if not _is_configured():
        print("[sheets] Google Sheets 미설정 - .env의 GOOGLE_SHEET_ID, GOOGLE_CREDENTIALS_PATH 확인")
        return False

    try:
        ss = _get_ss()
        today = date.today().strftime("%Y-%m-%d")

        # ── 탭1: 내 키워드 ──────────────────────────────────────────────────
        try:
            ws1 = ss.worksheet("내 키워드")
            print("[sheets] '내 키워드' 탭 이미 존재")
        except gspread.exceptions.WorksheetNotFound:
            ws1 = ss.add_worksheet("내 키워드", rows=300, cols=5)

            # 헤더
            ws1.append_row(["키워드", "분류", "추가일", "활성(O/X)", "메모"])
            ws1.format("A1:E1", {
                "backgroundColor": {"red": 0.13, "green": 0.45, "blue": 0.91},
                "textFormat": {
                    "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                    "bold": True,
                    "fontSize": 11,
                },
                "horizontalAlignment": "CENTER",
            })

            # 기본 키워드 (수건 8개 + 답례품 4개)
            defaults = [
                ["수건 추천",         "수건",  today, "O", ""],
                ["수건 선물",         "수건",  today, "O", ""],
                ["순면 수건 추천",    "수건",  today, "O", ""],
                ["수건 브랜드 추천",  "수건",  today, "O", ""],
                ["호텔 수건 구매",    "수건",  today, "O", ""],
                ["수건 선물 세트",    "수건",  today, "O", ""],
                ["면 수건 추천",      "수건",  today, "O", ""],
                ["수건 세탁 방법",    "수건",  today, "O", ""],
                ["답례품 수건",       "답례품", today, "O", ""],
                ["결혼 답례품 수건",  "답례품", today, "O", ""],
                ["돌잔치 답례품 수건","답례품", today, "O", ""],
                ["답례품 추천",       "답례품", today, "O", ""],
                ["결혼 답례품 추천",  "답례품", today, "O", ""],
                ["돌잔치 선물 추천",  "답례품", today, "O", ""],
                ["개업 답례품 추천",  "답례품", today, "O", ""],
            ]
            ws1.append_rows(defaults)

            # 분류별 행 색상 (수건=하늘, 답례품=연보라)
            ws1.format("A2:E9", {"backgroundColor": {"red": 0.88, "green": 0.94, "blue": 1.0}})
            ws1.format("A10:E16", {"backgroundColor": {"red": 0.94, "green": 0.88, "blue": 1.0}})

            print("[sheets] '내 키워드' 탭 생성 완료")

        # ── 탭2: AI 추천 키워드 ─────────────────────────────────────────────
        try:
            ss.worksheet("AI 추천 키워드")
            print("[sheets] 'AI 추천 키워드' 탭 이미 존재")
        except gspread.exceptions.WorksheetNotFound:
            ws2 = ss.add_worksheet("AI 추천 키워드", rows=500, cols=6)

            ws2.append_row(["키워드", "분류", "추천 이유", "추천일", "활성(O/X)", "주차"])
            ws2.format("A1:F1", {
                "backgroundColor": {"red": 0.35, "green": 0.18, "blue": 0.60},
                "textFormat": {
                    "foregroundColor": {"red": 1.0, "green": 1.0, "blue": 1.0},
                    "bold": True,
                    "fontSize": 11,
                },
                "horizontalAlignment": "CENTER",
            })
            print("[sheets] 'AI 추천 키워드' 탭 생성 완료")

        return True

    except Exception as e:
        print(f"[sheets] 초기화 실패: {e}")
        return False


# ── 키워드 읽기 ───────────────────────────────────────────────────────────────

def get_all_active_keywords() -> list[dict]:
    """
    두 탭의 활성(O) 키워드를 합쳐서 반환.
    Google Sheets 미설정 시 config.DEFAULT_KEYWORDS 폴백.
    Returns: [{"keyword": str, "source": "manual" | "ai"}, ...]
    """
    if not _is_configured():
        print("[sheets] 폴백: config.DEFAULT_KEYWORDS 사용")
        return [{"keyword": kw, "source": "manual"} for kw in config.DEFAULT_KEYWORDS]

    try:
        ss = _get_ss()
        result = []

        ws = ss.worksheet("내 키워드")
        for row in ws.get_all_records():
            kw = str(row.get("키워드", "")).strip()
            active = str(row.get("활성(O/X)", "O")).strip().upper()
            if kw and active == "O":
                result.append({"keyword": kw, "source": "manual"})

        print(f"[sheets] 키워드 {len(result)}개 로드 (내 키워드)")
        return result

    except Exception as e:
        print(f"[sheets] 키워드 로드 실패: {e} - 기본 키워드 사용")
        return [{"keyword": kw, "source": "manual"} for kw in config.DEFAULT_KEYWORDS]


# ── AI 추천 키워드 쓰기 ───────────────────────────────────────────────────────

def write_ai_recommendations(recommendations: list[dict]) -> bool:
    """
    Claude가 생성한 키워드 추천을 'AI 추천 키워드' 탭에 추가.
    recommendations: [{"keyword", "category", "reason"}, ...]
    """
    if not _is_configured():
        print("[sheets] Google Sheets 미설정 - AI 추천 키워드 저장 불가")
        return False

    try:
        ss = _get_ss()
        ws = ss.worksheet("AI 추천 키워드")
        today = date.today()
        iso = today.isocalendar()
        week_str = f"{iso[0]}년 {iso[1]}주차"

        rows = [
            [r.get("keyword", ""), r.get("category", ""), r.get("reason", ""),
             today.strftime("%Y-%m-%d"), "O", week_str]
            for r in recommendations
        ]
        ws.append_rows(rows)

        # 새로 추가된 행에 연한 초록 배경
        last_row = len(ws.get_all_values())
        first_new = last_row - len(rows) + 1
        ws.format(
            f"A{first_new}:F{last_row}",
            {"backgroundColor": {"red": 0.88, "green": 0.97, "blue": 0.88}},
        )

        print(f"[sheets] AI 추천 키워드 {len(rows)}개 추가 - {week_str}")
        return True

    except Exception as e:
        print(f"[sheets] AI 키워드 쓰기 실패: {e}")
        return False


def get_sheet_stats() -> dict:
    """대시보드 표시용 통계 반환."""
    if not _is_configured():
        return {"configured": False}

    try:
        ss = _get_ss()
        ws1 = ss.worksheet("내 키워드")
        ws2 = ss.worksheet("AI 추천 키워드")

        manual_rows  = [r for r in ws1.get_all_records() if str(r.get("활성(O/X)", "O")).upper() == "O" and r.get("키워드")]
        ai_rows      = [r for r in ws2.get_all_records() if str(r.get("활성(O/X)", "O")).upper() == "O" and r.get("키워드")]

        return {
            "configured": True,
            "manual_count": len(manual_rows),
            "ai_count": len(ai_rows),
            "total": len(manual_rows) + len(ai_rows),
            "sheet_url": config.GOOGLE_SHEET_URL,
        }
    except Exception as e:
        return {"configured": True, "error": str(e)}
