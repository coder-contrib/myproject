import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';

final invoicesProvider = AsyncNotifierProvider<InvoicesNotifier, InvoicesState>(() => InvoicesNotifier());

class InvoicesState {
  final List<Map<String, dynamic>> items;
  final int total;

  const InvoicesState({this.items = const [], this.total = 0});
}

class InvoicesNotifier extends AsyncNotifier<InvoicesState> {
  @override
  Future<InvoicesState> build() async {
    return await _fetch();
  }

  Dio get _dio => ref.read(dioProvider);

  Future<InvoicesState> _fetch({int page = 1}) async {
    final response = await _dio.get('/sales/invoices', queryParameters: {'page': page, 'per_page': 20});
    final data = response.data;
    return InvoicesState(
      items: List<Map<String, dynamic>>.from(data['data'] ?? []),
      total: data['total'] ?? 0,
    );
  }

  Future<void> refresh() async {
    state = const AsyncValue.loading();
    state = await AsyncValue.guard(() => _fetch());
  }
}
