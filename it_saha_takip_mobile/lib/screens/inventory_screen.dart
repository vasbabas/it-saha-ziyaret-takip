import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../models/models.dart';
import '../services/database_service.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  final _searchCtrl = TextEditingController();
  List<CompanyNote> _notes = [];
  final Set<int> _revealed = {};
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load([String? query]) async {
    setState(() => _loading = true);
    final notes = await DatabaseService.getCompanyNotes(query: query);
    setState(() {
      _notes = notes;
      _loading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🔑 BT Envanter & Şifreler',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: () => _load(_searchCtrl.text)),
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
                hintText: 'Firma veya IP ara...',
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
                : _notes.isEmpty
                    ? _emptyState()
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
                        itemCount: _notes.length,
                        itemBuilder: (ctx, i) => _buildNoteCard(_notes[i], i),
                      ),
          ),
        ],
      ),
    );
  }

  Widget _buildNoteCard(CompanyNote n, int index) {
    final revealed = _revealed.contains(index);
    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Padding(
        padding: const EdgeInsets.all(14),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              n.company,
              style: const TextStyle(
                  fontSize: 16, fontWeight: FontWeight.w700, color: Color(0xFF38BDF8)),
            ),
            const SizedBox(height: 10),
            _infoRow(Icons.lan_outlined, 'IP / Subnet', n.ipSubnet ?? '—'),
            const SizedBox(height: 6),
            _infoRow(Icons.vpn_lock_outlined, 'VPN / Erişim', n.vpnDetails ?? '—'),
            const SizedBox(height: 8),
            // Credentials with reveal toggle
            Container(
              padding: const EdgeInsets.all(10),
              decoration: BoxDecoration(
                color: const Color(0xFF0F172A),
                borderRadius: BorderRadius.circular(8),
                border: Border.all(color: const Color(0xFF334155)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Row(
                    children: [
                      Icon(Icons.lock_outlined, size: 14, color: Color(0xFFFBBF24)),
                      SizedBox(width: 6),
                      Text('Giriş Bilgileri',
                          style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w600,
                              color: Color(0xFFFBBF24),
                              letterSpacing: 0.5)),
                    ],
                  ),
                  const SizedBox(height: 6),
                  Text(
                    revealed ? (n.credentials ?? '—') : '••••••••••••••••',
                    style: TextStyle(
                      fontSize: 13,
                      color: revealed ? const Color(0xFFF8FAFC) : const Color(0xFF94A3B8),
                      fontFamily: revealed ? null : 'monospace',
                    ),
                  ),
                  const SizedBox(height: 8),
                  Row(
                    children: [
                      OutlinedButton.icon(
                        onPressed: () => setState(() {
                          if (revealed) {
                            _revealed.remove(index);
                          } else {
                            _revealed.add(index);
                          }
                        }),
                        icon: Icon(
                          revealed ? Icons.visibility_off : Icons.visibility,
                          size: 14,
                        ),
                        label: Text(revealed ? 'Gizle' : 'Göster', style: const TextStyle(fontSize: 12)),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFF60A5FA),
                          side: const BorderSide(color: Color(0xFF3B82F6)),
                          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                        ),
                      ),
                      if (revealed && n.credentials != null) ...[
                        const SizedBox(width: 8),
                        OutlinedButton.icon(
                          onPressed: () {
                            Clipboard.setData(ClipboardData(text: n.credentials!));
                            ScaffoldMessenger.of(context).showSnackBar(
                              const SnackBar(
                                content: Text('📋 Panoya kopyalandı!'),
                                duration: Duration(seconds: 2),
                                backgroundColor: Color(0xFF1D4ED8),
                              ),
                            );
                          },
                          icon: const Icon(Icons.copy, size: 14),
                          label: const Text('Kopyala', style: TextStyle(fontSize: 12)),
                          style: OutlinedButton.styleFrom(
                            foregroundColor: const Color(0xFF94A3B8),
                            side: const BorderSide(color: Color(0xFF475569)),
                            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                            minimumSize: Size.zero,
                            tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(8)),
                          ),
                        ),
                      ],
                    ],
                  ),
                ],
              ),
            ),
            if (n.otherNotes != null && n.otherNotes!.isNotEmpty) ...[
              const SizedBox(height: 8),
              _infoRow(Icons.notes_outlined, 'Notlar', n.otherNotes!),
            ],
          ],
        ),
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 14, color: const Color(0xFF94A3B8)),
        const SizedBox(width: 6),
        Text('$label: ', style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8))),
        Expanded(
          child: Text(value,
              style: const TextStyle(fontSize: 12, color: Color(0xFFCBD5E1)),
              overflow: TextOverflow.ellipsis,
              maxLines: 2),
        ),
      ],
    );
  }

  Widget _emptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.vpn_key_off, size: 72, color: Colors.white.withAlpha(30)),
          const SizedBox(height: 16),
          const Text('Envanter notu bulunamadı',
              style: TextStyle(color: Color(0xFF64748B), fontSize: 16)),
          const SizedBox(height: 8),
          const Text('PC ile eşitleyin veya\nbilgisayardan envanter ekleyin.',
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
