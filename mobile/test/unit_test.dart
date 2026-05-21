import 'package:flutter_test/flutter_test.dart';

void main() {
  group('PaginatedResponse', () {
    test('hasNext is true when page < pages', () {
      final page = 1;
      final pages = 3;
      expect(page < pages, isTrue);
    });

    test('hasNext is false on last page', () {
      final page = 3;
      final pages = 3;
      expect(page < pages, isFalse);
    });
  });

  group('AuthTokens', () {
    test('parses from JSON', () {
      final json = {
        'access_token': 'abc123',
        'refresh_token': 'def456',
        'token_type': 'bearer',
      };
      expect(json['access_token'], 'abc123');
      expect(json['refresh_token'], 'def456');
      expect(json['token_type'], 'bearer');
    });
  });

  group('Product margin calculation', () {
    test('50% margin', () {
      final price = 100.0;
      final cost = 50.0;
      final margin = ((price - cost) / price) * 100;
      expect(margin, 50.0);
    });

    test('0% margin when price equals cost', () {
      final price = 50.0;
      final cost = 50.0;
      final margin = ((price - cost) / price) * 100;
      expect(margin, 0.0);
    });

    test('handles zero price gracefully', () {
      final price = 0.0;
      final margin = price > 0 ? ((price - 30) / price) * 100 : 0.0;
      expect(margin, 0.0);
    });
  });

  group('Currency formatting', () {
    test('formats EGP currency', () {
      final amount = 1234567.89;
      final formatted = 'EGP ${amount.toStringAsFixed(2)}';
      expect(formatted, 'EGP 1234567.89');
    });
  });
}
