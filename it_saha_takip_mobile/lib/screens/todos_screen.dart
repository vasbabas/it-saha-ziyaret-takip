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
  final _focusNode = FocusNode();
  List<Todo> _todos = [];
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final todos = await DatabaseService.getTodos();
      if (mounted) setState(() => _todos = todos);
    } catch (_) {}
  }

  Future<void> _add() async {
    final t = _addCtrl.text.trim();
    if (t.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('⚠️ Lütfen önce bir görev tanımı yazın!'),
          backgroundColor: Color(0xFFD97706),
          duration: Duration(seconds: 2),
        ),
      );
      _focusNode.requestFocus();
      return;
    }

    _focusNode.unfocus();
    setState(() => _loading = true);

    try {
      final todo = Todo(title: t);
      await DatabaseService.insertTodo(todo);
      _addCtrl.clear();
      await _load();

      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          const SnackBar(
            content: Text('✅ Görev listeye eklendi!'),
            backgroundColor: Color(0xFF059669),
            duration: Duration(seconds: 2),
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Hata: $e'),
            backgroundColor: Colors.red,
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _toggle(Todo todo) async {
    if (todo.id == null) return;
    await DatabaseService.updateTodoDone(todo.id!, !todo.isDone);
    _load();
  }

  Future<void> _delete(Todo todo) async {
    if (todo.id == null) return;
    await DatabaseService.deleteTodo(todo.id!);
    _load();
  }

  @override
  Widget build(BuildContext context) {
    final pending = _todos.where((t) => !t.isDone).toList();
    final done = _todos.where((t) => t.isDone).toList();

    return Scaffold(
      appBar: AppBar(
        title: const Text('📋 Görev Listem',
            style: TextStyle(fontSize: 17, fontWeight: FontWeight.w700)),
      ),
      body: Column(
        children: [
          // Add new todo container
          Container(
            padding: const EdgeInsets.all(16),
            color: const Color(0xFF1E293B),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    controller: _addCtrl,
                    focusNode: _focusNode,
                    onSubmitted: (_) => _add(),
                    textInputAction: TextInputAction.done,
                    decoration: InputDecoration(
                      hintText: 'Görev yazın (Örn: Server yedek kontrol et)...',
                      hintStyle: const TextStyle(color: Color(0xFF64748B), fontSize: 13),
                      prefixIcon: const Icon(Icons.add_task, color: Color(0xFF3B82F6)),
                      suffixIcon: _addCtrl.text.isNotEmpty
                          ? IconButton(
                              icon: const Icon(Icons.clear, size: 18),
                              onPressed: () {
                                _addCtrl.clear();
                                setState(() {});
                              },
                            )
                          : null,
                    ),
                    onChanged: (_) => setState(() {}),
                  ),
                ),
                const SizedBox(width: 10),
                Material(
                  color: const Color(0xFF2563EB),
                  borderRadius: BorderRadius.circular(12),
                  child: InkWell(
                    onTap: _loading ? null : _add,
                    borderRadius: BorderRadius.circular(12),
                    child: Container(
                      padding: const EdgeInsets.all(14),
                      child: _loading
                          ? const SizedBox(
                              width: 24, height: 24,
                              child: CircularProgressIndicator(color: Colors.white, strokeWidth: 2))
                          : const Icon(Icons.add, color: Colors.white, size: 26),
                    ),
                  ),
                ),
              ],
            ),
          ),
          Expanded(
            child: _todos.isEmpty
                ? _emptyState()
                : ListView(
                    padding: const EdgeInsets.all(16),
                    children: [
                      if (pending.isNotEmpty) ...[
                        _sectionHeader('📌 BEKLEYEN GÖREVLER (${pending.length})'),
                        ...pending.map((t) => _buildTodoCard(t)),
                      ],
                      if (done.isNotEmpty) ...[
                        _sectionHeader('✅ TAMAMLATILAN GÖREVLER (${done.length})'),
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
      padding: const EdgeInsets.fromLTRB(0, 12, 0, 8),
      child: Text(text,
          style: const TextStyle(
              fontSize: 11.5,
              fontWeight: FontWeight.w700,
              color: Color(0xFF94A3B8),
              letterSpacing: 0.5)),
    );
  }

  Widget _buildTodoCard(Todo todo) {
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ListTile(
        contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 4),
        leading: InkWell(
          onTap: () => _toggle(todo),
          borderRadius: BorderRadius.circular(15),
          child: Container(
            width: 28,
            height: 28,
            decoration: BoxDecoration(
              shape: BoxShape.circle,
              color: todo.isDone ? const Color(0xFF059669) : Colors.transparent,
              border: Border.all(
                color: todo.isDone ? const Color(0xFF059669) : const Color(0xFF475569),
                width: 2,
              ),
            ),
            child: todo.isDone
                ? const Icon(Icons.check, size: 16, color: Colors.white)
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
          icon: const Icon(Icons.delete_outline, color: Color(0xFFEF4444), size: 20),
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
          const Text('Henüz görev eklenmemiş',
              style: TextStyle(color: Color(0xFF64748B), fontSize: 16)),
          const SizedBox(height: 8),
          const Text('Yukarıdaki metin kutusuna görev yazıp\nartı (+) butonuna basın.',
              textAlign: TextAlign.center,
              style: TextStyle(color: Color(0xFF475569), fontSize: 13)),
        ],
      ),
    );
  }

  @override
  void dispose() {
    _addCtrl.dispose();
    _focusNode.dispose();
    super.dispose();
  }
}
