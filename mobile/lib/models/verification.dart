class EvidenceSource {
  final String title;
  final String url;
  final String snippet;
  final String sourceName;
  final double credibilityScore;

  const EvidenceSource({
    required this.title,
    required this.url,
    required this.snippet,
    required this.sourceName,
    required this.credibilityScore,
  });

  factory EvidenceSource.fromJson(Map<String, dynamic> json) {
    return EvidenceSource(
      title: json['title'] as String? ?? 'Evidence Document',
      url: json['url'] as String? ?? '',
      snippet: json['snippet'] as String? ?? '',
      sourceName: json['source_name'] as String? ?? 'Verified Publisher',
      credibilityScore: (json['credibility_score'] as num?)?.toDouble() ?? 0.85,
    );
  }
}

class VerificationResponse {
  final int id;
  final String claimText;
  final String claimHash;
  final String verdict;
  final int truthScore;
  final List<String> explanationBullets;
  final List<EvidenceSource> evidenceSources;
  final String? debunkCardUrl;
  final DateTime createdAt;
  final bool cached;

  const VerificationResponse({
    required this.id,
    required this.claimText,
    required this.claimHash,
    required this.verdict,
    required this.truthScore,
    required this.explanationBullets,
    required this.evidenceSources,
    this.debunkCardUrl,
    required this.createdAt,
    required this.cached,
  });

  factory VerificationResponse.fromJson(Map<String, dynamic> json) {
    return VerificationResponse(
      id: json['id'] as int? ?? 0,
      claimText: json['claim_text'] as String? ?? '',
      claimHash: json['claim_hash'] as String? ?? '',
      verdict: (json['verdict'] as String? ?? 'UNVERIFIED').toUpperCase(),
      truthScore: (json['truth_score'] as num?)?.toInt() ?? 50,
      explanationBullets: (json['explanation_bullets'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      evidenceSources: (json['evidence_sources'] as List<dynamic>? ?? [])
          .map((e) => EvidenceSource.fromJson(e as Map<String, dynamic>))
          .toList(),
      debunkCardUrl: json['debunk_card_url'] as String?,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      cached: json['cached'] as bool? ?? false,
    );
  }

  /// Color / label helper for UI
  String get verdictDisplay {
    switch (verdict.toUpperCase()) {
      case 'TRUE':
        return 'VERIFIED TRUE';
      case 'MISLEADING':
        return 'MISLEADING';
      case 'FAKE':
        return 'DEBUNKED FAKE';
      case 'SATIRE':
        return 'SATIRE / HUMOR';
      case 'UNVERIFIED':
      default:
        return 'UNVERIFIED';
    }
  }
}
