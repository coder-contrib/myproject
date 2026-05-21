import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';
import '../models/product_model.dart';
import '../models/paginated_response.dart';

final productServiceProvider = Provider<ProductService>((ref) {
  return ProductService(ref.watch(dioProvider));
});

final productsProvider = FutureProvider.autoDispose.family<PaginatedResponse<Product>, ProductQuery>(
  (ref, query) => ref.watch(productServiceProvider).getProducts(query),
);

final productDetailProvider = FutureProvider.autoDispose.family<Product, int>(
  (ref, id) => ref.watch(productServiceProvider).getProduct(id),
);

class ProductQuery {
  final int page;
  final int size;
  final String? search;
  final int? categoryId;

  const ProductQuery({this.page = 1, this.size = 20, this.search, this.categoryId});
}

class ProductService {
  final Dio _dio;

  ProductService(this._dio);

  Future<PaginatedResponse<Product>> getProducts(ProductQuery query) async {
    final params = <String, dynamic>{
      'page': query.page,
      'size': query.size,
    };
    if (query.search != null) params['search'] = query.search;
    if (query.categoryId != null) params['category_id'] = query.categoryId;

    final response = await _dio.get('/products/', queryParameters: params);
    return PaginatedResponse.fromJson(response.data, Product.fromJson);
  }

  Future<Product> getProduct(int id) async {
    final response = await _dio.get('/products/$id');
    return Product.fromJson(response.data);
  }

  Future<Product> createProduct(Map<String, dynamic> data) async {
    final response = await _dio.post('/products/', data: data);
    return Product.fromJson(response.data);
  }

  Future<Product> updateProduct(int id, Map<String, dynamic> data) async {
    final response = await _dio.put('/products/$id', data: data);
    return Product.fromJson(response.data);
  }

  Future<void> deleteProduct(int id) async {
    await _dio.delete('/products/$id');
  }
}
