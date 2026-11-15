import 'dart:async';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class VerificationStepperModal extends StatefulWidget {
  final String claimText;

  const VerificationStepperModal({
    super.key,
    required this.claimText,
  });

  @override
  State<VerificationStepperModal> createState() => _VerificationStepperModalState();
}

class _VerificationStepperModalState extends State<VerificationStepperModal> {
  int _currentStep = 0;
  Timer? _stepTimer;

  final List<Map<String, dynamic>> _steps = [
    {
      'title': 'Decomposing Core Claims',
      'subtitle': 'Stripping clickbait & extracting atomic propositions with Gemini',
      'icon': Icons.psychology_outlined,
    },
    {
      'title': 'Cross-Referencing Live Evidence',
      'subtitle': 'Querying Google Fact Check registry, Tavily & whitelisted news wires',
      'icon': Icons.travel_explore_rounded,
    },
    {
      'title': 'Natural Language Inference',
      'subtitle': 'Evaluating entailment vs contradiction & calculating veracity score',
      'icon': Icons.balance_rounded,
    },
    {
      'title': 'Synthesizing Truth Dossier',
      'subtitle': 'Generating branded WhatsApp debunk card & citation graph',
      'icon': Icons.fact_check_rounded,
    },
  ];

  @override
  void initState() {
    super.initState();
    _startStepSimulation();
  }

  void _startStepSimulation() {
    _stepTimer = Timer.periodic(const Duration(milliseconds: 1400), (timer) {
      if (mounted) {
        setState(() {
          if (_currentStep < _steps.length - 1) {
            _currentStep++;
          }
        });
      }
    });
  }

  @override
  void dispose() {
    _stepTimer?.cancel();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;

    return Container(
      padding: const EdgeInsets.fromLTRB(24, 20, 24, 32),
      decoration: BoxDecoration(
        color: isDark
            ? theme.colorScheme.surfaceContainerHigh
            : theme.colorScheme.surface,
        borderRadius: const BorderRadius.vertical(top: Radius.circular(32)),
      ),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          // Drag handle
          Center(
            child: Container(
              width: 44,
              height: 4,
              decoration: BoxDecoration(
                color: isDark ? Colors.white24 : Colors.black12,
                borderRadius: BorderRadius.circular(2),
              ),
            ),
          ),
          const SizedBox(height: 20),

          // Header
          Row(
            children: [
              Container(
                padding: const EdgeInsets.all(10),
                decoration: BoxDecoration(
                  color: theme.colorScheme.primaryContainer,
                  shape: BoxShape.circle,
                ),
                child: Icon(
                  Icons.shield_outlined,
                  color: theme.colorScheme.primary,
                  size: 24,
                ),
              ),
              const SizedBox(width: 14),
              Expanded(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      'AI Fact-Checking Engine',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize: 18,
                        fontWeight: FontWeight.w700,
                        letterSpacing: -0.3,
                      ),
                    ),
                    Text(
                      'Investigating claim against verified sources',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize: 12,
                        color: isDark ? Colors.white60 : Colors.black54,
                      ),
                    ),
                  ],
                ),
              ),
            ],
          ),
          const SizedBox(height: 16),

          // Claim excerpt box
          Container(
            padding: const EdgeInsets.all(14),
            decoration: BoxDecoration(
              color: isDark ? Colors.white.withValues(alpha: 0.05) : Colors.black.withValues(alpha: 0.04),
              borderRadius: BorderRadius.circular(16),
              border: Border.all(
                color: isDark ? Colors.white12 : Colors.black12,
              ),
            ),
            child: Text(
              '"${widget.claimText}"',
              maxLines: 2,
              overflow: TextOverflow.ellipsis,
              style: GoogleFonts.plusJakartaSans(
                fontSize: 13,
                fontStyle: FontStyle.italic,
                color: isDark ? Colors.white70 : Colors.black87,
              ),
            ),
          ),
          const SizedBox(height: 24),

          // 4 Animated Verification Steps
          ...List.generate(_steps.length, (index) {
            final step = _steps[index];
            final isDone = index < _currentStep;
            final isCurrent = index == _currentStep;

            return Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Row(
                children: [
                  Container(
                    width: 36,
                    height: 36,
                    decoration: BoxDecoration(
                      shape: BoxShape.circle,
                      color: isDone
                          ? Colors.green.withValues(alpha: 0.2)
                          : isCurrent
                              ? theme.colorScheme.primary.withValues(alpha: 0.2)
                              : (isDark ? Colors.white10 : Colors.black12),
                    ),
                    child: Center(
                      child: isDone
                          ? const Icon(
                              Icons.check_rounded,
                              size: 20,
                              color: Colors.green,
                            )
                          : isCurrent
                              ? SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2.2,
                                    color: theme.colorScheme.primary,
                                  ),
                                )
                              : Icon(
                                  step['icon'] as IconData,
                                  size: 18,
                                  color: isDark ? Colors.white38 : Colors.black38,
                                ),
                    ),
                  ),
                  const SizedBox(width: 14),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          step['title'] as String,
                          style: GoogleFonts.plusJakartaSans(
                            fontSize: 14,
                            fontWeight: isCurrent ? FontWeight.w700 : FontWeight.w500,
                            color: isCurrent
                                ? theme.colorScheme.primary
                                : isDone
                                    ? (isDark ? Colors.white : Colors.black87)
                                    : (isDark ? Colors.white38 : Colors.black38),
                          ),
                        ),
                        Text(
                          step['subtitle'] as String,
                          style: GoogleFonts.plusJakartaSans(
                            fontSize: 11,
                            color: isDark ? Colors.white54 : Colors.black45,
                          ),
                        ),
                      ],
                    ),
                  ),
                ],
              ),
            );
          }),
        ],
      ),
    );
  }
}
