class Product {
  final int id;
  final String name;
  final String sku;
  final double price;
  final double cost;
  final int quantity;
  final int? categoryId;
  final String? categoryName;
  final String? description;
  final String? imageUrl;
  final bool isActive;

  const Product({
    required this.id,
    required this.name,
    required this.sku,
    required this.price,
    required this.cost,
    required this.quantity,
    this.categoryId,
    this.categoryName,
    this.description,
    this.imageUrl,
    this.isActive = true,
  });

  double get margin => price > 0 ? ((price - cost) / price) * 100 : 0;
  bool get isLowStock => quantity < 10;

  factory Product.fromJson(Map<String, dynamic> json) => Product(
    id: json['id'],
    name: json['name'] ?? '',
    sku: json['sku'] ?? '',
    price: (json['price'] ?? 0).toDouble(),
    cost: (json['cost'] ?? 0).toDouble(),
    quantity: json['quantity'] ?? 0,
    categoryId: json['category_id'],
    categoryName: json['category_name'],
    description: json['description'],
    imageUrl: json['image_url'],
    isActive: json['is_active'] ?? true,
  );

  Map<String, dynamic> toJson() => {
    'name': name,
    'sku': sku,
    'price': price,
    'cost': cost,
    'quantity': quantity,
    'category_id': categoryId,
    'description': description,
    'is_active': isActive,
  };
}
