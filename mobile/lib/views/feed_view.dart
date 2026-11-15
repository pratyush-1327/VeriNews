import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../core/location_service.dart';
import '../models/article.dart';
import '../models/city.dart';
import '../services/api_service.dart';
import 'widgets/article_card.dart';
import 'widgets/city_selector_sheet.dart';

class FeedView extends StatefulWidget {
  final ApiService apiService;
  final Function(String claimText) onFactCheckRequested;

  const FeedView({
    super.key,
    required this.apiService,
    required this.onFactCheckRequested,
  });

  @override
  State<FeedView> createState() => _FeedViewState();
}

class _FeedViewState extends State<FeedView> {
  String _activeScope = 'national'; // 'global', 'national', 'city'
  String _selectedCityId = 'delhi';
  String _selectedCityName = 'New Delhi';

  List<CityModel> _cities = [];
  List<Article> _articles = [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _initCitiesAndFeed();
  }

  Future<void> _initCitiesAndFeed() async {
    setState(() => _isLoading = true);

    try {
      // 1. Fetch cities
      final cities = await widget.apiService.fetchCities();
      _cities = cities;

      // 2. Auto-detect nearest city
      final nearestCity = await LocationService.detectNearestCity(availableCities: cities);
      _selectedCityId = nearestCity.id;
      _selectedCityName = nearestCity.name;
    } catch (e) {
      debugPrint('[FeedView] Error initializing cities: $e');
    }

    // 3. Load active feed
    await _loadArticles();
  }

  Future<void> _loadArticles() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    try {
      final feedResponse = await widget.apiService.fetchFeed(
        scope: _activeScope,
        city: _activeScope == 'city' ? _selectedCityId : null,
      );

      if (mounted) {
        setState(() {
          _articles = feedResponse.articles;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _errorMessage = e.toString();
          _isLoading = false;
        });
      }
    }
  }

  void _openCitySelector() {
    showModalBottomSheet(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => CitySelectorSheet(
        cities: _cities,
        selectedCityId: _selectedCityId,
        onCitySelected: (city) {
          setState(() {
            _selectedCityId = city.id;
            _selectedCityName = city.name;
          });
          if (_activeScope == 'city') {
            _loadArticles();
          }
        },
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Column(
      children: [
        // Top 3-Segment Feed Selector (Material 3 Android 17 style)
        Container(
          padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 10),
          decoration: BoxDecoration(
            color: isDark ? theme.colorScheme.surfaceContainerLow : Colors.white,
            border: Border(
              bottom: BorderSide(
                color: isDark ? Colors.white12 : Colors.black12,
                width: 0.5,
              ),
            ),
          ),
          child: Row(
            children: [
              _buildSegmentPill(
                scope: 'global',
                label: 'Global',
                icon: '🌐',
              ),
              const SizedBox(width: 8),
              _buildSegmentPill(
                scope: 'national',
                label: 'India',
                icon: '🇮🇳',
              ),
              const SizedBox(width: 8),
              _buildCitySegmentPill(),
            ],
          ),
        ),

        // Articles List or Loading/Error States
        Expanded(
          child: RefreshIndicator(
            onRefresh: _loadArticles,
            color: theme.colorScheme.primary,
            child: _buildContent(theme, isDark),
          ),
        ),
      ],
    );
  }

  Widget _buildSegmentPill({
    required String scope,
    required String label,
    required String icon,
  }) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isSelected = _activeScope == scope;

    return Expanded(
      child: InkWell(
        onTap: () {
          if (_activeScope != scope) {
            setState(() => _activeScope = scope);
            _loadArticles();
          }
        },
        borderRadius: BorderRadius.circular(20),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isSelected
                ? theme.colorScheme.primaryContainer
                : (isDark ? Colors.white.withValues(alpha: 0.05) : Colors.black.withValues(alpha: 0.04)),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isSelected
                  ? theme.colorScheme.primary.withValues(alpha: 0.5)
                  : Colors.transparent,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Text(icon, style: const TextStyle(fontSize: 13)),
              const SizedBox(width: 6),
              Text(
                label,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 13,
                  fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                  color: isSelected
                      ? theme.colorScheme.primary
                      : (isDark ? Colors.white70 : Colors.black87),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildCitySegmentPill() {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final isSelected = _activeScope == 'city';

    return Expanded(
      child: InkWell(
        onTap: () {
          if (_activeScope != 'city') {
            setState(() => _activeScope = 'city');
            _loadArticles();
          } else {
            _openCitySelector();
          }
        },
        borderRadius: BorderRadius.circular(20),
        child: AnimatedContainer(
          duration: const Duration(milliseconds: 200),
          padding: const EdgeInsets.symmetric(vertical: 8),
          decoration: BoxDecoration(
            color: isSelected
                ? theme.colorScheme.primaryContainer
                : (isDark ? Colors.white.withValues(alpha: 0.05) : Colors.black.withValues(alpha: 0.04)),
            borderRadius: BorderRadius.circular(20),
            border: Border.all(
              color: isSelected
                  ? theme.colorScheme.primary.withValues(alpha: 0.5)
                  : Colors.transparent,
            ),
          ),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              const Text('📍', style: TextStyle(fontSize: 13)),
              const SizedBox(width: 4),
              Flexible(
                child: Text(
                  _selectedCityName,
                  overflow: TextOverflow.ellipsis,
                  style: GoogleFonts.plusJakartaSans(
                    fontSize: 12,
                    fontWeight: isSelected ? FontWeight.w700 : FontWeight.w600,
                    color: isSelected
                        ? theme.colorScheme.primary
                        : (isDark ? Colors.white70 : Colors.black87),
                  ),
                ),
              ),
              InkWell(
                onTap: _openCitySelector,
                child: Icon(
                  Icons.arrow_drop_down_rounded,
                  size: 16,
                  color: isSelected ? theme.colorScheme.primary : (isDark ? Colors.white54 : Colors.black54),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }

  Widget _buildContent(ThemeData theme, bool isDark) {
    if (_isLoading) {
      return Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            CircularProgressIndicator(
              strokeWidth: 2.5,
              color: theme.colorScheme.primary,
            ),
            const SizedBox(height: 16),
            Text(
              'Loading verified 60-word feed...',
              style: GoogleFonts.plusJakartaSans(
                fontSize: 13,
                color: isDark ? Colors.white60 : Colors.black54,
              ),
            ),
          ],
        ),
      );
    }

    if (_errorMessage != null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.cloud_off_rounded,
                size: 48,
                color: isDark ? Colors.white38 : Colors.black38,
              ),
              const SizedBox(height: 16),
              Text(
                'Could not load feed',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Make sure the VeriNews backend is running at ${widget.apiService.checkHealth().toString()}',
                textAlign: TextAlign.center,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 12,
                  color: isDark ? Colors.white54 : Colors.black54,
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadArticles,
                icon: const Icon(Icons.refresh_rounded, size: 16),
                label: const Text('Try Again'),
              ),
            ],
          ),
        ),
      );
    }

    if (_articles.isEmpty) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisAlignment: MainAxisAlignment.center,
            children: [
              Icon(
                Icons.newspaper_rounded,
                size: 48,
                color: isDark ? Colors.white38 : Colors.black38,
              ),
              const SizedBox(height: 16),
              Text(
                'No articles in this feed yet',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                ),
              ),
              const SizedBox(height: 8),
              Text(
                'Run news ingestion on the backend or trigger feed update.',
                textAlign: TextAlign.center,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 12,
                  color: isDark ? Colors.white54 : Colors.black54,
                ),
              ),
              const SizedBox(height: 16),
              ElevatedButton.icon(
                onPressed: _loadArticles,
                icon: const Icon(Icons.refresh_rounded, size: 16),
                label: const Text('Refresh'),
              ),
            ],
          ),
        ),
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.symmetric(vertical: 8),
      itemCount: _articles.length,
      itemBuilder: (context, index) {
        final article = _articles[index];
        return ArticleCard(
          article: article,
          onFactCheck: () => widget.onFactCheckRequested(article.title),
        );
      },
    );
  }
}
