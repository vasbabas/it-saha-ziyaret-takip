double _parseDouble(dynamic val) {
  if (val == null) return 1.0;
  if (val is num) return val.toDouble();
  if (val is String) return double.tryParse(val) ?? 1.0;
  return 1.0;
}

bool _parseBool(dynamic val) {
  if (val == null) return false;
  if (val is bool) return val;
  if (val is num) return val == 1;
  if (val is String) return val == '1' || val.toLowerCase() == 'true';
  return false;
}

int? _parseInt(dynamic val) {
  if (val == null) return null;
  if (val is int) return val;
  if (val is num) return val.toInt();
  if (val is String) return int.tryParse(val);
  return null;
}

class Visit {
  final int? id;
  final String visitDate;
  final String company;
  final String subject;
  final String technician;
  final double duration;
  final String status;
  final String workNotes;
  final String? createdAt;
  final bool synced;

  Visit({
    this.id,
    required this.visitDate,
    required this.company,
    required this.subject,
    required this.technician,
    required this.duration,
    required this.status,
    required this.workNotes,
    this.createdAt,
    this.synced = false,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'visit_date': visitDate,
      'company': company,
      'subject': subject,
      'technician': technician,
      'duration': duration,
      'status': status,
      'work_notes': workNotes,
      'created_at': createdAt ?? DateTime.now().toIso8601String(),
      'synced': synced ? 1 : 0,
    };
  }

  factory Visit.fromMap(Map<String, dynamic> map) {
    return Visit(
      id: _parseInt(map['id']),
      visitDate: (map['visit_date'] ?? map['date'] ?? '').toString(),
      company: (map['company'] ?? '').toString(),
      subject: (map['subject'] ?? map['work_type'] ?? '').toString(),
      technician: (map['technician'] ?? map['category'] ?? '').toString(),
      duration: _parseDouble(map['duration']),
      status: (map['status'] ?? 'Tamamlandi').toString(),
      workNotes: (map['work_notes'] ?? map['notes'] ?? '').toString(),
      createdAt: map['created_at']?.toString(),
      synced: _parseBool(map['synced']),
    );
  }

  factory Visit.fromJson(Map<String, dynamic> json) => Visit.fromMap(json);

  Map<String, dynamic> toJson() => toMap();
}

class CompanyNote {
  final int? id;
  final String company;
  final String? ipSubnet;
  final String? vpnDetails;
  final String? credentials;
  final String? otherNotes;
  final String? updatedAt;

  CompanyNote({
    this.id,
    required this.company,
    this.ipSubnet,
    this.vpnDetails,
    this.credentials,
    this.otherNotes,
    this.updatedAt,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'company': company,
      'ip_subnet': ipSubnet,
      'vpn_details': vpnDetails,
      'credentials': credentials,
      'other_notes': otherNotes,
      'updated_at': updatedAt ?? DateTime.now().toIso8601String(),
    };
  }

  factory CompanyNote.fromMap(Map<String, dynamic> map) {
    return CompanyNote(
      id: _parseInt(map['id']),
      company: (map['company'] ?? '').toString(),
      ipSubnet: map['ip_subnet']?.toString(),
      vpnDetails: map['vpn_details']?.toString(),
      credentials: map['credentials']?.toString(),
      otherNotes: map['other_notes']?.toString(),
      updatedAt: map['updated_at']?.toString(),
    );
  }

  factory CompanyNote.fromJson(Map<String, dynamic> json) => CompanyNote.fromMap(json);
  Map<String, dynamic> toJson() => toMap();
}

class Todo {
  final int? id;
  final String title;
  final bool isDone;
  final String? dueDate;
  final String? createdAt;
  final bool synced;

  Todo({
    this.id,
    required this.title,
    this.isDone = false,
    this.dueDate,
    this.createdAt,
    this.synced = false,
  });

  Map<String, dynamic> toMap() {
    return {
      'id': id,
      'title': title,
      'is_done': isDone ? 1 : 0,
      'due_date': dueDate,
      'created_at': createdAt ?? DateTime.now().toIso8601String(),
      'synced': synced ? 1 : 0,
    };
  }

  factory Todo.fromMap(Map<String, dynamic> map) {
    return Todo(
      id: _parseInt(map['id']),
      title: (map['title'] ?? map['description'] ?? '').toString(),
      isDone: _parseBool(map['is_done'] ?? map['done']),
      dueDate: map['due_date']?.toString(),
      createdAt: map['created_at']?.toString(),
      synced: _parseBool(map['synced']),
    );
  }

  factory Todo.fromJson(Map<String, dynamic> json) => Todo.fromMap(json);
  Map<String, dynamic> toJson() => toMap();
}
