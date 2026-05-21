import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../core/network/dio_client.dart';
import '../models/invoice_model.dart';
import '../models/paginated_response.dart';

final invoiceServiceProvider = Provider<InvoiceService>((ref) {
  return InvoiceService(ref.watch(dioProvider));
});

final invoicesProvider = FutureProvider.autoDispose.family<PaginatedResponse<Invoice>, InvoiceQuery>(
  (ref, query) => ref.watch(invoiceServiceProvider).getInvoices(query),
);

final invoiceDetailProvider = FutureProvider.autoDispose.family<Invoice, int>(
  (ref, id) => ref.watch(invoiceServiceProvider).getInvoice(id),
);

class InvoiceQuery {
  final int page;
  final int size;
  final String? status;

  const InvoiceQuery({this.page = 1, this.size = 20, this.status});
}

class InvoiceService {
  final Dio _dio;

  InvoiceService(this._dio);

  Future<PaginatedResponse<Invoice>> getInvoices(InvoiceQuery query) async {
    final params = <String, dynamic>{'page': query.page, 'size': query.size};
    if (query.status != null) params['status'] = query.status;

    final response = await _dio.get('/sales/invoices/', queryParameters: params);
    return PaginatedResponse.fromJson(response.data, Invoice.fromJson);
  }

  Future<Invoice> getInvoice(int id) async {
    final response = await _dio.get('/sales/invoices/$id');
    return Invoice.fromJson(response.data);
  }

  Future<Invoice> createInvoice(Map<String, dynamic> data) async {
    final response = await _dio.post('/sales/invoices/', data: data);
    return Invoice.fromJson(response.data);
  }

  Future<Invoice> updateStatus(int id, String status) async {
    final response = await _dio.patch('/sales/invoices/$id/status', data: {'status': status});
    return Invoice.fromJson(response.data);
  }
}
