import 'package:flutter/material.dart';

import '../api/models.dart';

String formatPercent(double? value) => value == null ? '—' : '${(value * 100).toStringAsFixed(1)}%';

String formatSeconds(double? seconds) => seconds == null ? '—' : '${seconds.toStringAsFixed(1)} s';

String formatMs(double? ms) {
  if (ms == null) return '—';
  return ms >= 1000 ? '${(ms / 1000).toStringAsFixed(1)} s' : '${ms.round()} ms';
}

/// Page scaffold with a max content width so wide screens stay readable.
class PageFrame extends StatelessWidget {
  const PageFrame({
    super.key,
    required this.title,
    required this.subtitle,
    required this.children,
    this.maxWidth = 1200,
  });

  final String title;
  final String subtitle;
  final List<Widget> children;
  final double maxWidth;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 24),
      child: Center(
        child: ConstrainedBox(
          constraints: BoxConstraints(maxWidth: maxWidth),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              Text(title, style: theme.textTheme.headlineMedium),
              const SizedBox(height: 4),
              Text(subtitle, style: theme.textTheme.bodyLarge?.copyWith(color: theme.colorScheme.onSurfaceVariant)),
              const SizedBox(height: 24),
              ...children,
            ],
          ),
        ),
      ),
    );
  }
}

class ErrorBanner extends StatelessWidget {
  const ErrorBanner({super.key, required this.message, this.onRetry});

  final String message;
  final VoidCallback? onRetry;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    return Card(
      color: scheme.errorContainer,
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Row(
          children: [
            Icon(Icons.error_outline, color: scheme.onErrorContainer),
            const SizedBox(width: 12),
            Expanded(
              child: SelectableText(message, style: TextStyle(color: scheme.onErrorContainer)),
            ),
            if (onRetry != null) TextButton(onPressed: onRetry, child: const Text('Retry')),
          ],
        ),
      ),
    );
  }
}

class ModeSelector extends StatelessWidget {
  const ModeSelector({super.key, required this.value, required this.onChanged, this.enabled = true});

  final RetrievalMode value;
  final ValueChanged<RetrievalMode> onChanged;
  final bool enabled;

  @override
  Widget build(BuildContext context) => SegmentedButton<RetrievalMode>(
    segments: [
      for (final m in RetrievalMode.values) ButtonSegment(value: m, label: Text(m.label), tooltip: m.description),
    ],
    selected: {value},
    showSelectedIcon: false,
    onSelectionChanged: enabled ? (s) => onChanged(s.first) : null,
  );
}
