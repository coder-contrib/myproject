import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../data/providers/products_provider.dart';

class ProductsScreen extends ConsumerWidget {
  const ProductsScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final products = ref.watch(productsProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Products'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(productsProvider.notifier).refresh(),
          ),
        ],
      ),
      body: products.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Error: $e'),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: () => ref.read(productsProvider.notifier).refresh(), child: const Text('Retry')),
            ],
          ),
        ),
        data: (data) {
          if (data.items.isEmpty) {
            return const Center(child: Text('No products yet. Add your first product!'));
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(productsProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: data.items.length,
              itemBuilder: (context, index) {
                final p = data.items[index];
                return Card(
                  child: ListTile(
                    leading: const CircleAvatar(child: Icon(Icons.inventory_2)),
                    title: Text(p['name'] ?? 'Unnamed'),
                    subtitle: Text('SKU: ${p['sku'] ?? 'N/A'}'),
                    trailing: Text('\$${(p['sale_price'] ?? 0).toStringAsFixed(2)}'),
                    onTap: () => context.go('/products/${p['id']}'),
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        child: const Icon(Icons.add),
      ),
    );
  }
}
