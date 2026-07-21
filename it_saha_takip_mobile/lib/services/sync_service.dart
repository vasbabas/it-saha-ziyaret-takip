import 'dart:convert';
import 'package:http/http.dart' as http;
import 'package:shared_preferences/shared_preferences.dart';
import '../models/models.dart';
import 'database_service.dart';

class SyncService {
  static const _ipKey = 'pc_ip_address';
  static const _portKey = 'pc_port';
  static const int _timeout = 8;

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
      final port = await getSavedPort();
      if (ip.isEmpty) return false;
      final res = await http
          .get(Uri.parse('${_baseUrl(ip, port)}/api/sync_data'))
          .timeout(const Duration(seconds: _timeout));
      return res.statusCode == 200;
    } catch (_) {
      return false;
    }
  }

  /// Full two-way sync: push local unsynced → pull all from PC
  static Future<SyncResult> fullSync() async {
    final ip = await getSavedIP();
    final port = await getSavedPort();
    if (ip.isEmpty) {
      return SyncResult(success: false, message: 'Bilgisayar IP adresi girilmemiş.');
    }

    try {
      // 1. Push unsynced visits to PC
      final unsyncedVisits = await DatabaseService.getUnsyncedVisits();
      int pushed = 0;
      if (unsyncedVisits.isNotEmpty) {
        final payload = jsonEncode({
          'version': '3.0',
          'data': {
            'visits': unsyncedVisits.map((v) => v.toJson()).toList(),
            'company_notes': [],
            'todos': [],
          }
        });
        final uploadRes = await http
            .post(
              Uri.parse('${_baseUrl(ip, port)}/api/sync_upload'),
              headers: {'Content-Type': 'application/json'},
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
        return SyncResult(success: false, message: 'Sunucudan veri alınamadı.');
      }

      final data = jsonDecode(getRes.body);
      final pcData = data['data'] ?? data;

      // Import visits
      if (pcData['visits'] != null) {
        final visits = (pcData['visits'] as List)
            .map((j) => Visit.fromJson(j))
            .toList();
        await DatabaseService.upsertVisitsFromSync(visits);
      }

      // Import company notes
      if (pcData['company_notes'] != null) {
        final notes = (pcData['company_notes'] as List)
            .map((j) => CompanyNote.fromJson(j))
            .toList();
        await DatabaseService.upsertCompanyNotesFromSync(notes);
      }

      // Import todos
      if (pcData['todos'] != null) {
        final todos = (pcData['todos'] as List)
            .map((j) => Todo.fromJson(j))
            .toList();
        await DatabaseService.upsertTodosFromSync(todos);
      }

      return SyncResult(
        success: true,
        message: 'Eşitleme tamamlandı! $pushed yeni kayıt gönderildi.',
        pushed: pushed,
      );
    } catch (e) {
      return SyncResult(
        success: false,
        message: 'Bağlantı hatası: Bilgisayar açık ve aynı ağda mı?',
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
