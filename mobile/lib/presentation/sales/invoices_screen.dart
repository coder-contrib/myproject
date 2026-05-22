import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../data/providers/invoices_provider.dart';

class InvoicesScreen extends ConsumerWidget {
  const InvoicesScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final invoices = ref.watch(invoicesProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Invoices'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(invoicesProvider.notifier).refresh(),
          ),
        ],
      ),
      body: invoices.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Error: $e'),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: () => ref.read(invoicesProvider.notifier).refresh(), child: const Text('Retry')),
            ],
          ),
        ),
        data: (data) {
          if (data.items.isEmpty) {
            return const Center(child: Text('No invoices yet.'));
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(invoicesProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: data.items.length,
              itemBuilder: (context, index) {
                final inv = data.items[index];
                final status = inv['status'] ?? 'draft';
                final statusColor = switch (status) {
                  'paid' => Colors.green,
                  'overdue' => Colors.red,
                  'sent' => Colors.blue,
                  _ => Colors.grey,
                };
                return Card(
                  child: ListTile(
                    leading: const CircleAvatar(child: Icon(Icons.receipt_long)),
                    title: Text(inv['invoice_number'] ?? 'INV-???'),
                    subtitle: Text('Total: \$${(inv['total'] ?? 0).toStringAsFixed(2)}'),
                    trailing: Container(
                      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                      decoration: BoxDecoration(
                        color: statusColor.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(12),
                      ),
                      child: Text(status.toUpperCase(), style: TextStyle(fontSize: 11, color: statusColor, fontWeight: FontWeight.bold)),
                    ),
                    onTap: () => context.go('/sales/${inv['id']}'),
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => context.go('/sales/new'),
        icon: const Icon(Icons.add),
        label: const Text('New Invoice'),
      ),
    );
  }
}
