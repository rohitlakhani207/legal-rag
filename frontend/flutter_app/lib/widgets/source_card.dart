import 'package:flutter/material.dart';

import '../api/models.dart';

class SourceCard extends StatelessWidget {
  const SourceCard({
    super.key,
    required this.source,
    this.cited = false,
    this.highlighted = false,
    this.initiallyExpanded = false,
  });

  final Source source;
  final bool cited;
  final bool highlighted;
  final bool initiallyExpanded;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final scheme = theme.colorScheme;
    final signals = <String>[
      if (source.vectorRank != null) 'vector #${source.vectorRank}',
      if (source.fulltextRank != null) 'full-text #${source.fulltextRank}',
      if (source.rerankScore != null) 'rerank ${source.rerankScore!.toStringAsFixed(2)}',
    ];
    return AnimatedContainer(
      duration: const Duration(milliseconds: 300),
      decoration: BoxDecoration(
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: highlighted ? scheme.primary : scheme.outlineVariant, width: highlighted ? 2 : 1),
      ),
      child: Theme(
        data: theme.copyWith(dividerColor: Colors.transparent),
        child: ExpansionTile(
          key: PageStorageKey('source-${source.chunkId}-$highlighted'),
          initiallyExpanded: initiallyExpanded || highlighted,
          shape: const RoundedRectangleBorder(),
          leading: CircleAvatar(
            radius: 14,
            backgroundColor: cited ? scheme.primary : scheme.surfaceContainerHighest,
            foregroundColor: cited ? scheme.onPrimary : scheme.onSurfaceVariant,
            child: Text('${source.marker}', style: const TextStyle(fontSize: 13)),
          ),
          title: Text(source.citation, style: theme.textTheme.titleSmall),
          subtitle: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              if (source.sectionTitle.isNotEmpty)
                Text(source.sectionTitle, maxLines: 2, overflow: TextOverflow.ellipsis),
              const SizedBox(height: 4),
              Wrap(
                spacing: 6,
                runSpacing: 4,
                children: [
                  if (cited) _Tag(label: 'cited', color: scheme.primary),
                  for (final s in signals) _Tag(label: s, color: scheme.outline),
                ],
              ),
            ],
          ),
          childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
          expandedCrossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (source.hierarchy.isNotEmpty)
              Padding(
                padding: const EdgeInsets.only(bottom: 8),
                child: Text(
                  source.hierarchy,
                  style: theme.textTheme.labelMedium?.copyWith(color: scheme.onSurfaceVariant),
                ),
              ),
            SelectableText(source.content, style: theme.textTheme.bodyMedium?.copyWith(height: 1.5)),
          ],
        ),
      ),
    );
  }
}

class _Tag extends StatelessWidget {
  const _Tag({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
    decoration: BoxDecoration(
      border: Border.all(color: color),
      borderRadius: BorderRadius.circular(4),
    ),
    child: Text(label, style: TextStyle(fontSize: 11, color: color)),
  );
}
