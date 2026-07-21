import 'package:flutter/material.dart';
import '../models/models.dart';
import '../services/database_service.dart';

class TodosScreen extends StatefulWidget {
  const TodosScreen({super.key});

  @override
  State<TodosScreen> createState() => _TodosScreenState();
}

class _TodosScreenState extends State<TodosScreen> {
  final _addCtrl = TextEditingController();
  List<Todo> _todos = [];

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final todos = await DatabaseService.getTodos();
    setState(() => _todos = todos);
  }

  Future<void> _add() async {
    final t = _addCtrl.text.trim();
    if (t.isEmpty) return;
    await DatabaseService.insertTodo(Todo(title: t));
    _addCtrl.clear();
    _load();
  }

  Future<void> _toggle(Todo todo) async {
    await DatabaseService.updateTodoDone(todo.id!, !todo.isDone);
    _load();
  }

  Future<void> _delete(Todo todo) async {
    await DatabaseService.deleteTodo(todo.id!);
    _load();
  }

  @override
  Widget build(BuildContext context) {
    final pending = _todos.where((t) => !t.isDone).toList();
    final done = _todos.where((t) => t.isDone).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('📋 Görevler',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
      ),
      body: Column(
        children: [
          // Add new todo
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 12, 16, 8),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _addCtrl,
                    onSubmitted: (_) => _add(),
                    decoration: const InputDecoration(
                      hintText: 'Yeni görev ekle...',
                      prefixIcon: Icon(Icons.add_task, color: Color(0xFF64748B)),
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                ElevatedButton(
                  onPressed: _add,
                  style: ElevatedButton.styleFrom(
                    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
                    shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
                  ),
                  child: const Icon(Icons.add),
                ),
              ],
            ),
          ),
          Expanded(
            child: _todos.isEmpty
                ? _emptyState()
                : ListView(
                    padding: const EdgeInsets.fromLTRB(16, 4, 16, 16),
                    children: [
                      if (pending.isNotEmpty) ...[
                        _sectionHeader('📌 Bekleyen (${pending.length})'),
                        ...pending.map((t) => _buildTodoCard(t)),
                      ],
                      if (done.isNotEmpty) ...[
                        _sectionHeader('✅ Tamamlanan (${done.length})'),
                        ...done.map((t) => _buildTodoCard(t)),
                      ],
                    ],
                  ),
          ),
        ],
      ),
    );
  }

  Widget _sectionHeader(String text) {
    return Padding(
      padding: const EdgeInsets.fromLTRB(0, 12, 0, 6),
      child: Text(text,
          style: const TextStyle(
              fontSize: 12,
              fontWeight: FontWeight.w600,
              color: Color(0xFF94A3B8),
              letterSpacing: 0.5)),
    );
  }

  Widget _buildTodoCard(Todo todo) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        leading: GestureDetector(
          onTap: () => _toggle(todo),
          child: Container(
            width: 24,
            height: 24,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: todo.isDone ? const Color(0xFF059669) : Colors.transparent,
              border: Border.all(
                color: todo.isDone ? const Color(0xFF059669) : const Color(0xFF475569),
                width: 2,
              ),
            ),
            child: todo.isDone
                ? const Icon(Icons.check, size: 14, color: Colors.white)
                : null,
          ),
        ),
        title: Text(
          todo.title,
          style: TextStyle(
            fontSize: 14,
            color: todo.isDone ? const Color(0xFF64748B) : const Color(0xFFF8FAFC),
            decoration: todo.isDone ? TextDecoration.lineThrough : null,
          ),
        ),
        trailing: IconButton(
          icon: const Icon(Icons.delete_outline, color: Color(0xFF475569), size: 20),
          onPressed: () => _delete(todo),
        ),
      ),
    );
  }

  Widget _emptyState() {
    return Center(
      child: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        children: [
          Icon(Icons.checklist, size: 72, color: Colors.white.withAlpha(30)),
          const SizedBox(height: 16),
          const Text('Görev bulunamadı',
              style: TextStyle(color: Color(0xFF64748B), fontSize: 16)),
          const SizedBox(height: 8),
          const Text('Yukarıdan yeni görev ekleyin.',
              style: TextStyle(color: Color(0xFF475569), fontSize: 13)),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _addCtrl.dispose();
    super.dispose();
  }
}
