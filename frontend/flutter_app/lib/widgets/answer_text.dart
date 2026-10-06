import 'package:flutter/material.dart';

final _citationPattern = RegExp(r'\[(?:sources?\s*)?(\d+(?:\s*[,;–-]\s*\d+)*)\]', caseSensitive: false);

/// A piece of answer text: either plain prose or a group of citation markers.
class AnswerSegment {
  const AnswerSegment.text(this.text) : markers = const [];
  const AnswerSegment.citation(this.markers) : text = '';

  final String text;
  final List<int> markers;

  bool get isCitation => markers.isNotEmpty;
}

List<int> _expand(String group) {
  final out = <int>[];
  for (final part in group.split(RegExp(r'\s*[,;]\s*'))) {
    final range = part.split(RegExp(r'\s*[–-]\s*'));
    if (range.length == 2) {
      final lo = int.parse(range[0]);
      final hi = int.parse(range[1]);
      if (hi > lo && hi - lo < 20) {
        for (var i = lo; i <= hi; i++) {
          out.add(i);
        }
        continue;
      }
    }
    out.addAll(range.map(int.parse));
  }
  return out;
}

List<AnswerSegment> parseAnswer(String answer) {
  final segments = <AnswerSegment>[];
  var last = 0;
  for (final match in _citationPattern.allMatches(answer)) {
    if (match.start > last) segments.add(AnswerSegment.text(answer.substring(last, match.start)));
    segments.add(AnswerSegment.citation(_expand(match.group(1)!)));
    last = match.end;
  }
  if (last < answer.length) segments.add(AnswerSegment.text(answer.substring(last)));
  return segments;
}

final _bold = RegExp(r'\*\*(.+?)\*\*');

/// Small models sometimes emit **bold** despite the prompt; render it instead of showing asterisks.
List<TextSpan> _prose(String text) {
  final spans = <TextSpan>[];
  var last = 0;
  for (final match in _bold.allMatches(text)) {
    if (match.start > last) spans.add(TextSpan(text: text.substring(last, match.start)));
    spans.add(
      TextSpan(
        text: match.group(1),
        style: const TextStyle(fontWeight: FontWeight.bold),
      ),
    );
    last = match.end;
  }
  if (last < text.length) spans.add(TextSpan(text: text.substring(last)));
  return spans;
}

/// Renders an answer with its [n] markers turned into tappable chips.
class AnswerText extends StatelessWidget {
  const AnswerText({super.key, required this.answer, required this.onCitationTap, this.validMarkers = const {}});

  final String answer;
  final ValueChanged<int> onCitationTap;
  final Set<int> validMarkers;

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final style = theme.textTheme.bodyLarge?.copyWith(height: 1.6);
    return SelectableText.rich(
      TextSpan(
        style: style,
        children: [
          for (final segment in parseAnswer(answer))
            if (!segment.isCitation)
              ..._prose(segment.text)
            else
              for (final marker in segment.markers)
                WidgetSpan(
                  alignment: PlaceholderAlignment.middle,
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 2),
                    child: _CitationChip(
                      marker: marker,
                      valid: validMarkers.isEmpty || validMarkers.contains(marker),
                      onTap: () => onCitationTap(marker),
                    ),
                  ),
                ),
        ],
      ),
    );
  }
}

class _CitationChip extends StatelessWidget {
  const _CitationChip({required this.marker, required this.valid, required this.onTap});

  final int marker;
  final bool valid;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    final scheme = Theme.of(context).colorScheme;
    final background = valid ? scheme.primaryContainer : scheme.errorContainer;
    final foreground = valid ? scheme.onPrimaryContainer : scheme.onErrorContainer;
    return Tooltip(
      message: valid ? 'Show source $marker' : 'Source $marker was not provided to the model',
      child: InkWell(
        onTap: valid ? onTap : null,
        borderRadius: BorderRadius.circular(6),
        child: Container(
          padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 1),
          decoration: BoxDecoration(color: background, borderRadius: BorderRadius.circular(6)),
          child: Text(
            '$marker',
            style: TextStyle(color: foreground, fontSize: 12, fontWeight: FontWeight.w600),
          ),
        ),
      ),
    );
  }
}
