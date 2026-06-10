"""Claude API 기반 답변 가이드, 씨드 질문, 일일 추천 생성"""
import json
import re
from datetime import date
import anthropic
import config

_client = None


def get_client():
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
    return _client


def _call(prompt: str, max_tokens: int = 1200) -> str:
    if not config.ANTHROPIC_API_KEY:
        return "⚠️ ANTHROPIC_API_KEY가 설정되지 않았습니다."
    msg = get_client().messages.create(
        model="claude-sonnet-4-6",
        max_tokens=max_tokens,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def _parse_json(text: str, fallback: list) -> list:
    """응답 텍스트에서 JSON 배열 추출. 실패 시 fallback 반환."""
    match = re.search(r"\[.*?\]", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass
    return fallback


# ── 1. 개별 질문 답변 가이드 ──────────────────────────────────────────────────

def generate_answer_guide(title: str, description: str, keyword: str) -> str:
    """지식인 질문에 대한 테리크 브랜드 답변 가이드 생성."""
    return _call(f"""당신은 {config.BRAND_NAME} 수건 브랜드의 마케팅 담당자입니다.

[브랜드 정보]
{config.BRAND_DESCRIPTION}

[네이버 지식인 질문]
제목: {title}
내용: {description or "(내용 없음)"}
유입 키워드: {keyword}

아래 형식으로 답변 가이드를 작성해주세요.

## 📌 답변 전략
이 질문에 어떻게 접근할지 1~2줄 요약

## ✅ 핵심 포인트
- 포인트 1
- 포인트 2
- 포인트 3

## 💬 추천 답변 템플릿
(지식인에 바로 올릴 수 있는 완성형 답변. 테리크를 자연스럽게 언급. 300~400자.
답변 마지막에 아래 링크를 자연스럽게 포함:
테리크 스마트스토어: {config.BRAND_PRODUCT_URL})

## ⚠️ 주의사항
답변 시 지켜야 할 점 1~2가지

규칙: 질문자에게 실질적 도움 우선 / 광고 느낌 최소화 / 친근하고 신뢰감 있는 말투
""")


# ── 2. 전체 수집 질문 완성 답변 생성 ─────────────────────────────────────────

def generate_all_answers(all_questions: list[dict]) -> list[dict]:
    """
    수집된 모든 질문에 대해 바로 사용할 완성 답변 생성 (최대 20개).
    Returns: [{"title", "url", "keyword", "answer"}, ...]
    """
    if not all_questions:
        return []

    questions = all_questions[:20]
    q_list = "\n".join(
        f'{i+1}. [id:{q["id"]}] [{q["keyword"]}] {q["title"]}'
        for i, q in enumerate(questions)
    )
    id_map = {q["id"]: q for q in questions}

    prompt = f"""당신은 {config.BRAND_NAME} 수건 브랜드의 마케팅 담당자입니다.

[브랜드 정보]
{config.BRAND_DESCRIPTION}

[수집된 지식인 질문 목록]
{q_list}

위 질문 전체에 대해 각각 바로 복사해서 사용할 수 있는 완성된 답변(200~300자)을 작성해주세요.

답변 조건:
- 질문자에게 진짜 도움이 되는 내용 우선
- 테리크 브랜드를 자연스럽게 1~2회 언급
- 광고티 없이 경험담처럼 자연스럽게
- 친근하고 읽기 쉬운 말투
- 답변 마지막에 반드시 아래 링크 포함: {config.BRAND_PRODUCT_URL}

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
[
  {{
    "id": (질문 id 숫자),
    "answer": "완성된 답변 텍스트"
  }}
]"""

    raw = _call(prompt, max_tokens=6000)
    parsed = _parse_json(raw, [])

    result = []
    for item in parsed:
        qid = item.get("id")
        q = id_map.get(qid)
        if q:
            result.append({
                "title": q["title"],
                "url": q["url"],
                "keyword": q["keyword"],
                "answer": item.get("answer", ""),
            })
    return result


# ── 3. 오늘의 씨드 질문 3개 ──────────────────────────────────────────────────

def generate_daily_seed_questions() -> list[dict]:
    """
    오늘 직접 지식인에 올릴 씨드 질문 3개 생성 (계절·시즌 반영).
    Returns: [{"title", "category", "content", "tip"}, ...]
    """
    month = date.today().month
    if month in [3, 4, 5]:
        season = "봄 시즌 - 졸업/입학 선물, 새 학기 준비"
    elif month in [6, 7, 8]:
        season = "여름 시즌 - 바캉스, 돌잔치·결혼 성수기"
    elif month in [9, 10, 11]:
        season = "가을 시즌 - 결혼 성수기, 추석 선물, 개업 선물"
    else:
        season = "겨울 시즌 - 연말 선물, 새해 답례품, 크리스마스"

    prompt = f"""당신은 {config.BRAND_NAME} 수건 브랜드의 마케팅 전문가입니다.

[브랜드 정보]
{config.BRAND_DESCRIPTION}

[현재 시즌]
{season}

오늘 네이버 지식인에 직접 올릴 씨드 질문 3개를 만들어주세요.

[구성 규칙 - 반드시 지킬 것]
- 질문 1, 2: 수건 관련 질문 (수건 추천, 소재, 세탁법, 브랜드 비교 등 - 서로 다른 주제)
- 질문 3: 답례품 관련 질문 (결혼/돌잔치/개업 답례품, 수량, 맞춤 제작 등)

[공통 조건]
- 일반 소비자가 실제로 궁금해할 만한 자연스러운 질문
- 답변에서 테리크를 자연스럽게 소개할 수 있는 구조
- 검색 유입이 높을 구체적인 키워드 포함
- 질문 제목 25자 이내
- 질문 본문 3~4문장 (진짜 궁금한 사람처럼, 자연스러운 말투)
- 시즌 맥락 반영

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
[
  {{
    "type": "수건",
    "title": "질문 제목 (25자 이내)",
    "category": "지식인 카테고리 (예: 생활/가정 > 욕실용품)",
    "content": "질문 본문 (3~4문장)",
    "tip": "이 질문의 마케팅 효과 한 줄",
    "seed_answer": "이 질문에 달 예상 답변 (200~300자, 테리크를 자연스럽게 1~2회 언급, 마지막에 스마트스토어 링크 포함: {config.BRAND_PRODUCT_URL})"
  }},
  {{
    "type": "수건",
    "title": "...",
    "category": "...",
    "content": "...",
    "tip": "...",
    "seed_answer": "..."
  }},
  {{
    "type": "답례품",
    "title": "...",
    "category": "...",
    "content": "...",
    "tip": "...",
    "seed_answer": "..."
  }}
]"""

    raw = _call(prompt, max_tokens=2500)
    parsed = _parse_json(raw, [])
    return parsed[:3]


# ── 4. 주간 키워드 추천 (Google Sheets 기록용) ───────────────────────────────

def generate_keyword_recommendations() -> list[dict]:
    """
    매주 네이버 지식인 모니터링 키워드 추천 (시즌·트렌드 기반).
    Returns: [{"keyword", "category", "reason"}, ...]  최대 10개
    """
    month = date.today().month
    if month in [3, 4, 5]:
        season = "봄(3~5월) - 졸업·입학 선물, 봄 결혼 성수기 시작"
    elif month in [6, 7, 8]:
        season = "여름(6~8월) - 결혼·돌잔치 성수기, 바캉스 선물"
    elif month in [9, 10, 11]:
        season = "가을(9~11월) - 결혼 성수기, 추석 선물, 개업 선물"
    else:
        season = "겨울(12~2월) - 연말·크리스마스 선물, 새해 답례품"

    prompt = f"""당신은 네이버 지식인 마케팅 전문가이자 {config.BRAND_NAME} 수건 브랜드 담당자입니다.

[브랜드]
{config.BRAND_DESCRIPTION}

[현재 시즌]
{season}

다음 한 주간 네이버 지식인에서 모니터링할 키워드 10개를 추천해주세요.

구성:
- 수건 관련 6개 (소재·추천·세탁·선물·브랜드비교 등 다양하게)
- 답례품 관련 4개 (결혼·돌잔치·개업·수량·맞춤제작 등)

조건:
- 실제 소비자가 네이버에서 검색할 법한 구체적 키워드
- 시즌 트렌드 반영
- 2~5단어 조합의 롱테일 키워드 위주 (검색량 있고 경쟁 적당한 것)
- 아래 이미 기본으로 쓰는 키워드와 겹치지 않게:
  수건 추천, 수건 선물, 답례품 수건, 결혼 답례품 수건, 돌잔치 답례품 수건

반드시 아래 JSON 형식으로만 응답하세요 (다른 텍스트 없이):
[
  {{"keyword": "키워드", "category": "수건 또는 답례품", "reason": "이 키워드를 추천하는 이유 한 줄"}},
  ...
]"""

    raw = _call(prompt, max_tokens=1500)
    parsed = _parse_json(raw, [])
    return parsed[:10]


# ── 5. 수동 씨드 질문 생성기 (대시보드용) ────────────────────────────────────

def generate_seed_questions(topic: str, count: int = 5) -> str:
    """대시보드 질문 생성기 페이지용 - 주제 지정해서 생성."""
    return _call(f"""당신은 {config.BRAND_NAME} 수건 브랜드의 마케팅 전문가입니다.

[브랜드 정보]
{config.BRAND_DESCRIPTION}

주제: {topic}
네이버 지식인에 올릴 마케팅 씨드 질문 {count}개를 만들어주세요.

조건:
- 실제 소비자가 궁금해할 법한 자연스러운 질문
- 답변에서 테리크를 자연스럽게 소개할 수 있는 구조
- 검색량이 높을 키워드 포함
- 질문 제목 25자 이내

각 질문마다 아래 형식으로:

### 질문 N
**제목:** (질문 제목)
**카테고리:** (지식인 카테고리)
**질문 내용:** (3~4문장 본문)
**마케팅 포인트:** (이 질문의 효과)
**추천 답변 키포인트:** (답변 시 언급할 내용)

---
""", max_tokens=2500)
