import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme.dart';

class VerdictBadge extends StatelessWidget {
  final String verdict;
  final bool isLarge;

  const VerdictBadge({
    super.key,
    required this.verdict,
    this.isLarge = false,
  });

  IconData _getIcon(String v) {
    switch (v.toUpperCase()) {
      case 'TRUE':
        return Icons.verified_rounded;
      case 'MISLEADING':
        return Icons.warning_amber_rounded;
      case 'FAKE':
        return Icons.cancel_rounded;
      case 'SATIRE':
        return Icons.theater_comedy_rounded;
      case 'UNVERIFIED':
      default:
        return Icons.help_outline_rounded;
    }
  }

  String _getLabel(String v) {
    switch (v.toUpperCase()) {
      case 'TRUE':
        return 'VERIFIED TRUE';
      case 'MISLEADING':
        return 'MISLEADING';
      case 'FAKE':
        return 'DEBUNKED FAKE';
      case 'SATIRE':
        return 'SATIRE / HUMOR';
      case 'UNVERIFIED':
      default:
        return 'UNVERIFIED CLAIM';
    }
  }

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final color = VeriNewsColors.getVerdictColor(verdict, isDark: isDark);
    final containerColor = VeriNewsColors.getVerdictContainer(verdict, isDark: isDark);
    final icon = _getIcon(verdict);
    final label = _getLabel(verdict);

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isLarge ? 16 : 10,
        vertical: isLarge ? 8 : 4,
      ),
      decoration: BoxDecoration(
        color: containerColor,
        borderRadius: BorderRadius.circular(isLarge ? 24 : 16),
        border: Border.all(
          color: color.withValues(alpha: isDark ? 0.6 : 0.8),
          width: isLarge ? 1.5 : 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: isLarge ? 20 : 14,
            color: color,
          ),
          SizedBox(width: isLarge ? 8 : 5),
          Text(
            label,
            style: GoogleFonts.plusJakartaSans(
              fontSize: isLarge ? 13 : 11,
              fontWeight: FontWeight.w700,
              color: color,
              letterSpacing: 0.5,
            ),
          ),
        ],
      ),
    );
  }
}
