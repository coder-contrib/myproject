import 'package:flutter/material.dart';
import 'package:intl/intl.dart';
import '../../../data/models/dashboard_model.dart';

class TopProductsList extends StatelessWidget {
  final List<TopProduct> products;

  const TopProductsList({super.key, required this.products});

  @override
  Widget build(BuildContext context) {
    if (products.isEmpty) return const SizedBox.shrink();

    final currencyFormat = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 0);

    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Top Products',
              style: Theme.of(context).textTheme.titleMedium?.copyWith(
                fontWeight: FontWeight.w600,
              ),
            ),
            const SizedBox(height: 12),
            ...products.take(5).map((product) => ListTile(
              contentPadding: EdgeInsets.zero,
              leading: CircleAvatar(
                backgroundColor: Theme.of(context).colorScheme.primaryContainer,
                child: Text('${products.indexOf(product) + 1}'),
              ),
              title: Text(product.name, maxLines: 1, overflow: TextOverflow.ellipsis),
              subtitle: Text('${product.quantitySold} units sold'),
              trailing: Text(
                currencyFormat.format(product.revenue),
                style: const TextStyle(fontWeight: FontWeight.w600),
              ),
            )),
          ],
        ),
      ),
    );
  }
}
