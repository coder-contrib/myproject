import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';
import '../models/dashboard_model.dart';

final dashboardServiceProvider = Provider<DashboardService>((ref) {
  return DashboardService(ref.watch(dioProvider));
});

final dashboardProvider = FutureProvider.autoDispose<DashboardData>((ref) {
  return ref.watch(dashboardServiceProvider).getOverview();
});

final salesTrendProvider = FutureProvider.autoDispose.family<List<SalesTrend>, String>(
  (ref, period) => ref.watch(dashboardServiceProvider).getSalesTrend(period),
);

class DashboardService {
  final Dio _dio;

  DashboardService(this._dio);

  Future<DashboardData> getOverview() async {
    final response = await _dio.get('/reports/dashboard/overview');
    return DashboardData.fromJson(response.data);
  }

  Future<List<SalesTrend>> getSalesTrend(String period) async {
    final response = await _dio.get('/reports/dashboard/sales-trend', queryParameters: {'period': period});
    return (response.data as List).map((e) => SalesTrend.fromJson(e)).toList();
  }

  Future<List<TopProduct>> getTopProducts({int limit = 10}) async {
    final response = await _dio.get('/reports/dashboard/top-products', queryParameters: {'limit': limit});
    return (response.data as List).map((e) => TopProduct.fromJson(e)).toList();
  }
}
