import 'package:sqflite/sqflite.dart';
import 'package:path/path.dart';
import '../models/models.dart';

class DatabaseService {
  static Database? _db;

  static Future<Database> get database async {
    if (_db != null) return _db!;
    _db = await _initDB();
    return _db!;
  }

  static Future<Database> _initDB() async {
    final dbPath = await getDatabasesPath();
    final path = join(dbPath, 'it_saha_takip.db');
    return await openDatabase(
      path,
      version: 1,
      onCreate: (db, version) async {
        await db.execute('''
          CREATE TABLE visits (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            visit_date TEXT NOT NULL,
            company TEXT NOT NULL,
            subject TEXT,
            technician TEXT,
            duration REAL DEFAULT 1.0,
            status TEXT DEFAULT 'Tamamlandi',
            work_notes TEXT,
            created_at TEXT,
            synced INTEGER DEFAULT 0
          )
        ''');
        await db.execute('''
          CREATE TABLE company_notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company TEXT NOT NULL UNIQUE,
            ip_subnet TEXT,
            vpn_details TEXT,
            credentials TEXT,
            other_notes TEXT,
            updated_at TEXT
          )
        ''');
        await db.execute('''
          CREATE TABLE todos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            is_done INTEGER DEFAULT 0,
            due_date TEXT,
            created_at TEXT,
            synced INTEGER DEFAULT 0
          )
        ''');
      },
    );
  }

  // ── VISITS ──────────────────────────────────────────────────────

  static Future<int> insertVisit(Visit visit) async {
    final db = await database;
    return await db.insert('visits', visit.toMap(),
        conflictAlgorithm: ConflictAlgorithm.replace);
  }

  static Future<List<Visit>> getVisits({String? query}) async {
    final db = await database;
    List<Map<String, dynamic>> maps;
    if (query != null && query.isNotEmpty) {
      maps = await db.query(
        'visits',
        where: 'company LIKE ? OR subject LIKE ? OR work_notes LIKE ?',
        whereArgs: ['%$query%', '%$query%', '%$query%'],
        orderBy: 'visit_date DESC, id DESC',
      );
    } else {
      maps = await db.query('visits', orderBy: 'visit_date DESC, id DESC');
    }
    return maps.map((m) => Visit.fromMap(m)).toList();
  }

  static Future<void> upsertVisitsFromSync(List<Visit> visits) async {
    final db = await database;
    final batch = db.batch();
    for (final v in visits) {
      batch.insert('visits', v.toMap(),
          conflictAlgorithm: ConflictAlgorithm.ignore);
    }
    await batch.commit(noResult: true);
  }

  static Future<List<Visit>> getUnsyncedVisits() async {
    final db = await database;
    final maps = await db.query('visits', where: 'synced = 0');
    return maps.map((m) => Visit.fromMap(m)).toList();
  }

  static Future<void> markVisitsSynced(List<int> ids) async {
    final db = await database;
    if (ids.isEmpty) return;
    await db.rawUpdate(
      'UPDATE visits SET synced = 1 WHERE id IN (${ids.map((_) => '?').join(',')})',
      ids,
    );
  }

  // ── COMPANY NOTES ──────────────────────────────────────────────

  static Future<List<CompanyNote>> getCompanyNotes({String? query}) async {
    final db = await database;
    List<Map<String, dynamic>> maps;
    if (query != null && query.isNotEmpty) {
      maps = await db.query(
        'company_notes',
        where: 'company LIKE ? OR ip_subnet LIKE ?',
        whereArgs: ['%$query%', '%$query%'],
        orderBy: 'company ASC',
      );
    } else {
      maps = await db.query('company_notes', orderBy: 'company ASC');
    }
    return maps.map((m) => CompanyNote.fromMap(m)).toList();
  }

  static Future<void> upsertCompanyNotesFromSync(List<CompanyNote> notes) async {
    final db = await database;
    final batch = db.batch();
    for (final n in notes) {
      batch.insert('company_notes', n.toMap(),
          conflictAlgorithm: ConflictAlgorithm.replace);
    }
    await batch.commit(noResult: true);
  }

  static Future<List<String>> getCompanyNames() async {
    final db = await database;
    final result = await db.rawQuery(
        'SELECT DISTINCT company FROM company_notes UNION SELECT DISTINCT company FROM visits ORDER BY company ASC');
    return result.map((r) => r['company'] as String).toList();
  }

  // ── TODOS ──────────────────────────────────────────────────────

  static Future<int> insertTodo(Todo todo) async {
    final db = await database;
    return await db.insert('todos', todo.toMap());
  }

  static Future<List<Todo>> getTodos() async {
    final db = await database;
    final maps = await db.query('todos', orderBy: 'is_done ASC, id DESC');
    return maps.map((m) => Todo.fromMap(m)).toList();
  }

  static Future<void> updateTodoDone(int id, bool done) async {
    final db = await database;
    await db.update('todos', {'is_done': done ? 1 : 0}, where: 'id = ?', whereArgs: [id]);
  }

  static Future<void> deleteTodo(int id) async {
    final db = await database;
    await db.delete('todos', where: 'id = ?', whereArgs: [id]);
  }

  static Future<void> upsertTodosFromSync(List<Todo> todos) async {
    final db = await database;
    final batch = db.batch();
    for (final t in todos) {
      batch.insert('todos', t.toMap(),
          conflictAlgorithm: ConflictAlgorithm.ignore);
    }
    await batch.commit(noResult: true);
  }

  // ── STATS ──────────────────────────────────────────────────────

  static Future<Map<String, int>> getStats() async {
    final db = await database;
    final visitCount = Sqflite.firstIntValue(
            await db.rawQuery('SELECT COUNT(*) FROM visits')) ??
        0;
    final noteCount = Sqflite.firstIntValue(
            await db.rawQuery('SELECT COUNT(*) FROM company_notes')) ??
        0;
    final todoCount = Sqflite.firstIntValue(
            await db.rawQuery('SELECT COUNT(*) FROM todos')) ??
        0;
    return {'visits': visitCount, 'notes': noteCount, 'todos': todoCount};
  }
}
