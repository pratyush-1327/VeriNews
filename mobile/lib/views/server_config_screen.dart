import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:http/http.dart' as http;
import '../core/config.dart';
import '../services/api_service.dart';

class ServerConfigScreen extends StatefulWidget {
  final ApiService apiService;
  final VoidCallback onConfigChanged;

  const ServerConfigScreen({
    super.key,
    required this.apiService,
    required this.onConfigChanged,
  });

  @override
  State<ServerConfigScreen> createState() => _ServerConfigScreenState();
}

class _ServerConfigScreenState extends State<ServerConfigScreen> {
  late final TextEditingController _urlController;
  bool _testing = false;
  bool? _isSuccess;
  String? _statusDetails;
  int? _latencyMs;
  Map<String, dynamic>? _healthPayload;

  @override
  void initState() {
    super.initState();
    _urlController = TextEditingController(text: AppConfig.baseUrl);
    _runPingTest();
  }

  @override
  void dispose() {
    _urlController.dispose();
    super.dispose();
  }

  Future<void> _runPingTest() async {
    final rawUrl = _urlController.text.trim().replaceAll(RegExp(r'/+$'), '');
    if (rawUrl.isEmpty) return;

    setState(() {
      _testing = true;
      _isSuccess = null;
      _statusDetails = null;
      _latencyMs = null;
      _healthPayload = null;
    });

    final stopwatch = Stopwatch()..start();
    try {
      final uri = Uri.parse('$rawUrl/api/v1/health');
      final res = await http.get(uri).timeout(const Duration(seconds: 4));
      stopwatch.stop();

      if (res.statusCode == 200) {
        final data = json.decode(res.body) as Map<String, dynamic>;
        setState(() {
          _testing = false;
          _isSuccess = true;
          _latencyMs = stopwatch.elapsedMilliseconds;
          _healthPayload = data;
          _statusDetails = 'Online (HTTP 200 OK)';
        });
      } else {
        setState(() {
          _testing = false;
          _isSuccess = false;
          _latencyMs = stopwatch.elapsedMilliseconds;
          _statusDetails = 'HTTP error status: ${res.statusCode}';
        });
      }
    } catch (e) {
      stopwatch.stop();
      setState(() {
        _testing = false;
        _isSuccess = false;
        _latencyMs = stopwatch.elapsedMilliseconds;
        _statusDetails = 'Connection failed: ${e.toString().replaceAll('SocketException: ', '')}';
      });
    }
  }

  Future<void> _applyAndSave() async {
    final rawUrl = _urlController.text.trim().replaceAll(RegExp(r'/+$'), '');
    if (rawUrl.isEmpty) return;

    await AppConfig.setCustomBaseUrl(rawUrl);
    widget.onConfigChanged();

    if (mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          behavior: SnackBarBehavior.floating,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12)),
          content: Text(
            'Backend URL saved: $rawUrl',
            style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w600),
          ),
          backgroundColor: Theme.of(context).colorScheme.primary,
        ),
      );
      Navigator.of(context).pop();
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);

    return Scaffold(
      appBar: AppBar(
        title: Text(
          'Backend Server Configuration',
          style: GoogleFonts.plusJakartaSans(
            fontWeight: FontWeight.w800,
            fontSize: 18,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.refresh_rounded),
            tooltip: 'Ping Server',
            onPressed: _testing ? null : _runPingTest,
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 20, vertical: 16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Status Card
            _buildStatusCard(theme),
            const SizedBox(height: 20),

            // URL Input Card
            _buildUrlInputCard(theme),
            const SizedBox(height: 20),

            // Quick Preset IP Chips
            _buildPresetChips(theme),
            const SizedBox(height: 24),

            // Action Buttons
            Row(
              children: [
                Expanded(
                  child: OutlinedButton.icon(
                    onPressed: _testing ? null : _runPingTest,
                    icon: _testing
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(strokeWidth: 2),
                          )
                        : const Icon(Icons.bolt_rounded, size: 20),
                    label: Text(
                      _testing ? 'Testing...' : 'Test Ping',
                      style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w700),
                    ),
                    style: OutlinedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: FilledButton.icon(
                    onPressed: _applyAndSave,
                    icon: const Icon(Icons.check_rounded, size: 20),
                    label: Text(
                      'Save & Apply',
                      style: GoogleFonts.plusJakartaSans(fontWeight: FontWeight.w700),
                    ),
                    style: FilledButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(14)),
                    ),
                  ),
                ),
              ],
            ),
            const SizedBox(height: 28),

            // Physical Phone / Wi-Fi Diagnostic Guide
            _buildTroubleshootingCard(theme),
            const SizedBox(height: 40),
          ],
        ),
      ),
    );
  }

  Widget _buildStatusCard(ThemeData theme) {
    Color statusColor;
    IconData statusIcon;
    String statusTitle;

    if (_testing) {
      statusColor = Colors.blue;
      statusIcon = Icons.hourglass_top_rounded;
      statusTitle = 'Pinging Backend...';
    } else if (_isSuccess == true) {
      statusColor = const Color(0xFF10B981); // Emerald
      statusIcon = Icons.check_circle_rounded;
      statusTitle = 'Backend Online & Healthy';
    } else {
      statusColor = const Color(0xFFEF4444); // Red
      statusIcon = Icons.error_rounded;
      statusTitle = 'Backend Offline / Unreachable';
    }

    return Container(
      padding: const EdgeInsets.all(20),
      decoration: BoxDecoration(
        color: statusColor.withValues(alpha: 0.08),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: statusColor.withValues(alpha: 0.3),
          width: 1.5,
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: statusColor.withValues(alpha: 0.15),
                  shape: BoxShape.circle,
                ),
                child: Icon(statusIcon, color: statusColor, size: 24),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      statusTitle,
                      style: GoogleFonts.plusJakartaSans(
                        fontWeight: FontWeight.w800,
                        fontSize: 16,
                        color: statusColor,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      _statusDetails ?? 'Tap "Test Ping" to check endpoint response.',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize: 13,
                        color: theme.colorScheme.onSurfaceVariant,
                      ),
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                    ),
                  ],
                ),
              ),
            ],
          ),
          if (_latencyMs != null || _healthPayload != null) ...[
            const Divider(height: 24),
            Wrap(
              spacing: 16,
              runSpacing: 8,
              children: [
                if (_latencyMs != null)
                  _buildDetailPill(
                    Icons.speed_rounded,
                    'Latency: ${_latencyMs}ms',
                    theme,
                  ),
                if (_healthPayload != null) ...[
                  _buildDetailPill(
                    Icons.storage_rounded,
                    'DB: ${_healthPayload!['database'] ?? 'ok'}',
                    theme,
                  ),
                  _buildDetailPill(
                    Icons.memory_rounded,
                    'Redis: ${_healthPayload!['redis'] ?? 'ok'}',
                    theme,
                  ),
                ],
              ],
            ),
          ],
        ],
      ),
    );
  }

  Widget _buildDetailPill(IconData icon, String text, ThemeData theme) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 14, color: theme.colorScheme.onSurfaceVariant),
        const SizedBox(width: 4),
        Text(
          text,
          style: GoogleFonts.plusJakartaSans(
            fontSize: 12,
            fontWeight: FontWeight.w600,
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
      ],
    );
  }

  Widget _buildUrlInputCard(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'API Base URL',
          style: GoogleFonts.plusJakartaSans(
            fontWeight: FontWeight.w700,
            fontSize: 14,
            color: theme.colorScheme.onSurface,
          ),
        ),
        const SizedBox(height: 8),
        TextField(
          controller: _urlController,
          keyboardType: TextInputType.url,
          autocorrect: false,
          style: GoogleFonts.firaCode(
            fontSize: 14,
            fontWeight: FontWeight.w500,
          ),
          decoration: InputDecoration(
            hintText: 'http://192.168.1.68:8000',
            prefixIcon: const Icon(Icons.link_rounded),
            suffixIcon: IconButton(
              icon: const Icon(Icons.clear_rounded),
              onPressed: () => _urlController.clear(),
            ),
            filled: true,
            fillColor: theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.5),
            border: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide.none,
            ),
            focusedBorder: OutlineInputBorder(
              borderRadius: BorderRadius.circular(16),
              borderSide: BorderSide(color: theme.colorScheme.primary, width: 2),
            ),
          ),
          onSubmitted: (_) => _runPingTest(),
        ),
      ],
    );
  }

  Widget _buildPresetChips(ThemeData theme) {
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(
          'Quick Presets (Tap to select)',
          style: GoogleFonts.plusJakartaSans(
            fontWeight: FontWeight.w700,
            fontSize: 13,
            color: theme.colorScheme.onSurfaceVariant,
          ),
        ),
        const SizedBox(height: 10),
        Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [
            _buildPresetChip(
              label: '💻 Laptop Wi-Fi (${AppConfig.defaultHostLanIp})',
              url: 'http://${AppConfig.defaultHostLanIp}:8000',
              theme: theme,
              isRecommended: true,
            ),
            _buildPresetChip(
              label: '🔌 USB ADB Reverse (127.0.0.1)',
              url: 'http://127.0.0.1:8000',
              theme: theme,
            ),
            _buildPresetChip(
              label: '📱 Emulator (10.0.2.2)',
              url: 'http://10.0.2.2:8000',
              theme: theme,
            ),
            _buildPresetChip(
              label: '🖥️ Localhost',
              url: 'http://localhost:8000',
              theme: theme,
            ),
          ],
        ),
      ],
    );
  }

  Widget _buildPresetChip({
    required String label,
    required String url,
    required ThemeData theme,
    bool isRecommended = false,
  }) {
    final isSelected = _urlController.text.trim() == url;

    return ActionChip(
      avatar: isRecommended
          ? const Icon(Icons.star_rounded, size: 16, color: Colors.amber)
          : null,
      label: Text(label),
      labelStyle: GoogleFonts.plusJakartaSans(
        fontSize: 12,
        fontWeight: isSelected ? FontWeight.w800 : FontWeight.w600,
        color: isSelected ? theme.colorScheme.onPrimary : theme.colorScheme.onSurface,
      ),
      backgroundColor: isSelected
          ? theme.colorScheme.primary
          : theme.colorScheme.surfaceContainerHighest.withValues(alpha: 0.6),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(
          color: isSelected ? theme.colorScheme.primary : Colors.transparent,
        ),
      ),
      onPressed: () {
        setState(() {
          _urlController.text = url;
        });
        _runPingTest();
      },
    );
  }

  Widget _buildTroubleshootingCard(ThemeData theme) {
    return Container(
      padding: const EdgeInsets.all(18),
      decoration: BoxDecoration(
        color: theme.colorScheme.surfaceContainerLow,
        borderRadius: BorderRadius.circular(18),
        border: Border.all(
          color: theme.colorScheme.outlineVariant.withValues(alpha: 0.6),
        ),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Row(
            children: [
              Icon(Icons.wifi_find_rounded, color: theme.colorScheme.primary, size: 22),
              const SizedBox(width: 8),
              Text(
                'Wi-Fi & Physical Device Connection Guide',
                style: GoogleFonts.plusJakartaSans(
                  fontWeight: FontWeight.w800,
                  fontSize: 14,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildGuideItem(
            '1',
            'Same Wi-Fi Network',
            'Ensure both your phone and laptop are connected to the exact same Wi-Fi router (avoid guest networks or cellular data).',
            theme,
          ),
          const SizedBox(height: 10),
          _buildGuideItem(
            '2',
            'Use Laptop LAN IP',
            'Select "Laptop Wi-Fi (192.168.1.68:8000)". "localhost" and "10.0.2.2" will NEVER work on a physical phone.',
            theme,
          ),
          const SizedBox(height: 10),
          _buildGuideItem(
            '3',
            'Wi-Fi AP Isolation Issue?',
            'Some home/office routers isolate wireless devices from talking to each other. If it times out, turn on your Phone Hotspot and connect your laptop to it!',
            theme,
          ),
          const SizedBox(height: 10),
          _buildGuideItem(
            '4',
            '100% Reliable USB Tunnel (Zero-Wi-Fi ADB)',
            'Plug your phone via USB with USB Debugging enabled, then run this command on your laptop terminal:',
            theme,
          ),
          const SizedBox(height: 8),
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
            decoration: BoxDecoration(
              color: theme.colorScheme.surfaceContainerHighest,
              borderRadius: BorderRadius.circular(10),
            ),
            child: Row(
              children: [
                Expanded(
                  child: Text(
                    'adb reverse tcp:8000 tcp:8000',
                    style: GoogleFonts.firaCode(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: theme.colorScheme.primary,
                    ),
                  ),
                ),
                IconButton(
                  icon: const Icon(Icons.copy_rounded, size: 18),
                  tooltip: 'Copy ADB command',
                  onPressed: () {
                    Clipboard.setData(
                      const ClipboardData(text: 'adb reverse tcp:8000 tcp:8000'),
                    );
                    ScaffoldMessenger.of(context).showSnackBar(
                      const SnackBar(
                        content: Text('Copied: adb reverse tcp:8000 tcp:8000'),
                        duration: Duration(seconds: 2),
                      ),
                    );
                  },
                ),
              ],
            ),
          ),
          const SizedBox(height: 6),
          Text(
            'After running adb reverse, select "127.0.0.1:8000" in this screen. It will connect instantly over the cable!',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 12,
              color: theme.colorScheme.onSurfaceVariant,
            ),
          ),
        ],
      ),
    );
  }

  Widget _buildGuideItem(
    String step,
    String title,
    String description,
    ThemeData theme,
  ) {
    return Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Container(
          width: 22,
          height: 22,
          alignment: Alignment.center,
          decoration: BoxDecoration(
            color: theme.colorScheme.primaryContainer,
            shape: BoxShape.circle,
          ),
          child: Text(
            step,
            style: GoogleFonts.plusJakartaSans(
              fontSize: 12,
              fontWeight: FontWeight.w800,
              color: theme.colorScheme.primary,
            ),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: GoogleFonts.plusJakartaSans(
                  fontWeight: FontWeight.w700,
                  fontSize: 13,
                ),
              ),
              const SizedBox(height: 2),
              Text(
                description,
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 12,
                  color: theme.colorScheme.onSurfaceVariant,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
