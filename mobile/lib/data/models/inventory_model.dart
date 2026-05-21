class InventoryItem {
  final int productId;
  final String productName;
  final String sku;
  final int warehouseId;
  final String? warehouseName;
  final int quantity;
  final int reorderLevel;
  final double unitCost;

  const InventoryItem({
    required this.productId,
    required this.productName,
    required this.sku,
    required this.warehouseId,
    this.warehouseName,
    required this.quantity,
    this.reorderLevel = 10,
    this.unitCost = 0,
  });

  bool get isLowStock => quantity <= reorderLevel;
  bool get isOutOfStock => quantity == 0;
  double get stockValue => quantity * unitCost;

  factory InventoryItem.fromJson(Map<String, dynamic> json) => InventoryItem(
    productId: json['product_id'] ?? json['id'],
    productName: json['product_name'] ?? json['name'] ?? '',
    sku: json['sku'] ?? '',
    warehouseId: json['warehouse_id'] ?? 0,
    warehouseName: json['warehouse_name'],
    quantity: json['quantity'] ?? 0,
    reorderLevel: json['reorder_level'] ?? 10,
    unitCost: (json['unit_cost'] ?? json['cost'] ?? 0).toDouble(),
  );
}

class StockMovement {
  final int id;
  final int productId;
  final String productName;
  final int warehouseId;
  final int quantity;
  final String movementType;
  final String? reference;
  final DateTime? createdAt;

  const StockMovement({
    required this.id,
    required this.productId,
    required this.productName,
    required this.warehouseId,
    required this.quantity,
    required this.movementType,
    this.reference,
    this.createdAt,
  });

  factory StockMovement.fromJson(Map<String, dynamic> json) => StockMovement(
    id: json['id'],
    productId: json['product_id'],
    productName: json['product_name'] ?? '',
    warehouseId: json['warehouse_id'] ?? 0,
    quantity: json['quantity'] ?? 0,
    movementType: json['movement_type'] ?? '',
    reference: json['reference'],
    createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
  );
}
