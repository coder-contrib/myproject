import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:go_router/go_router.dart';
import '../../data/providers/invoice_provider.dart';
import '../../data/providers/product_provider.dart';
import '../../data/models/product_model.dart';

class CreateInvoiceScreen extends ConsumerStatefulWidget {
  const CreateInvoiceScreen({super.key});

  @override
  ConsumerState<CreateInvoiceScreen> createState() => _CreateInvoiceScreenState();
}

class _CreateInvoiceScreenState extends ConsumerState<CreateInvoiceScreen> {
  final List<_LineItem> _items = [];
  int? _customerId;
  String _notes = '';
  bool _isSubmitting = false;

  double get _subtotal => _items.fold(0, (sum, item) => sum + item.total);
  double get _tax => _subtotal * 0.14;
  double get _total => _subtotal + _tax;

  void _addItem(Product product) {
    setState(() {
      final existing = _items.indexWhere((i) => i.productId == product.id);
      if (existing >= 0) {
        _items[existing].quantity++;
      } else {
        _items.add(_LineItem(productId: product.id, name: product.name, unitPrice: product.price, quantity: 1));
      }
    });
  }

  void _removeItem(int index) {
    setState(() => _items.removeAt(index));
  }

  Future<void> _submit() async {
    if (_items.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Add at least one item')));
      return;
    }

    setState(() => _isSubmitting = true);
    try {
      await ref.read(invoiceServiceProvider).createInvoice({
        'customer_id': _customerId,
        'items': _items.map((i) => {
          'product_id': i.productId,
          'quantity': i.quantity,
          'unit_price': i.unitPrice,
        }).toList(),
        'notes': _notes.isNotEmpty ? _notes : null,
      });
      if (mounted) context.go('/sales');
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _isSubmitting = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('New Invoice'),
        actions: [
          TextButton.icon(
            onPressed: _isSubmitting ? null : _submit,
            icon: const Icon(Icons.check, color: Colors.white),
            label: const Text('Save', style: TextStyle(color: Colors.white)),
          ),
        ],
      ),
      body: Column(
        children: [
          Expanded(
            child: ListView(
              padding: const EdgeInsets.all(16),
              children: [
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text('Line Items', style: Theme.of(context).textTheme.titleMedium),
                        const SizedBox(height: 12),
                        ..._items.asMap().entries.map((entry) => ListTile(
                          contentPadding: EdgeInsets.zero,
                          title: Text(entry.value.name),
                          subtitle: Text('EGP ${entry.value.unitPrice.toStringAsFixed(2)} x ${entry.value.quantity}'),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text('EGP ${entry.value.total.toStringAsFixed(2)}'),
                              IconButton(
                                icon: const Icon(Icons.remove_circle_outline, color: Colors.red),
                                onPressed: () => _removeItem(entry.key),
                              ),
                            ],
                          ),
                        )),
                        OutlinedButton.icon(
                          onPressed: () => _showProductPicker(context),
                          icon: const Icon(Icons.add),
                          label: const Text('Add Item'),
                        ),
                      ],
                    ),
                  ),
                ),
                const SizedBox(height: 16),
                Card(
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: TextFormField(
                      decoration: const InputDecoration(labelText: 'Notes (optional)', border: InputBorder.none),
                      maxLines: 3,
                      onChanged: (v) => _notes = v,
                    ),
                  ),
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Theme.of(context).cardColor,
              boxShadow: [BoxShadow(color: Colors.black.withOpacity(0.05), blurRadius: 10, offset: const Offset(0, -2))],
            ),
            child: Column(
              children: [
                _TotalRow(label: 'Subtotal', value: _subtotal),
                _TotalRow(label: 'Tax (14%)', value: _tax),
                const Divider(),
                _TotalRow(label: 'Total', value: _total, bold: true),
              ],
            ),
          ),
        ],
      ),
    );
  }

  void _showProductPicker(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (context) => _ProductPickerSheet(onSelect: _addItem),
    );
  }
}

class _LineItem {
  final int productId;
  final String name;
  final double unitPrice;
  int quantity;

  _LineItem({required this.productId, required this.name, required this.unitPrice, required this.quantity});

  double get total => unitPrice * quantity;
}

class _TotalRow extends StatelessWidget {
  final String label;
  final double value;
  final bool bold;

  const _TotalRow({required this.label, required this.value, this.bold = false});

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 4),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label),
          Text('EGP ${value.toStringAsFixed(2)}', style: TextStyle(fontWeight: bold ? FontWeight.bold : FontWeight.normal, fontSize: bold ? 18 : 14)),
        ],
      ),
    );
  }
}

class _ProductPickerSheet extends ConsumerWidget {
  final void Function(Product) onSelect;

  const _ProductPickerSheet({required this.onSelect});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final productsAsync = ref.watch(productsProvider(const ProductQuery(size: 50)));

    return Container(
      height: MediaQuery.of(context).size.height * 0.6,
      padding: const EdgeInsets.all(16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Select Product', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 12),
          Expanded(
            child: productsAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
              data: (response) => ListView.builder(
                itemCount: response.items.length,
                itemBuilder: (context, index) {
                  final product = response.items[index];
                  return ListTile(
                    title: Text(product.name),
                    subtitle: Text('EGP ${product.price.toStringAsFixed(2)} | Stock: ${product.quantity}'),
                    onTap: () {
                      onSelect(product);
                      Navigator.pop(context);
                    },
                  );
                },
              ),
            ),
          ),
        ],
      ),
    );
  }
}
