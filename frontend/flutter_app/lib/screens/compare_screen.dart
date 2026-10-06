import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../widgets/common.dart';

/// Runs the same query through all three retrievers side by side (retrieval only, so it is fast).
class CompareScreen extends StatefulWidget {
  const CompareScreen({super.key, required this.api, this.initialQuery});

  final LegalRagApi api;

  /// Compared automatically on first build (from a shared link).
  final String? initialQuery;

  @override
  State<CompareScreen> createState() => _CompareScreenState();
}

class _CompareScreenState extends State<CompareScreen> {
  late final _controller = TextEditingController(
    text:
        widget.initialQuery ??
        'Can a bank reject my loan application purely through an algorithm without any human involvement?',
  );
  Map<RetrievalMode, SearchResult>? _results;
  String? _error;
  bool _loading = false;

  @override
  void initState() {
    super.initState();
    if (widget.initialQuery != null) WidgetsBinding.instance.addPostFrameCallback((_) => _run());
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  Future<void> _run() async {
    final query = _controller.text.trim();
    if (query.length < 2 || _loading) return;
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final results = await Future.wait(RetrievalMode.values.map((m) => widget.api.search(query, m)));
      setState(() => _results = {for (final r in results) r.mode: r});
    } on ApiException catch (e) {
      setState(() => _error = e.message);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final results = _results;
    final wide = MediaQuery.sizeOf(context).width >= 1000;
    // Provisions found by every retriever are shown plainly; the rest are highlighted.
    final common = results == null
        ? <String>{}
        : results.values.map((r) => r.sources.map((s) => s.citation).toSet()).reduce((a, b) => a.intersection(b));
    final columns = [
      for (final mode in RetrievalMode.values)
        if (results?[mode] != null) _ModeColumn(result: results![mode]!, common: common),
    ];
    return PageFrame(
      title: 'Compare retrievers',
      subtitle: 'See which provisions each strategy retrieves for the same question. No LLM call is needed.',
      children: [
        TextField(
          controller: _controller,
          onSubmitted: (_) => _run(),
          decoration: InputDecoration(
            border: const OutlineInputBorder(),
            hintText: 'Enter a legal question',
            suffixIcon: IconButton(icon: const Icon(Icons.compare_arrows), onPressed: _loading ? null : _run),
          ),
        ),
        const SizedBox(height: 16),
        if (_loading) const LinearProgressIndicator(),
        if (_error != null) ErrorBanner(message: _error!, onRetry: _run),
        if (columns.isNotEmpty)
          wide
              ? Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    for (final c in columns) ...[Expanded(child: c), if (c != columns.last) const SizedBox(width: 16)],
                  ],
                )
              : Column(
                  children: [for (final c in columns) Padding(padding: const EdgeInsets.only(bottom: 16), child: c)],
                ),
      ],
    );
  }
}

class _ModeColumn extends StatelessWidget {
  const _ModeColumn({required this.result, required this.common});

  final SearchResult result;
  final Set<String> common;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(result.mode.label, style: theme.textTheme.titleMedium),
            Text(
              '${formatMs(result.timingsMs['total'])} · ${result.mode.description}',
              style: theme.textTheme.bodySmall,
            ),
            const Divider(height: 24),
            for (final s in result.sources)
              ListTile(
                dense: true,
                contentPadding: EdgeInsets.zero,
                leading: Text('#${s.marker}', style: theme.textTheme.labelLarge),
                title: Text(
                  s.citation,
                  style: TextStyle(
                    fontWeight: common.contains(s.citation) ? FontWeight.normal : FontWeight.bold,
                    color: common.contains(s.citation) ? null : theme.colorScheme.primary,
                  ),
                ),
                subtitle: Text(s.sectionTitle, maxLines: 1, overflow: TextOverflow.ellipsis),
                trailing: Text(s.score.toStringAsFixed(3), style: theme.textTheme.bodySmall),
              ),
          ],
        ),
      ),
    );
  }
}
