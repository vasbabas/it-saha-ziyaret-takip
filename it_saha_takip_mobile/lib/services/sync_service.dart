import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';
import 'database_service.dart';

class SyncService {
  static const _ipKey = 'pc_ip_address';
  static const _portKey = 'pc_port';
  static const int _timeout = 10;

  static Future<String> getSavedIP() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getString(_ipKey) ?? '';
  }

  static Future<int> getSavedPort() async {
    final prefs = await SharedPreferences.getInstance();
    return prefs.getInt(_portKey) ?? 8502;
  }

  static Future<void> saveConnection(String ip, int port) async {
    final prefs = await SharedPreferences.getInstance();
    await prefs.setString(_ipKey, ip);
    await prefs.setInt(_portKey, port);
  }

  static String _baseUrl(String ip, int port) => 'http://$ip:$port';

  /// Returns true if PC is reachable
  static Future<bool> isReachable() async {
    try {
      final ip = await getSavedIP();
      var port = await getSavedPort();
      if (ip.isEmpty) return false;

      // Auto fallback to 8502 if 8501 was saved
      if (port == 8501) port = 8502;

      final res = await http
          .get(Uri.parse('${_baseUrl(ip, port)}/api/sync_data'))
          .timeout(const Duration(seconds: _timeout));
      return res.statusCode == 200 && !res.body.trim().startsWith('<');
    } catch (_) {
      return false;
    }
  }

  /// Full two-way sync: push local unsynced → pull all from PC
  static Future<SyncResult> fullSync() async {
    final ip = await getSavedIP();
    var port = await getSavedPort();

    if (ip.isEmpty) {
      return SyncResult(success: false, message: 'Bilgisayar IP adresi girilmemiş.');
    }

    // Auto-correct port if user entered Streamlit port 8501
    if (port == 8501) {
      port = 8502;
      await saveConnection(ip, 8502);
    }

    try {
      // 1. Push unsynced visits to PC
      final unsyncedVisits = await DatabaseService.getUnsyncedVisits();
      int pushed = 0;
      if (unsyncedVisits.isNotEmpty) {
        final payload = jsonEncode({
          'version': '3.0',
          'data': {
            'visits': unsyncedVisits.map((v) {
              final m = v.toJson();
              m['contact'] = ''; // Ensure contact field is set for Python SQLite
              return m;
            }).toList(),
            'company_notes': [],
            'todos': [],
          }
        });

        final uploadRes = await http
            .post(
              Uri.parse('${_baseUrl(ip, port)}/api/sync_upload'),
              headers: {'Content-Type': 'application/json; charset=utf-8'},
              body: payload,
            )
            .timeout(const Duration(seconds: _timeout));

        if (uploadRes.statusCode == 200) {
          final ids = unsyncedVisits
              .where((v) => v.id != null)
              .map((v) => v.id!)
              .toList();
          await DatabaseService.markVisitsSynced(ids);
          pushed = unsyncedVisits.length;
        }
      }

      // 2. Pull all data from PC
      final getRes = await http
          .get(Uri.parse('${_baseUrl(ip, port)}/api/sync_data'))
          .timeout(const Duration(seconds: _timeout));

      if (getRes.statusCode != 200) {
        return SyncResult(
            success: false,
            message: 'Sunucu hatası: HTTP ${getRes.statusCode} (Port 8502 açık mı?)');
      }

      final bodyText = getRes.body.trim();
      if (bodyText.startsWith('<')) {
        return SyncResult(
          success: false,
          message: '⚠️ Port Uyuşmazlığı: Girdiğiniz port (8501) Web sunucusuna ait. Lütfen Port alanına 8502 yazın!',
        );
      }

      final data = jsonDecode(bodyText);
      final pcData = data['data'] ?? data;

      // Import visits
      if (pcData['visits'] != null && pcData['visits'] is List) {
        final visits = <Visit>[];
        for (final j in pcData['visits']) {
          try {
            visits.add(Visit.fromJson(j as Map<String, dynamic>));
          } catch (_) {}
        }
        await DatabaseService.upsertVisitsFromSync(visits);
      }

      // Import company notes
      if (pcData['company_notes'] != null && pcData['company_notes'] is List) {
        final notes = <CompanyNote>[];
        for (final j in pcData['company_notes']) {
          try {
            notes.add(CompanyNote.fromJson(j as Map<String, dynamic>));
          } catch (_) {}
        }
        await DatabaseService.upsertCompanyNotesFromSync(notes);
      }

      // Import todos
      if (pcData['todos'] != null && pcData['todos'] is List) {
        final todos = <Todo>[];
        for (final j in pcData['todos']) {
          try {
            todos.add(Todo.fromJson(j as Map<String, dynamic>));
          } catch (_) {}
        }
        await DatabaseService.upsertTodosFromSync(todos);
      }

      return SyncResult(
        success: true,
        message: '✅ Eşitleme başarılı! $pushed yeni kayıt PC\'ye aktarıldı.',
        pushed: pushed,
      );
    } catch (e) {
      final errStr = e.toString();
      if (errStr.contains('Unexpected character') || errStr.contains('FormatException')) {
        return SyncResult(
          success: false,
          message: '⚠️ Port Hatası: Lütfen Port kısmına 8502 yazıp "Kaydet & Test Et" butonuna basın!',
        );
      }
      return SyncResult(
        success: false,
        message: 'Bağlantı Hatası: Bilgisayar açık ve aynı Wi-Fi ağında mı? ($e)',
      );
    }
  }
}

class SyncResult {
  final bool success;
  final String message;
  final int pushed;
  SyncResult({required this.success, required this.message, this.pushed = 0});
}
