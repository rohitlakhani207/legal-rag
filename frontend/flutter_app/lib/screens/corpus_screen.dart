import 'package:flutter/material.dart';

import '../api/api_client.dart';
import '../api/models.dart';
import '../widgets/common.dart';

class CorpusScreen extends StatefulWidget {
  const CorpusScreen({super.key, required this.api});

  final LegalRagApi api;

  @override
  State<CorpusScreen> createState() => _CorpusScreenState();
}

class _CorpusScreenState extends State<CorpusScreen> {
  late Future<(HealthStatus, List<DocumentInfo>)> _data = _load();

  Future<(HealthStatus, List<DocumentInfo>)> _load() async => (await widget.api.health(), await widget.api.documents());

  void _reload() => setState(() => _data = _load());

  @override
  Widget build(BuildContext context) => FutureBuilder<(HealthStatus, List<DocumentInfo>)>(
    future: _data,
    builder: (context, snapshot) {
      final children = <Widget>[];
      if (snapshot.connectionState != ConnectionState.done) {
        children.add(const LinearProgressIndicator());
      } else if (snapshot.hasError) {
        children.add(ErrorBanner(message: '${snapshot.error}', onRetry: _reload));
      } else {
        final (health, documents) = snapshot.data!;
        children.addAll([
          _HealthCard(health: health, onRefresh: _reload),
          const SizedBox(height: 24),
          Text('Indexed documents', style: Theme.of(context).textTheme.titleLarge),
          const SizedBox(height: 8),
          for (final d in documents)
            Card(
              margin: const EdgeInsets.only(bottom: 8),
              child: ListTile(
                leading: CircleAvatar(child: Text(d.jurisdiction ?? '?')),
                title: Text(d.title),
                subtitle: Text(
                  '${d.shortName} · ${d.sections} provisions · ${d.chunks} chunks'
                  '${d.sourceUrl == null ? '' : '\n${d.sourceUrl}'}',
                ),
                isThreeLine: d.sourceUrl != null,
              ),
            ),
          const SizedBox(height: 16),
          Text(
            'Add your own documents (PDF, HTML, TXT, MD) with POST /documents. See the README for the curl example.',
            style: Theme.of(context).textTheme.bodySmall,
          ),
        ]);
      }
      return PageFrame(
        title: 'Corpus & system',
        subtitle: 'What the assistant can cite, and which local models are serving it.',
        children: children,
      );
    },
  );
}

class _HealthCard extends StatelessWidget {
  const _HealthCard({required this.health, required this.onRefresh});

  final HealthStatus health;
  final VoidCallback onRefresh;

  @override
  Widget build(BuildContext context) {
    Widget status(String label, bool ok) => Chip(
      avatar: Icon(ok ? Icons.check_circle : Icons.error, color: ok ? Colors.green : Colors.red, size: 18),
      label: Text(label),
    );
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Expanded(child: Text('System status', style: Theme.of(context).textTheme.titleMedium)),
                IconButton(onPressed: onRefresh, icon: const Icon(Icons.refresh), tooltip: 'Refresh'),
              ],
            ),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: [
                status('PostgreSQL + pgvector (${health.chunks} chunks)', health.database),
                status('Ollama', health.ollama),
                for (final e in health.models.entries) Chip(label: Text('${e.key}: ${e.value}')),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
