import sqlite3
from datetime import datetime
from config import DB_PATH


def db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = db()
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users(
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        join_date TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS novels(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT, author TEXT, language TEXT, description TEXT,
        category TEXT, cover TEXT, views INTEGER DEFAULT 0,
        downloads INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS volumes(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        novel_id INTEGER, volume_number INTEGER, pdf_file_id TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS favorites(
        user_id INTEGER, novel_id INTEGER,
        PRIMARY KEY(user_id, novel_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS requests(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, content TEXT,
        status TEXT DEFAULT 'pending', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS reports(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, content TEXT,
        status TEXT DEFAULT 'pending', created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS read_stats(
        user_id INTEGER, novel_id INTEGER, read_date TEXT)""")
    conn.commit()
    conn.close()


def add_user(user_id, username, first_name):
    conn = db()
    conn.execute("INSERT OR IGNORE INTO users VALUES (?,?,?,?)",
        (user_id, username, first_name, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_all_users():
    conn = db()
    r = conn.execute("SELECT user_id FROM users").fetchall()
    conn.close()
    return [row["user_id"] for row in r]


def count_users():
    conn = db()
    r = conn.execute("SELECT COUNT(*) AS c FROM users").fetchone()
    conn.close()
    return r["c"]


def add_novel(title, author, language, description, category, cover=None):
    conn = db()
    cur = conn.execute(
        """INSERT INTO novels(title, author, language, description, category, cover, created_at)
           VALUES (?,?,?,?,?,?,?)""",
        (title, author, language, description, category, cover, datetime.now().isoformat()))
    nid = cur.lastrowid
    conn.commit()
    conn.close()
    return nid


def get_novel(nid):
    conn = db()
    r = conn.execute("SELECT * FROM novels WHERE id=?", (nid,)).fetchone()
    conn.close()
    return dict(r) if r else None


def get_all_novels():
    conn = db conn()
    r = conn.execute("SELECT *.close FROM novels ORDER BY id DESC").fetchall()


()
    conn.close()
    return [dictdef(x) for x in r]


def add get_new_novels(limit=10):
   _ conn = db()
    r = conn.execute("SELECT * FROM novels ORDER BY id DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(x) for x in r]


def get_top_rated(limit=10):
    conn = db()
    r = conn.execute("SELECT * FROM novels ORDER BY views DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(x) for x in r]


def get_most_viewed(limit=10):
    conn = db()
    r = conn.execute("SELECT * FROM novels ORDER BY views DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(x) for x in r]


def get_most_downloaded(limit=10):
    conn = db()
    r = conn.execute("SELECT * FROM novels ORDER BY downloads DESC LIMIT ?", (limit,)).fetchall()
    conn.close()
    return [dict(x) for x in r]


def get_random_novel():
    conn = db()
    r = conn.execute("SELECT * FROM novels ORDER BY RANDOM() LIMIT 1").fetchone()
    conn.close()
    return dict(r) if r else None


def search_novels(q):
    conn = db()
    r = conn.execute("SELECT * FROM novels WHERE title LIKE ? OR author LIKE ?",
        (f"%{q}%", f"%{q}%")).fetchall()
    conn.close()
    return [dict(x) for x in r]


def update_novel_field(nid, field, value):
    allowed = {"title", "author", "language", "description", "category"}
    if field not in allowed:
        return False
    conn = db()
    conn.execute(f"UPDATE novels SET {field}=? WHERE id=?", (value, nid))
    conn.commit()
    conn.close()
    return True


def delete_novel(nid):
    conn = db()
    conn.execute("DELETE FROM volumes WHERE novel_id=?", (nid,))
    conn.execute("DELETE FROM novels WHERE id=?", (nid,))
    conn.execute("DELETE FROM favorites WHERE novel_id=?", (nid,))
    conn.commit()
    conn.close()


def inc_views(nid):
    conn = db()
    conn.execute("UPDATE novels SET views=views+1 WHERE id=?", (nid,))
    conn.commit()
    conn.close()


def inc_downloads(nid):
    conn = db()
    conn.execute("UPDATE novels SET downloads=downloads+1 WHERE id=?", (nid,))
    conn.commit()
   volume(novel_id, volume_number, pdf_file_id):
    conn = db()
    conn.execute("INSERT INTO volumes(novel_id, volume_number, pdf_file_id) VALUES (?,?,?)",
        (novel_id, volume_number, pdf_file_id))
    conn.commit()
    conn.close()


def get_volumes(novel_id):
    conn = db()
    r = conn.execute("SELECT * FROM volumes WHERE novel_id=? ORDER BY volume_number",
        (novel_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]


def get_volume_by_number(novel_id, volume_number):
    conn = db()
    r = conn.execute("SELECT * FROM volumes WHERE novel_id=? AND volume_number=?",
        (novel_id, volume_number)).fetchone()
    conn.close()
    return dict(r) if r else None


def delete_volume(vol_id):
    conn = db()
    conn.execute("DELETE FROM volumes WHERE id=?", (vol_id,))
    conn.commit()
    conn.close()


def toggle_favorite(user_id, novel_id):
    conn = db()
    exists = conn.execute("SELECT 1 FROM favorites WHERE user_id=? AND novel_id=?",
        (user_id, novel_id)).fetchone()
    if exists:
        conn.execute("DELETE FROM favorites WHERE user_id=? AND novel_id=?", (user_id, novel_id))
        state = False
    else:
        conn.execute("INSERT INTO favorites VALUES (?,?)", (user_id, novel_id))
        state = True
    conn.commit()
    conn.close()
    return state


def is_favorite(user_id, novel_id):
    conn = db()
    r = conn.execute("SELECT 1 FROM favorites WHERE user_id=? AND novel_id=?",
        (user_id, novel_id)).fetchone()
    conn.close()
    return bool(r)


def get_favorites(user_id):
    conn = db()
    r = conn.execute(
        """SELECT n.* FROM novels n
           JOIN favorites f ON f.novel_id=n.id
           WHERE f.user_id=? ORDER BY n.id DESC""",
        (user_id,)).fetchall()
    conn.close()
    return [dict(x) for x in r]


def add_request(user_id, content):
    conn = db()
    conn.execute("INSERT INTO requests(user_id, content, created_at) VALUES (?,?,?)",
        (user_id, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def add_report(user_id, content):
    conn = db()
    conn.execute("INSERT INTO reports(user_id, content, created_at) VALUES (?,?,?)",
        (user_id, content, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def count_requests():
    conn = db()
    r = conn.execute("SELECT COUNT(*) AS c FROM requests").fetchone()
    conn.close()
    return r["c"]


def count_reports():
    conn = db()
    r = conn.execute("SELECT COUNT(*) AS c FROM reports").fetchone()
    conn.close()
    return r["c"]


def mark_read(user_id, novel_id):
    conn = db()
    conn.execute("INSERT INTO read_stats(user_id, novel_id, read_date) VALUES (?,?,?)",
        (user_id, novel_id, datetime.now().isoformat()))
    conn.commit()
    conn.close()


def get_user_stats(user_id):
    conn = db()
    favs = conn.execute("SELECT COUNT(*) AS c FROM favorites WHERE user_id=?", (user_id,)).fetchone()["c"]
    reads = conn.execute("SELECT COUNT(DISTINCT novel_id) AS c FROM read_stats WHERE user_id=?",
        (user_id,)).fetchone()["c"]
    conn.close()
    return {"favorites": favs, "reads": reads}
