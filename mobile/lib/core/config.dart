import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:shared_preferences/shared_preferences.dart';

class AppConfig {
  static const String appName = 'VeriNews';
  static const String appTagline = 'Trusted News & Evidence-Based Verification';
  static const String defaultHostLanIp = '192.168.1.68';
  static const String _storageKey = 'verinews_backend_url';

  /// Default API base URL auto-detection:
  /// - Android Emulator: 10.0.2.2:8000
  /// - Web / Linux / Desktop: localhost:8000
  /// - Physical Android device via USB/Wi-Fi: change to host IP if needed
  static String _customBaseUrl = '';

  static String get baseUrl {
    if (_customBaseUrl.isNotEmpty) {
      return _customBaseUrl;
    }
    if (kIsWeb) {
      return 'http://localhost:8000';
    }
    if (Platform.isAndroid) {
      return 'http://10.0.2.2:8000';
    }
    return 'http://localhost:8000';
  }

  static Future<void> loadSavedBaseUrl() async {
    try {
      final prefs = await SharedPreferences.getInstance();
      final saved = prefs.getString(_storageKey);
      if (saved != null && saved.trim().isNotEmpty) {
        _customBaseUrl = saved.trim().replaceAll(RegExp(r'/+$'), '');
      }
    } catch (e) {
      debugPrint('[AppConfig] Error loading saved base URL: $e');
    }
  }

  static Future<void> setCustomBaseUrl(String url) async {
    _customBaseUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
    try {
      final prefs = await SharedPreferences.getInstance();
      if (_customBaseUrl.isEmpty) {
        await prefs.remove(_storageKey);
      } else {
        await prefs.setString(_storageKey, _customBaseUrl);
      }
    } catch (e) {
      debugPrint('[AppConfig] Error persisting base URL: $e');
    }
  }

  /// 6 Supported City Hubs with official geo-coordinates
  static const Map<String, Map<String, dynamic>> supportedCities = {
    'delhi': {
      'id': 'delhi',
      'name': 'New Delhi',
      'state': 'Delhi',
      'lat': 28.6139,
      'lng': 77.2090,
    },
    'jaipur': {
      'id': 'jaipur',
      'name': 'Jaipur',
      'state': 'Rajasthan',
      'lat': 26.9124,
      'lng': 75.7873,
    },
    'mumbai': {
      'id': 'mumbai',
      'name': 'Mumbai',
      'state': 'Maharashtra',
      'lat': 19.0760,
      'lng': 72.8777,
    },
    'bengaluru': {
      'id': 'bengaluru',
      'name': 'Bengaluru',
      'state': 'Karnataka',
      'lat': 12.9716,
      'lng': 77.5946,
    },
    'chennai': {
      'id': 'chennai',
      'name': 'Chennai',
      'state': 'Tamil Nadu',
      'lat': 13.0827,
      'lng': 80.2707,
    },
    'kolkata': {
      'id': 'kolkata',
      'name': 'Kolkata',
      'state': 'West Bengal',
      'lat': 22.5726,
      'lng': 88.3639,
    },
  };

  static const String defaultCityId = 'delhi';
}
