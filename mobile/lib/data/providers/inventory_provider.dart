import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';
import '../models/inventory_model.dart';
import '../models/paginated_response.dart';

final inventoryServiceProvider = Provider<InventoryService>((ref) {
  return InventoryService(ref.watch(dioProvider));
});

final inventoryProvider = FutureProvider.autoDispose<List<InventoryItem>>((ref) {
  return ref.watch(inventoryServiceProvider).getStockLevels();
});

final lowStockProvider = FutureProvider.autoDispose<List<InventoryItem>>((ref) {
  return ref.watch(inventoryServiceProvider).getLowStockAlerts();
});

class InventoryService {
  final Dio _dio;

  InventoryService(this._dio);

  Future<List<InventoryItem>> getStockLevels() async {
    final response = await _dio.get('/inventory/stock/');
    final data = response.data;
    if (data is List) {
      return data.map((e) => InventoryItem.fromJson(e)).toList();
    }
    return (data['items'] as List).map((e) => InventoryItem.fromJson(e)).toList();
  }

  Future<List<InventoryItem>> getLowStockAlerts() async {
    final response = await _dio.get('/inventory/alerts/low-stock');
    final data = response.data;
    if (data is List) {
      return data.map((e) => InventoryItem.fromJson(e)).toList();
    }
    return (data['items'] as List).map((e) => InventoryItem.fromJson(e)).toList();
  }

  Future<void> recordMovement({
    required int productId,
    required int warehouseId,
    required int quantity,
    required String type,
    String? reference,
  }) async {
    await _dio.post('/inventory/movements/', data: {
      'product_id': productId,
      'warehouse_id': warehouseId,
      'quantity': quantity,
      'movement_type': type,
      'reference': reference,
    });
  }

  Future<void> transferStock({
    required int productId,
    required int fromWarehouseId,
    required int toWarehouseId,
    required int quantity,
  }) async {
    await _dio.post('/inventory/transfers/', data: {
      'product_id': productId,
      'from_warehouse_id': fromWarehouseId,
      'to_warehouse_id': toWarehouseId,
      'quantity': quantity,
    });
  }
}
