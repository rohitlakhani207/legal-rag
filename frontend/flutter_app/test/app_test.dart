import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:legal_rag/api/api_client.dart';
import 'package:legal_rag/api/models.dart';
import 'package:legal_rag/app.dart';
import 'package:legal_rag/deep_link.dart';
import 'package:legal_rag/widgets/answer_text.dart';

Source _source(int marker, String citation) => Source(
      marker: marker,
      chunkId: marker,
      documentId: 'gdpr',
      docShortName: 'GDPR',
      sectionId: citation.replaceFirst('GDPR ', ''),
      sectionTitle: 'Title of $citation',
      hierarchy: 'Chapter IV',
      citation: citation,
      content: 'Full text of $citation.',
      score: 0.9,
      vectorRank: marker,
    );

class FakeApi implements LegalRagApi {
  final asked = <(String, RetrievalMode)>[];

  @override
  Future<AskResult> ask(String question, RetrievalMode mode, {int topK = 5}) async {
    asked.add((question, mode));
    return AskResult(
      question: question,
      mode: mode,
      model: 'qwen3.5:4b',
      answer: 'Notify within **72 hours** under GDPR Article 33 [1]. The processor informs the controller [2].',
      abstained: false,
      citedMarkers: {1, 2},
      sources: [_source(1, 'GDPR Article 33'), _source(2, 'GDPR Article 34')],
      timingsMs: {'retrieval_total': 120, 'generation': 9000, 'total': 9120},
    );
  }

  @override
  Future<SearchResult> search(String query, RetrievalMode mode, {int topK = 5}) async => SearchResult(
        mode: mode,
        sources: [_source(1, 'GDPR Article 33'), if (mode == RetrievalMode.vector) _source(2, 'GDPR Article 4')],
        timingsMs: {'total': 42},
      );

  @override
  Future<List<DocumentInfo>> documents() async =>
      [DocumentInfo(id: 'gdpr', title: 'GDPR', shortName: 'GDPR', sections: 99, chunks: 202, jurisdiction: 'EU')];

  @override
  Future<EvalReport> latestEvaluation() async => EvalReport.fromJson({
        'run_id': 'test-run',
        'config': {'top_k': 5, 'n_questions': 1, 'hardware': {'cpus': 8, 'memory_gb': 16}},
        'summary': {
          'vector': {'retrieval_recall': 0.9, 'citation_accuracy': 0.7, 'faithfulness': 0.8, 'avg_latency_s': 20.0},
          'hybrid_rerank': {'retrieval_recall': 0.98, 'citation_accuracy': 0.8, 'faithfulness': 0.9, 'avg_latency_s': 25.0},
        },
        'records': [
          {'mode': 'hybrid_rerank', 'id': 'gdpr-01', 'type': 'specific', 'question': 'Breach deadline?',
           'gold': ['gdpr:Article 33'], 'retrieved': ['GDPR Article 33'], 'recall': 1.0},
        ],
      });

  @override
  Future<HealthStatus> health() async => HealthStatus(
        ok: true,
        database: true,
        ollama: true,
        chunks: 273,
        models: {'generator': 'qwen3.5:4b'},
      );
}

Future<void> _pumpApp(WidgetTester tester, LegalRagApi api, {DeepLink link = const DeepLink()}) async {
  tester.view.physicalSize = const Size(1400, 1000);
  tester.view.devicePixelRatio = 1.0;
  addTearDown(tester.view.reset);
  await tester.pumpWidget(LegalRagApp(api: api, link: link));
  await tester.pumpAndSettle();
}

void main() {
  test('DeepLink parses tab, question and mode, ignoring junk', () {
    final link = DeepLink.fromUri(Uri.parse('http://x/?tab=compare&q=%20Breach%3F%20&mode=hybrid'));
    expect(link.tab, 1);
    expect(link.question, 'Breach?');
    expect(link.mode, RetrievalMode.hybrid);
    final junk = DeepLink.fromUri(Uri.parse('http://x/?tab=nope&mode=bm25&q='));
    expect((junk.tab, junk.question, junk.mode), (0, null, null));
  });

  testWidgets('a shared link asks its question on start-up', (tester) async {
    final api = FakeApi();
    await _pumpApp(tester, api, link: const DeepLink(question: 'Breach deadline?', mode: RetrievalMode.vector));

    expect(api.asked.single, ('Breach deadline?', RetrievalMode.vector));
    expect(find.text('Sources (2)'), findsOneWidget);
  });

  test('parseAnswer splits prose and citation groups', () {
    final segments = parseAnswer('A [1]. B [2, 3]. C [4-6].');
    expect(segments.where((s) => s.isCitation).map((s) => s.markers).toList(), [
      [1],
      [2, 3],
      [4, 5, 6],
    ]);
    expect(segments.first.text, 'A ');
  });

  test('HttpLegalRagApi posts the API mode value and surfaces errors', () async {
    late Map<String, dynamic> sent;
    final client = MockClient((request) async {
      sent = jsonDecode(request.body) as Map<String, dynamic>;
      if (request.url.path.endsWith('/search')) {
        return http.Response(jsonEncode({'query': 'q', 'mode': 'hybrid', 'sources': [], 'timings_ms': {'total': 1}}), 200);
      }
      return http.Response(jsonEncode({'detail': 'Local LLM unavailable'}), 503);
    });
    final api = HttpLegalRagApi(baseUrl: 'http://api/', client: client);
    final result = await api.search('q', RetrievalMode.hybrid);
    expect(sent['mode'], 'hybrid');
    expect(result.mode, RetrievalMode.hybrid);
    await expectLater(
      api.ask('q', RetrievalMode.hybridRerank),
      throwsA(isA<ApiException>().having((e) => e.message, 'message', 'Local LLM unavailable')),
    );
  });

  testWidgets('asking a question shows the answer, citations and sources', (tester) async {
    final api = FakeApi();
    await _pumpApp(tester, api);

    await tester.enterText(find.byType(TextField).first, 'When must a breach be reported?');
    await tester.tap(find.byTooltip('Ask'));
    await tester.pumpAndSettle();

    expect(api.asked.single, ('When must a breach be reported?', RetrievalMode.hybridRerank));
    expect(find.textContaining('Notify within 72 hours under', findRichText: true), findsOneWidget);
    expect(find.textContaining('**', findRichText: true), findsNothing);
    expect(find.text('GDPR Article 33'), findsOneWidget);
    expect(find.text('Sources (2)'), findsOneWidget);
    expect(find.text('cited'), findsNWidgets(2));
  });

  testWidgets('pages start at the top in the wide layout', (tester) async {
    await _pumpApp(tester, FakeApi());
    expect(tester.getTopLeft(find.text('Ask the law')).dy, lessThan(60));
  });

  testWidgets('mode selector changes the retrieval mode sent to the API', (tester) async {
    final api = FakeApi();
    await _pumpApp(tester, api);

    await tester.tap(find.text('Vector').first);
    await tester.pumpAndSettle();
    await tester.tap(find.text(exampleQuestionsLabel).first);
    await tester.pumpAndSettle();

    expect(api.asked.single.$2, RetrievalMode.vector);
  });

  testWidgets('evaluation tab renders the metrics table', (tester) async {
    await _pumpApp(tester, FakeApi());
    await tester.tap(find.text('Evaluation'));
    await tester.pumpAndSettle();

    expect(find.text('Retrieval Recall@5'), findsOneWidget);
    expect(find.text('98.0%'), findsOneWidget);
    expect(find.text('Breach deadline?'), findsOneWidget);
  });

  testWidgets('compare tab highlights provisions unique to one retriever', (tester) async {
    await _pumpApp(tester, FakeApi());
    await tester.tap(find.text('Compare'));
    await tester.pumpAndSettle();
    await tester.tap(find.byIcon(Icons.compare_arrows).last);
    await tester.pumpAndSettle();

    expect(find.text('GDPR Article 33'), findsNWidgets(3));
    expect(find.text('GDPR Article 4'), findsOneWidget);
  });
}

const exampleQuestionsLabel = 'Within how many hours must a controller notify a personal data breach?';
