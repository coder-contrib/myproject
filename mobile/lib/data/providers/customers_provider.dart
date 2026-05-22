import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';

final customersProvider = AsyncNotifierProvider<CustomersNotifier, CustomersState>(() => CustomersNotifier());

class CustomersState {
  final List<Map<String, dynamic>> items;
  final int total;

  const CustomersState({this.items = const [], this.total = 0});
}

class CustomersNotifier extends AsyncNotifier<CustomersState> {
  @override
  Future<CustomersState> build() async {
    return await _fetch();
  }

  Dio get _dio => ref.read(dioProvider);

  Future<CustomersState> _fetch({int page = 1}) async {
    final response = await _dio.get('/users', queryParameters: {'page': page, 'per_page': 20});
    final data = response.data;
    return CustomersState(
      items: List<Map<String, dynamic>>.from(data['data'] ?? []),
      total: data['total'] ?? 0,
    );
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetch());
  }
}
