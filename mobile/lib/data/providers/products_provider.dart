import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';

final productsProvider = AsyncNotifierProvider<ProductsNotifier, ProductsState>(() => ProductsNotifier());

class ProductsState {
  final List<Map<String, dynamic>> items;
  final int total;
  final bool isLoading;

  const ProductsState({this.items = const [], this.total = 0, this.isLoading = false});

  ProductsState copyWith({List<Map<String, dynamic>>? items, int? total, bool? isLoading}) {
    return ProductsState(items: items ?? this.items, total: total ?? this.total, isLoading: isLoading ?? this.isLoading);
  }
}

class ProductsNotifier extends AsyncNotifier<ProductsState> {
  @override
  Future<ProductsState> build() async {
    return await _fetch();
  }

  Dio get _dio => ref.read(dioProvider);

  Future<ProductsState> _fetch({int page = 1, int perPage = 20}) async {
    final response = await _dio.get('/products', queryParameters: {'page': page, 'per_page': perPage});
    final data = response.data;
    return ProductsState(
      items: List<Map<String, dynamic>>.from(data['data'] ?? []),
      total: data['total'] ?? 0,
    );
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetch());
  }
}
