import 'dart:convert';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import '../models/models.dart';
import '../services/database_service.dart';
import '../services/sync_service.dart';

class InventoryScreen extends StatefulWidget {
  const InventoryScreen({super.key});

  @override
  State<InventoryScreen> createState() => _InventoryScreenState();
}

class _InventoryScreenState extends State<InventoryScreen> {
  final _searchCtrl = TextEditingController();
  List<CompanyNote> _notes = [];
  final Set<int> _revealed = {};
  final Set<String> _expandedCompanies = {};
  bool _loading = true;

  final _picker = ImagePicker();

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
      if (query != null && query.isNotEmpty) {
        _expandedCompanies.addAll(notes.map((n) => n.company));
      }
    });
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

  void _showAddNoteDialog() {
    final companyCtrl = TextEditingController();
    final ipCtrl = TextEditingController();
    final vpnCtrl = TextEditingController();
    final credCtrl = TextEditingController();
    final notesCtrl = TextEditingController();
    final formKey = GlobalKey<FormState>();

    String? base64Image;
    Uint8List? imageBytes;

    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: const Color(0xFF1E293B),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) {
        return StatefulBuilder(
          builder: (dialogCtx, setDialogState) {
            Future<void> pickImg(ImageSource source) async {
              try {
                final file = await _picker.pickImage(
                  source: source,
                  maxWidth: 1024,
                  maxHeight: 1024,
                  imageQuality: 80,
                );
                if (file != null) {
                  final b = await file.readAsBytes();
                  setDialogState(() {
                    imageBytes = b;
                    base64Image = base64Encode(b);
                  });
                }
              } catch (_) {}
            }

            return Padding(
              padding: EdgeInsets.only(
                bottom: MediaQuery.of(dialogCtx).viewInsets.bottom + 20,
                top: 20,
                left: 16,
                right: 16,
              ),
              child: Form(
                key: formKey,
                child: SingleChildScrollView(
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          const Text('🔑 Yeni Envanter & Şifre Ekle',
                              style: TextStyle(
                                  fontSize: 16,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFF38BDF8))),
                          IconButton(
                            icon: const Icon(Icons.close, color: Color(0xFF94A3B8)),
                            onPressed: () => Navigator.pop(dialogCtx),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),

                      TextFormField(
                        controller: companyCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Firma / Kurum Adı *',
                          hintText: 'Örn: ABC Holding',
                          prefixIcon: Icon(Icons.business, color: Color(0xFF64748B)),
                        ),
                        validator: (v) => v == null || v.trim().isEmpty ? 'Firma adı zorunlu' : null,
                      ),
                      const SizedBox(height: 12),

                      TextFormField(
                        controller: ipCtrl,
                        decoration: const InputDecoration(
                          labelText: 'IP / Subnet / Blok',
                          hintText: 'Örn: 192.168.1.0/24',
                          prefixIcon: Icon(Icons.lan_outlined, color: Color(0xFF64748B)),
                        ),
                      ),
                      const SizedBox(height: 12),

                      TextFormField(
                        controller: vpnCtrl,
                        decoration: const InputDecoration(
                          labelText: 'VPN / Uzak Erişim Detayları',
                          hintText: 'Örn: FortiClient SSL-VPN vpn.firma.com',
                          prefixIcon: Icon(Icons.vpn_lock_outlined, color: Color(0xFF64748B)),
                        ),
                      ),
                      const SizedBox(height: 12),

                      TextFormField(
                        controller: credCtrl,
                        decoration: const InputDecoration(
                          labelText: 'Giriş Bilgileri (Kullanıcı & Şifre)',
                          hintText: 'Örn: admin / Secr3tP@ss!',
                          prefixIcon: Icon(Icons.lock_outlined, color: Color(0xFF64748B)),
                        ),
                      ),
                      const SizedBox(height: 12),

                      TextFormField(
                        controller: notesCtrl,
                        maxLines: 3,
                        decoration: const InputDecoration(
                          labelText: 'Diğer Notlar / Açıklama',
                          hintText: 'Sunucu modelleri, yetkili kişi telefon vb...',
                        ),
                      ),
                      const SizedBox(height: 14),

                      // Photo Button in Modal
                      if (imageBytes == null)
                        OutlinedButton.icon(
                          onPressed: () {
                            showModalBottomSheet(
                              context: dialogCtx,
                              backgroundColor: const Color(0xFF0F172A),
                              builder: (bCtx) => SafeArea(
                                child: Wrap(
                                  children: [
                                    ListTile(
                                      leading: const Icon(Icons.camera_alt, color: Color(0xFF38BDF8)),
                                      title: const Text('📷 Kamera İle Çek', style: TextStyle(color: Colors.white)),
                                      onTap: () {
                                        Navigator.pop(bCtx);
                                        pickImg(ImageSource.camera);
                                      },
                                    ),
                                    ListTile(
                                      leading: const Icon(Icons.photo_library, color: Color(0xFF38BDF8)),
                                      title: const Text('🖼️ Galeriden Seç', style: TextStyle(color: Colors.white)),
                                      onTap: () {
                                        Navigator.pop(bCtx);
                                        pickImg(ImageSource.gallery);
                                      },
                                    ),
                                  ],
                                ),
                              ),
                            );
                          },
                          icon: const Icon(Icons.add_a_photo, color: Color(0xFF38BDF8), size: 18),
                          label: const Text('📷 Kabin / Cihaz Fotoğrafı Ekle', style: TextStyle(color: Color(0xFF38BDF8), fontSize: 13)),
                        )
                      else
                        Stack(
                          alignment: Alignment.topRight,
                          children: [
                            Container(
                              height: 120,
                              width: double.infinity,
                              decoration: BoxDecoration(
                                borderRadius: BorderRadius.circular(10),
                                border: Border.all(color: const Color(0xFF38BDF8)),
                              ),
                              child: ClipRRect(
                                borderRadius: BorderRadius.circular(10),
                                child: Image.memory(imageBytes!, fit: BoxFit.cover),
                              ),
                            ),
                            IconButton(
                              icon: const Icon(Icons.close, color: Colors.red),
                              onPressed: () => setDialogState(() {
                                imageBytes = null;
                                base64Image = null;
                              }),
                            ),
                          ],
                        ),

                      const SizedBox(height: 20),

                      SizedBox(
                        width: double.infinity,
                        child: ElevatedButton.icon(
                          onPressed: () async {
                            if (!formKey.currentState!.validate()) return;
                            final note = CompanyNote(
                              company: companyCtrl.text.trim(),
                              ipSubnet: ipCtrl.text.trim().isEmpty ? null : ipCtrl.text.trim(),
                              vpnDetails: vpnCtrl.text.trim().isEmpty ? null : vpnCtrl.text.trim(),
                              credentials: credCtrl.text.trim().isEmpty ? null : credCtrl.text.trim(),
                              otherNotes: notesCtrl.text.trim().isEmpty ? null : notesCtrl.text.trim(),
                              synced: false,
                              imageData: base64Image,
                            );

                            await DatabaseService.insertCompanyNote(note);
                            if (mounted) Navigator.pop(dialogCtx);
                            _load();

                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                const SnackBar(
                                  content: Text('✅ Envanter kaydı eklendi! Eşitleniyor...'),
                                  backgroundColor: Color(0xFF059669),
                                  duration: Duration(seconds: 2),
                                ),
                              );
                            }

                            SyncService.fullSync();
                          },
                          icon: const Icon(Icons.save),
                          label: const Text('💾 Envanteri Kaydet'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            );
          },
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🔑 BT Envanter Defteri',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        actions: [
          IconButton(icon: const Icon(Icons.refresh), onPressed: () => _load(_searchCtrl.text)),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _searchCtrl,
                    onChanged: (v) => _load(v),
                    decoration: InputDecoration(
                      hintText: 'Firma, IP veya not ara...',
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
                const SizedBox(width: 10),
                ElevatedButton.icon(
                  onPressed: _showAddNoteDialog,
                  icon: const Icon(Icons.add, size: 20),
                  label: const Text('Ekle'),
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                ),
              ],
            ),
          ),

          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator(color: Color(0xFF3B82F6)))
                : _notes.isEmpty
                    ? _emptyState()
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                        itemCount: _notes.length,
                        itemBuilder: (ctx, i) => _buildCompanyFolderCard(_notes[i], i),
                      ),
          ),
        ],
      ),
    );
  }

  /// Folder Accordion View per Company
  Widget _buildCompanyFolderCard(CompanyNote n, int index) {
    final isExpanded = _expandedCompanies.contains(n.company);
    final revealed = _revealed.contains(index);

    Uint8List? imageBytes;
    if (n.imageData != null && n.imageData!.isNotEmpty) {
      try {
        imageBytes = base64Decode(n.imageData!);
      } catch (_) {}
    }

    return Card(
      margin: const EdgeInsets.only(bottom: 10),
      child: Column(
        children: [
          // Company Folder Header Button
          InkWell(
            onTap: () {
              setState(() {
                if (isExpanded) {
                  _expandedCompanies.remove(n.company);
                } else {
                  _expandedCompanies.add(n.company);
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
                          n.company,
                          style: const TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                            color: Color(0xFFF8FAFC),
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          n.ipSubnet ?? 'IP tanımlanmamış',
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

          // Expanded Details Section
          if (isExpanded)
            Container(
              padding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
              decoration: const BoxDecoration(
                border: Border(top: BorderSide(color: Color(0xFF334155), width: 1)),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const SizedBox(height: 12),
                  _infoRow(Icons.lan_outlined, 'IP / Subnet', n.ipSubnet ?? '—'),
                  const SizedBox(height: 8),
                  _infoRow(Icons.vpn_lock_outlined, 'VPN / Erişim', n.vpnDetails ?? '—'),
                  const SizedBox(height: 10),

                  // Credentials box
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: const Color(0xFF0F172A),
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(color: const Color(0xFF334155)),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Row(
                          children: [
                            Icon(Icons.lock_outlined, size: 14, color: Color(0xFFFBBF24)),
                            SizedBox(width: 6),
                            Text('Giriş Bilgileri / Şifreler',
                                style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: Color(0xFFFBBF24),
                                    letterSpacing: 0.5)),
                          ],
                        ),
                        const SizedBox(height: 6),
                        SelectableText(
                          revealed ? (n.credentials ?? '—') : '••••••••••••••••',
                          style: TextStyle(
                            fontSize: 13,
                            color: revealed ? const Color(0xFFF8FAFC) : const Color(0xFF94A3B8),
                            fontFamily: revealed ? null : 'monospace',
                          ),
                        ),
                        const SizedBox(height: 10),
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
                              label: Text(revealed ? 'Gizle' : 'Göster',
                                  style: const TextStyle(fontSize: 12)),
                              style: OutlinedButton.styleFrom(
                                foregroundColor: const Color(0xFF60A5FA),
                                side: const BorderSide(color: Color(0xFF3B82F6)),
                                padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 6),
                                minimumSize: Size.zero,
                                tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                                shape: RoundedRectangleBorder(
                                    borderRadius: BorderRadius.circular(8)),
                              ),
                            ),
                            if (revealed && n.credentials != null) ...[
                              const SizedBox(width: 8),
                              OutlinedButton.icon(
                                onPressed: () {
                                  Clipboard.setData(ClipboardData(text: n.credentials!));
                                  ScaffoldMessenger.of(context).showSnackBar(
                                    const SnackBar(
                                      content: Text('📋 Şifre panoya kopyalandı!'),
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
                                  shape: RoundedRectangleBorder(
                                      borderRadius: BorderRadius.circular(8)),
                                ),
                              ),
                            ],
                          ],
                        ),
                      ],
                    ),
                  ),

                  if (n.otherNotes != null && n.otherNotes!.isNotEmpty) ...[
                    const SizedBox(height: 10),
                    _infoRow(Icons.notes_outlined, 'Açıklama Notu', n.otherNotes!),
                  ],

                  // Photo Attachment Preview
                  if (imageBytes != null) ...[
                    const SizedBox(height: 10),
                    GestureDetector(
                      onTap: () => _showImageDialog(n.imageData!),
                      child: Container(
                        height: 120,
                        width: double.infinity,
                        decoration: BoxDecoration(
                          borderRadius: BorderRadius.circular(8),
                          border: Border.all(color: const Color(0xFF334155)),
                        ),
                        child: ClipRRect(
                          borderRadius: BorderRadius.circular(8),
                          child: Image.memory(imageBytes, width: double.infinity, fit: BoxFit.cover),
                        ),
                      ),
                    ),
                  ],

                  if (!n.synced)
                    const Padding(
                      padding: EdgeInsets.only(top: 10),
                      child: Row(
                        children: [
                          Icon(Icons.cloud_upload_outlined, size: 12, color: Color(0xFFFBBF24)),
                          SizedBox(width: 4),
                          Text('PC\'ye henüz eşitlenmedi',
                              style: TextStyle(fontSize: 10, color: Color(0xFFFBBF24))),
                        ],
                      ),
                    ),

                  const SizedBox(height: 10),
                  Row(
                    mainAxisAlignment: MainAxisAlignment.end,
                    children: [
                      TextButton.icon(
                        onPressed: () async {
                          final confirm = await showDialog<bool>(
                            context: context,
                            builder: (ctx) => AlertDialog(
                              backgroundColor: const Color(0xFF1E293B),
                              title: const Text('🗑️ Envanter Silinsin mi?', style: TextStyle(color: Colors.white)),
                              content: Text('${n.company} firmasına ait envanter bilgileri silinecek.', style: const TextStyle(color: Color(0xFFCBD5E1))),
                              actions: [
                                TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('İptal')),
                                TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Sil', style: TextStyle(color: Colors.red))),
                              ],
                            ),
                          );
                          if (confirm == true) {
                            await DatabaseService.deleteCompanyNote(n.company);
                            _load();
                            if (mounted) {
                              ScaffoldMessenger.of(context).showSnackBar(
                                SnackBar(
                                  content: Text('🗑️ ${n.company} envanteri silindi.'),
                                  backgroundColor: const Color(0xFFDC2626),
                                  duration: const Duration(seconds: 2),
                                ),
                              );
                            }
                          }
                        },
                        icon: const Icon(Icons.delete_outline, color: Color(0xFFEF4444), size: 16),
                        label: const Text('Envanteri Sil', style: TextStyle(color: Color(0xFFEF4444), fontSize: 12)),
                      ),
                    ],
                  ),
                ],
              ),
            ),
        ],
      ),
    );
  }

  Widget _infoRow(IconData icon, String label, String value) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Icon(icon, size: 14, color: const Color(0xFF94A3B8)),
        const SizedBox(width: 6),
        Text('$label: ',
            style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8), fontWeight: FontWeight.w600)),
        Expanded(
          child: Text(value,
              style: const TextStyle(fontSize: 12, color: Color(0xFFCBD5E1))),
        ),
      ],
    );
  }

  Widget _emptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.folder_open, size: 72, color: Colors.white.withAlpha(30)),
          const SizedBox(height: 16),
          const Text('Henüz envanter kaydı yok',
              style: TextStyle(color: Color(0xFF64748B), fontSize: 16)),
          const SizedBox(height: 8),
          const Text('Sağ üstteki "Ekle" butonuna basarak veya\nPC ile eşitleyerek firma notu ekleyin.',
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
