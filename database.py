"""
database.py
-----------
IT Saha Ziyaret Takip Uygulamasi - Veritabani Katmani
SQLite tabanli veri saklama, sorgulama ve yonetim fonksiyonlari.
"""

import sqlite3
import os
import shutil
import glob
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

    # Firma IP & BT Envanter Defteri tablosu
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS company_notes (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            company     TEXT    NOT NULL UNIQUE,
            ip_subnet   TEXT    DEFAULT '',
            vpn_details TEXT    DEFAULT '',
            credentials TEXT    DEFAULT '',
            other_notes TEXT    DEFAULT '',
            updated_at  TEXT    DEFAULT (datetime('now', 'localtime'))
        )
    """)

    # Genel Ayarlar tablosu (SMTP vb. ayarlar icin)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key         TEXT PRIMARY KEY,
            value       TEXT
        )
    """)

    # Performans icin indeksler (sik sorgulanan sutunlar)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_date      ON visits(visit_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_visits_company   ON visits(company)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_reminders_date   ON reminders(remind_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_todos_done       ON todos(is_done)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_comp_notes_co    ON company_notes(company)")

    # Resim / Fotograf ekleri destegi
    try:
        cursor.execute("ALTER TABLE visits ADD COLUMN image_data TEXT")
    except Exception:
        pass
    try:
        cursor.execute("ALTER TABLE company_notes ADD COLUMN image_data TEXT")
    except Exception:
        pass

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
    image_data: str = "",
) -> int:
    """Yeni bir ziyaret kaydi ekler. Yeni eklenen kaydin ID'sini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO visits (visit_date, company, contact, subject, work_notes, duration, technician, status, image_data)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (visit_date, company, contact, subject, work_notes, duration, technician, status, image_data),
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


# ---------------------------------------------------------------------------
# Firma IP & BT Envanter Defteri (Company Notes) CRUD
# ---------------------------------------------------------------------------

def get_company_notes(company: str) -> Optional[dict]:
    """Belirli bir firmaya ait IP, VPN ve diger BT envanter notlarini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_notes WHERE LOWER(company) = ?", (company.strip().lower(),))
    row = cursor.fetchone()
    conn.close()
    return dict(row) if row else None


def save_company_notes(company: str, ip_subnet: str = "", vpn_details: str = "", credentials: str = "", other_notes: str = "", image_data: str = ""):
    """Firma BT envanter notlarini kaydeder (varsa gunceller, yoksa ekler)."""
    conn = get_connection()
    cursor = conn.cursor()
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute(
        """
        INSERT INTO company_notes (company, ip_subnet, vpn_details, credentials, other_notes, updated_at, image_data)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(company) DO UPDATE SET
            ip_subnet = excluded.ip_subnet,
            vpn_details = excluded.vpn_details,
            credentials = excluded.credentials,
            other_notes = excluded.other_notes,
            updated_at = excluded.updated_at,
            image_data = COALESCE(NULLIF(excluded.image_data, ''), company_notes.image_data)
        """,
        (company.strip(), ip_subnet.strip(), vpn_details.strip(), credentials.strip(), other_notes.strip(), now, image_data),
    )
    conn.commit()
    conn.close()


def delete_company_notes(company: str):
    """Bir firmaya ait BT envanter notlarini siler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM company_notes WHERE LOWER(company) = ?", (company.strip().lower(),))
    conn.commit()
    conn.close()


def get_all_company_notes() -> list:
    """Kayitli tum firma envanter notlarini listeler."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM company_notes ORDER BY company ASC")
    rows = cursor.fetchall()
    conn.close()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------------------
# Yedekleme Yonetimi (Backup Management)
# ---------------------------------------------------------------------------

def create_backup() -> str:
    """Mevcut visits.db veritabanini backups/ dizinine yedekler."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(project_dir, "backups")
    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"visits_backup_{timestamp}.db"
    backup_path = os.path.join(backup_dir, backup_filename)
    
    # SQLite yazim islemlerinin bitmesini garanti altina almak icin baglanti acip kapatilabilir
    # ama shutil.copy2 yerel kullanimda yeterince guvenlidir.
    shutil.copy2(DB_PATH, backup_path)
    return backup_filename


def list_backups() -> list:
    """Mevcut yedek veritabanlarini listeler."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    backup_dir = os.path.join(project_dir, "backups")
    if not os.path.exists(backup_dir):
        return []
    
    files = glob.glob(os.path.join(backup_dir, "visits_backup_*.db"))
    backups = []
    for f in files:
        stat = os.stat(f)
        filename = os.path.basename(f)
        ts_str = filename.replace("visits_backup_", "").replace(".db", "")
        try:
            dt = datetime.strptime(ts_str, "%Y%m%d_%H%M%S").strftime("%d.%m.%Y %H:%M:%S")
        except:
            dt = datetime.fromtimestamp(stat.st_mtime).strftime("%d.%m.%Y %H:%M:%S")
            
        backups.append({
            "filename": filename,
            "filepath": f,
            "date": dt,
            "size": f"{stat.st_size / 1024:.1f} KB"
        })
    return sorted(backups, key=lambda x: x["filename"], reverse=True)


def delete_backup(filename: str) -> bool:
    """Belirtilen yedek dosyasini kalici olarak siler."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    backup_path = os.path.join(project_dir, "backups", filename)
    if os.path.exists(backup_path) and os.path.basename(backup_path).startswith("visits_backup_"):
        os.remove(backup_path)
        return True
    return False


def restore_backup(filename: str) -> bool:
    """Belirtilen yedek dosyasini ana visits.db olarak geri yukler."""
    project_dir = os.path.dirname(os.path.abspath(__file__))
    backup_path = os.path.join(project_dir, "backups", filename)
    if os.path.exists(backup_path) and os.path.basename(backup_path).startswith("visits_backup_"):
        # Geri yuklemeden once mevcut durumu guvenlik amaciyla gecici olarak yedekle
        temp_backup = os.path.join(project_dir, "backups", "temp_before_restore.db")
        if os.path.exists(DB_PATH):
            shutil.copy2(DB_PATH, temp_backup)
        
        try:
            shutil.copy2(backup_path, DB_PATH)
            if os.path.exists(temp_backup):
                os.remove(temp_backup)
            return True
        except Exception as e:
            # Hata durumunda gecici yedekten geri don
            if os.path.exists(temp_backup):
                shutil.copy2(temp_backup, DB_PATH)
                os.remove(temp_backup)
            raise e
    return False


def get_setting(key: str, default: str = "") -> str:
    """Belirtilen ayarin degerini dondurur."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = cursor.fetchone()
    conn.close()
    if row:
        return row["value"]
    return default


def set_setting(key: str, value: str):
    """Ayari kaydeder veya gunceller."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)", (key, value))
    conn.commit()
    conn.close()


def export_data_json() -> str:
    """Tum veritabani tablolarini JSON formatinda paketler."""
    import json
    conn = get_connection()
    cursor = conn.cursor()
    
    export_payload = {
        "version": "3.0",
        "exported_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "data": {}
    }
    
    tables = ["visits", "reminders", "todos", "company_notes", "settings"]
    for tbl in tables:
        cursor.execute(f"SELECT * FROM {tbl}")
        rows = [dict(r) for r in cursor.fetchall()]
        export_payload["data"][tbl] = rows
        
    conn.close()
    return json.dumps(export_payload, ensure_ascii=False, indent=2)


def import_data_json(json_str: str, mode: str = "merge") -> tuple[bool, str]:
    """JSON paketinden veritabanina aktarim yapar (merge veya overwrite)."""
    import json
    try:
        payload = json.loads(json_str)
        if "data" not in payload:
            return False, "Gecersiz yedek dosyasi formati! ('data' anahtari bulunamadi)"
            
        data = payload["data"]
        conn = get_connection()
        cursor = conn.cursor()
        
        if mode == "overwrite":
            for tbl in ["visits", "reminders", "todos", "company_notes", "settings"]:
                cursor.execute(f"DELETE FROM {tbl}")
                
        # 1. Ziyaretler
        visits = data.get("visits", [])
        for v in visits:
            img = v.get("image_data") or ""
            if mode == "overwrite":
                cursor.execute("""
                    INSERT INTO visits (id, visit_date, company, contact, subject, work_notes, duration, technician, status, created_at, image_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (v.get("id"), v.get("visit_date"), v.get("company"), v.get("contact"), v.get("subject"), v.get("work_notes"), v.get("duration"), v.get("technician"), v.get("status"), v.get("created_at"), img))
            else:
                cursor.execute("SELECT id FROM visits WHERE visit_date=? AND company=? AND subject=?", (v.get("visit_date"), v.get("company"), v.get("subject")))
                row = cursor.fetchone()
                if not row:
                    cursor.execute("""
                        INSERT INTO visits (visit_date, company, contact, subject, work_notes, duration, technician, status, created_at, image_data)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (v.get("visit_date"), v.get("company"), v.get("contact"), v.get("subject"), v.get("work_notes"), v.get("duration"), v.get("technician"), v.get("status"), v.get("created_at"), img))
                elif img:
                    cursor.execute("UPDATE visits SET image_data = ? WHERE id = ?", (img, row["id"]))

        # 2. Hatirlaticilar
        reminders = data.get("reminders", [])
        for r in reminders:
            if mode == "overwrite":
                cursor.execute("""
                    INSERT INTO reminders (id, remind_date, company, title, notes, priority, is_done, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (r.get("id"), r.get("remind_date"), r.get("company"), r.get("title"), r.get("notes"), r.get("priority"), r.get("is_done"), r.get("created_at")))
            else:
                cursor.execute("SELECT id FROM reminders WHERE remind_date=? AND company=? AND title=?", (r.get("remind_date"), r.get("company"), r.get("title")))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO reminders (remind_date, company, title, notes, priority, is_done, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    """, (r.get("remind_date"), r.get("company"), r.get("title"), r.get("notes"), r.get("priority"), r.get("is_done"), r.get("created_at")))

        # 3. Yapilacaklar
        todos = data.get("todos", [])
        for t in todos:
            title_val = t.get("title") or t.get("description") or ""
            if not title_val:
                continue
            is_done_val = 1 if t.get("is_done") in (1, True, "1") else 0
            if mode == "overwrite":
                cursor.execute("""
                    INSERT INTO todos (id, visit_id, company, title, description, due_date, priority, is_done, done_at, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (t.get("id"), t.get("visit_id"), t.get("company") or "", title_val, t.get("description") or title_val, t.get("due_date"), t.get("priority") or "Normal", is_done_val, t.get("done_at"), t.get("created_at")))
            else:
                cursor.execute("SELECT id FROM todos WHERE title=? OR description=?", (title_val, title_val))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO todos (visit_id, company, title, description, due_date, priority, is_done, done_at, created_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (t.get("visit_id"), t.get("company") or "", title_val, t.get("description") or title_val, t.get("due_date"), t.get("priority") or "Normal", is_done_val, t.get("done_at"), t.get("created_at")))

        # 4. Firma Notlari
        notes = data.get("company_notes", [])
        for n in notes:
            if n.get("company"):
                cursor.execute("""
                    INSERT INTO company_notes (company, ip_subnet, vpn_details, credentials, other_notes, updated_at, image_data)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(company) DO UPDATE SET
                        ip_subnet = excluded.ip_subnet,
                        vpn_details = excluded.vpn_details,
                        credentials = excluded.credentials,
                        other_notes = excluded.other_notes,
                        updated_at = excluded.updated_at,
                        image_data = COALESCE(NULLIF(excluded.image_data, ''), company_notes.image_data)
                """, (n.get("company"), n.get("ip_subnet"), n.get("vpn_details"), n.get("credentials"), n.get("other_notes"), n.get("updated_at") or datetime.now().strftime("%Y-%m-%d %H:%M:%S"), n.get("image_data") or ""))

        # 5. Ayarlar
        settings = data.get("settings", [])
        for s in settings:
            cursor.execute("""
                INSERT OR REPLACE INTO settings (key, value)
                VALUES (?, ?)
            """, (s.get("key"), s.get("value")))

        # 6. Mobilden iletilen Silme İstekleri (deleted)
        deleted = payload.get("deleted", {})
        if isinstance(deleted, dict):
            for comp in deleted.get("company_notes", []):
                if comp:
                    cursor.execute("DELETE FROM company_notes WHERE LOWER(company) = ?", (str(comp).strip().lower(),))
            for v_id in deleted.get("visits", []):
                if v_id:
                    cursor.execute("DELETE FROM visits WHERE id = ?", (v_id,))
            for t_id in deleted.get("todos", []):
                if t_id:
                    cursor.execute("DELETE FROM todos WHERE id = ?", (t_id,))

        conn.commit()
        conn.close()
        return True, "Tüm veriler başarıyla içe aktarıldı ve işlendi!"
    except Exception as e:
        return False, f"İçe aktarım hatası: {str(e)}"

