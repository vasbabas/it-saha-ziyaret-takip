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
      id: map['id'],
      visitDate: map['visit_date'] ?? '',
      company: map['company'] ?? '',
      subject: map['subject'] ?? '',
      technician: map['technician'] ?? '',
      duration: (map['duration'] ?? 1.0).toDouble(),
      status: map['status'] ?? 'Tamamlandi',
      workNotes: map['work_notes'] ?? '',
      createdAt: map['created_at'],
      synced: (map['synced'] ?? 0) == 1,
    );
  }

  factory Visit.fromJson(Map<String, dynamic> json) {
    return Visit(
      visitDate: json['visit_date'] ?? '',
      company: json['company'] ?? '',
      subject: json['subject'] ?? json['work_type'] ?? '',
      technician: json['technician'] ?? json['category'] ?? '',
      duration: (json['duration'] ?? 1.0).toDouble(),
      status: json['status'] ?? 'Tamamlandi',
      workNotes: json['work_notes'] ?? json['notes'] ?? '',
      createdAt: json['created_at'],
      synced: true,
    );
  }

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
      id: map['id'],
      company: map['company'] ?? '',
      ipSubnet: map['ip_subnet'],
      vpnDetails: map['vpn_details'],
      credentials: map['credentials'],
      otherNotes: map['other_notes'],
      updatedAt: map['updated_at'],
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
      id: map['id'],
      title: map['title'] ?? map['description'] ?? '',
      isDone: (map['is_done'] ?? map['done'] ?? 0) == 1,
      dueDate: map['due_date'],
      createdAt: map['created_at'],
      synced: (map['synced'] ?? 0) == 1,
    );
  }

  factory Todo.fromJson(Map<String, dynamic> json) => Todo.fromMap(json);
  Map<String, dynamic> toJson() => toMap();
}
