import 'dart:convert';
import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../models/models.dart';
import '../services/database_service.dart';
import '../services/sync_service.dart';

class NewVisitScreen extends StatefulWidget {
  const NewVisitScreen({super.key});

  @override
  State<NewVisitScreen> createState() => _NewVisitScreenState();
}

class _NewVisitScreenState extends State<NewVisitScreen> {
  final _formKey = GlobalKey<FormState>();
  final _companyCtrl = TextEditingController();
  final _subjectCtrl = TextEditingController();
  final _notesCtrl = TextEditingController();
  DateTime _selectedDate = DateTime.now();
  String _category = 'Sistem ve Sunucu';
  double _duration = 1.0;
  String _status = 'Tamamlandi';
  List<String> _companySuggestions = [];
  String? _base64Image;
  Uint8List? _imageBytes;
  bool _saving = false;

  final _picker = ImagePicker();

  final _categories = [
    'Sistem ve Sunucu',
    'Network ve Ağ',
    'Saha Ziyareti',
    'Kullanıcı Desteği',
    'Yedekleme ve Güvenlik',
    'Diğer',
  ];

  final _templates = {
    '🖥️ Sunucu Bakımı': {
      'subject': 'Sunucu Rutin Bakımı ve Sağlık Kontrolü',
      'notes':
          '— Sunucu disk doluluk oranları kontrol edildi.\n— Windows Update uygulandı.\n— Event Viewer günlükleri incelendi, hata yok.',
    },
    '🔥 Firewall & Ağ': {
      'subject': 'Firewall ve VLAN Kural Güncellemesi',
      'notes': '— Güvenlik duvarı kuralları güncellendi.\n— VPN erişim izinleri denetlendi.',
    },
    '💻 PC Kurulumu': {
      'subject': 'Kullanıcı Bilgisayarı Format ve Kurulum',
      'notes':
          '— Windows 11 yeniden kuruldu.\n— Domain ve Antivirüs tanımlamaları yapıldı.',
    },
    '💾 Yedek Kontrolü': {
      'subject': 'Yedekleme Kontrolü ve Veri Sağlığı',
      'notes': '— Veeam/NAS yedekleme günlükleri incelendi.\n— Test restore işlemi yapıldı.',
    },
  };

  @override
  void initState() {
    super.initState();
    _loadCompanies();
  }

  Future<void> _loadCompanies() async {
    try {
      final names = await DatabaseService.getCompanyNames();
      if (mounted) setState(() => _companySuggestions = names);
    } catch (_) {}
  }

  Future<void> _pickImage(ImageSource source) async {
    try {
      final XFile? file = await _picker.pickImage(
        source: source,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 80,
      );
      if (file != null) {
        final bytes = await file.readAsBytes();
        final base64Str = base64Encode(bytes);
        setState(() {
          _imageBytes = bytes;
          _base64Image = base64Str;
        });
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Fotoğraf seçme hatası: $e')),
        );
      }
    }
  }

  void _showImagePickerOptions() {
    showModalBottomSheet(
      context: context,
      backgroundColor: const Color(0xFF1E293B),
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      builder: (ctx) => SafeArea(
        child: Wrap(
          children: [
            ListTile(
              leading: const Icon(Icons.camera_alt, color: Color(0xFF38BDF8)),
              title: const Text('📷 Kamera İle Fotoğraf Çek', style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(ctx);
                _pickImage(ImageSource.camera);
              },
            ),
            ListTile(
              leading: const Icon(Icons.photo_library, color: Color(0xFF38BDF8)),
              title: const Text('🖼️ Galeriden Fotoğraf Seç', style: TextStyle(color: Colors.white)),
              onTap: () {
                Navigator.pop(ctx);
                _pickImage(ImageSource.gallery);
              },
            ),
          ],
        ),
      ),
    );
  }

  Future<void> _pickDate() async {
    final picked = await showDatePicker(
      context: context,
      initialDate: _selectedDate,
      firstDate: DateTime(2020),
      lastDate: DateTime(2030),
      builder: (ctx, child) => Theme(
        data: Theme.of(ctx).copyWith(
          colorScheme: const ColorScheme.dark(primary: Color(0xFF3B82F6)),
        ),
        child: child!,
      ),
    );
    if (picked != null) setState(() => _selectedDate = picked);
  }

  String _formatDateDisplay(DateTime dt) {
    final months = [
      'Ocak', 'Şubat', 'Mart', 'Nisan', 'Mayıs', 'Haziran',
      'Temmuz', 'Ağustos', 'Eylül', 'Ekim', 'Kasım', 'Aralık'
    ];
    return '${dt.day} ${months[dt.month - 1]} ${dt.year}';
  }

  String _formatDateISO(DateTime dt) {
    final y = dt.year.toString().padLeft(4, '0');
    final m = dt.month.toString().padLeft(2, '0');
    final d = dt.day.toString().padLeft(2, '0');
    return '$y-$m-$d';
  }

  void _applyTemplate(String key) {
    final t = _templates[key];
    if (t != null) {
      setState(() {
        _subjectCtrl.text = t['subject'] ?? '';
        _notesCtrl.text = t['notes'] ?? '';
      });
    }
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);

    try {
      final visit = Visit(
        visitDate: _formatDateISO(_selectedDate),
        company: _companyCtrl.text.trim(),
        subject: _subjectCtrl.text.trim().isEmpty ? _category : _subjectCtrl.text.trim(),
        technician: _category,
        duration: _duration,
        status: _status,
        workNotes: _notesCtrl.text.trim(),
        synced: false,
        imageData: _base64Image,
      );
      await DatabaseService.insertVisit(visit);

      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('✅ Kayıt eklendi! Eşitleniyor...'),
          backgroundColor: Color(0xFF059669),
          duration: Duration(seconds: 2),
        ),
      );
      _companyCtrl.clear();
      _subjectCtrl.clear();
      _notesCtrl.clear();
      setState(() {
        _selectedDate = DateTime.now();
        _duration = 1.0;
        _base64Image = null;
        _imageBytes = null;
        _saving = false;
      });

      // Reload companies list & auto-sync
      _loadCompanies();
      SyncService.fullSync();
    } catch (e) {
      if (mounted) {
        setState(() => _saving = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(content: Text('Hata: $e'), backgroundColor: Colors.red),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('➕ Yeni Saha Kaydı', style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
        backgroundColor: const Color(0xFF1E293B),
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            // Quick templates
            _buildSectionTitle('⚡ HIZLI ŞABLON SEÇİN'),
            const SizedBox(height: 8),
            SizedBox(
              height: 42,
              child: ListView(
                scrollDirection: Axis.horizontal,
                children: _templates.keys.map((k) {
                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: OutlinedButton(
                      onPressed: () => _applyTemplate(k),
                      style: OutlinedButton.styleFrom(
                        foregroundColor: const Color(0xFF60A5FA),
                        side: const BorderSide(color: Color(0xFF3B82F6)),
                        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(20)),
                        padding: const EdgeInsets.symmetric(horizontal: 14),
                      ),
                      child: Text(k, style: const TextStyle(fontSize: 13)),
                    ),
                  );
                }).toList(),
              ),
            ),
            const SizedBox(height: 20),

            // Date
            _buildSectionTitle('📅 TARİH'),
            const SizedBox(height: 6),
            InkWell(
              onTap: _pickDate,
              child: Container(
                padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                decoration: BoxDecoration(
                  color: const Color(0xFF0F172A),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFF334155)),
                ),
                child: Row(
                  mainAxisAlignment: MainAxisAlignment.spaceBetween,
                  children: [
                    Text(
                      _formatDateDisplay(_selectedDate),
                      style: const TextStyle(color: Colors.white, fontSize: 15),
                    ),
                    const Icon(Icons.calendar_today, color: Color(0xFF3B82F6), size: 20),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Company Input + Quick Selector Chips
            _buildSectionTitle('🏢 FİRMA / KURUM ADI *'),
            const SizedBox(height: 6),
            TextFormField(
              controller: _companyCtrl,
              decoration: const InputDecoration(
                hintText: 'Firma adını girin veya aşağıdan seçin...',
                prefixIcon: Icon(Icons.business, color: Color(0xFF64748B)),
              ),
              validator: (v) => v == null || v.trim().isEmpty ? 'Firma adı zorunlu' : null,
            ),

            if (_companySuggestions.isNotEmpty) ...[
              const SizedBox(height: 8),
              SizedBox(
                height: 38,
                child: ListView.builder(
                  scrollDirection: Axis.horizontal,
                  itemCount: _companySuggestions.length,
                  itemBuilder: (ctx, i) {
                    final comp = _companySuggestions[i];
                    return Padding(
                      padding: const EdgeInsets.only(right: 6),
                      child: ActionChip(
                        avatar: const Icon(Icons.apartment, size: 14, color: Color(0xFF38BDF8)),
                        label: Text(comp, style: const TextStyle(fontSize: 12, color: Colors.white)),
                        backgroundColor: const Color(0xFF1E293B),
                        side: const BorderSide(color: Color(0xFF334155)),
                        onPressed: () {
                          setState(() {
                            _companyCtrl.text = comp;
                          });
                        },
                      ),
                    );
                  },
                ),
              ),
            ],
            const SizedBox(height: 16),

            // Subject
            _buildSectionTitle('📌 ÇALIŞMA KONUSU'),
            const SizedBox(height: 6),
            TextFormField(
              controller: _subjectCtrl,
              decoration: const InputDecoration(
                hintText: 'Örn: Sunucu Bakımı ve Güncelleme...',
                prefixIcon: Icon(Icons.work_outline, color: Color(0xFF64748B)),
              ),
            ),
            const SizedBox(height: 16),

            // Category
            _buildSectionTitle('🗂️ KATEGORİ'),
            const SizedBox(height: 6),
            DropdownButtonFormField<String>(
              value: _category,
              dropdownColor: const Color(0xFF1E293B),
              decoration: const InputDecoration(
                prefixIcon: Icon(Icons.category_outlined, color: Color(0xFF64748B)),
              ),
              items: _categories.map((c) => DropdownMenuItem(value: c, child: Text(c))).toList(),
              onChanged: (v) => setState(() => _category = v!),
            ),
            const SizedBox(height: 16),

            // Duration + Status row
            Row(
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildSectionTitle('⏱️ SÜRE (SAAT)'),
                      const SizedBox(height: 6),
                      DropdownButtonFormField<double>(
                        value: _duration,
                        dropdownColor: const Color(0xFF1E293B),
                        decoration: const InputDecoration(
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                        ),
                        items: [0.5, 1.0, 1.5, 2.0, 2.5, 3.0, 4.0, 5.0, 6.0, 8.0]
                            .map((d) => DropdownMenuItem(value: d, child: Text('$d saat')))
                            .toList(),
                        onChanged: (v) => setState(() => _duration = v!),
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      _buildSectionTitle('📊 DURUM'),
                      const SizedBox(height: 6),
                      DropdownButtonFormField<String>(
                        value: _status,
                        dropdownColor: const Color(0xFF1E293B),
                        decoration: const InputDecoration(
                          contentPadding: EdgeInsets.symmetric(horizontal: 12, vertical: 14),
                        ),
                        items: const [
                          DropdownMenuItem(value: 'Tamamlandi', child: Text('✅ Tamamlandı')),
                          DropdownMenuItem(value: 'Devam Ediyor', child: Text('⏳ Devam Ediyor')),
                        ],
                        onChanged: (v) => setState(() => _status = v!),
                      ),
                    ],
                  ),
                ),
              ],
            ),
            const SizedBox(height: 16),

            // Notes
            _buildSectionTitle('📝 ÇALIŞMA DETAYLARI VE NOTLAR'),
            const SizedBox(height: 6),
            TextFormField(
              controller: _notesCtrl,
              maxLines: 4,
              decoration: const InputDecoration(
                hintText: 'Yapılan işlemleri detaylıca yazın...',
              ),
            ),
            const SizedBox(height: 16),

            // Photo Attachment Section
            _buildSectionTitle('📷 FOTOĞRAF / GÖRSEL EKLE (OPSİYONEL)'),
            const SizedBox(height: 8),
            if (_imageBytes == null)
              OutlinedButton.icon(
                onPressed: _showImagePickerOptions,
                icon: const Icon(Icons.add_a_photo, color: Color(0xFF38BDF8)),
                label: const Text('Fotoğraf Çek / Görsel Seç', style: TextStyle(color: Color(0xFF38BDF8))),
                style: OutlinedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 14),
                  side: const BorderSide(color: Color(0xFF38BDF8)),
                  shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                ),
              )
            else
              Stack(
                alignment: Alignment.topRight,
                children: [
                  Container(
                    height: 160,
                    width: double.infinity,
                    decoration: BoxDecoration(
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: const Color(0xFF38BDF8), width: 2),
                    ),
                    child: ClipRRect(
                      borderRadius: BorderRadius.circular(10),
                      child: Image.memory(_imageBytes!, fit: BoxFit.cover),
                    ),
                  ),
                  Positioned(
                    top: 8,
                    right: 8,
                    child: CircleAvatar(
                      backgroundColor: Colors.black87,
                      radius: 18,
                      child: IconButton(
                        icon: const Icon(Icons.close, color: Colors.red, size: 18),
                        onPressed: () => setState(() {
                          _imageBytes = null;
                          _base64Image = null;
                        }),
                      ),
                    ),
                  ),
                ],
              ),

            const SizedBox(height: 24),

            // Submit Button
            SizedBox(
              height: 52,
              child: ElevatedButton.icon(
                onPressed: _saving ? null : _save,
                icon: _saving
                    ? const SizedBox(
                        width: 20,
                        height: 20,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                      )
                    : const Icon(Icons.save, size: 22),
                label: Text(
                  _saving ? 'Kaydediliyor...' : '💾 SAHA KAYDINI KAYDET',
                  style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(height: 30),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String title) {
    return Text(
      title,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w700,
        color: Color(0xFF94A3B8),
        letterSpacing: 0.5,
      ),
    );
  }

  @override
  void dispose() {
    _companyCtrl.dispose();
    _subjectCtrl.dispose();
    _notesCtrl.dispose();
    super.dispose();
  }
}
