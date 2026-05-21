import 'package:dio/dio.dart';
import '../errors/app_exception.dart';

class ErrorInterceptor extends Interceptor {
  @override
  void onError(DioException err, ErrorInterceptorHandler handler) {
    final exception = switch (err.type) {
      DioExceptionType.connectionTimeout ||
      DioExceptionType.sendTimeout ||
      DioExceptionType.receiveTimeout =>
        AppException.network('Connection timed out'),
      DioExceptionType.connectionError =>
        AppException.network('No internet connection'),
      DioExceptionType.badResponse => _handleBadResponse(err.response!),
      _ => AppException.unknown(err.message ?? 'Unknown error'),
    };

    handler.reject(DioException(
      requestOptions: err.requestOptions,
      response: err.response,
      type: err.type,
      error: exception,
    ));
  }

  AppException _handleBadResponse(Response response) {
    final data = response.data;
    final message = data is Map ? (data['detail'] ?? data['message'] ?? '') : '';

    return switch (response.statusCode) {
      400 => AppException.badRequest(message.toString()),
      401 => AppException.unauthorized(message.toString()),
      403 => AppException.forbidden(message.toString()),
      404 => AppException.notFound(message.toString()),
      409 => AppException.conflict(message.toString()),
      422 => AppException.validation(message.toString()),
      429 => AppException.rateLimited(message.toString()),
      >= 500 => AppException.server(message.toString()),
      _ => AppException.unknown(message.toString()),
    };
  }
}
