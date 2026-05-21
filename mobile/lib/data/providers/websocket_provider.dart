import 'dart:async';
import 'dart:convert';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:flutter_secure_storage/flutter_secure_storage.dart';
import 'package:web_socket_channel/web_socket_channel.dart';
import '../../core/constants/app_constants.dart';

final webSocketServiceProvider = Provider<WebSocketService>((ref) {
  return WebSocketService();
});

final notificationsStreamProvider = StreamProvider<Map<String, dynamic>>((ref) {
  final wsService = ref.watch(webSocketServiceProvider);
  return wsService.notifications;
});

class WebSocketService {
  WebSocketChannel? _channel;
  final _notificationsController = StreamController<Map<String, dynamic>>.broadcast();
  final _storage = const FlutterSecureStorage();
  Timer? _reconnectTimer;
  bool _isConnected = false;

  Stream<Map<String, dynamic>> get notifications => _notificationsController.stream;
  bool get isConnected => _isConnected;

  Future<void> connect() async {
    final token = await _storage.read(key: StorageKeys.accessToken);
    if (token == null) return;

    final wsUrl = ApiConstants.baseUrl
        .replaceFirst('http://', 'ws://')
        .replaceFirst('https://', 'wss://');

    try {
      _channel = WebSocketChannel.connect(
        Uri.parse('$wsUrl/ws/notifications?token=$token'),
      );

      _isConnected = true;
      _channel!.stream.listen(
        (data) {
          final message = jsonDecode(data as String) as Map<String, dynamic>;
          _notificationsController.add(message);
        },
        onError: (error) {
          _isConnected = false;
          _scheduleReconnect();
        },
        onDone: () {
          _isConnected = false;
          _scheduleReconnect();
        },
      );
    } catch (_) {
      _scheduleReconnect();
    }
  }

  void send(Map<String, dynamic> message) {
    if (_channel != null && _isConnected) {
      _channel!.sink.add(jsonEncode(message));
    }
  }

  void subscribe(String channel) {
    send({'action': 'subscribe', 'channel': channel});
  }

  void unsubscribe(String channel) {
    send({'action': 'unsubscribe', 'channel': channel});
  }

  void _scheduleReconnect() {
    _reconnectTimer?.cancel();
    _reconnectTimer = Timer(const Duration(seconds: 5), connect);
  }

  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    _isConnected = false;
    await _channel?.sink.close();
    _channel = null;
  }

  void dispose() {
    disconnect();
    _notificationsController.close();
  }
}
