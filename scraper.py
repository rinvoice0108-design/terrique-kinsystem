"""Naver 지식인 검색 - 네이버 공식 검색 API 사용 (무료, 일 25,000회)"""
import requests
import config


def _clean(text: str) -> str:
    """Remove HTML bold tags from Naver API response."""
    return text.replace("<b>", "").replace("</b>", "").strip()


BRAND_WORDS = ["수건", "답례품", "타올", "타월"]

def _is_relevant(title: str) -> bool:
    """제목에 브랜드 핵심 단어(수건/답례품)가 포함된 질문만 수집."""
    return any(w in title for w in BRAND_WORDS)




def search_kin(keyword: str, display: int = 3) -> list[dict]:
    """
    Returns list of dicts: {title, url, description, keyword}
    Returns empty list on API error or missing credentials.
    """
    if not config.NAVER_CLIENT_ID or not config.NAVER_CLIENT_SECRET:
        print("[scraper] 네이버 API 키가 설정되지 않았습니다.")
        return []

    try:
        resp = requests.get(
            "https://openapi.naver.com/v1/search/kin.json",
            headers={
                "X-Naver-Client-Id": config.NAVER_CLIENT_ID,
                "X-Naver-Client-Secret": config.NAVER_CLIENT_SECRET,
            },
            params={"query": keyword, "display": display, "sort": "date"},
            timeout=10,
        )
    except requests.RequestException as e:
        print(f"[scraper] 네트워크 오류: {e}")
        return []

    if resp.status_code != 200:
        print(f"[scraper] API 오류 {resp.status_code}: {resp.text[:200]}")
        return []

    items = resp.json().get("items", [])
    results = []
    for item in items:
        if not item.get("link", "").startswith("https://kin.naver.com"):
            continue
        title = _clean(item.get("title", ""))
        description = _clean(item.get("description", ""))
        pub_date = item.get("pubDate", "")
        if not _is_relevant(title):
            continue
        results.append({"title": title, "url": item["link"], "description": description, "keyword": keyword})
    return results


def search_all_keywords(keywords: list[dict]) -> list[dict]:
    """키워드 병렬 검색 - 모든 키워드를 동시에 호출해서 속도 향상."""
    from concurrent.futures import ThreadPoolExecutor, as_completed
    results = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = {executor.submit(search_kin, kw["keyword"]): kw for kw in keywords}
        for future in as_completed(futures):
            results.extend(future.result())
    return results
