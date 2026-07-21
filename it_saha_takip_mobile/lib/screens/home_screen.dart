import 'dart:async';
import 'package:flutter/material.dart';
import '../services/sync_service.dart';
import 'new_visit_screen.dart';
import 'records_screen.dart';
import 'inventory_screen.dart';
import 'todos_screen.dart';
import 'sync_screen.dart';

class HomeScreen extends StatefulWidget {
  const HomeScreen({super.key});

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  int _refreshCounter = 0;
  Timer? _autoSyncTimer;

  @override
  void initState() {
    super.initState();
    // Initial silent sync on app open
    SyncService.fullSync();

    // Periodic silent auto-sync every 30 seconds
    _autoSyncTimer = Timer.periodic(const Duration(seconds: 30), (_) {
      SyncService.fullSync();
    });
  }

  @override
  void dispose() {
    _autoSyncTimer?.cancel();
    super.dispose();
  }

  Widget _buildScreen(int index) {
    switch (index) {
      case 0:
        return const NewVisitScreen();
      case 1:
        return RecordsScreen(key: ValueKey('records_$_refreshCounter'));
      case 2:
        return InventoryScreen(key: ValueKey('inventory_$_refreshCounter'));
      case 3:
        return TodosScreen(key: ValueKey('todos_$_refreshCounter'));
      case 4:
        return SyncScreen(key: ValueKey('sync_$_refreshCounter'));
      default:
        return const NewVisitScreen();
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: _buildScreen(_currentIndex),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Color(0xFF334155), width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (i) {
            setState(() {
              _currentIndex = i;
              _refreshCounter++;
            });
          },
          items: const [
            BottomNavigationBarItem(
              icon: Icon(Icons.add_circle_outline),
              activeIcon: Icon(Icons.add_circle),
              label: 'Yeni Kayıt',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.folder_outlined),
              activeIcon: Icon(Icons.folder),
              label: 'Günlükler',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.vpn_key_outlined),
              activeIcon: Icon(Icons.vpn_key),
              label: 'Envanter',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.checklist_outlined),
              activeIcon: Icon(Icons.checklist),
              label: 'Görevler',
            ),
            BottomNavigationBarItem(
              icon: Icon(Icons.sync_outlined),
              activeIcon: Icon(Icons.sync),
              label: 'Eşitle',
            ),
          ],
        ),
      ),
    );
  }
}
