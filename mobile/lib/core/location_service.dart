import 'dart:math';
import 'package:flutter/foundation.dart';
import 'package:geolocator/geolocator.dart';
import '../models/city.dart';
import 'config.dart';

class LocationService {
  /// Calculate great-circle distance between two coordinates in kilometers (Haversine formula)
  static double calculateDistanceKm(
    double lat1,
    double lon1,
    double lat2,
    double lon2,
  ) {
    const double earthRadiusKm = 6371.0;
    final double dLat = _degToRad(lat2 - lat1);
    final double dLon = _degToRad(lon2 - lon1);

    final double a = sin(dLat / 2) * sin(dLat / 2) +
        cos(_degToRad(lat1)) *
            cos(_degToRad(lat2)) *
            sin(dLon / 2) *
            sin(dLon / 2);
    final double c = 2 * atan2(sqrt(a), sqrt(1 - a));
    return earthRadiusKm * c;
  }

  static double _degToRad(double deg) => deg * (pi / 180.0);

  /// Request location permission and determine current position
  static Future<Position?> getCurrentPosition() async {
    try {
      bool serviceEnabled = await Geolocator.isLocationServiceEnabled();
      if (!serviceEnabled) {
        debugPrint('[LocationService] Location services are disabled.');
        return null;
      }

      LocationPermission permission = await Geolocator.checkPermission();
      if (permission == LocationPermission.denied) {
        permission = await Geolocator.requestPermission();
        if (permission == LocationPermission.denied) {
          debugPrint('[LocationService] Location permissions are denied');
          return null;
        }
      }

      if (permission == LocationPermission.deniedForever) {
        debugPrint('[LocationService] Location permissions permanently denied');
        return null;
      }

      return await Geolocator.getCurrentPosition(
        locationSettings: const LocationSettings(
          accuracy: LocationAccuracy.medium,
          timeLimit: Duration(seconds: 5),
        ),
      );
    } catch (e) {
      debugPrint('[LocationService] Error fetching position: $e');
      return null;
    }
  }

  /// Match current device position to the nearest of the 6 supported cities
  static Future<CityModel> detectNearestCity({
    List<CityModel>? availableCities,
  }) async {
    final cities = availableCities ??
        AppConfig.supportedCities.entries.map((e) {
          return CityModel.fromJson(e.value);
        }).toList();

    final position = await getCurrentPosition();
    if (position == null) {
      // Default to Delhi or first city if location unavailable
      final defaultCity = cities.firstWhere(
        (c) => c.id == AppConfig.defaultCityId,
        orElse: () => cities.first,
      );
      return defaultCity;
    }

    CityModel? nearestCity;
    double minDistance = double.infinity;

    for (final city in cities) {
      final dist = calculateDistanceKm(
        position.latitude,
        position.longitude,
        city.lat,
        city.lng,
      );
      if (dist < minDistance) {
        minDistance = dist;
        nearestCity = city.copyWith(distanceKm: dist);
      }
    }

    return nearestCity ??
        cities.firstWhere(
          (c) => c.id == AppConfig.defaultCityId,
          orElse: () => cities.first,
        );
  }

  /// Annotate a list of cities with distances from user position
  static Future<List<CityModel>> getCitiesWithDistances(
    List<CityModel> cities,
  ) async {
    final position = await getCurrentPosition();
    if (position == null) {
      return cities;
    }

    return cities.map((city) {
      final dist = calculateDistanceKm(
        position.latitude,
        position.longitude,
        city.lat,
        city.lng,
      );
      return city.copyWith(distanceKm: dist);
    }).toList();
  }
}
