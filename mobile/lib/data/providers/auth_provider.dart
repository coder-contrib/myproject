import 'package:dio/dio.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import '../../core/constants/app_constants.dart';
import '../../core/network/dio_client.dart';
import '../models/user_model.dart';

final authServiceProvider = Provider<AuthService>((ref) {
  return AuthService(ref.watch(dioProvider));
});

final authStateProvider = NotifierProvider<AuthNotifier, AsyncValue<User?>>(() {
  return AuthNotifier();
});

class AuthService {
  final Dio _dio;
  final _storage = const FlutterSecureStorage();

  AuthService(this._dio);

  Future<AuthTokens> login(String email, String password) async {
    final response = await _dio.post('/auth/login', data: {
      'email': email,
      'password': password,
    });
    final data = response.data is Map && response.data['data'] != null
        ? response.data['data']
        : response.data;
    final tokens = AuthTokens.fromJson(data);
    await _storage.write(key: StorageKeys.accessToken, value: tokens.accessToken);
    await _storage.write(key: StorageKeys.refreshToken, value: tokens.refreshToken);
    return tokens;
  }

  Future<User> getCurrentUser() async {
    final response = await _dio.get('/users/me');
    final data = response.data is Map && response.data['data'] != null
        ? response.data['data']
        : response.data;
    return User.fromJson(data);
  }

  Future<void> logout() async {
    await _storage.deleteAll();
  }

  Future<bool> isAuthenticated() async {
    final token = await _storage.read(key: StorageKeys.accessToken);
    return token != null;
  }
}

class AuthNotifier extends Notifier<AsyncValue<User?>> {
  @override
  AsyncValue<User?> build() {
    _checkAuth();
    return const AsyncValue.data(null);
  }

  AuthService get _service => ref.read(authServiceProvider);

  Future<void> _checkAuth() async {
    if (await _service.isAuthenticated()) {
      try {
        final user = await _service.getCurrentUser();
        state = AsyncValue.data(user);
      } catch (_) {
        state = const AsyncValue.data(null);
      }
    }
  }

  Future<void> login(String email, String password) async {
    state = const AsyncValue.loading();
    try {
      await _service.login(email, password);
      final user = await _service.getCurrentUser();
      state = AsyncValue.data(user);
    } catch (e, st) {
      state = AsyncValue.error(e, st);
      rethrow;
    }
  }

  Future<void> logout() async {
    await _service.logout();
    state = const AsyncValue.data(null);
  }
}
