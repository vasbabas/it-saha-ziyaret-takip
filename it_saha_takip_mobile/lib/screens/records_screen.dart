import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/database_service.dart';
import '../services/sync_service.dart';

class RecordsScreen extends StatefulWidget {
  const RecordsScreen({super.key});

  @override
  State<RecordsScreen> createState() => _RecordsScreenState();
}

class _RecordsScreenState extends State<RecordsScreen> {
  final _searchCtrl = TextEditingController();
  List<Visit> _visits = [];
  Map<String, List<Visit>> _groupedVisits = {};
  final Set<String> _expandedCompanies = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load([String? query]) async {
    setState(() => _loading = true);
    final visits = await DatabaseService.getVisits(query: query);

    // Group visits by company
    final Map<String, List<Visit>> grouped = {};
    for (final v in visits) {
      final key = v.company.trim().isEmpty ? 'Belirtilmemiş Firma' : v.company.trim();
      grouped.putIfAbsent(key, () => []).add(v);
    }

    setState(() {
      _visits = visits;
      _groupedVisits = grouped;
      _loading = false;
      // Auto expand folders if searching
      if (query != null && query.isNotEmpty) {
        _expandedCompanies.addAll(grouped.keys);
      }
    });
  }

  String _formatDate(String isoDate) {
    if (isoDate.isEmpty) return '';
    try {
      final dt = DateTime.parse(isoDate);
      final months = [
        'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
        'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
      ];
      return '${dt.day} ${months[dt.month - 1]} ${dt.year}';
    } catch (_) {
      return isoDate;
    }
  }

  void _showImageDialog(String base64Str) {
    try {
      final bytes = base64Decode(base64Str);
      showDialog(
        context: context,
        builder: (ctx) => Dialog(
          backgroundColor: Colors.transparent,
          insetPadding: const EdgeInsets.all(12),
          child: Stack(
            alignment: Alignment.topRight,
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(16),
                child: Image.memory(bytes, fit: BoxFit.contain),
              ),
              IconButton(
                icon: const Icon(Icons.close, color: Colors.white, size: 30),
                onPressed: () => Navigator.pop(ctx),
              ),
            ],
          ),
        ),
      );
    } catch (_) {}
  }

  @override
  Widget build(BuildContext context) {
    final companies = _groupedVisits.keys.toList()..sort();

    return Scaffold(
      appBar: AppBar(
        title: const Text('🗂️ Ziyaret & Faaliyet Günlüğü',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
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
                hintText: 'Firma, konu veya çalışma notu ara...',
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
                          padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                          itemCount: companies.length,
                          itemBuilder: (ctx, i) {
                            final compName = companies[i];
                            final list = _groupedVisits[compName] ?? [];
                            return _buildCompanyFolderCard(compName, list);
                          },
                        ),
                      ),
          ),
        ],
      ),
    );
  }

  /// Folder Accordion for Visits per Company
  Widget _buildCompanyFolderCard(String company, List<Visit> visits) {
    final isExpanded = _expandedCompanies.contains(company);
    final totalHours = visits.fold(0.0, (sum, v) => sum + v.duration);

    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Column(
        children: [
          // Company Folder Header Button
          InkWell(
            onTap: () {
              setState(() {
                if (isExpanded) {
                  _expandedCompanies.remove(company);
                } else {
                  _expandedCompanies.add(company);
                }
              });
            },
            borderRadius: BorderRadius.circular(16),
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(10),
                    decoration: BoxDecoration(
                      color: isExpanded ? const Color(0xFF2563EB) : const Color(0xFF0F172A),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: Icon(
                      isExpanded ? Icons.folder_open : Icons.folder,
                      color: isExpanded ? Colors.white : const Color(0xFF38BDF8),
                      size: 22,
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          company,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFFF8FAFC),
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          '${visits.length} Kayıt · Toplam ${totalHours.toStringAsFixed(1)} Saat',
                          style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8)),
                        ),
                      ],
                    ),
                  ),
                  Icon(
                    isExpanded ? Icons.keyboard_arrow_up : Icons.keyboard_arrow_down,
                    color: const Color(0xFF94A3B8),
                  ),
                ],
              ),
            ),
          ),

          // Expanded Visits List inside Company Folder
          if (isExpanded)
            Container(
              padding: const EdgeInsets.fromLTRB(14, 4, 14, 14),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: Color(0xFF334155), width: 1)),
              ),
              child: Column(
                children: visits.map((v) => _buildVisitItem(v)).toList(),
              ),
            ),
        ],
      ),
    );
  }

  /// Single Visit Item inside Company Folder
  Widget _buildVisitItem(Visit v) {
    final isCompleted = v.status == 'Tamamlandi';
    Uint8List? imageBytes;
    if (v.imageData != null && v.imageData!.isNotEmpty) {
      try {
        imageBytes = base64Decode(v.imageData!);
      } catch (_) {}
    }

    return Container(
      margin: const EdgeInsets.only(top: 8),
      padding: const EdgeInsets.all(12),
      decoration: BoxDecoration(
        color: const Color(0xFF0F172A),
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: const Color(0xFF1E293B)),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Row(
                children: [
                  const Icon(Icons.calendar_today, size: 12, color: Color(0xFF38BDF8)),
                  const SizedBox(width: 4),
                  Text(
                    _formatDate(v.visitDate),
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w700,
                      color: Color(0xFF38BDF8),
                    ),
                  ),
                ],
              ),
              Row(
                children: [
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: isCompleted ? const Color(0xFF064E3B) : const Color(0xFF78350F),
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
                  const SizedBox(width: 4),
                  IconButton(
                    constraints: const BoxConstraints(),
                    padding: const EdgeInsets.all(4),
                    icon: const Icon(Icons.delete_outline, color: Color(0xFFEF4444), size: 18),
                    onPressed: () async {
                      final confirm = await showDialog<bool>(
                        context: context,
                        builder: (ctx) => AlertDialog(
                          backgroundColor: const Color(0xFF1E293B),
                          title: const Text('🗑️ Kayıt Silinsin mi?', style: TextStyle(color: Colors.white)),
                          content: Text('${v.company} firmasına ait bu ziyaret kaydı silinecektir.', style: const TextStyle(color: Color(0xFFCBD5E1))),
                          actions: [
                            TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('İptal')),
                            TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Sil', style: TextStyle(color: Colors.red))),
                          ],
                        ),
                      );
                      if (confirm == true && v.id != null) {
                        await DatabaseService.deleteVisit(v.id!);
                        _load(_searchCtrl.text);
                        SyncService.fullSync();
                      }
                    },
                  ),
                ],
              ),
            ],
          ),
          const SizedBox(height: 6),

          Row(
            children: [
              const Icon(Icons.work_outline, size: 12, color: Color(0xFF94A3B8)),
              const SizedBox(width: 4),
              Expanded(
                child: Text(
                  '${v.subject} · ${v.duration} saat · Uzman: ${v.technician}',
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
            ),
          ],

          // Image Attachment Preview
          if (imageBytes != null) ...[
            const SizedBox(height: 10),
            GestureDetector(
              onTap: () => _showImageDialog(v.imageData!),
              child: Container(
                height: 120,
                width: double.infinity,
                decoration: BoxDecoration(
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: ClipRRect(
                  borderRadius: BorderRadius.circular(8),
                  child: Stack(
                    alignment: Alignment.bottomRight,
                    children: [
                      Image.memory(imageBytes, width: double.infinity, fit: BoxFit.cover),
                      Container(
                        margin: const EdgeInsets.all(6),
                        padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                        decoration: BoxDecoration(
                          color: Colors.black.withOpacity(0.7),
                          borderRadius: BorderRadius.circular(6),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(Icons.zoom_in, color: Colors.white, size: 12),
                            SizedBox(width: 4),
                            Text('Büyüt', style: TextStyle(color: Colors.white, fontSize: 10)),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ),
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
    );
  }

  Widget _emptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.folder_open, size: 72, color: Colors.white.withAlpha(30)),
          const SizedBox(height: 16),
          const Text('Henüz kayıtlı ziyaret yok',
              style: TextStyle(color: Color(0xFF64748B), fontSize: 16)),
          const SizedBox(height: 8),
          const Text('Yeni Kayıt sekmesinden ilk ziyaretinizi ekleyin.',
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
