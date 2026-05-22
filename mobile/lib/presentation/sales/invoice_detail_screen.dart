import 'package:flutter/material.dart';

class InvoiceDetailScreen extends StatelessWidget {
  final int invoiceId;

  const InvoiceDetailScreen({super.key, required this.invoiceId});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: Text('Invoice #$invoiceId'),
        actions: [
          IconButton(icon: const Icon(Icons.print), onPressed: () {}),
          IconButton(icon: const Icon(Icons.share), onPressed: () {}),
        ],
      ),
      body: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Invoice Details', style: Theme.of(context).textTheme.titleLarge),
                        Chip(label: const Text('Draft'), backgroundColor: Colors.grey.shade200),
                      ],
                    ),
                    const Divider(height: 24),
                    _buildRow('Invoice No.', 'INV-$invoiceId'),
                    _buildRow('Customer', 'Loading...'),
                    _buildRow('Date', '---'),
                    _buildRow('Due Date', '---'),
                    _buildRow('Total', '\$0.00'),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _buildRow(String label, String value) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 8),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: const TextStyle(color: Colors.grey)),
          Text(value, style: const TextStyle(fontWeight: FontWeight.w600)),
        ],
      ),
    );
  }
}
