import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import '../../data/providers/customers_provider.dart';

class CustomersScreen extends ConsumerWidget {
  const CustomersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final customers = ref.watch(customersProvider);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Customers'),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh),
            onPressed: () => ref.read(customersProvider.notifier).refresh(),
          ),
        ],
      ),
      body: customers.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text('Error: $e'),
              const SizedBox(height: 16),
              ElevatedButton(onPressed: () => ref.read(customersProvider.notifier).refresh(), child: const Text('Retry')),
            ],
          ),
        ),
        data: (data) {
          if (data.items.isEmpty) {
            return const Center(child: Text('No customers yet.'));
          }
          return RefreshIndicator(
            onRefresh: () => ref.read(customersProvider.notifier).refresh(),
            child: ListView.builder(
              padding: const EdgeInsets.all(8),
              itemCount: data.items.length,
              itemBuilder: (context, index) {
                final c = data.items[index];
                return Card(
                  child: ListTile(
                    leading: CircleAvatar(
                      child: Text((c['full_name'] ?? '?')[0].toUpperCase()),
                    ),
                    title: Text(c['full_name'] ?? 'Unknown'),
                    subtitle: Text(c['email'] ?? ''),
                    trailing: Icon(
                      Icons.circle,
                      size: 12,
                      color: (c['is_active'] ?? false) ? Colors.green : Colors.grey,
                    ),
                  ),
                );
              },
            ),
          );
        },
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {},
        child: const Icon(Icons.person_add),
      ),
    );
  }
}
