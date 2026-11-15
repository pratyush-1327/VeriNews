class CityModel {
  final String id;
  final String name;
  final String state;
  final double lat;
  final double lng;
  final double? distanceKm;

  const CityModel({
    required this.id,
    required this.name,
    required this.state,
    required this.lat,
    required this.lng,
    this.distanceKm,
  });

  factory CityModel.fromJson(Map<String, dynamic> json, {double? distanceKm}) {
    return CityModel(
      id: json['id'] as String? ?? '',
      name: json['name'] as String? ?? '',
      state: json['state'] as String? ?? '',
      lat: (json['lat'] as num?)?.toDouble() ?? 0.0,
      lng: (json['lng'] as num?)?.toDouble() ?? 0.0,
      distanceKm: distanceKm,
    );
  }

  CityModel copyWith({
    String? id,
    String? name,
    String? state,
    double? lat,
    double? lng,
    double? distanceKm,
  }) {
    return CityModel(
      id: id ?? this.id,
      name: name ?? this.name,
      state: state ?? this.state,
      lat: lat ?? this.lat,
      lng: lng ?? this.lng,
      distanceKm: distanceKm ?? this.distanceKm,
    );
  }
}
