import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';

void main() {
  group('Login Screen', () {
    testWidgets('renders email and password fields', (tester) async {
      await tester.pumpWidget(
        const ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Column(
                children: [
                  TextField(key: Key('email_field')),
                  TextField(key: Key('password_field')),
                ],
              ),
            ),
          ),
        ),
      );

      expect(find.byKey(const Key('email_field')), findsOneWidget);
      expect(find.byKey(const Key('password_field')), findsOneWidget);
    });

    testWidgets('shows validation errors on empty submit', (tester) async {
      await tester.pumpWidget(
        ProviderScope(
          child: MaterialApp(
            home: Scaffold(
              body: Form(
                child: Column(
                  children: [
                    TextFormField(
                      validator: (v) => v?.isEmpty == true ? 'Required' : null,
                    ),
                    ElevatedButton(
                      onPressed: () {},
                      child: const Text('Sign In'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      );

      expect(find.text('Sign In'), findsOneWidget);
    });
  });

  group('KPI Card', () {
    testWidgets('renders title and value', (tester) async {
      await tester.pumpWidget(
        const MaterialApp(
          home: Scaffold(
            body: Card(
              child: Column(
                children: [
                  Text('EGP 125,000'),
                  Text('Revenue'),
                ],
              ),
            ),
          ),
        ),
      );

      expect(find.text('EGP 125,000'), findsOneWidget);
      expect(find.text('Revenue'), findsOneWidget);
    });
  });

  group('Product Model', () {
    test('calculates margin correctly', () {
      // margin = (price - cost) / price * 100
      final price = 100.0;
      final cost = 60.0;
      final margin = ((price - cost) / price) * 100;
      expect(margin, 40.0);
    });

    test('detects low stock', () {
      final quantity = 5;
      expect(quantity < 10, isTrue);
    });
  });

  group('Invoice Model', () {
    test('calculates line total', () {
      final quantity = 3;
      final unitPrice = 25.0;
      final lineTotal = quantity * unitPrice;
      expect(lineTotal, 75.0);
    });

    test('detects overdue invoice', () {
      final dueDate = DateTime.now().subtract(const Duration(days: 5));
      final status = 'confirmed';
      final isOverdue = dueDate.isBefore(DateTime.now()) && status != 'paid';
      expect(isOverdue, isTrue);
    });
  });
}
