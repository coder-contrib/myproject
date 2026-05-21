class Invoice {
  final int id;
  final String invoiceNumber;
  final int? customerId;
  final String? customerName;
  final List<InvoiceItem> items;
  final double subtotal;
  final double taxAmount;
  final double total;
  final String status;
  final String? notes;
  final DateTime? createdAt;
  final DateTime? dueDate;

  const Invoice({
    required this.id,
    required this.invoiceNumber,
    this.customerId,
    this.customerName,
    this.items = const [],
    required this.subtotal,
    required this.taxAmount,
    required this.total,
    required this.status,
    this.notes,
    this.createdAt,
    this.dueDate,
  });

  bool get isDraft => status == 'draft';
  bool get isPaid => status == 'paid';
  bool get isOverdue => dueDate != null && dueDate!.isBefore(DateTime.now()) && !isPaid;

  factory Invoice.fromJson(Map<String, dynamic> json) => Invoice(
    id: json['id'],
    invoiceNumber: json['invoice_number'] ?? '',
    customerId: json['customer_id'],
    customerName: json['customer_name'],
    items: (json['items'] as List<dynamic>?)
        ?.map((e) => InvoiceItem.fromJson(e))
        .toList() ?? [],
    subtotal: (json['subtotal'] ?? 0).toDouble(),
    taxAmount: (json['tax_amount'] ?? 0).toDouble(),
    total: (json['total'] ?? 0).toDouble(),
    status: json['status'] ?? 'draft',
    notes: json['notes'],
    createdAt: json['created_at'] != null ? DateTime.parse(json['created_at']) : null,
    dueDate: json['due_date'] != null ? DateTime.parse(json['due_date']) : null,
  );

  Map<String, dynamic> toJson() => {
    'customer_id': customerId,
    'items': items.map((e) => e.toJson()).toList(),
    'notes': notes,
  };
}

class InvoiceItem {
  final int? id;
  final int productId;
  final String? productName;
  final int quantity;
  final double unitPrice;
  final double? discount;

  const InvoiceItem({
    this.id,
    required this.productId,
    this.productName,
    required this.quantity,
    required this.unitPrice,
    this.discount,
  });

  double get lineTotal => (quantity * unitPrice) - (discount ?? 0);

  factory InvoiceItem.fromJson(Map<String, dynamic> json) => InvoiceItem(
    id: json['id'],
    productId: json['product_id'],
    productName: json['product_name'],
    quantity: json['quantity'] ?? 0,
    unitPrice: (json['unit_price'] ?? 0).toDouble(),
    discount: json['discount']?.toDouble(),
  );

  Map<String, dynamic> toJson() => {
    'product_id': productId,
    'quantity': quantity,
    'unit_price': unitPrice,
    'discount': discount,
  };
}
