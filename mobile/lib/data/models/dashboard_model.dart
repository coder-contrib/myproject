class DashboardData {
  final double totalRevenue;
  final int totalOrders;
  final int totalCustomers;
  final int totalProducts;
  final double averageOrderValue;
  final double revenueGrowth;
  final List<SalesTrend> salesTrend;
  final List<TopProduct> topProducts;

  const DashboardData({
    required this.totalRevenue,
    required this.totalOrders,
    required this.totalCustomers,
    required this.totalProducts,
    required this.averageOrderValue,
    required this.revenueGrowth,
    this.salesTrend = const [],
    this.topProducts = const [],
  });

  factory DashboardData.fromJson(Map<String, dynamic> json) => DashboardData(
    totalRevenue: (json['total_revenue'] ?? json['revenue'] ?? 0).toDouble(),
    totalOrders: json['total_orders'] ?? json['orders'] ?? 0,
    totalCustomers: json['total_customers'] ?? json['customers'] ?? 0,
    totalProducts: json['total_products'] ?? json['products'] ?? 0,
    averageOrderValue: (json['average_order_value'] ?? json['avg_order'] ?? 0).toDouble(),
    revenueGrowth: (json['revenue_growth'] ?? json['growth'] ?? 0).toDouble(),
    salesTrend: (json['sales_trend'] as List<dynamic>?)
        ?.map((e) => SalesTrend.fromJson(e)).toList() ?? [],
    topProducts: (json['top_products'] as List<dynamic>?)
        ?.map((e) => TopProduct.fromJson(e)).toList() ?? [],
  );
}

class SalesTrend {
  final String date;
  final double revenue;
  final int orders;

  const SalesTrend({required this.date, required this.revenue, required this.orders});

  factory SalesTrend.fromJson(Map<String, dynamic> json) => SalesTrend(
    date: json['date'] ?? '',
    revenue: (json['revenue'] ?? json['total'] ?? 0).toDouble(),
    orders: json['orders'] ?? json['count'] ?? 0,
  );
}

class TopProduct {
  final int id;
  final String name;
  final int quantitySold;
  final double revenue;

  const TopProduct({required this.id, required this.name, required this.quantitySold, required this.revenue});

  factory TopProduct.fromJson(Map<String, dynamic> json) => TopProduct(
    id: json['id'] ?? 0,
    name: json['name'] ?? json['product_name'] ?? '',
    quantitySold: json['quantity_sold'] ?? json['quantity'] ?? 0,
    revenue: (json['revenue'] ?? json['total'] ?? 0).toDouble(),
  );
}
