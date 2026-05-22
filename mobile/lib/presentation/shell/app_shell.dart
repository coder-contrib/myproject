import 'package:flutter/material.dart';
import 'package:go_router/go_router.dart';

class AppShell extends StatelessWidget {
  final Widget child;

  const AppShell({super.key, required this.child});

  int _currentIndex(BuildContext context) {
    final location = GoRouterState.of(context).matchedLocation;
    if (location.startsWith('/dashboard')) return 0;
    if (location.startsWith('/products')) return 1;
    if (location.startsWith('/sales')) return 2;
    if (location.startsWith('/inventory')) return 3;
    if (location.startsWith('/customers')) return 4;
    if (location.startsWith('/reports')) return 5;
    if (location.startsWith('/settings')) return 6;
    return 0;
  }

  void _onTap(BuildContext context, int index) {
    switch (index) {
      case 0: context.go('/dashboard');
      case 1: context.go('/products');
      case 2: context.go('/sales');
      case 3: context.go('/inventory');
      case 4: context.go('/customers');
      case 5: context.go('/reports');
      case 6: context.go('/settings');
    }
  }

  @override
  Widget build(BuildContext context) {
    final isWide = MediaQuery.of(context).size.width > 800;
    final index = _currentIndex(context);

    if (isWide) {
      return Scaffold(
        body: Row(
          children: [
            NavigationRail(
              selectedIndex: index,
              onDestinationSelected: (i) => _onTap(context, i),
              labelType: NavigationRailLabelType.all,
              destinations: const [
                NavigationRailDestination(icon: Icon(Icons.dashboard), label: Text('Dashboard')),
                NavigationRailDestination(icon: Icon(Icons.inventory_2), label: Text('Products')),
                NavigationRailDestination(icon: Icon(Icons.receipt_long), label: Text('Sales')),
                NavigationRailDestination(icon: Icon(Icons.warehouse), label: Text('Inventory')),
                NavigationRailDestination(icon: Icon(Icons.people), label: Text('Customers')),
                NavigationRailDestination(icon: Icon(Icons.bar_chart), label: Text('Reports')),
                NavigationRailDestination(icon: Icon(Icons.settings), label: Text('Settings')),
              ],
            ),
            const VerticalDivider(width: 1),
            Expanded(child: child),
          ],
        ),
      );
    }

    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: index > 4 ? 4 : index,
        onDestinationSelected: (i) {
          if (i == 4) {
            _showMoreMenu(context);
          } else {
            _onTap(context, i);
          }
        },
        destinations: const [
          NavigationDestination(icon: Icon(Icons.dashboard), label: 'Dashboard'),
          NavigationDestination(icon: Icon(Icons.inventory_2), label: 'Products'),
          NavigationDestination(icon: Icon(Icons.receipt_long), label: 'Sales'),
          NavigationDestination(icon: Icon(Icons.warehouse), label: 'Inventory'),
          NavigationDestination(icon: Icon(Icons.more_horiz), label: 'More'),
        ],
      ),
    );
  }

  void _showMoreMenu(BuildContext context) {
    showModalBottomSheet(
      context: context,
      builder: (ctx) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            ListTile(leading: const Icon(Icons.people), title: const Text('Customers'), onTap: () { Navigator.pop(ctx); context.go('/customers'); }),
            ListTile(leading: const Icon(Icons.bar_chart), title: const Text('Reports'), onTap: () { Navigator.pop(ctx); context.go('/reports'); }),
            ListTile(leading: const Icon(Icons.settings), title: const Text('Settings'), onTap: () { Navigator.pop(ctx); context.go('/settings'); }),
          ],
        ),
      ),
    );
  }
}
