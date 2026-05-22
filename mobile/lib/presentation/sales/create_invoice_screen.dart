import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class CreateInvoiceScreen extends StatefulWidget {
  const CreateInvoiceScreen({super.key});

  @override
  State<CreateInvoiceScreen> createState() => _CreateInvoiceScreenState();
}

class _CreateInvoiceScreenState extends State<CreateInvoiceScreen> {
  final _formKey = GlobalKey<FormState>();
  final _customerController = TextEditingController();

  @override
  void dispose() {
    _customerController.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('New Invoice'),
        actions: [
          TextButton.icon(
            onPressed: () {},
            icon: const Icon(Icons.save, color: Colors.white),
            label: const Text('Save', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: Form(
        key: _formKey,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text('Customer', style: Theme.of(context).textTheme.titleMedium),
                    const SizedBox(height: 8),
                    TextFormField(
                      controller: _customerController,
                      decoration: const InputDecoration(hintText: 'Search customer...', prefixIcon: Icon(Icons.person_search)),
                      validator: (v) => v == null || v.isEmpty ? 'Customer is required' : null,
                    ),
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
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        Text('Line Items', style: Theme.of(context).textTheme.titleMedium),
                        TextButton.icon(onPressed: () {}, icon: const Icon(Icons.add), label: const Text('Add Item')),
                      ],
                    ),
                    const SizedBox(height: 8),
                    const Center(child: Text('No items added yet', style: TextStyle(color: Colors.grey))),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),
            Card(
              child: Padding(
                padding: const EdgeInsets.all(16),
                child: Column(
                  children: [
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Subtotal'), const Text('\$0.00')]),
                    const SizedBox(height: 8),
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [const Text('Tax'), const Text('\$0.00')]),
                    const Divider(height: 24),
                    Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [
                      Text('Total', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                      Text('\$0.00', style: Theme.of(context).textTheme.titleMedium?.copyWith(fontWeight: FontWeight.bold)),
                    ]),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
