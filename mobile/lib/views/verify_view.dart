import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:google_fonts/google_fonts.dart';
import '../models/verification.dart';
import '../services/api_service.dart';
import 'dossier_screen.dart';
import 'widgets/verdict_badge.dart';
import 'widgets/verification_stepper_modal.dart';

class VerifyView extends StatefulWidget {
  final ApiService apiService;
  final String? initialClaimText;

  const VerifyView({
    super.key,
    required this.apiService,
    this.initialClaimText,
  });

  @override
  State<VerifyView> createState() => VerifyViewState();
}

class VerifyViewState extends State<VerifyView> {
  late final TextEditingController _textController;
  final TextEditingController _urlController = TextEditingController();
  bool _isUrlMode = false;
  bool _isVerifying = false;
  List<VerificationResponse> _recentVerifications = [];

  final List<Map<String, String>> _sampleRumors = [
    {
      'label': 'NASA Darkness Rumor',
      'text': 'NASA confirmed that the earth will experience 3 days of total darkness in 2026 due to solar storm',
    },
    {
      'label': 'Free Scheme Forward',
      'text': 'Government announces free ₹5000 recharge for all students under new PM welfare scheme link in description',
    },
    {
      'label': 'UPI Limit Update',
      'text': 'RBI announces new guidelines and revised transaction limits for UPI payments',
    },
    {
      'label': 'Satire Headline',
      'text': 'The Onion reports scientists successfully invent caffeine-resistant morning sleep',
    },
  ];

  @override
  void initState() {
    super.initState();
    _textController = TextEditingController(text: widget.initialClaimText ?? '');
    _loadRecentVerifications();
  }

  @override
  void didUpdateWidget(covariant VerifyView oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.initialClaimText != null &&
        widget.initialClaimText != oldWidget.initialClaimText) {
      _textController.text = widget.initialClaimText!;
    }
  }

  @override
  void dispose() {
    _textController.dispose();
    _urlController.dispose();
    super.dispose();
  }

  void setClaimText(String text) {
    setState(() {
      _textController.text = text;
      _isUrlMode = false;
    });
  }

  Future<void> _loadRecentVerifications() async {
    try {
      final recents = await widget.apiService.fetchRecentVerifications(limit: 10);
      if (mounted) {
        setState(() => _recentVerifications = recents);
      }
    } catch (e) {
      debugPrint('[VerifyView] Error loading recent verifications: $e');
    }
  }

  Future<void> _pasteFromClipboard() async {
    final data = await Clipboard.getData(Clipboard.kTextPlain);
    if (data != null && data.text != null && data.text!.isNotEmpty) {
      setState(() {
        if (_isUrlMode) {
          _urlController.text = data.text!;
        } else {
          _textController.text = data.text!;
        }
      });
    }
  }

  Future<void> triggerVerification() async {
    final claim = _isUrlMode ? _urlController.text.trim() : _textController.text.trim();
    if (claim.isEmpty) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Please enter a claim, message, or URL to verify')),
      );
      return;
    }

    setState(() => _isVerifying = true);

    // Show the animated 4-step progress modal
    showModalBottomSheet(
      context: context,
      isDismissible: false,
      enableDrag: false,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (context) => VerificationStepperModal(claimText: claim),
    );

    try {
      final dossier = await widget.apiService.verifyClaim(
        text: _isUrlMode ? null : claim,
        url: _isUrlMode ? claim : null,
      );

      if (mounted) {
        // Dismiss stepper
        Navigator.pop(context);
        setState(() => _isVerifying = false);

        // Open Truth Dossier
        Navigator.push(
          context,
          MaterialPageRoute(
            builder: (context) => DossierScreen(
              dossier: dossier,
              apiService: widget.apiService,
            ),
          ),
        );

        // Refresh recent verifications list
        _loadRecentVerifications();
      }
    } catch (e) {
      if (mounted) {
        Navigator.pop(context); // Dismiss stepper
        setState(() => _isVerifying = false);
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text('Verification error: $e'),
            backgroundColor: Colors.redAccent,
          ),
        );
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return SingleChildScrollView(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 16),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Header Card
          Container(
            padding: const EdgeInsets.all(20),
            decoration: BoxDecoration(
              color: isDark ? theme.colorScheme.surfaceContainerHigh : theme.colorScheme.primaryContainer.withValues(alpha: 0.4),
              borderRadius: BorderRadius.circular(24),
              border: Border.all(
                color: theme.colorScheme.primary.withValues(alpha: 0.2),
              ),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: theme.colorScheme.primary,
                    shape: BoxShape.circle,
                  ),
                  child: Icon(
                    Icons.shield_rounded,
                    color: theme.colorScheme.onPrimary,
                    size: 24,
                  ),
                ),
                const SizedBox(width: 14),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        'Fact-Check AI Engine',
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 18,
                          fontWeight: FontWeight.w700,
                          letterSpacing: -0.3,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Text(
                        'Paste suspicious forwards, news claims, or URLs to cross-check against whitelisted sources & Google Fact Check.',
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 12,
                          color: isDark ? Colors.white70 : Colors.black87,
                          height: 1.35,
                        ),
                      ),
                    ],
                  ),
                ),
              ],
            ),
          ),
          const SizedBox(height: 16),

          // Input Card
          Card(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Mode Switcher (Text vs URL)
                  Row(
                    children: [
                      ChoiceChip(
                        label: const Text('Text / Forward'),
                        selected: !_isUrlMode,
                        onSelected: (val) {
                          if (val) setState(() => _isUrlMode = false);
                        },
                      ),
                      const SizedBox(width: 8),
                      ChoiceChip(
                        label: const Text('Article Link / URL'),
                        selected: _isUrlMode,
                        onSelected: (val) {
                          if (val) setState(() => _isUrlMode = true);
                        },
                      ),
                      const Spacer(),
                      IconButton(
                        icon: const Icon(Icons.content_paste_rounded, size: 20),
                        tooltip: 'Paste from clipboard',
                        onPressed: _pasteFromClipboard,
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Text Field
                  if (!_isUrlMode)
                    TextField(
                      controller: _textController,
                      maxLines: 4,
                      style: GoogleFonts.plusJakartaSans(fontSize: 14),
                      decoration: InputDecoration(
                        hintText: 'Paste suspicious message, WhatsApp forward, rumor, or tweet...',
                        hintStyle: GoogleFonts.plusJakartaSans(
                          fontSize: 14,
                          color: isDark ? Colors.white38 : Colors.black38,
                        ),
                        filled: true,
                        fillColor: isDark ? Colors.white.withValues(alpha: 0.04) : Colors.black.withValues(alpha: 0.03),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(
                            color: isDark ? Colors.white12 : Colors.black12,
                          ),
                        ),
                        enabledBorder: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(
                            color: isDark ? Colors.white12 : Colors.black12,
                          ),
                        ),
                      ),
                    )
                  else
                    TextField(
                      controller: _urlController,
                      keyboardType: TextInputType.url,
                      style: GoogleFonts.plusJakartaSans(fontSize: 14),
                      decoration: InputDecoration(
                        hintText: 'https://example.com/news-story...',
                        prefixIcon: const Icon(Icons.link_rounded),
                        filled: true,
                        fillColor: isDark ? Colors.white.withValues(alpha: 0.04) : Colors.black.withValues(alpha: 0.03),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(16),
                          borderSide: BorderSide(
                            color: isDark ? Colors.white12 : Colors.black12,
                          ),
                        ),
                      ),
                    ),
                  const SizedBox(height: 16),

                  // Verify Button
                  SizedBox(
                    width: double.infinity,
                    height: 52,
                    child: ElevatedButton.icon(
                      onPressed: _isVerifying ? null : triggerVerification,
                      icon: const Icon(Icons.travel_explore_rounded, size: 20),
                      label: Text(
                        _isVerifying ? 'Investigating...' : 'Verify Fact Now',
                        style: GoogleFonts.plusJakartaSans(
                          fontSize: 15,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                      style: ElevatedButton.styleFrom(
                        backgroundColor: theme.colorScheme.primary,
                        foregroundColor: theme.colorScheme.onPrimary,
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(18),
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Quick Sample Rumor Chips
          Text(
            'TEST WITH POPULAR RUMORS',
            style: GoogleFonts.plusJakartaSans(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              letterSpacing: 0.8,
              color: isDark ? Colors.white60 : Colors.black54,
            ),
          ),
          const SizedBox(height: 10),
          Wrap(
            spacing: 8,
            runSpacing: 8,
            children: _sampleRumors.map((sample) {
              return ActionChip(
                label: Text(sample['label']!),
                avatar: const Icon(Icons.bolt_rounded, size: 16),
                onPressed: () {
                  setState(() {
                    _isUrlMode = false;
                    _textController.text = sample['text']!;
                  });
                },
              );
            }).toList(),
          ),
          const SizedBox(height: 24),

          // Recently Verified Claims
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                'RECENTLY VERIFIED CLAIMS',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 12,
                  fontWeight: FontWeight.w700,
                  letterSpacing: 0.8,
                  color: isDark ? Colors.white60 : Colors.black54,
                ),
              ),
              IconButton(
                icon: const Icon(Icons.refresh_rounded, size: 18),
                onPressed: _loadRecentVerifications,
                tooltip: 'Refresh recent debunks',
              ),
            ],
          ),
          const SizedBox(height: 8),

          if (_recentVerifications.isEmpty)
            Container(
              padding: const EdgeInsets.all(24),
              alignment: Alignment.center,
              child: Text(
                'No recent verifications found yet.',
                style: GoogleFonts.plusJakartaSans(
                  fontSize: 13,
                  color: isDark ? Colors.white38 : Colors.black38,
                ),
              ),
            )
          else
            ..._recentVerifications.map((dossier) => Card(
                  margin: const EdgeInsets.only(bottom: 10),
                  child: InkWell(
                    onTap: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) => DossierScreen(
                            dossier: dossier,
                            apiService: widget.apiService,
                          ),
                        ),
                      );
                    },
                    borderRadius: BorderRadius.circular(24),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            mainAxisAlignment: MainAxisAlignment.spaceBetween,
                            children: [
                              VerdictBadge(verdict: dossier.verdict),
                              Text(
                                '${dossier.truthScore}% Truth',
                                style: GoogleFonts.plusJakartaSans(
                                  fontSize: 12,
                                  fontWeight: FontWeight.w700,
                                  color: isDark ? Colors.white70 : Colors.black87,
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 10),
                          Text(
                            '"${dossier.claimText}"',
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 14,
                              fontWeight: FontWeight.w600,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                          const SizedBox(height: 8),
                          Row(
                            children: [
                              Icon(
                                Icons.source_rounded,
                                size: 14,
                                color: isDark ? Colors.white38 : Colors.black38,
                              ),
                              const SizedBox(width: 4),
                              Text(
                                '${dossier.evidenceSources.length} sources cited',
                                style: GoogleFonts.plusJakartaSans(
                                  fontSize: 11,
                                  color: isDark ? Colors.white54 : Colors.black54,
                                ),
                              ),
                              const Spacer(),
                              Icon(
                                Icons.chevron_right_rounded,
                                size: 18,
                                color: isDark ? Colors.white38 : Colors.black38,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                )),
        ],
      ),
    );
  }
}
