import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../presentation/auth/login_screen.dart';
import '../../presentation/dashboard/dashboard_screen.dart';
import '../../presentation/products/products_screen.dart';
import '../../presentation/products/product_detail_screen.dart';
import '../../presentation/sales/invoices_screen.dart';
import '../../presentation/sales/invoice_detail_screen.dart';
import '../../presentation/sales/create_invoice_screen.dart';
import '../../presentation/inventory/inventory_screen.dart';
import '../../presentation/customers/customers_screen.dart';
import '../../presentation/reports/reports_screen.dart';
import '../../presentation/settings/settings_screen.dart';
import '../../presentation/shell/app_shell.dart';
import '../../data/providers/auth_provider.dart';

final appRouterProvider = Provider<GoRouter>((ref) {
  final authState = ref.watch(authStateProvider);

  return GoRouter(
    initialLocation: '/dashboard',
    redirect: (context, state) {
      final isLoggedIn = authState.value != null;
      final isLoginRoute = state.matchedLocation == '/login';

      if (!isLoggedIn && !isLoginRoute) return '/login';
      if (isLoggedIn && isLoginRoute) return '/dashboard';
      return null;
    },
    routes: [
      GoRoute(
        path: '/login',
        builder: (context, state) => const LoginScreen(),
      ),
      ShellRoute(
        builder: (context, state, child) => AppShell(child: child),
        routes: [
          GoRoute(
            path: '/dashboard',
            builder: (context, state) => const DashboardScreen(),
          ),
          GoRoute(
            path: '/products',
            builder: (context, state) => const ProductsScreen(),
            routes: [
              GoRoute(
                path: ':id',
                builder: (context, state) => ProductDetailScreen(
                  productId: int.parse(state.pathParameters['id']!),
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/sales',
            builder: (context, state) => const InvoicesScreen(),
            routes: [
              GoRoute(
                path: 'new',
                builder: (context, state) => const CreateInvoiceScreen(),
              ),
              GoRoute(
                path: ':id',
                builder: (context, state) => InvoiceDetailScreen(
                  invoiceId: int.parse(state.pathParameters['id']!),
                ),
              ),
            ],
          ),
          GoRoute(
            path: '/inventory',
            builder: (context, state) => const InventoryScreen(),
          ),
          GoRoute(
            path: '/customers',
            builder: (context, state) => const CustomersScreen(),
          ),
          GoRoute(
            path: '/reports',
            builder: (context, state) => const ReportsScreen(),
          ),
          GoRoute(
            path: '/settings',
            builder: (context, state) => const SettingsScreen(),
          ),
        ],
      ),
    ],
  );
});
