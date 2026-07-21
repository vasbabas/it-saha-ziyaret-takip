import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
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
  bool _saving = false;

  final _categories = [
    'Sistem ve Sunucu',
    'Network ve Ağ',
    'Saha Ziyareti',
    'Kullanıcı Desteği',
    'Yedekleme ve Güvenlik',
    'Diğer',
  ];

  final _templates = {
    '🖥️ Sunucu Rutin Bakımı': {
      'subject': 'Sunucu Rutin Bakımı ve Sağlık Kontrolü',
      'notes':
          '— Sunucu disk doluluk oranları kontrol edildi.\n— Windows Update uygulandı.\n— Event Viewer günlükleri incelendi, hata yok.',
    },
    '🔥 Firewall & Ağ': {
      'subject': 'Firewall ve VLAN Kural Güncellemesi',
      'notes': '— Güvenlik duvarı kuralları güncellendi.\n— VPN erişim izinleri denetlendi.',
    },
    '💻 PC Format / Kurulum': {
      'subject': 'Kullanıcı Bilgisayarı Format ve Kurulum',
      'notes':
          '— Windows 11 yeniden kuruldu.\n— Domain ve Antivirüs tanımlamaları yapıldı.',
    },
    '💾 Yedekleme Kontrolü': {
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
    final names = await DatabaseService.getCompanyNames();
    setState(() => _companySuggestions = names);
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

  void _applyTemplate(String key) {
    final t = _templates[key]!;
    _subjectCtrl.text = t['subject']!;
    _notesCtrl.text = t['notes']!;
    setState(() {});
  }

  Future<void> _save() async {
    if (!_formKey.currentState!.validate()) return;
    setState(() => _saving = true);
    final visit = Visit(
      visitDate: DateFormat('yyyy-MM-dd').format(_selectedDate),
      company: _companyCtrl.text.trim(),
      subject: _subjectCtrl.text.trim().isEmpty ? 'Genel Destek' : _subjectCtrl.text.trim(),
      technician: _category,
      duration: _duration,
      status: _status,
      workNotes: _notesCtrl.text.trim(),
      synced: false,
    );
    await DatabaseService.insertVisit(visit);
    setState(() => _saving = false);

    if (!mounted) return;
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(
        content: Text('✅ Kayıt eklendi! Eşitleme sekmesinden PC\'ye gönderin.'),
        backgroundColor: Color(0xFF059669),
        duration: Duration(seconds: 3),
      ),
    );
    _companyCtrl.clear();
    _subjectCtrl.clear();
    _notesCtrl.clear();
    setState(() {
      _selectedDate = DateTime.now();
      _duration = 1.0;
    });

    // Auto-sync in background
    SyncService.fullSync();
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
            _buildSectionTitle('⚡ Hızlı Şablon'),
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
            _buildSectionTitle('📅 Tarih'),
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
                      DateFormat('dd MMMM yyyy', 'tr').format(_selectedDate),
                      style: const TextStyle(color: Colors.white, fontSize: 15),
                    ),
                    const Icon(Icons.calendar_today, color: Color(0xFF3B82F6), size: 20),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Company
            _buildSectionTitle('🏢 Firma / Kurum *'),
            const SizedBox(height: 6),
            Autocomplete<String>(
              optionsBuilder: (value) {
                if (value.text.isEmpty) return const [];
                return _companySuggestions.where(
                  (s) => s.toLowerCase().contains(value.text.toLowerCase()),
                );
              },
              onSelected: (s) => _companyCtrl.text = s,
              fieldViewBuilder: (ctx, ctrl, fn, onSubmit) {
                // Sync external controller text
                ctrl.text = _companyCtrl.text;
                ctrl.addListener(() => _companyCtrl.text = ctrl.text);
                return TextFormField(
                  controller: ctrl,
                  focusNode: fn,
                  decoration: const InputDecoration(
                    hintText: 'Firma adı girin...',
                    prefixIcon: Icon(Icons.business, color: Color(0xFF64748B)),
                  ),
                  validator: (v) => v == null || v.trim().isEmpty ? 'Firma adı zorunlu' : null,
                );
              },
            ),
            const SizedBox(height: 16),

            // Subject
            _buildSectionTitle('📌 Çalışma Konusu'),
            const SizedBox(height: 6),
            TextFormField(
              controller: _subjectCtrl,
              decoration: const InputDecoration(
                hintText: 'Örn: Sunucu Bakımı...',
                prefixIcon: Icon(Icons.work_outline, color: Color(0xFF64748B)),
              ),
            ),
            const SizedBox(height: 16),

            // Category
            _buildSectionTitle('🗂️ Kategori'),
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
                      _buildSectionTitle('⏱️ Süre (Saat)'),
                      const SizedBox(height: 6),
                      DropdownButtonFormField<double>(
                        value: _duration,
                        dropdownColor: const Color(0xFF1E293B),
                        decoration: const InputDecoration(
                          prefixIcon: Icon(Icons.timer_outlined, color: Color(0xFF64748B)),
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
                      _buildSectionTitle('✅ Durum'),
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
            _buildSectionTitle('📝 Teknik Notlar *'),
            const SizedBox(height: 6),
            TextFormField(
              controller: _notesCtrl,
              maxLines: 5,
              decoration: const InputDecoration(
                hintText: 'Yapılan teknik işlemleri buraya yazın...',
                alignLabelWithHint: true,
              ),
              validator: (v) => v == null || v.trim().isEmpty ? 'Notlar zorunlu' : null,
            ),
            const SizedBox(height: 24),

            SizedBox(
              width: double.infinity,
              child: ElevatedButton.icon(
                onPressed: _saving ? null : _save,
                icon: _saving
                    ? const SizedBox(
                        width: 18, height: 18,
                        child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                    : const Icon(Icons.save),
                label: Text(_saving ? 'Kaydediliyor...' : '💾 Kaydı Ekle'),
                style: ElevatedButton.styleFrom(
                  padding: const EdgeInsets.symmetric(vertical: 16),
                  textStyle: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
                ),
              ),
            ),
            const SizedBox(height: 24),
          ],
        ),
      ),
    );
  }

  Widget _buildSectionTitle(String text) {
    return Text(
      text,
      style: const TextStyle(
        fontSize: 12,
        fontWeight: FontWeight.w600,
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
