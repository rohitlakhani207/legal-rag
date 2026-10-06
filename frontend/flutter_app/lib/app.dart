import 'package:flutter/material.dart';

import 'api/api_client.dart';
import 'deep_link.dart';
import 'screens/ask_screen.dart';
import 'screens/compare_screen.dart';
import 'screens/corpus_screen.dart';
import 'screens/evaluation_screen.dart';

class LegalRagApp extends StatelessWidget {
  const LegalRagApp({super.key, required this.api, this.link = const DeepLink()});

  final LegalRagApi api;
  final DeepLink link;

  ThemeData _theme(Brightness brightness) => ThemeData(
    colorScheme: ColorScheme.fromSeed(seedColor: const Color(0xFF2F4B7C), brightness: brightness),
    useMaterial3: true,
    cardTheme: const CardThemeData(margin: EdgeInsets.zero),
  );

  @override
  Widget build(BuildContext context) => MaterialApp(
    title: 'Legal RAG',
    debugShowCheckedModeBanner: false,
    theme: _theme(Brightness.light),
    darkTheme: _theme(Brightness.dark),
    home: HomeShell(api: api, link: link),
  );
}

class _Destination {
  const _Destination(this.label, this.icon, this.selectedIcon);

  final String label;
  final IconData icon;
  final IconData selectedIcon;
}

const _destinations = [
  _Destination('Ask', Icons.gavel_outlined, Icons.gavel),
  _Destination('Compare', Icons.compare_arrows_outlined, Icons.compare_arrows),
  _Destination('Evaluation', Icons.insights_outlined, Icons.insights),
  _Destination('Corpus', Icons.library_books_outlined, Icons.library_books),
];

class HomeShell extends StatefulWidget {
  const HomeShell({super.key, required this.api, this.link = const DeepLink()});

  final LegalRagApi api;
  final DeepLink link;

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  late int _index = widget.link.tab;

  @override
  Widget build(BuildContext context) {
    final screens = [
      AskScreen(
        api: widget.api,
        initialQuestion: widget.link.tab == 0 ? widget.link.question : null,
        initialMode: widget.link.mode,
      ),
      CompareScreen(api: widget.api, initialQuery: widget.link.tab == 1 ? widget.link.question : null),
      EvaluationScreen(api: widget.api),
      CorpusScreen(api: widget.api),
    ];
    final body = IndexedStack(index: _index, children: screens);
    final wide = MediaQuery.sizeOf(context).width >= 840;

    if (wide) {
      return Scaffold(
        body: Row(
          // Stretch so each page fills the height; otherwise short pages are centred vertically.
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            NavigationRail(
              selectedIndex: _index,
              onDestinationSelected: (i) => setState(() => _index = i),
              labelType: NavigationRailLabelType.all,
              leading: const Padding(padding: EdgeInsets.symmetric(vertical: 16), child: Icon(Icons.balance, size: 32)),
              destinations: [
                for (final d in _destinations)
                  NavigationRailDestination(
                    icon: Icon(d.icon),
                    selectedIcon: Icon(d.selectedIcon),
                    label: Text(d.label),
                  ),
              ],
            ),
            const VerticalDivider(width: 1),
            Expanded(child: body),
          ],
        ),
      );
    }
    return Scaffold(
      body: SafeArea(child: body),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: (i) => setState(() => _index = i),
        destinations: [
          for (final d in _destinations)
            NavigationDestination(icon: Icon(d.icon), selectedIcon: Icon(d.selectedIcon), label: d.label),
        ],
      ),
    );
  }
}
