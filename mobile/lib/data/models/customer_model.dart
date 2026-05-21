class Customer {
  final int id;
  final String name;
  final String? email;
  final String? phone;
  final String? address;
  final String? city;
  final double totalPurchases;
  final int orderCount;
  final bool isActive;

  const Customer({
    required this.id,
    required this.name,
    this.email,
    this.phone,
    this.address,
    this.city,
    this.totalPurchases = 0,
    this.orderCount = 0,
    this.isActive = true,
  });

  factory Customer.fromJson(Map<String, dynamic> json) => Customer(
    id: json['id'],
    name: json['name'] ?? '',
    email: json['email'],
    phone: json['phone'],
    address: json['address'],
    city: json['city'],
    totalPurchases: (json['total_purchases'] ?? 0).toDouble(),
    orderCount: json['order_count'] ?? 0,
    isActive: json['is_active'] ?? true,
  );

  Map<String, dynamic> toJson() => {
    'name': name,
    'email': email,
    'phone': phone,
    'address': address,
    'city': city,
  };
}
