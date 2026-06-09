"""일일 다이제스트 이메일 - 추천 답변 3개 + 씨드 질문 3개 + 전체 수집 질문 + 가이드"""
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import config


# ── HTML 유틸 ─────────────────────────────────────────────────────────────────

def _md_to_html(text: str) -> str:
    """마크다운 → 이메일용 인라인 HTML 변환."""
    lines = text.split("\n")
    out = []
    in_ul = False

    for line in lines:
        s = line.strip()
        if not s:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append("<br>")
            continue
        if s.startswith("## "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f'<p style="font-weight:700;color:#1e293b;margin:14px 0 4px;border-bottom:1px solid #e2e8f0;padding-bottom:4px;">{s[3:]}</p>')
        elif s.startswith("### "):
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f'<p style="font-weight:600;color:#334155;margin:10px 0 3px;">{s[4:]}</p>')
        elif s.startswith(("- ", "* ")):
            if not in_ul:
                out.append('<ul style="margin:4px 0;padding-left:18px;">')
                in_ul = True
            out.append(f'<li style="margin-bottom:4px;color:#374151;">{s[2:]}</li>')
        else:
            if in_ul:
                out.append("</ul>")
                in_ul = False
            out.append(f'<p style="margin:4px 0;color:#374151;line-height:1.7;">{s}</p>')

    if in_ul:
        out.append("</ul>")
    return "\n".join(out)


def _section_header(emoji: str, title: str, subtitle: str, color: str) -> str:
    return f"""
    <div style="margin:28px 0 16px;padding:14px 20px;background:{color};border-radius:10px;">
      <div style="font-size:18px;font-weight:700;color:#0f172a;">{emoji} {title}</div>
      <div style="font-size:13px;color:#475569;margin-top:3px;">{subtitle}</div>
    </div>
    """


# ── 섹션 빌더 ────────────────────────────────────────────────────────────────

def _build_all_answers_section(answers: list[dict]) -> str:
    """수집된 전체 질문 완성 답변 섹션."""
    if not answers:
        return ""

    cards = ""
    for i, item in enumerate(answers, 1):
        answer_text = (item.get("answer") or "").replace("\n", "<br>")
        cards += f"""
        <div style="margin-bottom:20px;border:2px solid #dcfce7;border-radius:10px;overflow:hidden;">
          <div style="background:#f0fdf4;padding:12px 18px;border-bottom:1px solid #dcfce7;">
            <div style="font-size:11px;color:#16a34a;font-weight:700;margin-bottom:3px;letter-spacing:.5px;">
              #{i} &nbsp;·&nbsp; {item.get('keyword','')}
            </div>
            <div style="font-size:15px;font-weight:600;color:#0f172a;">{item.get('title','')}</div>
          </div>
          <div style="background:white;padding:10px 18px;border-bottom:1px solid #dcfce7;">
            <a href="{item.get('url','#')}"
               style="background:#03c75a;color:white;padding:7px 16px;border-radius:6px;
                      text-decoration:none;font-size:13px;font-weight:700;">
              네이버 지식인 답변 달기
            </a>
          </div>
          <div style="background:#fafffe;padding:16px 18px;">
            <div style="font-size:11px;font-weight:700;color:#16a34a;letter-spacing:.5px;margin-bottom:8px;">
              완성 답변 (복사 후 바로 붙여넣기)
            </div>
            <div style="background:white;border:1px solid #dcfce7;border-radius:8px;padding:14px;
                        font-size:13px;line-height:1.8;color:#1e293b;white-space:pre-wrap;">{answer_text}</div>
          </div>
        </div>
        """

    return _section_header("📋", "수집 질문 완성 답변", f"총 {len(answers)}개 질문 - 복사 후 바로 답변 달기", "#f0fdf4") + cards


def _build_seeds_section(seeds: list[dict]) -> str:
    """오늘 직접 올릴 씨드 질문 3개 섹션."""
    if not seeds:
        return ""

    # 타입별 뱃지 색상
    TYPE_STYLE = {
        "수건":  ("🧴", "#e0f2fe", "#0369a1", "#bae6fd"),
        "답례품": ("🎁", "#fef3c7", "#92400e", "#fde68a"),
    }

    cards = ""
    for i, s in enumerate(seeds, 1):
        content_text = (s.get("content") or "").replace("\n", "<br>")
        q_type = s.get("type", "수건")
        emoji, bg, text_color, border = TYPE_STYLE.get(q_type, TYPE_STYLE["수건"])

        cards += f"""
        <div style="margin-bottom:20px;border:2px solid {border};border-radius:10px;overflow:hidden;">
          <!-- 제목 -->
          <div style="background:{bg};padding:12px 18px;border-bottom:2px solid {border};">
            <div style="display:inline-block;background:{border};color:{text_color};
                        font-size:11px;font-weight:700;padding:2px 8px;border-radius:4px;margin-bottom:6px;">
              {emoji} {q_type} 질문 &nbsp;#{i}
            </div>
            <div style="font-size:15px;font-weight:700;color:#0f172a;">{s.get('title','')}</div>
            <div style="font-size:12px;color:#6b7280;margin-top:4px;">
              📂 카테고리: {s.get('category','')}
            </div>
          </div>
          <!-- 질문 본문 -->
          <div style="background:white;padding:14px 18px;border-bottom:1px solid {border};">
            <div style="font-size:11px;font-weight:700;color:{text_color};margin-bottom:6px;">질문 내용 (복사해서 그대로 올리기)</div>
            <div style="background:{bg};border:1px solid {border};border-radius:8px;padding:12px;
                        font-size:13px;line-height:1.8;color:#1e293b;">{content_text}</div>
          </div>
          <!-- 마케팅 포인트 -->
          <div style="background:white;padding:10px 18px;">
            <div style="font-size:12px;color:{text_color};">
              💡 마케팅 효과: {s.get('tip','')}
            </div>
          </div>
        </div>
        """

    return _section_header("🌱", "오늘의 씨드 질문", "수건 2개 · 답례품 1개 - 복사해서 바로 지식인에 올리세요", "#fefce8") + cards


def _build_collected_section(grouped: dict, total: int, top3_urls: set = None) -> str:
    """수집 질문 중 추천 답변 3개를 제외한 나머지를 간단한 목록으로 표시."""
    top3_urls = top3_urls or set()
    rows = ""
    idx = 1
    for keyword, questions in grouped.items():
        for q in questions:
            if q.get("url") in top3_urls:
                continue
            rows += f"""
            <tr>
              <td style="padding:10px 14px;border-bottom:1px solid #f1f5f9;font-size:13px;color:#1e293b;">
                {idx}. {q.get('title','')}
                <span style="font-size:11px;color:#94a3b8;margin-left:6px;">[{keyword}]</span>
              </td>
              <td style="padding:10px 14px;border-bottom:1px solid #f1f5f9;text-align:right;white-space:nowrap;">
                <a href="{q.get('url','#')}"
                   style="background:#03c75a;color:white;padding:4px 12px;border-radius:5px;
                          text-decoration:none;font-size:11px;font-weight:600;">답변 달기</a>
              </td>
            </tr>
            """
            idx += 1

    if idx == 1:
        return ""

    header = _section_header("📋", "나머지 수집 질문", f"추천 답변 3개 외 {idx-1}건 - 추가로 답변할 질문을 골라보세요", "#f0f9ff")
    return header + f"""
    <table style="width:100%;border-collapse:collapse;background:white;border-radius:10px;overflow:hidden;border:1px solid #e2e8f0;">
      {rows}
    </table>"""


# ── 이메일 발송 ───────────────────────────────────────────────────────────────

def _sanitize(text: str) -> str:
    """CP949 인코딩 문제 문자를 ASCII 대체 문자로 교체."""
    return (text
        .replace("-", "-")   # em dash
        .replace("–", "-")   # en dash
        .replace("’", "'")   # right single quote
        .replace("‘", "'")   # left single quote
        .replace("“", '"')   # left double quote
        .replace("”", '"')   # right double quote
        .replace("…", "...")  # ellipsis
        .replace("·", "·")   # middle dot (keep as-is, safe in UTF-8 email)
    )


def _send_html(subject: str, html: str) -> bool:
    if not config.EMAIL_SENDER or not config.EMAIL_PASSWORD:
        print("[notifier] 이메일 설정이 없습니다. .env 파일을 확인하세요.")
        return False
    subject = _sanitize(subject)
    html = _sanitize(html)

    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = config.EMAIL_SENDER
    msg["To"] = config.EMAIL_RECIPIENT
    msg.attach(MIMEText(html, "html", "utf-8"))

    try:
        with smtplib.SMTP(config.SMTP_SERVER, config.SMTP_PORT) as server:
            server.starttls()
            server.login(config.EMAIL_SENDER, config.EMAIL_PASSWORD)
            server.sendmail(config.EMAIL_SENDER, config.EMAIL_RECIPIENT, msg.as_string())
        print(f"[notifier] 발송 완료: {subject}")
        return True
    except Exception as e:
        print(f"[notifier] 발송 실패: {e}")
        return False


def send_daily_digest(
    grouped: dict[str, list],
    target_date: str,
    answers: list[dict] | None = None,
    seeds: list[dict] | None = None,
) -> bool:
    """
    grouped     : {keyword: [question_dict, ...]}
    target_date : "YYYY-MM-DD"
    answers     : 전체 질문 완성 답변 [{title, url, keyword, answer}]
    seeds       : 씨드 질문 3개 [{title, category, content, tip}]
    """
    total = sum(len(v) for v in grouped.values())
    answers = answers or []
    seeds = seeds or []

    if total == 0 and not answers and not seeds:
        print("[notifier] 발송할 내용 없음")
        return True

    month = int(target_date[5:7])
    day   = int(target_date[8:10])
    display_date = f"{month}월 {day}일"

    # ── 섹션 구성 ─────────────────────────────────────────────────────────────
    s1 = _build_all_answers_section(answers)
    s2 = _build_seeds_section(seeds)
    s3 = ""  # 나머지 목록 불필요

    # ── 요약 통계 ─────────────────────────────────────────────────────────────
    stats = " / ".join(filter(None, [
        f"수집 질문 <strong style='color:#e94560;'>{total}건</strong>" if total else "",
        f"씨드 질문 <strong style='color:#b45309;'>{len(seeds)}개</strong>" if seeds else "",
    ]))

    html = f"""<!DOCTYPE html>
<html lang="ko">
<body style="margin:0;padding:0;background:#f1f5f9;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;">
<div style="max-width:700px;margin:24px auto;">

  <!-- 헤더 -->
  <div style="background:#0f172a;color:white;padding:28px 32px;border-radius:12px 12px 0 0;">
    <div style="font-size:12px;color:#64748b;margin-bottom:6px;letter-spacing:.5px;text-transform:uppercase;">테리크 지식인 일일 리포트</div>
    <div style="font-size:26px;font-weight:800;margin-bottom:6px;">{display_date}</div>
    <div style="color:#94a3b8;font-size:14px;">{stats}</div>
  </div>

  <!-- 사용 안내 -->
  <div style="background:#1e3a5f;padding:12px 24px;">
    <p style="margin:0;font-size:13px;color:#93c5fd;line-height:1.6;">
      ① <strong>추천 답변</strong>을 먼저 달고 &nbsp;→&nbsp;
      ② <strong>씨드 질문</strong>을 지식인에 올린 뒤 &nbsp;→&nbsp;
      ③ 나머지 수집 질문 중 더 답변할 것을 골라보세요
    </p>
  </div>

  <!-- 본문 -->
  <div style="background:#f8fafc;padding:24px;">
    {s1}
    {s2}
    {s3}
  </div>

  <!-- 푸터 -->
  <div style="background:white;padding:20px;text-align:center;border-top:1px solid #e2e8f0;border-radius:0 0 12px 12px;">
    <a href="http://localhost:5000"
       style="background:#0f172a;color:white;padding:12px 28px;border-radius:8px;
              text-decoration:none;font-size:14px;font-weight:600;">
      대시보드 전체 보기
    </a>
    <p style="margin:14px 0 0;font-size:12px;color:#94a3b8;">
      다음 리포트: 내일 오전 {config.DIGEST_HOUR}시 &nbsp;·&nbsp; 테리크 지식인 모니터링
    </p>
  </div>

</div>
</body>
</html>"""

    subject = f"[테리크 지식인] {display_date} 리포트 - 완성답변 {len(answers)}개 / 씨드질문 {len(seeds)}개 / 수집 {total}건"
    return _send_html(subject, html)
