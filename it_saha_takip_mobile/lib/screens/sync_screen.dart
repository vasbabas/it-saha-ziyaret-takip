import 'package:flutter/material.dart';
import '../services/sync_service.dart';
import '../services/database_service.dart';

class SyncScreen extends StatefulWidget {
  const SyncScreen({super.key});

  @override
  State<SyncScreen> createState() => _SyncScreenState();
}

class _SyncScreenState extends State<SyncScreen> {
  final _ipCtrl = TextEditingController();
  final _portCtrl = TextEditingController(text: '8502');
  bool _syncing = false;
  String _statusMsg = '';
  bool _statusOk = true;
  bool _connected = false;
  Map<String, int> _stats = {};

  @override
  void initState() {
    super.initState();
    _loadSavedSettings();
    _loadStats();
  }

  Future<void> _loadSavedSettings() async {
    final ip = await SyncService.getSavedIP();
    final port = await SyncService.getSavedPort();
    setState(() {
      _ipCtrl.text = ip;
      _portCtrl.text = port.toString();
    });
    if (ip.isNotEmpty) _checkConnection();
  }

  Future<void> _loadStats() async {
    final stats = await DatabaseService.getStats();
    setState(() => _stats = stats);
  }

  Future<void> _saveSettings() async {
    final ip = _ipCtrl.text.trim();
    final port = int.tryParse(_portCtrl.text.trim()) ?? 8502;
    await SyncService.saveConnection(ip, port);
    await _checkConnection();
  }

  Future<void> _checkConnection() async {
    final reachable = await SyncService.isReachable();
    setState(() => _connected = reachable);
  }

  Future<void> _sync() async {
    if (_ipCtrl.text.trim().isEmpty) {
      setState(() {
        _statusMsg = 'Lütfen bilgisayarın IP adresini girin!';
        _statusOk = false;
      });
      return;
    }
    await _saveSettings();
    setState(() {
      _syncing = true;
      _statusMsg = '🔄 Eşitleme başlatılıyor...';
      _statusOk = true;
    });
    final result = await SyncService.fullSync();
    await _loadStats();
    setState(() {
      _syncing = false;
      _statusMsg = result.message;
      _statusOk = result.success;
      _connected = result.success;
    });
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('🔄 PC ile Eşitleme',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
      ),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          // Connection status banner
          AnimatedContainer(
            duration: const Duration(milliseconds: 300),
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: BoxDecoration(
              color: _connected
                  ? const Color(0xFF064E3B)
                  : const Color(0xFF1C1917),
              borderRadius: BorderRadius.circular(12),
              border: Border.all(
                color: _connected ? const Color(0xFF059669) : const Color(0xFF44403C),
              ),
            ),
            child: Row(
              children: [
                Icon(
                  _connected ? Icons.wifi : Icons.wifi_off,
                  color: _connected ? const Color(0xFF34D399) : const Color(0xFF78716C),
                  size: 22,
                ),
                const SizedBox(width: 10),
                Text(
                  _connected ? '🟢 Bilgisayara Bağlı' : '🔴 Bilgisayara Bağlanamıyor',
                  style: TextStyle(
                    fontWeight: FontWeight.w600,
                    color: _connected ? const Color(0xFF34D399) : const Color(0xFFA8A29E),
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 20),

          // IP Settings card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('🖥️ Bilgisayar Bağlantı Ayarları',
                      style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF60A5FA))),
                  const SizedBox(height: 6),
                  const Text(
                    'Bilgisayarın sol panelindeki QR kodun altındaki IP adresini girin. '
                    'Telefon ve bilgisayar aynı Wi-Fi ağında olmalı.',
                    style: TextStyle(fontSize: 12, color: Color(0xFF94A3B8), height: 1.5),
                  ),
                  const SizedBox(height: 14),
                  TextField(
                    controller: _ipCtrl,
                    keyboardType: const TextInputType.numberWithOptions(decimal: true),
                    decoration: const InputDecoration(
                      labelText: 'Bilgisayar IP Adresi',
                      hintText: 'Örn: 192.168.1.100',
                      prefixIcon: Icon(Icons.computer, color: Color(0xFF64748B)),
                    ),
                  ),
                  const SizedBox(height: 12),
                  Row(
                    children: [
                      Expanded(
                        flex: 2,
                        child: TextField(
                          controller: _portCtrl,
                          keyboardType: TextInputType.number,
                          decoration: const InputDecoration(
                            labelText: 'Port',
                            hintText: '8502',
                            prefixIcon: Icon(Icons.settings_ethernet, color: Color(0xFF64748B)),
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        flex: 3,
                        child: ElevatedButton.icon(
                          onPressed: _saveSettings,
                          icon: const Icon(Icons.save, size: 18),
                          label: const Text('Kaydet & Test Et'),
                          style: ElevatedButton.styleFrom(
                            padding: const EdgeInsets.symmetric(vertical: 14),
                            backgroundColor: const Color(0xFF1D4ED8),
                          ),
                        ),
                      ),
                    ],
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 16),

          // Sync button
          SizedBox(
            width: double.infinity,
            child: ElevatedButton.icon(
              onPressed: _syncing ? null : _sync,
              icon: _syncing
                  ? const SizedBox(
                      width: 18,
                      height: 18,
                      child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2),
                    )
                  : const Icon(Icons.sync),
              label: Text(
                _syncing ? 'Eşitleniyor...' : '🚀 Bilgisayarla Şimdi Eşitle',
                style: const TextStyle(fontSize: 16, fontWeight: FontWeight.bold),
              ),
              style: ElevatedButton.styleFrom(
                padding: const EdgeInsets.symmetric(vertical: 18),
                backgroundColor: const Color(0xFF059669),
              ),
            ),
          ),

          // Status message
          if (_statusMsg.isNotEmpty) ...[
            const SizedBox(height: 12),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(
                color: _statusOk ? const Color(0xFF064E3B) : const Color(0xFF450A0A),
                borderRadius: BorderRadius.circular(10),
                border: Border.all(
                  color: _statusOk ? const Color(0xFF059669) : const Color(0xFF991B1B),
                ),
              ),
              child: Text(
                _statusMsg,
                style: TextStyle(
                  color: _statusOk ? const Color(0xFF6EE7B7) : const Color(0xFFFCA5A5),
                  fontSize: 13,
                ),
              ),
            ),
          ],
          const SizedBox(height: 20),

          // Stats card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('📊 Telefondaki Veri İstatistikleri',
                      style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF60A5FA))),
                  const SizedBox(height: 14),
                  _statRow(Icons.folder_outlined, 'Ziyaret Kaydı', '${_stats['visits'] ?? 0} kayıt'),
                  const Divider(color: Color(0xFF334155), height: 20),
                  _statRow(Icons.business_outlined, 'Firma Envanter Notu', '${_stats['notes'] ?? 0} firma'),
                  const Divider(color: Color(0xFF334155), height: 20),
                  _statRow(Icons.checklist_outlined, 'Görevler', '${_stats['todos'] ?? 0} görev'),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Info card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const Text('ℹ️ Nasıl Çalışır?',
                      style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: Color(0xFF60A5FA))),
                  const SizedBox(height: 10),
                  _infoStep('1', 'Bilgisayarda IT Saha Takip uygulaması açık olmalı.'),
                  _infoStep('2', 'Telefon ve bilgisayar aynı Wi-Fi ağında olmalı.'),
                  _infoStep('3', '"Eşitle" butonuna basın — telefondaki yeni kayıtlar bilgisayara, bilgisayardaki kayıtlar telefona aktarılır.'),
                  _infoStep('4', 'Wi-Fi yokken bile yeni kayıt girebilirsiniz. Bağlandığınızda otomatik eşitlenir.'),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }

  Widget _statRow(IconData icon, String label, String value) {
    return Row(
      children: [
        Icon(icon, size: 18, color: const Color(0xFF94A3B8)),
        const SizedBox(width: 10),
        Expanded(child: Text(label, style: const TextStyle(color: Color(0xFFCBD5E1), fontSize: 13))),
        Text(value,
            style: const TextStyle(
                color: Color(0xFF38BDF8), fontWeight: FontWeight.w600, fontSize: 13)),
      ],
    );
  }

  Widget _infoStep(String num, String text) {
    return Padding(
      padding: const EdgeInsets.only(bottom: 10),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Container(
            width: 22,
            height: 22,
            decoration: BoxDecoration(
              color: const Color(0xFF1D4ED8),
              borderRadius: BorderRadius.circular(11),
            ),
            alignment: Alignment.center,
            child: Text(num, style: const TextStyle(fontSize: 11, fontWeight: FontWeight.bold, color: Colors.white)),
          ),
          const SizedBox(width: 10),
          Expanded(
            child: Text(text,
                style: const TextStyle(fontSize: 12, color: Color(0xFF94A3B8), height: 1.5)),
          ),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _ipCtrl.dispose();
    _portCtrl.dispose();
    super.dispose();
  }
}
