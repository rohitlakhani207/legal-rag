import 'api/models.dart';

/// Start-up state read from the URL, so questions can be shared as links:
/// `/?q=When+must+a+breach+be+reported%3F&mode=hybrid` or `/?tab=evaluation`.
class DeepLink {
  const DeepLink({this.tab = 0, this.question, this.mode});

  factory DeepLink.fromUri(Uri uri) {
    final params = uri.queryParameters;
    final question = params['q']?.trim();
    final modeValue = params['mode'];
    return DeepLink(
      tab: tabs.indexOf(params['tab'] ?? '').clamp(0, tabs.length - 1),
      question: question == null || question.isEmpty ? null : question,
      mode: modeValue == null ? null : RetrievalMode.values.where((m) => m.apiValue == modeValue).firstOrNull,
    );
  }

  static const tabs = ['ask', 'compare', 'evaluation', 'corpus'];

  final int tab;
  final String? question;
  final RetrievalMode? mode;
}
