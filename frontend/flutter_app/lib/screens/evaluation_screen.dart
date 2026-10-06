import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../widgets/common.dart';

class EvaluationScreen extends StatefulWidget {
  const EvaluationScreen({super.key, required this.api});

  final LegalRagApi api;

  @override
  State<EvaluationScreen> createState() => _EvaluationScreenState();
}

class _EvaluationScreenState extends State<EvaluationScreen> {
  late Future<EvalReport> _report = widget.api.latestEvaluation();
  RetrievalMode _filter = RetrievalMode.hybridRerank;

  void _reload() => setState(() => _report = widget.api.latestEvaluation());

  @override
  Widget build(BuildContext context) => FutureBuilder<EvalReport>(
    future: _report,
    builder: (context, snapshot) {
      final children = <Widget>[];
      if (snapshot.connectionState != ConnectionState.done) {
        children.add(const LinearProgressIndicator());
      } else if (snapshot.hasError) {
        children.add(ErrorBanner(message: '${snapshot.error}', onRetry: _reload));
      } else {
        final report = snapshot.data!;
        children.addAll([
          _MetricsTable(report: report),
          const SizedBox(height: 12),
          _RunInfo(report: report),
          const SizedBox(height: 32),
          Row(
            children: [
              Expanded(child: Text('Per-question results', style: Theme.of(context).textTheme.titleLarge)),
              ModeSelector(value: _filter, onChanged: (m) => setState(() => _filter = m)),
            ],
          ),
          const SizedBox(height: 12),
          for (final r in report.records.where((r) => r.mode == _filter)) _RecordTile(record: r),
        ]);
      }
      return PageFrame(
        title: 'Evaluation',
        subtitle: 'Benchmark of the three retrieval strategies on a labelled question set (latest run).',
        children: children,
      );
    },
  );
}

class _MetricsTable extends StatelessWidget {
  const _MetricsTable({required this.report});

  final EvalReport report;

  @override
  Widget build(BuildContext context) {
    final best = <String, double>{};
    void track(String key, double? v, {bool lowerIsBetter = false}) {
      if (v == null) return;
      final current = best[key];
      if (current == null || (lowerIsBetter ? v < current : v > current)) best[key] = v;
    }

    for (final s in report.summaries) {
      track('recall', s.retrievalRecall);
      track('citation', s.citationAccuracy);
      track('faith', s.faithfulness);
      track('latency', s.avgLatencyS, lowerIsBetter: true);
    }
    Widget cell(String text, bool isBest) =>
        Text(text, style: TextStyle(fontWeight: isBest ? FontWeight.bold : FontWeight.normal));

    final k = report.config['top_k'];
    return Card(
      child: SingleChildScrollView(
        scrollDirection: Axis.horizontal,
        child: DataTable(
          columns: [
            const DataColumn(label: Text('Approach')),
            DataColumn(label: Text('Retrieval Recall@$k'), numeric: true),
            const DataColumn(label: Text('Citation Accuracy'), numeric: true),
            const DataColumn(label: Text('Faithfulness'), numeric: true),
            const DataColumn(label: Text('Avg. Latency'), numeric: true),
          ],
          rows: [
            for (final s in report.summaries)
              DataRow(
                cells: [
                  DataCell(Text(s.mode.label)),
                  DataCell(cell(formatPercent(s.retrievalRecall), s.retrievalRecall == best['recall'])),
                  DataCell(cell(formatPercent(s.citationAccuracy), s.citationAccuracy == best['citation'])),
                  DataCell(cell(formatPercent(s.faithfulness), s.faithfulness == best['faith'])),
                  DataCell(cell(formatSeconds(s.avgLatencyS), s.avgLatencyS == best['latency'])),
                ],
              ),
          ],
        ),
      ),
    );
  }
}

class _RunInfo extends StatelessWidget {
  const _RunInfo({required this.report});

  final EvalReport report;

  @override
  Widget build(BuildContext context) {
    final c = report.config;
    final hw = (c['hardware'] as Map<String, dynamic>?) ?? {};
    final items = {
      'Run': report.runId,
      'Questions': '${c['n_questions']}',
      'Generator': '${c['generator_model'] ?? '—'}',
      'Judge': '${c['judge_model'] ?? '—'}',
      'Embeddings': '${c['embedding_model']}',
      'Reranker': '${c['reranker_model']}',
      'Hardware': '${hw['cpus']} CPUs · ${hw['memory_gb']} GB RAM · no GPU',
    };
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [for (final e in items.entries) Chip(label: Text('${e.key}: ${e.value}'))],
    );
  }
}

class _RecordTile extends StatelessWidget {
  const _RecordTile({required this.record});

  final EvalRecord record;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final recall = record.recall;
    final ok = recall == null ? null : recall >= 1.0;
    return Card(
      margin: const EdgeInsets.only(bottom: 8),
      child: ExpansionTile(
        shape: const RoundedRectangleBorder(),
        leading: Icon(
          ok == null ? Icons.block : (ok ? Icons.check_circle : Icons.cancel),
          color: ok == null ? theme.colorScheme.outline : (ok ? Colors.green : theme.colorScheme.error),
        ),
        title: Text(record.question),
        subtitle: Text(
          '${record.id} · ${record.type} · recall ${formatPercent(recall)} · '
          'citation ${formatPercent(record.citationAccuracy)} · faithfulness ${formatPercent(record.faithfulness)} · '
          '${formatMs(record.latencyMs)}',
        ),
        childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
        expandedCrossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text('Gold: ${record.gold.isEmpty ? '(unanswerable)' : record.gold.join(', ')}'),
          Text('Retrieved: ${record.retrieved.join(', ')}'),
          if (record.answer != null) ...[
            const SizedBox(height: 8),
            SelectableText(record.answer!, style: theme.textTheme.bodyMedium),
          ],
        ],
      ),
    );
  }
}
