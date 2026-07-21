import 'package:flutter/material.dart';
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

  final List<Widget> _screens = const [
    NewVisitScreen(),
    RecordsScreen(),
    InventoryScreen(),
    TodosScreen(),
    SyncScreen(),
  ];

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: _screens,
      ),
      bottomNavigationBar: Container(
        decoration: const BoxDecoration(
          border: Border(top: BorderSide(color: Color(0xFF334155), width: 1)),
        ),
        child: BottomNavigationBar(
          currentIndex: _currentIndex,
          onTap: (i) => setState(() => _currentIndex = i),
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
