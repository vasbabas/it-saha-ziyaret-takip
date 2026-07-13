"""
database.py
-----------
IT Saha Ziyaret Takip Uygulamasi - Veritabani Katmani
SQLite tabanli veri saklama, sorgulama ve yonetim fonksiyonlari.
"""

import sqlite3
import os
from datetime import date, datetime
from typing import Optional

# Veritabani dosyasinin yolu (uygulama ile ayni dizinde)
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "visits.db")


def get_connection() -> sqlite3.Connection:
    """Veritabani baglantisi dondurur. Row nesnelerini dict gibi kullanmak icin row_factory ayarlanir."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """
    Uygulama ilk acildiginda cagrilir.
    Veritabani dosyasi yoksa olusturur, gerekli tablolari kurar.
    Mevcut DB'de eksik tablolar varsa onlari da ekler.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Ana ziyaret kayitlari tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS visits (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_date  TEXT    NOT NULL,
            company     TEXT    NOT NULL,
            contact     TEXT,
            subject     TEXT,
            work_notes  TEXT,
            duration    REAL    DEFAULT 0,
            technician  TEXT,
            status      TEXT    DEFAULT 'Tamamlandi',
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Hatirlatici tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reminders (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            remind_date TEXT    NOT NULL,
            company     TEXT    NOT NULL,
            title       TEXT    NOT NULL,
            notes       TEXT    DEFAULT '',
            priority    TEXT    DEFAULT 'Normal',
            is_done     INTEGER DEFAULT 0,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Yapilacaklar (To-Do) tablosu
    # visit_id: bagli oldugu ziyaret kaydi (NULL olabilir - bagimsiz gorev)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS todos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_id    INTEGER REFERENCES visits(id) ON DELETE SET NULL,
            company     TEXT    NOT NULL DEFAULT '',
            title       TEXT    NOT NULL,
            description TEXT    DEFAULT '',
            due_date    TEXT,
            priority    TEXT    DEFAULT 'Normal',
            is_done     INTEGER DEFAULT 0,
            done_at     TEXT,
            created_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Performans icin indeksler (sik sorgulanan sutunlar)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_date    ON visits(visit_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_company ON visits(company)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_date ON reminders(remind_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_todos_done     ON todos(is_done)")

    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Ziyaret CRUD
# ---------------------------------------------------------------------------

def add_visit(
    visit_date: str,
    company: str,
    contact: str = "",
    subject: str = "",
    work_notes: str = "",
    duration: float = 0.0,
    technician: str = "",
    status: str = "Tamamlandi",
) -> int:
    """Yeni bir ziyaret kaydi ekler. Yeni eklenen kaydin ID'sini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO visits (visit_date, company, contact, subject, work_notes, duration, technician, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (visit_date, company, contact, subject, work_notes, duration, technician, status),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_visit(
    visit_id: int,
    visit_date: str,
    company: str,
    contact: str,
    subject: str,
    work_notes: str,
    duration: float,
    technician: str,
    status: str,
):
    """Mevcut bir ziyaret kaydini gunceller."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE visits
        SET visit_date=?, company=?, contact=?, subject=?, work_notes=?, duration=?, technician=?, status=?
        WHERE id=?
        """,
        (visit_date, company, contact, subject, work_notes, duration, technician, status, visit_id),
    )
    conn.commit()
    conn.close()


def delete_visit(visit_id: int):
    """Belirtilen ID'ye sahip ziyaret kaydini siler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM visits WHERE id=?", (visit_id,))
    conn.commit()
    conn.close()


def get_all_companies() -> list:
    """Veritabanindaki tum benzersiz firma adlarini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT DISTINCT company FROM visits ORDER BY company ASC")
    rows = cursor.fetchall()
    conn.close()
    return [row["company"] for row in rows]


def get_visits(
    company_filter: str = "",
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    month: Optional[int] = None,
    year: Optional[int] = None,
) -> list:
    """Belirtilen filtrelere gore ziyaret kayitlarini sorgular."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT * FROM visits WHERE 1=1"
    params = []

    if company_filter:
        query += " AND LOWER(company) LIKE ?"
        params.append(f"%{company_filter.lower()}%")

    if date_from:
        query += " AND visit_date >= ?"
        params.append(date_from)

    if date_to:
        query += " AND visit_date <= ?"
        params.append(date_to)

    if month and year:
        query += " AND strftime('%m', visit_date) = ? AND strftime('%Y', visit_date) = ?"
        params.append(f"{month:02d}")
        params.append(str(year))

    query += " ORDER BY visit_date DESC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_visits_by_date(visit_date: str) -> list:
    """Belirli bir tarihteki tum ziyaretleri dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM visits WHERE visit_date = ? ORDER BY id DESC", (visit_date,))
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_summary_stats() -> dict:
    """Dashboard icin ozet istatistikler dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    today = date.today()

    cursor.execute("SELECT COUNT(*) as total, SUM(duration) as total_hours FROM visits")
    total_row = cursor.fetchone()

    cursor.execute(
        """
        SELECT COUNT(*) as cnt, SUM(duration) as hrs
        FROM visits
        WHERE strftime('%m', visit_date) = ? AND strftime('%Y', visit_date) = ?
        """,
        (f"{today.month:02d}", str(today.year)),
    )
    month_row = cursor.fetchone()

    cursor.execute("SELECT COUNT(DISTINCT company) as company_count FROM visits")
    company_row = cursor.fetchone()

    conn.close()

    return {
        "total_visits":      total_row["total"] or 0,
        "total_hours":       round(total_row["total_hours"] or 0, 1),
        "month_visits":      month_row["cnt"] or 0,
        "month_hours":       round(month_row["hrs"] or 0, 1),
        "unique_companies":  company_row["company_count"] or 0,
    }


# ---------------------------------------------------------------------------
# Grafik / Analiz Sorgulari
# ---------------------------------------------------------------------------

def get_monthly_trend(year: int) -> list:
    """Belirli bir yilin aylik ziyaret sayisi ve toplam suresini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            CAST(strftime('%m', visit_date) AS INTEGER) AS month_num,
            COUNT(*) AS visit_count,
            ROUND(SUM(duration), 1) AS total_hours
        FROM visits
        WHERE strftime('%Y', visit_date) = ?
        GROUP BY month_num
        ORDER BY month_num
        """,
        (str(year),),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_company_distribution(top_n: int = 10) -> list:
    """En cok ziyaret edilen firmalarin ziyaret sayisini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT company, COUNT(*) AS visit_count, ROUND(SUM(duration), 1) AS total_hours
        FROM visits
        GROUP BY company
        ORDER BY visit_count DESC
        LIMIT ?
        """,
        (top_n,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_technician_stats() -> list:
    """Teknisyen bazli ziyaret sayisi ve toplam sure."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            COALESCE(NULLIF(technician, ''), 'Belirtilmemis') AS technician,
            COUNT(*) AS visit_count,
            ROUND(SUM(duration), 1) AS total_hours
        FROM visits
        GROUP BY technician
        ORDER BY visit_count DESC
        """
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_calendar_data(month: int, year: int) -> dict:
    """
    Belirli ay/yil icin tarih -> ziyaret sayisi eslemesi dondurur.
    Takvim gorunumu icin kullanilir.
    Ornek: {'2026-07-01': 2, '2026-07-05': 1}
    """
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT visit_date, COUNT(*) AS cnt
        FROM visits
        WHERE strftime('%Y', visit_date) = ? AND strftime('%m', visit_date) = ?
        GROUP BY visit_date
        """,
        (str(year), f"{month:02d}"),
    )
    rows = cursor.fetchall()
    conn.close()
    return {row["visit_date"]: row["cnt"] for row in rows}


# ---------------------------------------------------------------------------
# Hatirlatici (Reminder) CRUD
# ---------------------------------------------------------------------------

def add_reminder(
    remind_date: str,
    company: str,
    title: str,
    notes: str = "",
    priority: str = "Normal",
) -> int:
    """Yeni bir hatirlatici kaydi ekler. Yeni eklenen kaydin ID'sini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO reminders (remind_date, company, title, notes, priority)
        VALUES (?, ?, ?, ?, ?)
        """,
        (remind_date, company, title, notes, priority),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_reminders(
    include_done: bool = False,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
) -> list:
    """Hatirlaticilari sorgular."""
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM reminders WHERE 1=1"
    params = []
    if not include_done:
        query += " AND is_done = 0"
    if date_from:
        query += " AND remind_date >= ?"
        params.append(date_from)
    if date_to:
        query += " AND remind_date <= ?"
        params.append(date_to)
    query += " ORDER BY remind_date ASC"
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_due_reminders_today() -> list:
    """Bugun veya oncesinde vadesi gelmis, henuz tamamlanmamis hatirlaticilari dondurur."""
    today = date.today().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reminders WHERE is_done = 0 AND remind_date <= ? ORDER BY remind_date ASC",
        (today,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_reminder(reminder_id: int):
    """Hatirlaticiyi tamamlandi olarak isaretler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE reminders SET is_done = 1 WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


def delete_reminder(reminder_id: int):
    """Hatirlaticiyi kalici olarak siler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM reminders WHERE id = ?", (reminder_id,))
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Global Arama
# ---------------------------------------------------------------------------

def global_search(query: str) -> list:
    """
    Tum ziyaret kayitlarinda tam metin aramasi yapar.
    Arama alanlari: firma, konu, iletisim kisi, teknisyen, yapilan islem notlari.
    Buyuk/kucuk harf duyarsiz, kismi esleme destekler.

    Args:
        query: Aranacak kelime veya ifade

    Returns:
        Eslesen ziyaret kayitlarinin listesi, puan sirali (en cok eslesen uste)
    """
    if not query or not query.strip():
        return []

    conn = get_connection()
    cursor = conn.cursor()
    q = f"%{query.strip().lower()}%"
    cursor.execute(
        """
        SELECT *,
            -- Esleme skoru: daha fazla alanda geciyorsa daha yukari cikar
            (
                (CASE WHEN LOWER(company)    LIKE ? THEN 3 ELSE 0 END) +
                (CASE WHEN LOWER(subject)    LIKE ? THEN 2 ELSE 0 END) +
                (CASE WHEN LOWER(work_notes) LIKE ? THEN 2 ELSE 0 END) +
                (CASE WHEN LOWER(contact)    LIKE ? THEN 1 ELSE 0 END) +
                (CASE WHEN LOWER(technician) LIKE ? THEN 1 ELSE 0 END)
            ) AS score
        FROM visits
        WHERE score > 0
        ORDER BY score DESC, visit_date DESC
        LIMIT 100
        """,
        (q, q, q, q, q),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Yapilacaklar (To-Do) CRUD
# ---------------------------------------------------------------------------

def add_todo(
    title: str,
    company: str = "",
    description: str = "",
    due_date: Optional[str] = None,
    priority: str = "Normal",
    visit_id: Optional[int] = None,
) -> int:
    """Yeni bir yapilacak gorevi ekler. Yeni eklenen kaydin ID'sini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO todos (title, company, description, due_date, priority, visit_id)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        (title, company, description, due_date, priority, visit_id),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def get_todos(include_done: bool = False) -> list:
    """Yapilacak gorevleri dondurur. include_done=True ise tamamlananlar da gelir."""
    conn = get_connection()
    cursor = conn.cursor()
    if include_done:
        cursor.execute("SELECT * FROM todos ORDER BY is_done ASC, due_date ASC, priority DESC")
    else:
        cursor.execute(
            "SELECT * FROM todos WHERE is_done = 0 ORDER BY due_date ASC, priority DESC"
        )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def get_overdue_todos() -> list:
    """Vadesi gecmis, tamamlanmamis gorevleri dondurur."""
    today = date.today().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM todos WHERE is_done = 0 AND due_date IS NOT NULL AND due_date < ? ORDER BY due_date ASC",
        (today,),
    )
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


def complete_todo(todo_id: int):
    """Gorevi tamamlandi olarak isaretler, tamamlanma zamanini kaydeder."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE todos SET is_done = 1, done_at = ? WHERE id = ?",
        (now, todo_id),
    )
    conn.commit()
    conn.close()


def reopen_todo(todo_id: int):
    """Tamamlanmis gorevi yeniden acar."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE todos SET is_done = 0, done_at = NULL WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()


def delete_todo(todo_id: int):
    """Gorevi kalici olarak siler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM todos WHERE id = ?", (todo_id,))
    conn.commit()
    conn.close()


def get_todo_stats() -> dict:
    """Dashboard icin todo istatistikleri."""
    today = date.today().strftime("%Y-%m-%d")
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM todos WHERE is_done = 0")
    pending = cursor.fetchone()[0]
    cursor.execute(
        "SELECT COUNT(*) FROM todos WHERE is_done = 0 AND due_date IS NOT NULL AND due_date < ?",
        (today,),
    )
    overdue = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM todos WHERE is_done = 1")
    done = cursor.fetchone()[0]
    conn.close()
    return {"pending": pending, "overdue": overdue, "done": done}
