import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../core/config.dart';
import '../services/api_service.dart';
import '../services/share_intent_service.dart';
import 'feed_view.dart';
import 'verify_view.dart';

class HomeScreen extends StatefulWidget {
  final ApiService apiService;
  final VoidCallback onToggleTheme;
  final bool isDarkMode;

  const HomeScreen({
    super.key,
    required this.apiService,
    required this.onToggleTheme,
    required this.isDarkMode,
  });

  @override
  State<HomeScreen> createState() => _HomeScreenState();
}

class _HomeScreenState extends State<HomeScreen> {
  int _currentIndex = 0;
  bool _isBackendOnline = false;
  final GlobalKey<VerifyViewState> _verifyKey = GlobalKey<VerifyViewState>();

  @override
  void initState() {
    super.initState();
    _checkBackendStatus();

    // Listen to OS Share Intent updates
    final shareService = ShareIntentService();
    shareService.addListener(_onShareIntentReceived);

    // Check if there is an initial shared text on launch
    if (shareService.pendingPayload != null) {
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _onShareIntentReceived();
      });
    }
  }

  @override
  void dispose() {
    ShareIntentService().removeListener(_onShareIntentReceived);
    super.dispose();
  }

  void _onShareIntentReceived() {
    final payload = ShareIntentService().pendingPayload;
    if (payload != null && (payload.text != null || payload.imagePath != null)) {
      final sharedText = payload.text ?? 'Shared Image from OS';
      ShareIntentService().clearPendingPayload();

      setState(() => _currentIndex = 1); // Switch to Verify Tab
      WidgetsBinding.instance.addPostFrameCallback((_) {
        _verifyKey.currentState?.setClaimText(sharedText);
        _verifyKey.currentState?.triggerVerification();
      });
    }
  }

  Future<void> _checkBackendStatus() async {
    final online = await widget.apiService.checkHealth();
    if (mounted) {
      setState(() => _isBackendOnline = online);
    }
  }

  void _onFactCheckRequestedFromFeed(String claimText) {
    setState(() => _currentIndex = 1);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      _verifyKey.currentState?.setClaimText(claimText);
      _verifyKey.currentState?.triggerVerification();
    });
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Row(
          children: [
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
              decoration: BoxDecoration(
                color: theme.colorScheme.primary,
                borderRadius: BorderRadius.circular(12),
              ),
              child: Text(
                'VN',
                style: GoogleFonts.plusJakartaSans(
                  fontWeight: FontWeight.w900,
                  fontSize: 14,
                  color: theme.colorScheme.onPrimary,
                  letterSpacing: -0.5,
                ),
              ),
            ),
            const SizedBox(width: 10),
            Text(
              AppConfig.appName,
              style: GoogleFonts.plusJakartaSans(
                fontWeight: FontWeight.w800,
                fontSize: 22,
                letterSpacing: -0.8,
              ),
            ),
            const SizedBox(width: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
              decoration: BoxDecoration(
                color: theme.colorScheme.primaryContainer.withValues(alpha: 0.6),
                borderRadius: BorderRadius.circular(8),
              ),
              child: Text(
                'AI RAG',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 10,
                  fontWeight: FontWeight.w800,
                  color: theme.colorScheme.primary,
                  letterSpacing: 0.5,
                ),
              ),
            ),
          ],
        ),
        actions: [
          // Backend connectivity status dot
          Tooltip(
            message: _isBackendOnline ? 'Backend Online' : 'Backend Connecting...',
            child: Padding(
              padding: const EdgeInsets.symmetric(horizontal: 8),
              child: Row(
                children: [
                  Container(
                    width: 8,
                    height: 8,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: _isBackendOnline ? Colors.greenAccent[400] : Colors.amberAccent[400],
                    ),
                  ),
                ],
              ),
            ),
          ),

          // Theme Mode Switcher
          IconButton(
            icon: Icon(
              widget.isDarkMode ? Icons.light_mode_rounded : Icons.dark_mode_rounded,
              size: 20,
            ),
            tooltip: 'Toggle Theme',
            onPressed: widget.onToggleTheme,
          ),
          const SizedBox(width: 4),
        ],
      ),
      body: IndexedStack(
        index: _currentIndex,
        children: [
          FeedView(
            apiService: widget.apiService,
            onFactCheckRequested: _onFactCheckRequestedFromFeed,
          ),
          VerifyView(
            key: _verifyKey,
            apiService: widget.apiService,
          ),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _currentIndex,
        onDestinationSelected: (index) {
          setState(() => _currentIndex = index);
        },
        destinations: const [
          NavigationDestination(
            icon: Icon(Icons.newspaper_outlined),
            selectedIcon: Icon(Icons.newspaper_rounded),
            label: 'News Feed',
          ),
          NavigationDestination(
            icon: Icon(Icons.fact_check_outlined),
            selectedIcon: Icon(Icons.fact_check_rounded),
            label: 'Fact Check',
          ),
        ],
      ),
      floatingActionButton: _currentIndex == 0
          ? FloatingActionButton.extended(
              onPressed: () {
                setState(() => _currentIndex = 1);
              },
              icon: const Icon(Icons.shield_outlined),
              label: Text(
                'Fact-Check Claim',
                style: GoogleFonts.plusJakartaSans(
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
              backgroundColor: theme.colorScheme.primary,
              foregroundColor: theme.colorScheme.onPrimary,
              elevation: 3,
            )
          : null,
    );
  }
}
