import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import '../models/article.dart';
import '../models/city.dart';
import '../models/verification.dart';

class ApiService {
  final http.Client _client;

  ApiService({http.Client? client}) : _client = client ?? http.Client();

  String get _baseUrl => AppConfig.baseUrl;

  /// Check backend connection health
  Future<bool> checkHealth() async {
    try {
      final uri = Uri.parse('$_baseUrl/api/v1/health');
      final res = await _client.get(uri).timeout(const Duration(seconds: 4));
      return res.statusCode == 200;
    } catch (e) {
      debugPrint('[ApiService] Health check error: $e');
      return false;
    }
  }

  /// Fetch supported city hubs
  Future<List<CityModel>> fetchCities() async {
    try {
      final uri = Uri.parse('$_baseUrl/api/v1/news/cities');
      final res = await _client.get(uri).timeout(const Duration(seconds: 6));

      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        final citiesJson = data['cities'] as List<dynamic>? ?? [];
        return citiesJson
            .map((c) => CityModel.fromJson(c as Map<String, dynamic>))
            .toList();
      }
    } catch (e) {
      debugPrint('[ApiService] Failed to fetch cities from backend: $e');
    }

    // Graceful fallback to static config if backend is unreachable
    return AppConfig.supportedCities.entries.map((e) {
      return CityModel.fromJson(e.value);
    }).toList();
  }

  /// Fetch 60-word news feed
  Future<ArticleFeedResponse> fetchFeed({
    required String scope,
    String? city,
    int limit = 20,
    int offset = 0,
  }) async {
    final queryParams = {
      'scope': scope,
      'limit': limit.toString(),
      'offset': offset.toString(),
    };
    if (scope == 'city' && city != null) {
      queryParams['city'] = city.toLowerCase();
    }

    final uri = Uri.parse('$_baseUrl/api/v1/news/feed').replace(
      queryParameters: queryParams,
    );

    final res = await _client.get(uri).timeout(const Duration(seconds: 15));

    if (res.statusCode == 200) {
      final data = json.decode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      return ArticleFeedResponse.fromJson(data);
    } else {
      throw Exception('Failed to load feed: ${res.statusCode} ${res.body}');
    }
  }

  /// Submit claim for real-time RAG fact-checking
  Future<VerificationResponse> verifyClaim({
    String? text,
    String? url,
    String? imageBase64,
  }) async {
    final uri = Uri.parse('$_baseUrl/api/v1/verify');
    final payload = <String, dynamic>{};

    if (text != null && text.trim().isNotEmpty) {
      payload['text'] = text.trim();
    }
    if (url != null && url.trim().isNotEmpty) {
      payload['url'] = url.trim();
    }
    if (imageBase64 != null && imageBase64.isNotEmpty) {
      payload['image_base64'] = imageBase64;
    }

    final res = await _client.post(
      uri,
      headers: {'Content-Type': 'application/json'},
      body: json.encode(payload),
    ).timeout(const Duration(seconds: 45));

    if (res.statusCode == 200) {
      final data = json.decode(utf8.decode(res.bodyBytes)) as Map<String, dynamic>;
      return VerificationResponse.fromJson(data);
    } else {
      throw Exception('Verification failed: ${res.statusCode} ${res.body}');
    }
  }

  /// Fetch recent verified claims
  Future<List<VerificationResponse>> fetchRecentVerifications({
    int limit = 10,
  }) async {
    try {
      final uri = Uri.parse('$_baseUrl/api/v1/verify/recent?limit=$limit');
      final res = await _client.get(uri).timeout(const Duration(seconds: 10));

      if (res.statusCode == 200) {
        final list = json.decode(utf8.decode(res.bodyBytes)) as List<dynamic>;
        return list
            .map((item) => VerificationResponse.fromJson(item as Map<String, dynamic>))
            .toList();
      }
    } catch (e) {
      debugPrint('[ApiService] Error fetching recent verifications: $e');
    }
    return [];
  }

  /// Construct absolute URL for debunk card PNG
  String? getDebunkCardFullUrl(String? relativePath) {
    if (relativePath == null || relativePath.isEmpty) return null;
    if (relativePath.startsWith('http://') || relativePath.startsWith('https://')) {
      return relativePath;
    }
    final cleanPath = relativePath.startsWith('/') ? relativePath : '/$relativePath';
    return '$_baseUrl$cleanPath';
  }
}
