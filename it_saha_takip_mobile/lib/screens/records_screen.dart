import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../models/models.dart';
import '../services/database_service.dart';

class RecordsScreen extends StatefulWidget {
  const RecordsScreen({super.key});

  @override
  State<RecordsScreen> createState() => _RecordsScreenState();
}

class _RecordsScreenState extends State<RecordsScreen> {
  final _searchCtrl = TextEditingController();
  List<Visit> _visits = [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load([String? query]) async {
    setState(() => _loading = true);
    final visits = await DatabaseService.getVisits(query: query);
    setState(() {
      _visits = visits;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🗂️ Ziyaret Günlüğü', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => _load(_searchCtrl.text),
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: TextField(
              controller: _searchCtrl,
              onChanged: (v) => _load(v),
              decoration: InputDecoration(
                hintText: 'Firma, konu veya not ara...',
                prefixIcon: const Icon(Icons.search, color: Color(0xFF64748B)),
                suffixIcon: _searchCtrl.text.isNotEmpty
                    ? IconButton(
                        icon: const Icon(Icons.clear, color: Color(0xFF64748B)),
                        onPressed: () {
                          _searchCtrl.clear();
                          _load();
                        },
                      )
                    : null,
              ),
            ),
          ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF3B82F6)))
                : _visits.isEmpty
                    ? _emptyState()
                    : RefreshIndicator(
                        onRefresh: () => _load(_searchCtrl.text),
                        color: const Color(0xFF3B82F6),
                        child: ListView.builder(
                          padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                          itemCount: _visits.length,
                          itemBuilder: (ctx, i) => _buildVisitCard(_visits[i]),
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildVisitCard(Visit v) {
    final isCompleted = v.status == 'Tamamlandi';
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(
                  child: Text(
                    v.company,
                    style: const TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF38BDF8),
                    ),
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                  decoration: BoxDecoration(
                    color: isCompleted
                        ? const Color(0xFF064E3B)
                        : const Color(0xFF78350F),
                    borderRadius: BorderRadius.circular(20),
                  ),
                  child: Text(
                    isCompleted ? '✅ Tamamlandı' : '⏳ Devam Ediyor',
                    style: TextStyle(
                      fontSize: 10,
                      fontWeight: FontWeight.w600,
                      color: isCompleted ? const Color(0xFF34D399) : const Color(0xFFFBBF24),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 6),
            Row(
              children: [
                const Icon(Icons.calendar_today, size: 12, color: Color(0xFF94A3B8)),
                const SizedBox(width: 4),
                Text(
                  _formatDate(v.visitDate),
                  style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                ),
                const SizedBox(width: 12),
                const Icon(Icons.pin_drop, size: 12, color: Color(0xFF94A3B8)),
                const SizedBox(width: 4),
                Expanded(
                  child: Text(
                    '${v.subject} · ${v.duration} saat',
                    style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                    overflow: TextOverflow.ellipsis,
                  ),
                ),
              ],
            ),
            if (v.workNotes.isNotEmpty) ...[
              const SizedBox(height: 8),
              Text(
                v.workNotes,
                style: const TextStyle(fontSize: 13, color: Color(0xFFCBD5E1), height: 1.4),
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            if (!v.synced)
              const Padding(
                padding: EdgeInsets.only(top: 8),
                child: Row(
                  children: [
                    Icon(Icons.cloud_upload_outlined, size: 12, color: Color(0xFFFBBF24)),
                    SizedBox(width: 4),
                    Text('PC\'ye henüz eşitlenmedi',
                        style: TextStyle(fontSize: 10, color: Color(0xFFFBBF24))),
                  ],
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _formatDate(String raw) {
    try {
      final d = DateTime.parse(raw);
      return DateFormat('dd MMM yyyy', 'tr').format(d);
    } catch (_) {
      return raw;
    }
  }

  Widget _emptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.folder_open, size: 72, color: Colors.white.withAlpha(30)),
          const SizedBox(height: 16),
          const Text('Kayıt bulunamadı',
              style: TextStyle(color: Color(0xFF64748B), fontSize: 16)),
          const SizedBox(height: 8),
          const Text('"Yeni Kayıt" sekmesinden kayıt ekleyin\nveya PC ile eşitleyin.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFF475569), fontSize: 13)),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _searchCtrl.dispose();
    super.dispose();
  }
}
