import 'package:flutter/material.dart';

class AppShell extends StatelessWidget {
  final Widget child;

  const AppShell({super.key, required this.child});

  @override
  Widget build(BuildContext context) {
    return LayoutBuilder(
      builder: (context, constraints) {
        if (constraints.maxWidth >= 900) {
          return _DesktopLayout(child: child);
        }
        return _MobileLayout(child: child);
      },
    );
  }
}

class _DesktopLayout extends StatefulWidget {
  final Widget child;
  const _DesktopLayout({required this.child});

  @override
  State<_DesktopLayout> createState() => _DesktopLayoutState();
}

class _DesktopLayoutState extends State<_DesktopLayout> {
  bool _isExpanded = true;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            extended: _isExpanded,
            leading: IconButton(
              icon: Icon(_isExpanded ? Icons.menu_open : Icons.menu),
              onPressed: () => setState(() => _isExpanded = !_isExpanded),
            ),
            destinations: _navDestinations,
            selectedIndex: _getSelectedIndex(context),
            onDestinationSelected: (index) => _navigate(context, index),
          ),
          const VerticalDivider(thickness: 1, width: 1),
          Expanded(child: widget.child),
        ],
      ),
    );
  }
}

class _MobileLayout extends StatelessWidget {
  final Widget child;
  const _MobileLayout({required this.child});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: child,
      bottomNavigationBar: NavigationBar(
        selectedIndex: _getSelectedIndex(context),
        onDestinationSelected: (index) => _navigate(context, index),
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
}

const _navDestinations = [
  NavigationRailDestination(icon: Icon(Icons.dashboard), label: Text('Dashboard')),
  NavigationRailDestination(icon: Icon(Icons.inventory_2), label: Text('Products')),
  NavigationRailDestination(icon: Icon(Icons.receipt_long), label: Text('Sales')),
  NavigationRailDestination(icon: Icon(Icons.warehouse), label: Text('Inventory')),
  NavigationRailDestination(icon: Icon(Icons.people), label: Text('Customers')),
  NavigationRailDestination(icon: Icon(Icons.bar_chart), label: Text('Reports')),
  NavigationRailDestination(icon: Icon(Icons.settings), label: Text('Settings')),
];

const _routes = [
  '/dashboard',
  '/products',
  '/sales',
  '/inventory',
  '/customers',
  '/reports',
  '/settings',
];

int _getSelectedIndex(BuildContext context) {
  final location = GoRouterState.of(context).matchedLocation;
  for (var i = 0; i < _routes.length; i++) {
    if (location.startsWith(_routes[i])) return i;
  }
  return 0;
}

void _navigate(BuildContext context, int index) {
  if (index < _routes.length) {
    GoRouter.of(context).go(_routes[index]);
  }
}
