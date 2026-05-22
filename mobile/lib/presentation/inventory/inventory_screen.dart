import 'package:flutter/material.dart';

class InventoryScreen extends StatelessWidget {
  const InventoryScreen({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Inventory'),
        actions: [
          IconButton(icon: const Icon(Icons.search), onPressed: () {}),
          IconButton(icon: const Icon(Icons.warehouse), onPressed: () {}),
        ],
      ),
      body: ListView.builder(
        padding: const EdgeInsets.all(8),
        itemCount: 0,
        itemBuilder: (context, index) {
          return Card(
            child: ListTile(
              leading: const CircleAvatar(child: Icon(Icons.inventory)),
              title: const Text('Product Name'),
              subtitle: const Text('Warehouse: Main'),
              trailing: Column(
                mainAxisAlignment: MainAxisAlignment.center,
                crossAxisAlignment: CrossAxisAlignment.end,
                children: [
                  const Text('0 units', style: TextStyle(fontWeight: FontWeight.bold)),
                  Text('In stock', style: TextStyle(fontSize: 11, color: Colors.green.shade700)),
                ],
              ),
            ),
          );
        },
      ),
    );
  }
}
