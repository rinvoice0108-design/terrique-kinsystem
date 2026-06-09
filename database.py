import sqlite3
from datetime import datetime
from config import DATABASE_PATH


def get_conn():
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS questions (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            url         TEXT    UNIQUE,
            title       TEXT,
            content     TEXT,
            keyword     TEXT,
            found_at    TEXT,
            is_read     INTEGER DEFAULT 0,
            answer_guide TEXT
        );

        CREATE TABLE IF NOT EXISTS keywords (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword    TEXT UNIQUE,
            is_active  INTEGER DEFAULT 1,
            created_at TEXT
        );

        CREATE TABLE IF NOT EXISTS seed_results (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            topic      TEXT,
            result     TEXT,
            created_at TEXT
        );
    """)
    conn.commit()
    conn.close()


def save_question(url, title, content, keyword):
    """Returns True if newly inserted, False if already exists."""
    conn = get_conn()
    cur = conn.execute(
        "INSERT OR IGNORE INTO questions (url, title, content, keyword, found_at) VALUES (?,?,?,?,?)",
        (url, title, content, keyword, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    inserted = cur.rowcount > 0
    conn.commit()
    conn.close()
    return inserted


def get_questions(limit=100, unread_only=False):
    conn = get_conn()
    if unread_only:
        rows = conn.execute(
            "SELECT * FROM questions WHERE is_read=0 ORDER BY found_at DESC LIMIT ?", (limit,)
        ).fetchall()
    else:
        rows = conn.execute(
            "SELECT * FROM questions ORDER BY found_at DESC LIMIT ?", (limit,)
        ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_question(qid):
    conn = get_conn()
    row = conn.execute("SELECT * FROM questions WHERE id=?", (qid,)).fetchone()
    conn.close()
    return dict(row) if row else None


def mark_as_read(qid):
    conn = get_conn()
    conn.execute("UPDATE questions SET is_read=1 WHERE id=?", (qid,))
    conn.commit()
    conn.close()


def save_answer_guide(qid, guide):
    conn = get_conn()
    conn.execute("UPDATE questions SET answer_guide=?, is_read=1 WHERE id=?", (guide, qid))
    conn.commit()
    conn.close()


def get_unread_count():
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM questions WHERE is_read=0").fetchone()[0]
    conn.close()
    return count


def get_questions_for_digest(date_str: str) -> dict[str, list]:
    """특정 날짜(YYYY-MM-DD)에 수집된 질문을 키워드별로 그룹화하여 반환."""
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM questions WHERE found_at LIKE ? ORDER BY keyword, found_at",
        (f"{date_str}%",),
    ).fetchall()
    conn.close()

    grouped: dict[str, list] = {}
    for r in rows:
        item = dict(r)
        kw = item["keyword"]
        grouped.setdefault(kw, []).append(item)
    return grouped


def get_keywords():
    conn = get_conn()
    rows = conn.execute("SELECT * FROM keywords WHERE is_active=1 ORDER BY id").fetchall()
    conn.close()
    return [dict(r) for r in rows]


def add_keyword(keyword):
    conn = get_conn()
    conn.execute(
        "INSERT OR IGNORE INTO keywords (keyword, created_at) VALUES (?,?)",
        (keyword.strip(), datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()


def delete_keyword(kid):
    conn = get_conn()
    conn.execute("UPDATE keywords SET is_active=0 WHERE id=?", (kid,))
    conn.commit()
    conn.close()


def save_seed_result(topic, result):
    conn = get_conn()
    conn.execute(
        "INSERT INTO seed_results (topic, result, created_at) VALUES (?,?,?)",
        (topic, result, datetime.now().strftime("%Y-%m-%d %H:%M")),
    )
    conn.commit()
    conn.close()


def get_seed_results(limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT * FROM seed_results ORDER BY created_at DESC LIMIT ?", (limit,)
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
