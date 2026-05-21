import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:fl_chart/fl_chart.dart';
import 'package:intl/intl.dart';
import '../../data/providers/dashboard_provider.dart';
import '../../data/models/dashboard_model.dart';
import 'widgets/kpi_card.dart';
import 'widgets/sales_chart.dart';
import 'widgets/top_products_list.dart';

class DashboardScreen extends ConsumerWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final dashboardAsync = ref.watch(dashboardProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Dashboard'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.invalidate(dashboardProvider),
          ),
        ],
      ),
      body: dashboardAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Icon(Icons.error_outline, size: 48, color: Colors.red),
              const SizedBox(height: 16),
              Text('Failed to load dashboard: $e'),
              const SizedBox(height: 16),
              ElevatedButton(
                onPressed: () => ref.invalidate(dashboardProvider),
                child: const Text('Retry'),
              ),
            ],
          ),
        ),
        data: (data) => RefreshIndicator(
          onRefresh: () async => ref.invalidate(dashboardProvider),
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                _buildKPIGrid(context, data),
                const SizedBox(height: 24),
                SalesChart(salesTrend: data.salesTrend),
                const SizedBox(height: 24),
                TopProductsList(products: data.topProducts),
              ],
            ),
          ),
        ),
      ),
    );
  }

  Widget _buildKPIGrid(BuildContext context, DashboardData data) {
    final currencyFormat = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 0);

    return LayoutBuilder(
      builder: (context, constraints) {
        final crossAxisCount = constraints.maxWidth > 800 ? 4 : 2;
        return GridView.count(
          crossAxisCount: crossAxisCount,
          shrinkWrap: true,
          physics: const NeverScrollableScrollPhysics(),
          crossAxisSpacing: 12,
          mainAxisSpacing: 12,
          childAspectRatio: 1.6,
          children: [
            KPICard(
              title: 'Revenue',
              value: currencyFormat.format(data.totalRevenue),
              icon: Icons.trending_up,
              color: Colors.green,
              change: data.revenueGrowth,
            ),
            KPICard(
              title: 'Orders',
              value: NumberFormat.compact().format(data.totalOrders),
              icon: Icons.receipt_long,
              color: Colors.blue,
            ),
            KPICard(
              title: 'Customers',
              value: NumberFormat.compact().format(data.totalCustomers),
              icon: Icons.people,
              color: Colors.purple,
            ),
            KPICard(
              title: 'Avg Order',
              value: currencyFormat.format(data.averageOrderValue),
              icon: Icons.shopping_cart,
              color: Colors.orange,
            ),
          ],
        );
      },
    );
  }
}
