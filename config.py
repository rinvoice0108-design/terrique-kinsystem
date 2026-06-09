import os
from dotenv import load_dotenv

load_dotenv()

NAVER_CLIENT_ID = os.getenv("NAVER_CLIENT_ID", "")
NAVER_CLIENT_SECRET = os.getenv("NAVER_CLIENT_SECRET", "")

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

EMAIL_SENDER = os.getenv("EMAIL_SENDER", "")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "")
EMAIL_RECIPIENT = os.getenv("EMAIL_RECIPIENT", "")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

# 수집 시각: 하루 1회 (기본 저녁 11시)
COLLECT_HOUR = int(os.getenv("COLLECT_HOUR", "23"))

# 일일 다이제스트 발송 시각 (기본 오전 9시)
DIGEST_HOUR = int(os.getenv("DIGEST_HOUR", "9"))

# 주간 AI 키워드 추천 요일·시각 (기본 월요일 오전 8시)
KEYWORD_RECO_DAY  = os.getenv("KEYWORD_RECO_DAY", "mon")
KEYWORD_RECO_HOUR = int(os.getenv("KEYWORD_RECO_HOUR", "8"))

SECRET_KEY    = os.getenv("SECRET_KEY", "terik-kin-secret-2024")
DATABASE_PATH = "kin_monitor.db"

# ── Google Sheets ──────────────────────────────────────────────────────────────
# 구글 서비스 계정 JSON 파일 경로 (프로젝트 폴더에 저장)
GOOGLE_CREDENTIALS_PATH = os.getenv("GOOGLE_CREDENTIALS_PATH", "google_credentials.json")
# 구글 시트 ID (URL에서 /d/ 뒤의 긴 문자열)
GOOGLE_SHEET_ID = os.getenv("GOOGLE_SHEET_ID", "")
# 구글 시트 URL (대시보드에서 바로가기용)
GOOGLE_SHEET_URL = (
    f"https://docs.google.com/spreadsheets/d/{GOOGLE_SHEET_ID}"
    if GOOGLE_SHEET_ID else ""
)

BRAND_NAME = "테리크"
BRAND_PRODUCT_URL = "https://smartstore.naver.com/terrique/products/10902513336"
BRAND_DESCRIPTION = """
- 브랜드명: 테리크 (Terrique)
- 태그라인: Colorful Classic, Terrique
- 슬로건: 변하지 않는 클래식에, 다채로운 색감을 더하다
- 핵심 가치: 컬러풀 클래식 (Colorful Classic)
- 브랜드 존재 이유: 지루하고 단조로운 공간에 클래식한 디자인과 다채로운 색감을 더해, 매일의 일상에 기분 좋은 감정이 흐르게 만드는 것
- 미션: 가장 익숙한 클래식 디자인에 다채로운 컬러 플레이를 더해, 누구나 일상 속에서 가장 쉽고 직관적으로 아름다움을 누리게 만드는 것. 컬러풀 클래식이라는 독보적인 장르를 개척하고 전 세계의 가장 프라이빗한 순간을 책임지는 유일무이한 시그니처 브랜드가 되는 것
- 카테고리: 프리미엄 수건 전문 브랜드
- 주요 제품: 순면 타월, 호텔식 수건, 답례품 수건 세트, 자수/인쇄 맞춤 수건
- 답례품 종류: 결혼 답례품, 돌잔치 답례품, 개업 선물, 기념품
- 강점: 클래식 디자인 + 다채로운 컬러, 부드럽고 흡수력 뛰어난 코튼 소재, 맞춤 인쇄/자수 서비스, 소량 주문 가능
- 생산: 해외 생산 (고품질 관리)
- 가격대: 합리적인 프리미엄
- 스마트스토어: https://smartstore.naver.com/terrique/products/10902513336
"""

# Google Sheets 연동 전 DB 폴백용 기본 키워드
DEFAULT_KEYWORDS = [
    "수건 추천", "수건 선물", "답례품 수건", "결혼 답례품 수건",
    "돌잔치 답례품 수건", "수건 브랜드 추천", "호텔 수건 구매",
    "순면 수건 추천", "답례품 추천", "결혼 답례품 추천",
    "돌잔치 선물 추천", "개업 답례품 추천",
]
