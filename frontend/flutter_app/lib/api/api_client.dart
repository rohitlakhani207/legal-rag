import 'dart:convert';

import 'package:http/http.dart' as http;

import 'models.dart';

/// Base URL of the FastAPI backend. The Docker web image serves the app behind nginx,
/// which proxies `/api` to the backend, so the default works without CORS.
/// Override with `--dart-define=API_BASE_URL=http://localhost:8000` for `flutter run`.
const String kApiBaseUrl = String.fromEnvironment('API_BASE_URL', defaultValue: '/api');

class ApiException implements Exception {
  ApiException(this.message, {this.statusCode});

  final String message;
  final int? statusCode;

  @override
  String toString() => message;
}

/// Interface so widgets can be tested with a fake backend.
abstract class LegalRagApi {
  Future<AskResult> ask(String question, RetrievalMode mode, {int topK = 5});
  Future<SearchResult> search(String query, RetrievalMode mode, {int topK = 5});
  Future<List<DocumentInfo>> documents();
  Future<EvalReport> latestEvaluation();
  Future<HealthStatus> health();
}

class HttpLegalRagApi implements LegalRagApi {
  HttpLegalRagApi({String baseUrl = kApiBaseUrl, http.Client? client})
    : _base = baseUrl.endsWith('/') ? baseUrl.substring(0, baseUrl.length - 1) : baseUrl,
      _client = client ?? http.Client();

  final String _base;
  final http.Client _client;

  Uri _uri(String path) => Uri.parse('$_base$path');

  Future<dynamic> _send(Future<http.Response> request) async {
    final http.Response response;
    try {
      // Local CPU inference can take a minute or more for long answers.
      response = await request.timeout(const Duration(minutes: 5));
    } on Exception catch (e) {
      throw ApiException('Cannot reach the API at $_base ($e)');
    }
    final body = utf8.decode(response.bodyBytes);
    if (response.statusCode >= 400) {
      String detail = body;
      try {
        detail = '${(jsonDecode(body) as Map<String, dynamic>)['detail']}';
      } on FormatException {
        // keep raw body
      }
      throw ApiException(detail, statusCode: response.statusCode);
    }
    return jsonDecode(body);
  }

  Future<dynamic> _post(String path, Map<String, dynamic> payload) =>
      _send(_client.post(_uri(path), headers: {'Content-Type': 'application/json'}, body: jsonEncode(payload)));

  @override
  Future<AskResult> ask(String question, RetrievalMode mode, {int topK = 5}) async => AskResult.fromJson(
    await _post('/ask', {'question': question, 'mode': mode.apiValue, 'top_k': topK}) as Map<String, dynamic>,
  );

  @override
  Future<SearchResult> search(String query, RetrievalMode mode, {int topK = 5}) async => SearchResult.fromJson(
    await _post('/search', {'query': query, 'mode': mode.apiValue, 'top_k': topK}) as Map<String, dynamic>,
  );

  @override
  Future<List<DocumentInfo>> documents() async => ((await _send(_client.get(_uri('/documents')))) as List)
      .map((d) => DocumentInfo.fromJson(d as Map<String, dynamic>))
      .toList();

  @override
  Future<EvalReport> latestEvaluation() async =>
      EvalReport.fromJson(await _send(_client.get(_uri('/evaluation/latest'))) as Map<String, dynamic>);

  @override
  Future<HealthStatus> health() async =>
      HealthStatus.fromJson(await _send(_client.get(_uri('/health'))) as Map<String, dynamic>);
}
