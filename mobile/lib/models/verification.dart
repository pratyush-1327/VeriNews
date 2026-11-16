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
      title: json['title']?.toString() ?? 'Evidence Document',
      url: json['url']?.toString() ?? '',
      snippet: json['snippet']?.toString() ?? '',
      sourceName: json['source_name']?.toString() ??
          json['publisher']?.toString() ??
          'Verified Publisher',
      credibilityScore: (json['credibility_score'] as num?)?.toDouble() ?? 0.85,
    );
  }
}

class VerificationResponse {
  final String id;
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
      id: json['id']?.toString() ?? '',
      claimText: json['claim_text']?.toString() ?? '',
      claimHash: json['claim_hash']?.toString() ?? '',
      verdict: (json['verdict']?.toString() ?? 'UNVERIFIED').toUpperCase(),
      truthScore: (json['truth_score'] as num?)?.toInt() ?? 50,
      explanationBullets: (json['explanation_bullets'] as List<dynamic>? ?? [])
          .map((e) => e.toString())
          .toList(),
      evidenceSources: (json['evidence_sources'] as List<dynamic>? ?? [])
          .map((e) => EvidenceSource.fromJson(e as Map<String, dynamic>))
          .toList(),
      debunkCardUrl: json['debunk_card_url']?.toString(),
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
