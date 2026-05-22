import 'package:flutter/material.dart';

class DashboardScreen extends StatelessWidget {
  const DashboardScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: GridView.count(
          crossAxisCount: MediaQuery.of(context).size.width > 800 ? 4 : 2,
          mainAxisSpacing: 16,
          crossAxisSpacing: 16,
          children: const [
            _MetricCard(title: 'Total Sales', value: '\$0', icon: Icons.attach_money, color: Colors.green),
            _MetricCard(title: 'Orders', value: '0', icon: Icons.shopping_cart, color: Colors.blue),
            _MetricCard(title: 'Products', value: '0', icon: Icons.inventory_2, color: Colors.orange),
            _MetricCard(title: 'Customers', value: '0', icon: Icons.people, color: Colors.purple),
          ],
        ),
      ),
    );
  }
}

class _MetricCard extends StatelessWidget {
  final String title;
  final String value;
  final IconData icon;
  final Color color;

  const _MetricCard({required this.title, required this.value, required this.icon, required this.color});

  @override
  Widget build(BuildContext context) {
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(icon, size: 40, color: color),
            const SizedBox(height: 12),
            Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
            const SizedBox(height: 4),
            Text(title, style: Theme.of(context).textTheme.bodySmall?.copyWith(color: Colors.grey)),
          ],
        ),
      ),
    );
  }
}
