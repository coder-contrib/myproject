import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class InvoicesScreen extends StatelessWidget {
  const InvoicesScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Invoices'),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
        ],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: 0,
        itemBuilder: (context, index) {
          return Card(
            child: ListTile(
              leading: const CircleAvatar(child: Icon(Icons.receipt_long)),
              title: const Text('INV-0001'),
              subtitle: const Text('Customer Name'),
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text('\$0.00', style: TextStyle(fontWeight: FontWeight.bold)),
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 2),
                    decoration: BoxDecoration(color: Colors.green.shade100, borderRadius: BorderRadius.circular(12)),
                    child: const Text('Paid', style: TextStyle(fontSize: 11, color: Colors.green)),
                  ),
                ],
              ),
              onTap: () => context.go('/sales/$index'),
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
