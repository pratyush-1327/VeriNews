class Article {
  final int id;
  final String title;
  final String summary60Words;
  final String url;
  final String? imageUrl;
  final DateTime publishedAt;
  final String scope;
  final String? cityTag;
  final int sourceId;
  final String sourceName;
  final DateTime createdAt;

  const Article({
    required this.id,
    required this.title,
    required this.summary60Words,
    required this.url,
    this.imageUrl,
    required this.publishedAt,
    required this.scope,
    this.cityTag,
    required this.sourceId,
    required this.sourceName,
    required this.createdAt,
  });

  /// Parse the 3 bullet points from summary_60_words
  List<String> get bullets {
    final lines = summary60Words
        .split('\n')
        .map((line) => line.trim())
        .where((line) => line.isNotEmpty)
        .toList();

    final cleanBullets = <String>[];
    for (var line in lines) {
      // Strip leading bullet markers like •, -, *, 1., 2.
      line = line.replaceFirst(RegExp(r'^[\s\-\*\•\d\.\)]+\s*'), '').trim();
      if (line.isNotEmpty) {
        cleanBullets.add(line);
      }
    }

    if (cleanBullets.isEmpty) {
      return [summary60Words];
    }
    return cleanBullets;
  }

  /// Relative time formatting helper
  String get timeAgo {
    final now = DateTime.now();
    final difference = now.difference(publishedAt);

    if (difference.inSeconds < 60) {
      return 'Just now';
    } else if (difference.inMinutes < 60) {
      return '${difference.inMinutes}m ago';
    } else if (difference.inHours < 24) {
      return '${difference.inHours}h ago';
    } else if (difference.inDays < 7) {
      return '${difference.inDays}d ago';
    } else {
      return '${(difference.inDays / 7).floor()}w ago';
    }
  }

  factory Article.fromJson(Map<String, dynamic> json) {
    return Article(
      id: json['id'] as int? ?? 0,
      title: json['title'] as String? ?? 'Untitled Article',
      summary60Words: json['summary_60_words'] as String? ?? '',
      url: json['url'] as String? ?? '',
      imageUrl: json['image_url'] as String?,
      publishedAt: json['published_at'] != null
          ? DateTime.tryParse(json['published_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
      scope: json['scope'] as String? ?? 'national',
      cityTag: json['city_tag'] as String?,
      sourceId: json['source_id'] as int? ?? 0,
      sourceName: json['source_name'] as String? ?? 'Verified Source',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString()) ?? DateTime.now()
          : DateTime.now(),
    );
  }
}

class ArticleFeedResponse {
  final String scope;
  final String? cityTag;
  final int total;
  final List<Article> articles;

  const ArticleFeedResponse({
    required this.scope,
    this.cityTag,
    required this.total,
    required this.articles,
  });

  factory ArticleFeedResponse.fromJson(Map<String, dynamic> json) {
    return ArticleFeedResponse(
      scope: json['scope'] as String? ?? 'national',
      cityTag: json['city_tag'] as String?,
      total: json['total'] as int? ?? 0,
      articles: (json['articles'] as List<dynamic>? ?? [])
          .map((item) => Article.fromJson(item as Map<String, dynamic>))
          .toList(),
    );
  }
}
