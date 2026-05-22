import 'package:flutter/material.dart';

class ReportsScreen extends StatelessWidget {
  const ReportsScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Reports')),
      body: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          _ReportTile(icon: Icons.bar_chart, title: 'Sales Report', subtitle: 'Revenue, orders, and trends', onTap: () {}),
          _ReportTile(icon: Icons.inventory, title: 'Inventory Report', subtitle: 'Stock levels and movements', onTap: () {}),
          _ReportTile(icon: Icons.people, title: 'Customer Report', subtitle: 'Activity and top customers', onTap: () {}),
          _ReportTile(icon: Icons.account_balance, title: 'Financial Report', subtitle: 'P&L, balance sheet', onTap: () {}),
          _ReportTile(icon: Icons.trending_up, title: 'AI Insights', subtitle: 'AI-powered business analytics', onTap: () {}),
        ],
      ),
    );
  }
}

class _ReportTile extends StatelessWidget {
  final IconData icon;
  final String title;
  final String subtitle;
  final VoidCallback onTap;

  const _ReportTile({required this.icon, required this.title, required this.subtitle, required this.onTap});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: ListTile(
        leading: CircleAvatar(backgroundColor: Theme.of(context).colorScheme.primaryContainer, child: Icon(icon, color: Theme.of(context).colorScheme.primary)),
        title: Text(title),
        subtitle: Text(subtitle),
        trailing: const Icon(Icons.chevron_right),
        onTap: onTap,
      ),
    );
  }
}
