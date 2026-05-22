import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';

final dashboardProvider = AsyncNotifierProvider<DashboardNotifier, DashboardState>(() => DashboardNotifier());

class DashboardState {
  final int totalProducts;
  final int totalInvoices;
  final int totalCustomers;
  final double totalSales;

  const DashboardState({
    this.totalProducts = 0,
    this.totalInvoices = 0,
    this.totalCustomers = 0,
    this.totalSales = 0,
  });
}

class DashboardNotifier extends AsyncNotifier<DashboardState> {
  @override
  Future<DashboardState> build() async {
    return await _fetch();
  }

  Dio get _dio => ref.read(dioProvider);

  Future<DashboardState> _fetch() async {
    final results = await Future.wait([
      _dio.get('/products', queryParameters: {'page': 1, 'per_page': 1}),
      _dio.get('/sales/invoices', queryParameters: {'page': 1, 'per_page': 1}),
      _dio.get('/users', queryParameters: {'page': 1, 'per_page': 1}),
    ]);

    return DashboardState(
      totalProducts: results[0].data['total'] ?? 0,
      totalInvoices: results[1].data['total'] ?? 0,
      totalCustomers: results[2].data['total'] ?? 0,
      totalSales: 0,
    );
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetch());
  }
}
