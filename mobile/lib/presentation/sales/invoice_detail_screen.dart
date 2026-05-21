import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../data/providers/invoice_provider.dart';

class InvoiceDetailScreen extends ConsumerWidget {
  final int invoiceId;

  const InvoiceDetailScreen({super.key, required this.invoiceId});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final invoiceAsync = ref.watch(invoiceDetailProvider(invoiceId));
    final currencyFormat = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 2);

    return Scaffold(
      appBar: AppBar(title: const Text('Invoice Details')),
      body: invoiceAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (invoice) => SingleChildScrollView(
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
                          Text(invoice.invoiceNumber, style: Theme.of(context).textTheme.titleLarge),
                          Chip(
                            label: Text(invoice.status.toUpperCase()),
                            backgroundColor: _getStatusColor(invoice.status).withOpacity(0.1),
                            labelStyle: TextStyle(color: _getStatusColor(invoice.status)),
                          ),
                        ],
                      ),
                      const Divider(),
                      _Row(label: 'Customer', value: invoice.customerName ?? 'Walk-in'),
                      if (invoice.createdAt != null)
                        _Row(label: 'Date', value: DateFormat('MMM d, yyyy').format(invoice.createdAt!)),
                      if (invoice.dueDate != null)
                        _Row(label: 'Due Date', value: DateFormat('MMM d, yyyy').format(invoice.dueDate!)),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Items', style: Theme.of(context).textTheme.titleMedium),
                      const Divider(),
                      ...invoice.items.map((item) => Padding(
                        padding: const EdgeInsets.symmetric(vertical: 8),
                        child: Row(
                          children: [
                            Expanded(child: Text(item.productName ?? 'Product #${item.productId}')),
                            Text('${item.quantity} x ${currencyFormat.format(item.unitPrice)}'),
                            const SizedBox(width: 16),
                            Text(currencyFormat.format(item.lineTotal), style: const TextStyle(fontWeight: FontWeight.w600)),
                          ],
                        ),
                      )),
                      const Divider(),
                      _Row(label: 'Subtotal', value: currencyFormat.format(invoice.subtotal)),
                      _Row(label: 'Tax', value: currencyFormat.format(invoice.taxAmount)),
                      const Divider(),
                      _Row(label: 'Total', value: currencyFormat.format(invoice.total), bold: true),
                    ],
                  ),
                ),
              ),
              if (invoice.isDraft) ...[
                const SizedBox(height: 24),
                Row(
                  children: [
                    Expanded(
                      child: ElevatedButton.icon(
                        onPressed: () => _updateStatus(ref, 'confirmed'),
                        icon: const Icon(Icons.check),
                        label: const Text('Confirm'),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: OutlinedButton.icon(
                        onPressed: () => _updateStatus(ref, 'void'),
                        icon: const Icon(Icons.cancel),
                        label: const Text('Void'),
                        style: OutlinedButton.styleFrom(foregroundColor: Colors.red),
                      ),
                    ),
                  ],
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _updateStatus(WidgetRef ref, String status) async {
    await ref.read(invoiceServiceProvider).updateStatus(invoiceId, status);
    ref.invalidate(invoiceDetailProvider(invoiceId));
  }

  Color _getStatusColor(String status) => switch (status) {
    'draft' => Colors.grey,
    'confirmed' => Colors.blue,
    'paid' => Colors.green,
    'void' => Colors.red,
    _ => Colors.grey,
  };
}

class _Row extends StatelessWidget {
  final String label;
  final String value;
  final bool bold;

  const _Row({required this.label, required this.value, this.bold = false});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: TextStyle(color: Colors.grey.shade600)),
          Text(value, style: TextStyle(fontWeight: bold ? FontWeight.bold : FontWeight.normal)),
        ],
      ),
    );
  }
}
