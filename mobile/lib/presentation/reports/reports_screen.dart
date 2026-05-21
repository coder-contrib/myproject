import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../data/providers/dashboard_provider.dart';

class ReportsScreen extends ConsumerWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reports & Analytics')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _ReportCategory(
            title: 'Sales Reports',
            icon: Icons.receipt_long,
            color: Colors.blue,
            reports: [
              _ReportItem('Daily Sales Summary', 'Today\'s sales performance', Icons.today),
              _ReportItem('Monthly Revenue', 'Revenue breakdown by month', Icons.calendar_month),
              _ReportItem('Sales by Product', 'Top performing products', Icons.category),
              _ReportItem('Sales by Customer', 'Customer purchase analysis', Icons.people),
            ],
          ),
          const SizedBox(height: 16),
          _ReportCategory(
            title: 'Financial Reports',
            icon: Icons.account_balance,
            color: Colors.green,
            reports: [
              _ReportItem('Profit & Loss', 'Income vs expenses', Icons.trending_up),
              _ReportItem('Cash Flow', 'Cash inflows and outflows', Icons.money),
              _ReportItem('Accounts Receivable', 'Outstanding customer balances', Icons.receipt),
              _ReportItem('Tax Summary', 'Tax collected and payable', Icons.gavel),
            ],
          ),
          const SizedBox(height: 16),
          _ReportCategory(
            title: 'Inventory Reports',
            icon: Icons.warehouse,
            color: Colors.orange,
            reports: [
              _ReportItem('Stock Valuation', 'Current inventory value', Icons.attach_money),
              _ReportItem('Low Stock Report', 'Items below reorder level', Icons.warning),
              _ReportItem('Stock Movement', 'Movement history', Icons.swap_vert),
            ],
          ),
          const SizedBox(height: 16),
          Card(
            child: Padding(
              padding: const EdgeInsets.all(16),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      Icon(Icons.smart_toy, color: Colors.purple.shade700),
                      const SizedBox(width: 8),
                      Text('AI Insights', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
                    ],
                  ),
                  const SizedBox(height: 12),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.auto_awesome),
                    title: const Text('Executive Summary'),
                    subtitle: const Text('AI-generated business overview'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {},
                  ),
                  ListTile(
                    contentPadding: EdgeInsets.zero,
                    leading: const Icon(Icons.query_stats),
                    title: const Text('Ask AI'),
                    subtitle: const Text('Natural language query assistant'),
                    trailing: const Icon(Icons.chevron_right),
                    onTap: () {},
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _ReportCategory extends StatelessWidget {
  final String title;
  final IconData icon;
  final Color color;
  final List<_ReportItem> reports;

  const _ReportCategory({required this.title, required this.icon, required this.color, required this.reports});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icon, color: color),
                const SizedBox(width: 8),
                Text(title, style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.w600)),
              ],
            ),
            const Divider(),
            ...reports.map((report) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: Icon(report.icon, size: 20, color: Colors.grey),
              title: Text(report.title),
              subtitle: Text(report.subtitle, style: const TextStyle(fontSize: 12)),
              trailing: Row(
                mainAxisSize: MainAxisSize.min,
                children: [
                  IconButton(icon: const Icon(Icons.picture_as_pdf, size: 20), onPressed: () {}, tooltip: 'Export PDF'),
                  IconButton(icon: const Icon(Icons.table_chart, size: 20), onPressed: () {}, tooltip: 'Export Excel'),
                ],
              ),
              onTap: () {},
            )),
          ],
        ),
      ),
    );
  }
}

class _ReportItem {
  final String title;
  final String subtitle;
  final IconData icon;

  const _ReportItem(this.title, this.subtitle, this.icon);
}
