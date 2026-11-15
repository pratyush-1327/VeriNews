import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/location_service.dart';
import '../../models/city.dart';

class CitySelectorSheet extends StatefulWidget {
  final List<CityModel> cities;
  final String selectedCityId;
  final ValueChanged<CityModel> onCitySelected;

  const CitySelectorSheet({
    super.key,
    required this.cities,
    required this.selectedCityId,
    required this.onCitySelected,
  });

  @override
  State<CitySelectorSheet> createState() => _CitySelectorSheetState();
}

class _CitySelectorSheetState extends State<CitySelectorSheet> {
  List<CityModel> _citiesWithDistances = [];
  bool _isLoadingGps = true;
  String? _nearestCityId;

  @override
  void initState() {
    super.initState();
    _loadGpsDistances();
  }

  Future<void> _loadGpsDistances() async {
    final updated = await LocationService.getCitiesWithDistances(widget.cities);
    final nearest = await LocationService.detectNearestCity(availableCities: widget.cities);

    if (mounted) {
      setState(() {
        _citiesWithDistances = updated;
        _nearestCityId = nearest.id;
        _isLoadingGps = false;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final displayCities = _citiesWithDistances.isNotEmpty
        ? _citiesWithDistances
        : widget.cities;

    return Container(
      padding: const EdgeInsets.fromLTRB(20, 16, 20, 28),
      decoration: BoxDecoration(
        color: isDark ? theme.colorScheme.surfaceContainerHigh : theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 40,
              height: 4,
              decoration: BoxDecoration(
                color: isDark ? Colors.white24 : Colors.black12,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 18),

          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(8),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.location_on_rounded,
                  color: theme.colorScheme.primary,
                  size: 20,
                ),
              ),
              const SizedBox(width: 12),
              Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    'Select City Hub',
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                  Text(
                    _isLoadingGps
                        ? 'Detecting nearest city via GPS...'
                        : 'Nearest: ${_nearestCityId?.toUpperCase() ?? 'Delhi'}',
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: 12,
                      color: isDark ? Colors.white60 : Colors.black54,
                    ),
                  ),
                ],
              ),
              const Spacer(),
              if (_isLoadingGps)
                const SizedBox(
                  width: 16,
                  height: 16,
                  child: CircularProgressIndicator(strokeWidth: 2),
                ),
            ],
          ),
          const SizedBox(height: 18),

          ...displayCities.map((city) {
            final isSelected = city.id == widget.selectedCityId;
            final isNearest = city.id == _nearestCityId;

            return Padding(
              padding: const EdgeInsets.only(bottom: 8),
              child: InkWell(
                onTap: () {
                  widget.onCitySelected(city);
                  Navigator.pop(context);
                },
                borderRadius: BorderRadius.circular(20),
                child: Container(
                  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
                  decoration: BoxDecoration(
                    color: isSelected
                        ? theme.colorScheme.primaryContainer.withValues(alpha: 0.7)
                        : (isDark ? Colors.white.withValues(alpha: 0.04) : Colors.black.withValues(alpha: 0.03)),
                    borderRadius: BorderRadius.circular(20),
                    border: Border.all(
                      color: isSelected
                          ? theme.colorScheme.primary
                          : (isDark ? Colors.white12 : Colors.black12),
                      width: isSelected ? 1.5 : 1,
                    ),
                  ),
                  child: Row(
                    children: [
                      Icon(
                        isSelected ? Icons.check_circle_rounded : Icons.location_city_rounded,
                        size: 20,
                        color: isSelected
                            ? theme.colorScheme.primary
                            : (isDark ? Colors.white60 : Colors.black45),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  city.name,
                                  style: GoogleFonts.plusJakartaSans(
                                    fontSize: 15,
                                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                                  ),
                                ),
                                if (isNearest) ...[
                                  const SizedBox(width: 8),
                                  Container(
                                    padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                    decoration: BoxDecoration(
                                      color: Colors.green.withValues(alpha: 0.2),
                                      borderRadius: BorderRadius.circular(8),
                                    ),
                                    child: Text(
                                      'NEAREST',
                                      style: GoogleFonts.plusJakartaSans(
                                        fontSize: 9,
                                        fontWeight: FontWeight.w800,
                                        color: Colors.green,
                                      ),
                                    ),
                                  ),
                                ],
                              ],
                            ),
                            Text(
                              city.state,
                              style: GoogleFonts.plusJakartaSans(
                                fontSize: 12,
                                color: isDark ? Colors.white54 : Colors.black45,
                              ),
                            ),
                          ],
                        ),
                      ),
                      if (city.distanceKm != null)
                        Text(
                          '${city.distanceKm!.toStringAsFixed(0)} km',
                          style: GoogleFonts.plusJakartaSans(
                            fontSize: 13,
                            fontWeight: FontWeight.w600,
                            color: isDark ? Colors.white60 : Colors.black54,
                          ),
                        ),
                    ],
                  ),
                ),
              ),
            );
          }),
        ],
      ),
    );
  }
}
