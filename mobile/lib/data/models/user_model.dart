class User {
  final int id;
  final String email;
  final String fullName;
  final String role;
  final int tenantId;
  final bool isActive;
  final DateTime? createdAt;

  const User({
    required this.id,
    required this.email,
    required this.fullName,
    required this.role,
    required this.tenantId,
    this.isActive = true,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) => User(
    id: json['id'],
    email: json['email'],
    fullName: json['full_name'] ?? '',
    role: json['role'] ?? 'user',
    tenantId: json['tenant_id'] ?? 0,
    isActive: json['is_active'] ?? true,
    createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
  );

  Map<String, dynamic> toJson() => {
    'id': id,
    'email': email,
    'full_name': fullName,
    'role': role,
    'tenant_id': tenantId,
    'is_active': isActive,
  };
}

class AuthTokens {
  final String accessToken;
  final String refreshToken;
  final String tokenType;

  const AuthTokens({
    required this.accessToken,
    required this.refreshToken,
    this.tokenType = 'bearer',
  });

  factory AuthTokens.fromJson(Map<String, dynamic> json) => AuthTokens(
    accessToken: json['access_token'],
    refreshToken: json['refresh_token'],
    tokenType: json['token_type'] ?? 'bearer',
  );
}
