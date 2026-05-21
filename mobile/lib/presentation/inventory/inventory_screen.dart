import 'package:flutter/material.dart';
import 'package:flutter_riverpod/flutter_riverpod.dart';
import 'package:intl/intl.dart';
import '../../data/providers/inventory_provider.dart';
import '../../data/models/inventory_model.dart';

class InventoryScreen extends ConsumerWidget {
  const InventoryScreen({super.key});

  @override
  Widget build(BuildContext context, WidgetRef ref) {
    final inventoryAsync = ref.watch(inventoryProvider);
    final lowStockAsync = ref.watch(lowStockProvider);

    return DefaultTabController(
      length: 2,
      child: Scaffold(
        appBar: AppBar(
          title: const Text('Inventory'),
          bottom: const TabBar(
            tabs: [
              Tab(text: 'Stock Levels', icon: Icon(Icons.warehouse)),
              Tab(text: 'Low Stock Alerts', icon: Icon(Icons.warning)),
            ],
          ),
          actions: [
            IconButton(
              icon: const Icon(Icons.refresh),
              onPressed: () {
                ref.invalidate(inventoryProvider);
                ref.invalidate(lowStockProvider);
              },
            ),
          ],
        ),
        floatingActionButton: FloatingActionButton.extended(
          onPressed: () => _showMovementDialog(context, ref),
          icon: const Icon(Icons.swap_vert),
          label: const Text('Movement'),
        ),
        body: TabBarView(
          children: [
            inventoryAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
              data: (items) => _StockList(items: items),
            ),
            lowStockAsync.when(
              loading: () => const Center(child: CircularProgressIndicator()),
              error: (e, _) => Center(child: Text('Error: $e')),
              data: (items) => items.isEmpty
                  ? const Center(child: Text('No low stock alerts'))
                  : _StockList(items: items, showAlert: true),
            ),
          ],
        ),
      ),
    );
  }

  void _showMovementDialog(BuildContext context, WidgetRef ref) {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      builder: (context) => _MovementForm(ref: ref),
    );
  }
}

class _StockList extends StatelessWidget {
  final List<InventoryItem> items;
  final bool showAlert;

  const _StockList({required this.items, this.showAlert = false});

  @override
  Widget build(BuildContext context) {
    final currencyFormat = NumberFormat.currency(symbol: 'EGP ', decimalDigits: 0);

    return ListView.builder(
      itemCount: items.length,
      itemBuilder: (context, index) {
        final item = items[index];
        return ListTile(
          leading: CircleAvatar(
            backgroundColor: item.isOutOfStock
                ? Colors.red.shade50
                : item.isLowStock
                    ? Colors.orange.shade50
                    : Colors.green.shade50,
            child: Icon(
              item.isOutOfStock ? Icons.error : item.isLowStock ? Icons.warning : Icons.check_circle,
              color: item.isOutOfStock ? Colors.red : item.isLowStock ? Colors.orange : Colors.green,
              size: 20,
            ),
          ),
          title: Text(item.productName),
          subtitle: Text('SKU: ${item.sku} | ${item.warehouseName ?? 'Warehouse #${item.warehouseId}'}'),
          trailing: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            crossAxisAlignment: CrossAxisAlignment.end,
            children: [
              Text('${item.quantity} units', style: TextStyle(
                fontWeight: FontWeight.w600,
                color: item.isLowStock ? Colors.red : null,
              )),
              Text(currencyFormat.format(item.stockValue), style: const TextStyle(fontSize: 12, color: Colors.grey)),
            ],
          ),
        );
      },
    );
  }
}

class _MovementForm extends StatefulWidget {
  final WidgetRef ref;
  const _MovementForm({required this.ref});

  @override
  State<_MovementForm> createState() => _MovementFormState();
}

class _MovementFormState extends State<_MovementForm> {
  final _productIdController = TextEditingController();
  final _quantityController = TextEditingController();
  String _type = 'in';
  bool _isLoading = false;

  Future<void> _submit() async {
    setState(() => _isLoading = true);
    try {
      await widget.ref.read(inventoryServiceProvider).recordMovement(
        productId: int.parse(_productIdController.text),
        warehouseId: 1,
        quantity: int.parse(_quantityController.text),
        type: _type,
      );
      widget.ref.invalidate(inventoryProvider);
      if (mounted) Navigator.pop(context);
    } catch (e) {
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text('Error: $e')));
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: EdgeInsets.fromLTRB(16, 16, 16, MediaQuery.of(context).viewInsets.bottom + 16),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Text('Stock Movement', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 16),
          SegmentedButton<String>(
            segments: const [
              ButtonSegment(value: 'in', label: Text('Stock In')),
              ButtonSegment(value: 'out', label: Text('Stock Out')),
            ],
            selected: {_type},
            onSelectionChanged: (v) => setState(() => _type = v.first),
          ),
          const SizedBox(height: 12),
          TextField(controller: _productIdController, decoration: const InputDecoration(labelText: 'Product ID'), keyboardType: TextInputType.number),
          const SizedBox(height: 12),
          TextField(controller: _quantityController, decoration: const InputDecoration(labelText: 'Quantity'), keyboardType: TextInputType.number),
          const SizedBox(height: 24),
          ElevatedButton(
            onPressed: _isLoading ? null : _submit,
            child: _isLoading ? const CircularProgressIndicator() : const Text('Record Movement'),
          ),
        ],
      ),
    );
  }
}
