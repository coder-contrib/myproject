import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/providers/inventory_provider.dart';

class InventoryScreen extends ConsumerWidget {
  const InventoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final inventory = ref.watch(inventoryProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Inventory'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(inventoryProvider.notifier).refresh(),
          ),
        ],
      ),
      body: inventory.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Error: $e'),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: () => ref.read(inventoryProvider.notifier).refresh(), child: const Text('Retry')),
            ],
          ),
        ),
        data: (data) {
          if (data.items.isEmpty) {
            return const Center(child: Text('No stock records yet.'));
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(inventoryProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: data.items.length,
              itemBuilder: (context, index) {
                final item = data.items[index];
                final qty = item['quantity'] ?? 0;
                final available = item['available_quantity'] ?? 0;
                return Card(
                  child: ListTile(
                    leading: const CircleAvatar(child: Icon(Icons.inventory)),
                    title: Text('Product: ${item['product_id']?.toString().substring(0, 8) ?? 'N/A'}...'),
                    subtitle: Text('Warehouse: ${item['warehouse_id']?.toString().substring(0, 8) ?? 'N/A'}...'),
                    trailing: Column(
                      mainAxisAlignment: MainAxisAlignment.center,
                      crossAxisAlignment: CrossAxisAlignment.end,
                      children: [
                        Text('$qty units', style: const TextStyle(fontWeight: FontWeight.bold)),
                        Text('$available avail.', style: TextStyle(fontSize: 11, color: available > 0 ? Colors.green.shade700 : Colors.red.shade700)),
                      ],
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
    );
  }
}
