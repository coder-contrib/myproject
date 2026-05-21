import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import 'package:intl/intl.dart';
import '../../data/providers/invoice_provider.dart';
import '../../data/models/invoice_model.dart';

class InvoicesScreen extends ConsumerStatefulWidget {
  const InvoicesScreen({super.key});

  @override
  ConsumerState<InvoicesScreen> createState() => _InvoicesScreenState();
}

class _InvoicesScreenState extends ConsumerState<InvoicesScreen> {
  String? _statusFilter;
  int _page = 1;

  @override
  Widget build(BuildContext context) {
    final query = InvoiceQuery(page: _page, status: _statusFilter);
    final invoicesAsync = ref.watch(invoicesProvider(query));

    return Scaffold(
      appBar: AppBar(
        title: const Text('Sales & Invoices'),
        actions: [
          PopupMenuButton<String?>(
            icon: const Icon(Icons.filter_list),
            onSelected: (value) => setState(() { _statusFilter = value; _page = 1; }),
            itemBuilder: (context) => [
              const PopupMenuItem(value: null, child: Text('All')),
              const PopupMenuItem(value: 'draft', child: Text('Draft')),
              const PopupMenuItem(value: 'confirmed', child: Text('Confirmed')),
              const PopupMenuItem(value: 'paid', child: Text('Paid')),
              const PopupMenuItem(value: 'void', child: Text('Void')),
            ],
          ),
        ],
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.go('/sales/new'),
        icon: const Icon(Icons.add),
        label: const Text('New Invoice'),
      ),
      body: invoicesAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (response) {
          if (response.items.isEmpty) {
            return const Center(child: Text('No invoices found'));
          }
          return ListView.builder(
            itemCount: response.items.length,
            itemBuilder: (context, index) => _InvoiceTile(
              invoice: response.items[index],
              onTap: () => context.go('/sales/${response.items[index].id}'),
            ),
          );
        },
      ),
    );
  }
}

class _InvoiceTile extends StatelessWidget {
  final Invoice invoice;
  final VoidCallback onTap;

  const _InvoiceTile({required this.invoice, required this.onTap});

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 2);
    final dateFormat = DateFormat('MMM d, yyyy');

    return ListTile(
      onTap: onTap,
      leading: CircleAvatar(
        backgroundColor: _statusColor.withOpacity(0.1),
        child: Icon(_statusIcon, color: _statusColor, size: 20),
      ),
      title: Text(invoice.invoiceNumber),
      subtitle: Text(
        '${invoice.customerName ?? 'Walk-in'} | ${invoice.createdAt != null ? dateFormat.format(invoice.createdAt!) : ''}',
      ),
      trailing: Column(
        mainAxisAlignment: MainAxisAlignment.center,
        crossAxisAlignment: CrossAxisAlignment.end,
        children: [
          Text(currencyFormat.format(invoice.total), style: const TextStyle(fontWeight: FontWeight.w600)),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
            decoration: BoxDecoration(
              color: _statusColor.withOpacity(0.1),
              borderRadius: BorderRadius.circular(8),
            ),
            child: Text(
              invoice.status.toUpperCase(),
              style: TextStyle(fontSize: 10, fontWeight: FontWeight.w600, color: _statusColor),
            ),
          ),
        ],
      ),
    );
  }

  Color get _statusColor => switch (invoice.status) {
    'draft' => Colors.grey,
    'confirmed' => Colors.blue,
    'paid' => Colors.green,
    'void' => Colors.red,
    _ => Colors.grey,
  };

  IconData get _statusIcon => switch (invoice.status) {
    'draft' => Icons.edit_note,
    'confirmed' => Icons.check_circle_outline,
    'paid' => Icons.paid,
    'void' => Icons.cancel_outlined,
    _ => Icons.receipt,
  };
}
