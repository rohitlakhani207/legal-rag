enum RetrievalMode {
  vector('vector', 'Vector', 'pgvector cosine similarity'),
  hybrid('hybrid', 'Hybrid', 'Vector + PostgreSQL full-text, fused with RRF'),
  hybridRerank('hybrid_rerank', 'Hybrid + Reranker', 'Hybrid candidates re-scored by a cross-encoder');

  const RetrievalMode(this.apiValue, this.label, this.description);

  final String apiValue;
  final String label;
  final String description;

  static RetrievalMode fromApi(String value) =>
      RetrievalMode.values.firstWhere((m) => m.apiValue == value, orElse: () => RetrievalMode.hybridRerank);
}

double _toDouble(Object? value) => (value as num?)?.toDouble() ?? 0;

class Source {
  Source({
    required this.marker,
    required this.chunkId,
    required this.documentId,
    required this.docShortName,
    required this.sectionId,
    required this.sectionTitle,
    required this.hierarchy,
    required this.citation,
    required this.content,
    required this.score,
    this.vectorRank,
    this.fulltextRank,
    this.rerankScore,
  });

  factory Source.fromJson(Map<String, dynamic> json) => Source(
    marker: json['marker'] as int,
    chunkId: json['chunk_id'] as int,
    documentId: json['document_id'] as String,
    docShortName: json['doc_short_name'] as String,
    sectionId: json['section_id'] as String,
    sectionTitle: json['section_title'] as String? ?? '',
    hierarchy: json['hierarchy'] as String? ?? '',
    citation: json['citation'] as String,
    content: json['content'] as String,
    score: _toDouble(json['score']),
    vectorRank: json['vector_rank'] as int?,
    fulltextRank: json['fulltext_rank'] as int?,
    rerankScore: (json['rerank_score'] as num?)?.toDouble(),
  );

  final int marker;
  final int chunkId;
  final String documentId;
  final String docShortName;
  final String sectionId;
  final String sectionTitle;
  final String hierarchy;
  final String citation;
  final String content;
  final double score;
  final int? vectorRank;
  final int? fulltextRank;
  final double? rerankScore;
}

class SearchResult {
  SearchResult({required this.mode, required this.sources, required this.timingsMs});

  factory SearchResult.fromJson(Map<String, dynamic> json) => SearchResult(
    mode: RetrievalMode.fromApi(json['mode'] as String),
    sources: (json['sources'] as List).map((s) => Source.fromJson(s as Map<String, dynamic>)).toList(),
    timingsMs: (json['timings_ms'] as Map<String, dynamic>).map((k, v) => MapEntry(k, _toDouble(v))),
  );

  final RetrievalMode mode;
  final List<Source> sources;
  final Map<String, double> timingsMs;
}

class AskResult {
  AskResult({
    required this.question,
    required this.mode,
    required this.model,
    required this.answer,
    required this.abstained,
    required this.citedMarkers,
    required this.sources,
    required this.timingsMs,
  });

  factory AskResult.fromJson(Map<String, dynamic> json) => AskResult(
    question: json['question'] as String,
    mode: RetrievalMode.fromApi(json['mode'] as String),
    model: json['model'] as String,
    answer: json['answer'] as String,
    abstained: json['abstained'] as bool,
    citedMarkers: (json['citations'] as List).map((c) => (c as Map<String, dynamic>)['marker'] as int).toSet(),
    sources: (json['sources'] as List).map((s) => Source.fromJson(s as Map<String, dynamic>)).toList(),
    timingsMs: (json['timings_ms'] as Map<String, dynamic>).map((k, v) => MapEntry(k, _toDouble(v))),
  );

  final String question;
  final RetrievalMode mode;
  final String model;
  final String answer;
  final bool abstained;
  final Set<int> citedMarkers;
  final List<Source> sources;
  final Map<String, double> timingsMs;
}

class DocumentInfo {
  DocumentInfo({
    required this.id,
    required this.title,
    required this.shortName,
    required this.sections,
    required this.chunks,
    this.jurisdiction,
    this.sourceUrl,
  });

  factory DocumentInfo.fromJson(Map<String, dynamic> json) => DocumentInfo(
    id: json['id'] as String,
    title: json['title'] as String,
    shortName: json['short_name'] as String,
    jurisdiction: json['jurisdiction'] as String?,
    sourceUrl: json['source_url'] as String?,
    sections: json['sections'] as int,
    chunks: json['chunks'] as int,
  );

  final String id;
  final String title;
  final String shortName;
  final String? jurisdiction;
  final String? sourceUrl;
  final int sections;
  final int chunks;
}

class ModeSummary {
  ModeSummary({
    required this.mode,
    required this.retrievalRecall,
    required this.mrr,
    required this.citationAccuracy,
    required this.faithfulness,
    required this.avgLatencyS,
    required this.avgRetrievalMs,
    required this.unanswerableAbstention,
  });

  factory ModeSummary.fromJson(String mode, Map<String, dynamic> json) => ModeSummary(
    mode: RetrievalMode.fromApi(mode),
    retrievalRecall: (json['retrieval_recall'] as num?)?.toDouble(),
    mrr: (json['mrr'] as num?)?.toDouble(),
    citationAccuracy: (json['citation_accuracy'] as num?)?.toDouble(),
    faithfulness: (json['faithfulness'] as num?)?.toDouble(),
    avgLatencyS: (json['avg_latency_s'] as num?)?.toDouble(),
    avgRetrievalMs: (json['avg_retrieval_ms'] as num?)?.toDouble(),
    unanswerableAbstention: (json['abstention_rate_unanswerable'] as num?)?.toDouble(),
  );

  final RetrievalMode mode;
  final double? retrievalRecall;
  final double? mrr;
  final double? citationAccuracy;
  final double? faithfulness;
  final double? avgLatencyS;
  final double? avgRetrievalMs;
  final double? unanswerableAbstention;
}

class EvalRecord {
  EvalRecord({
    required this.mode,
    required this.id,
    required this.type,
    required this.question,
    required this.gold,
    required this.retrieved,
    this.recall,
    this.citationAccuracy,
    this.faithfulness,
    this.latencyMs,
    this.answer,
  });

  factory EvalRecord.fromJson(Map<String, dynamic> json) => EvalRecord(
    mode: RetrievalMode.fromApi(json['mode'] as String),
    id: json['id'] as String,
    type: json['type'] as String? ?? '',
    question: json['question'] as String,
    gold: (json['gold'] as List? ?? []).cast<String>(),
    retrieved: (json['retrieved'] as List? ?? []).cast<String>(),
    recall: (json['recall'] as num?)?.toDouble(),
    citationAccuracy: (json['citation_accuracy'] as num?)?.toDouble(),
    faithfulness: (json['faithfulness'] as num?)?.toDouble(),
    latencyMs: (json['latency_ms'] as num?)?.toDouble(),
    answer: json['answer'] as String?,
  );

  final RetrievalMode mode;
  final String id;
  final String type;
  final String question;
  final List<String> gold;
  final List<String> retrieved;
  final double? recall;
  final double? citationAccuracy;
  final double? faithfulness;
  final double? latencyMs;
  final String? answer;
}

class EvalReport {
  EvalReport({required this.runId, required this.config, required this.summaries, required this.records});

  factory EvalReport.fromJson(Map<String, dynamic> json) {
    final summary = json['summary'] as Map<String, dynamic>;
    final order = RetrievalMode.values.map((m) => m.apiValue).toList();
    final modes = summary.keys.toList()..sort((a, b) => order.indexOf(a).compareTo(order.indexOf(b)));
    return EvalReport(
      runId: json['run_id'] as String,
      config: json['config'] as Map<String, dynamic>,
      summaries: [for (final m in modes) ModeSummary.fromJson(m, summary[m] as Map<String, dynamic>)],
      records: (json['records'] as List).map((r) => EvalRecord.fromJson(r as Map<String, dynamic>)).toList(),
    );
  }

  final String runId;
  final Map<String, dynamic> config;
  final List<ModeSummary> summaries;
  final List<EvalRecord> records;
}

class HealthStatus {
  HealthStatus({
    required this.ok,
    required this.database,
    required this.ollama,
    required this.chunks,
    required this.models,
  });

  factory HealthStatus.fromJson(Map<String, dynamic> json) => HealthStatus(
    ok: json['status'] == 'ok',
    database: json['database'] as bool? ?? false,
    ollama: json['ollama'] as bool? ?? false,
    chunks: json['chunks'] as int? ?? 0,
    models: (json['models'] as Map<String, dynamic>? ?? {}).map((k, v) => MapEntry(k, '$v')),
  );

  final bool ok;
  final bool database;
  final bool ollama;
  final int chunks;
  final Map<String, String> models;
}
