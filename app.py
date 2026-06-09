"""테리크 네이버 지식인 모니터링 & 답변 가이드 시스템"""
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import atexit
import database
import scraper
import ai_guide
import notifier
import sheets
import config

app = Flask(__name__)
app.secret_key = config.SECRET_KEY

# ── 스케줄러 ──────────────────────────────────────────────────────────────────
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler(daemon=True)


def _is_workday() -> bool:
    """평일이고 한국 공휴일이 아닌지 확인."""
    import holidays
    from datetime import date
    today = date.today()
    if today.weekday() >= 5:  # 토(5), 일(6)
        return False
    kr_holidays = holidays.SouthKorea(years=today.year)
    return today not in kr_holidays


def run_collect_job():
    """하루 1회 수집 (저녁 11시) - Google Sheets 키워드 읽어서 DB 저장 + 가이드 미리 생성."""
    from datetime import datetime, date
    if not _is_workday():
        print(f"[collect] 주말 또는 공휴일 - 수집 건너뜀")
        return
    today = date.today().strftime("%Y-%m-%d")
    print(f"[collect] 스캔 시작 ({datetime.now().strftime('%Y-%m-%d %H:%M')})")

    keywords = sheets.get_all_active_keywords()
    if not keywords:
        print("[collect] 활성 키워드 없음")
        return

    results = scraper.search_all_keywords(keywords)
    new_count = sum(
        1 for item in results
        if database.save_question(item["url"], item["title"], item["description"], item["keyword"])
    )
    print(f"[collect] 저장 완료 - 키워드 {len(keywords)}개 / 신규 질문 {new_count}개")

    # 가이드 생성은 백그라운드 스레드에서 처리
    if new_count > 0:
        import threading
        def _generate_guides():
            grouped = database.get_questions_for_digest(today)
            no_guide = [q for qs in grouped.values() for q in qs if not q.get("answer_guide")]
            print(f"[collect] 답변 가이드 미리 생성 중 ({len(no_guide)}개)...")
            for q in no_guide:
                guide = ai_guide.generate_answer_guide(q["title"], q["content"], q["keyword"])
                database.save_answer_guide(q["id"], guide)
            print(f"[collect] 가이드 생성 완료")
        threading.Thread(target=_generate_guides, daemon=True).start()

    print(f"[collect] 완료")


def run_digest_job():
    """매일 오전 9시 (평일+공휴일 제외): 수집 질문 완성답변 + 씨드 질문 - 이메일 발송."""
    from datetime import date, timedelta
    if not _is_workday():
        print(f"[digest] 주말 또는 공휴일 - 발송 건너뜀")
        return
    yesterday = (date.today() - timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"[digest] {yesterday} 다이제스트 생성 시작")

    grouped = database.get_questions_for_digest(yesterday)
    total = sum(len(v) for v in grouped.values())

    # ① 개별 가이드 생성
    for questions in grouped.values():
        for q in questions:
            if not q.get("answer_guide"):
                print(f"  [가이드] {q['title'][:35]}...")
                guide = ai_guide.generate_answer_guide(q["title"], q["content"], q["keyword"])
                database.save_answer_guide(q["id"], guide)
                q["answer_guide"] = guide

    # ② 전체 질문 완성 답변 생성
    all_q_flat = [q for qs in grouped.values() for q in qs]
    print(f"  [완성 답변] {len(all_q_flat)}개 답변 생성 중...")
    answers = ai_guide.generate_all_answers(all_q_flat) if all_q_flat else []

    # ③ 씨드 질문 3개 (수건 2 + 답례품 1)
    print(f"  [씨드 질문] 생성 중...")
    seeds = ai_guide.generate_daily_seed_questions()

    # ④ 발송
    grouped = database.get_questions_for_digest(yesterday)
    notifier.send_daily_digest(grouped, yesterday, answers=answers, seeds=seeds)
    print(f"[digest] 완료 - 수집 {total}건 / 완성답변 {len(answers)}개 / 씨드 {len(seeds)}개")


def run_weekly_keyword_job():
    """매주 월요일 오전 8시: Claude가 키워드 추천 → Google Sheets 기록."""
    from datetime import date
    iso = date.today().isocalendar()
    print(f"[keyword] {iso[0]}년 {iso[1]}주차 키워드 추천 생성 시작")

    recommendations = ai_guide.generate_keyword_recommendations()
    if recommendations:
        ok = sheets.write_ai_recommendations(recommendations)
        if ok:
            print(f"[keyword] {len(recommendations)}개 추천 키워드 → Google Sheets 기록 완료")
        else:
            print(f"[keyword] Google Sheets 기록 실패")
    else:
        print("[keyword] 추천 키워드 생성 실패")


# 하루 1회 수집 - 저녁 11시
scheduler.add_job(run_collect_job, "cron", hour=config.COLLECT_HOUR, minute=0, id="collect")

# 매일 오전 9시 - 다이제스트 이메일 발송
scheduler.add_job(run_digest_job, "cron", hour=config.DIGEST_HOUR, minute=0, id="daily_digest")

# 매주 월요일 오전 8시 - AI 키워드 추천 → Google Sheets
scheduler.add_job(
    run_weekly_keyword_job, "cron",
    day_of_week=config.KEYWORD_RECO_DAY,
    hour=config.KEYWORD_RECO_HOUR, minute=0,
    id="weekly_keywords",
)

scheduler.start()
atexit.register(lambda: scheduler.shutdown(wait=False))


# ── 초기화 ────────────────────────────────────────────────────────────────────
database.init_db()
sheets.init_sheets()   # Google Sheets 탭 구조 생성 (최초 1회)


# ── 라우트 ────────────────────────────────────────────────────────────────────

@app.route("/")
def dashboard():
    questions = database.get_questions(limit=100)
    unread_count = database.get_unread_count()
    sheet_stats = sheets.get_sheet_stats()
    return render_template(
        "dashboard.html",
        questions=questions,
        unread_count=unread_count,
        sheet_stats=sheet_stats,
    )


@app.route("/question/<int:qid>")
def question_detail(qid):
    q = database.get_question(qid)
    if not q:
        flash("질문을 찾을 수 없습니다.", "danger")
        return redirect(url_for("dashboard"))
    database.mark_as_read(qid)
    return render_template("question_detail.html", q=q)


@app.route("/api/guide/<int:qid>")
def api_guide(qid):
    """가이드 조회 - 없으면 생성 후 반환."""
    q = database.get_question(qid)
    if not q:
        return jsonify({"error": "not found"}), 404
    if not q.get("answer_guide"):
        guide = ai_guide.generate_answer_guide(q["title"], q["content"], q["keyword"])
        database.save_answer_guide(qid, guide)
        return jsonify({"guide": guide})
    return jsonify({"guide": q["answer_guide"]})


@app.route("/seed-questions", methods=["GET", "POST"])
def seed_questions():
    result = None
    topic = ""
    history = database.get_seed_results(limit=5)

    if request.method == "POST":
        topic = request.form.get("topic", "").strip()
        count = int(request.form.get("count", 5))
        if topic:
            result = ai_guide.generate_seed_questions(topic, count)
            database.save_seed_result(topic, result)

    return render_template("seed_questions.html", result=result, topic=topic, history=history)


@app.route("/keywords")
def keywords():
    """Google Sheets 키워드 현황 페이지."""
    sheet_stats = sheets.get_sheet_stats()
    active_keywords = sheets.get_all_active_keywords()
    manual = [k for k in active_keywords if k["source"] == "manual"]
    ai_kws = [k for k in active_keywords if k["source"] == "ai"]
    return render_template(
        "keywords.html",
        sheet_stats=sheet_stats,
        manual=manual,
        ai_kws=ai_kws,
    )


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/scan", methods=["POST"])
def api_scan():
    run_collect_job()
    return jsonify({"status": "ok", "unread": database.get_unread_count()})


@app.route("/api/send-digest", methods=["POST"])
def api_send_digest():
    from datetime import date
    data = request.get_json(silent=True) or {}
    target = data.get("date") or date.today().strftime("%Y-%m-%d")

    grouped = database.get_questions_for_digest(target)
    for questions in grouped.values():
        for q in questions:
            if not q.get("answer_guide"):
                guide = ai_guide.generate_answer_guide(q["title"], q["content"], q["keyword"])
                database.save_answer_guide(q["id"], guide)
                q["answer_guide"] = guide

    all_q_flat = [q for qs in grouped.values() for q in qs]
    answers = ai_guide.generate_all_answers(all_q_flat) if all_q_flat else []
    seeds = ai_guide.generate_daily_seed_questions()
    grouped = database.get_questions_for_digest(target)
    ok = notifier.send_daily_digest(grouped, target, answers=answers, seeds=seeds)
    total = sum(len(v) for v in grouped.values())
    return jsonify({"status": "ok" if ok else "error", "date": target,
                    "total": total, "answers": len(answers), "seeds": len(seeds)})


@app.route("/api/run-keyword-reco", methods=["POST"])
def api_run_keyword_reco():
    """수동으로 AI 키워드 추천 실행 → Google Sheets 기록."""
    run_weekly_keyword_job()
    stats = sheets.get_sheet_stats()
    return jsonify({"status": "ok", "ai_count": stats.get("ai_count", 0)})


@app.route("/api/regenerate/<int:qid>", methods=["POST"])
def api_regenerate(qid):
    q = database.get_question(qid)
    if not q:
        return jsonify({"error": "not found"}), 404
    guide = ai_guide.generate_answer_guide(q["title"], q["content"], q["keyword"])
    database.save_answer_guide(qid, guide)
    return jsonify({"guide": guide})


@app.route("/api/unread")
def api_unread():
    return jsonify({"count": database.get_unread_count()})


@app.route("/api/clear-questions", methods=["POST"])
def api_clear_questions():
    """질문 DB 전체 초기화."""
    conn = database.get_conn()
    conn.execute("DELETE FROM questions")
    conn.commit()
    conn.close()
    return jsonify({"status": "ok"})


if __name__ == "__main__":
    print("=" * 55)
    print("  테리크 지식인 모니터링 시스템")
    print(f"  http://localhost:5000")
    print(f"  수집:       매일 저녁 {config.COLLECT_HOUR}시")
    print(f"  발송:       매일 오전 {config.DIGEST_HOUR}시")
    print(f"  키워드 추천: 매주 월요일 오전 {config.KEYWORD_RECO_HOUR}시 → Google Sheets")
    print("=" * 55)
    app.run(debug=False, port=5000)
