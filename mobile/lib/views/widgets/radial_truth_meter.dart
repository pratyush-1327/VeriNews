import 'dart:math';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import '../../core/theme.dart';

class RadialTruthMeter extends StatelessWidget {
  final int score;
  final String verdict;
  final double size;

  const RadialTruthMeter({
    super.key,
    required this.score,
    required this.verdict,
    this.size = 140,
  });

  @override
  Widget build(BuildContext context) {
    final isDark = Theme.of(context).brightness == Brightness.dark;
    final primaryColor = VeriNewsColors.getVerdictColor(verdict, isDark: isDark);
    final trackColor = isDark
        ? Colors.white.withValues(alpha: 0.08)
        : Colors.black.withValues(alpha: 0.06);

    return TweenAnimationBuilder<double>(
      tween: Tween<double>(begin: 0.0, end: score / 100.0),
      duration: const Duration(milliseconds: 1200),
      curve: Curves.easeOutCubic,
      builder: (context, animatedValue, child) {
        return SizedBox(
          width: size,
          height: size,
          child: Stack(
            alignment: Alignment.center,
            children: [
              CustomPaint(
                size: Size(size, size),
                painter: _RadialPainter(
                  progress: animatedValue,
                  trackColor: trackColor,
                  progressColor: primaryColor,
                  strokeWidth: size * 0.09,
                ),
              ),
              Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text(
                    '${(animatedValue * 100).toInt()}%',
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: size * 0.22,
                      fontWeight: FontWeight.w800,
                      color: primaryColor,
                      letterSpacing: -1,
                    ),
                  ),
                  Text(
                    'TRUTH SCORE',
                    style: GoogleFonts.plusJakartaSans(
                      fontSize: size * 0.075,
                      fontWeight: FontWeight.w700,
                      color: isDark ? Colors.white60 : Colors.black45,
                      letterSpacing: 0.8,
                    ),
                  ),
                ],
              ),
            ],
          ),
        );
      },
    );
  }
}

class _RadialPainter extends CustomPainter {
  final double progress;
  final Color trackColor;
  final Color progressColor;
  final double strokeWidth;

  _RadialPainter({
    required this.progress,
    required this.trackColor,
    required this.progressColor,
    required this.strokeWidth,
  });

  @override
  void paint(Canvas canvas, Size size) {
    final center = Offset(size.width / 2, size.height / 2);
    final radius = (size.width - strokeWidth) / 2;

    // Draw background track arc (270 degrees sweep)
    const startAngle = 135 * (pi / 180);
    const sweepAngle = 270 * (pi / 180);

    final trackPaint = Paint()
      ..color = trackColor
      ..style = PaintingStyle.stroke
      ..strokeWidth = strokeWidth
      ..strokeCap = StrokeCap.round;

    canvas.drawArc(
      Rect.fromCircle(center: center, radius: radius),
      startAngle,
      sweepAngle,
      false,
      trackPaint,
    );

    // Draw active progress arc
    if (progress > 0) {
      final activePaint = Paint()
        ..color = progressColor
        ..style = PaintingStyle.stroke
        ..strokeWidth = strokeWidth
        ..strokeCap = StrokeCap.round;

      final currentSweep = sweepAngle * progress.clamp(0.0, 1.0);
      canvas.drawArc(
        Rect.fromCircle(center: center, radius: radius),
        startAngle,
        currentSweep,
        false,
        activePaint,
      );
    }
  }

  @override
  bool shouldRepaint(covariant _RadialPainter oldDelegate) {
    return oldDelegate.progress != progress ||
        oldDelegate.progressColor != progressColor;
  }
}
