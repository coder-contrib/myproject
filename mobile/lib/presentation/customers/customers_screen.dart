import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:dio/dio.dart';
import '../../core/network/dio_client.dart';
import '../../data/models/customer_model.dart';

final customersProvider = FutureProvider.autoDispose<List<Customer>>((ref) async {
  final dio = ref.watch(dioProvider);
  final response = await dio.get('/sales/customers/');
  final data = response.data;
  if (data is List) return data.map((e) => Customer.fromJson(e)).toList();
  return (data['items'] as List).map((e) => Customer.fromJson(e)).toList();
});

class CustomersScreen extends ConsumerWidget {
  const CustomersScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final customersAsync = ref.watch(customersProvider);

    return Scaffold(
      appBar: AppBar(title: const Text('Customers')),
      floatingActionButton: FloatingActionButton.extended(
        onPressed: () => _showAddCustomerDialog(context),
        icon: const Icon(Icons.person_add),
        label: const Text('Add Customer'),
      ),
      body: customersAsync.when(
        loading: () => const Center(child: CircularProgressIndicator()),
        error: (e, _) => Center(child: Text('Error: $e')),
        data: (customers) {
          if (customers.isEmpty) return const Center(child: Text('No customers found'));
          return ListView.builder(
            itemCount: customers.length,
            itemBuilder: (context, index) {
              final customer = customers[index];
              return ListTile(
                leading: CircleAvatar(
                  child: Text(customer.name.isNotEmpty ? customer.name[0].toUpperCase() : '?'),
                ),
                title: Text(customer.name),
                subtitle: Text(customer.email ?? customer.phone ?? ''),
                trailing: Column(
                  mainAxisAlignment: MainAxisAlignment.center,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: [
                    Text('${customer.orderCount} orders'),
                    Text('EGP ${customer.totalPurchases.toStringAsFixed(0)}', style: const TextStyle(fontSize: 12, color: Colors.grey)),
                  ],
                ),
              );
            },
          );
        },
      ),
    );
  }

  void _showAddCustomerDialog(BuildContext context) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('Add Customer'),
        content: const Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            TextField(decoration: InputDecoration(labelText: 'Name')),
            SizedBox(height: 8),
            TextField(decoration: InputDecoration(labelText: 'Email')),
            SizedBox(height: 8),
            TextField(decoration: InputDecoration(labelText: 'Phone')),
          ],
        ),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancel')),
          ElevatedButton(onPressed: () => Navigator.pop(context), child: const Text('Save')),
        ],
      ),
    );
  }
}
