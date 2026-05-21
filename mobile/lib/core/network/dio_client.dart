import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../constants/app_constants.dart';
import 'auth_interceptor.dart';
import 'error_interceptor.dart';

final dioProvider = Provider<Dio>((ref) {
  final dio = Dio(BaseOptions(
    baseUrl: '${ApiConstants.baseUrl}${ApiConstants.apiPrefix}',
    connectTimeout: ApiConstants.connectTimeout,
    receiveTimeout: ApiConstants.receiveTimeout,
    headers: {'Content-Type': 'application/json'},
  ));

  dio.interceptors.addAll([
    AuthInterceptor(ref),
    ErrorInterceptor(),
    LogInterceptor(requestBody: true, responseBody: true),
  ]);

  return dio;
});
