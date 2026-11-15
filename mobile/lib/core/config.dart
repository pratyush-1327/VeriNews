import 'dart:io';
import 'package:flutter/foundation.dart';

class AppConfig {
  static const String appName = 'VeriNews';
  static const String appTagline = 'Trusted News & Evidence-Based Verification';

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

  static void setCustomBaseUrl(String url) {
    _customBaseUrl = url.trim().replaceAll(RegExp(r'/+$'), '');
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
