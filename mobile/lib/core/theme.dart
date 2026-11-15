import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';

class VeriNewsColors {
  // Google M3 Expressive Palette (Light)
  static const Color lightPrimary = Color(0xFF00639B);
  static const Color lightOnPrimary = Color(0xFFFFFFFF);
  static const Color lightPrimaryContainer = Color(0xFFCEE5FF);
  static const Color lightOnPrimaryContainer = Color(0xFF001D33);

  static const Color lightSecondary = Color(0xFF006874);
  static const Color lightOnSecondary = Color(0xFFFFFFFF);
  static const Color lightSecondaryContainer = Color(0xFF97F0FF);
  static const Color lightOnSecondaryContainer = Color(0xFF001F24);

  static const Color lightTertiary = Color(0xFF725572);
  static const Color lightSurface = Color(0xFFF8F9FA);
  static const Color lightOnSurface = Color(0xFF191C1E);
  static const Color lightSurfaceVariant = Color(0xFFDFE2EB);
  static const Color lightOutline = Color(0xFF72777F);

  // Google M3 Expressive Palette (Dark - Android 17 Obsidian Style)
  static const Color darkPrimary = Color(0xFF9ECAFF);
  static const Color darkOnPrimary = Color(0xFF003256);
  static const Color darkPrimaryContainer = Color(0xFF004978);
  static const Color darkOnPrimaryContainer = Color(0xFFCEE5FF);

  static const Color darkSecondary = Color(0xFF4FD8EB);
  static const Color darkOnSecondary = Color(0xFF00363D);
  static const Color darkSecondaryContainer = Color(0xFF004F58);
  static const Color darkOnSecondaryContainer = Color(0xFF97F0FF);

  static const Color darkTertiary = Color(0xFFE0BBDE);
  static const Color darkSurface = Color(0xFF0E1418);
  static const Color darkSurfaceContainerLowest = Color(0xFF0A0F12);
  static const Color darkSurfaceContainerLow = Color(0xFF161C20);
  static const Color darkSurfaceContainer = Color(0xFF1B2125);
  static const Color darkSurfaceContainerHigh = Color(0xFF252B30);
  static const Color darkSurfaceContainerHighest = Color(0xFF30363C);
  static const Color darkOnSurface = Color(0xFFE0E3E8);
  static const Color darkOnSurfaceVariant = Color(0xFFC2C7CF);
  static const Color darkOutline = Color(0xFF8C9199);
  static const Color darkOutlineVariant = Color(0xFF42474E);

  // VeriNews Verdict Colors
  static const Color verdictTrue = Color(0xFF00875A); // Emerald
  static const Color verdictTrueDark = Color(0xFF34D399);

  static const Color verdictMisleading = Color(0xFFE65100); // Amber/Orange
  static const Color verdictMisleadingDark = Color(0xFFFB923C);

  static const Color verdictFake = Color(0xFFD93025); // Crimson
  static const Color verdictFakeDark = Color(0xFFF87171);

  static const Color verdictSatire = Color(0xFF9333EA); // Purple
  static const Color verdictSatireDark = Color(0xFFC084FC);

  static const Color verdictUnverified = Color(0xFF5F6368); // Slate
  static const Color verdictUnverifiedDark = Color(0xFF94A3B8);

  static Color getVerdictColor(String verdict, {bool isDark = true}) {
    switch (verdict.toUpperCase()) {
      case 'TRUE':
        return isDark ? verdictTrueDark : verdictTrue;
      case 'MISLEADING':
        return isDark ? verdictMisleadingDark : verdictMisleading;
      case 'FAKE':
        return isDark ? verdictFakeDark : verdictFake;
      case 'SATIRE':
        return isDark ? verdictSatireDark : verdictSatire;
      case 'UNVERIFIED':
      default:
        return isDark ? verdictUnverifiedDark : verdictUnverified;
    }
  }

  static Color getVerdictContainer(String verdict, {bool isDark = true}) {
    final base = getVerdictColor(verdict, isDark: isDark);
    return isDark ? base.withValues(alpha: 0.18) : base.withValues(alpha: 0.12);
  }
}

class VeriNewsTheme {
  static ThemeData get lightTheme {
    final baseColorScheme = ColorScheme.fromSeed(
      seedColor: VeriNewsColors.lightPrimary,
      brightness: Brightness.light,
    ).copyWith(
      surface: VeriNewsColors.lightSurface,
      primary: VeriNewsColors.lightPrimary,
      primaryContainer: VeriNewsColors.lightPrimaryContainer,
      secondary: VeriNewsColors.lightSecondary,
      secondaryContainer: VeriNewsColors.lightSecondaryContainer,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.light,
      colorScheme: baseColorScheme,
      scaffoldBackgroundColor: VeriNewsColors.lightSurface,
      textTheme: GoogleFonts.plusJakartaSansTextTheme(
        ThemeData.light().textTheme,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: VeriNewsColors.lightSurface,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.plusJakartaSans(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: VeriNewsColors.lightOnSurface,
          letterSpacing: -0.5,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: BorderSide(
            color: VeriNewsColors.lightOutline.withValues(alpha: 0.2),
            width: 1,
          ),
        ),
        color: Colors.white,
      ),
      chipTheme: ChipThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        labelStyle: GoogleFonts.plusJakartaSans(
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: Colors.white,
        elevation: 3,
        indicatorColor: VeriNewsColors.lightPrimaryContainer,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.plusJakartaSans(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: VeriNewsColors.lightPrimary,
            );
          }
          return GoogleFonts.plusJakartaSans(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: VeriNewsColors.lightOutline,
          );
        }),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.plusJakartaSans(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }

  static ThemeData get darkTheme {
    final baseColorScheme = ColorScheme.fromSeed(
      seedColor: VeriNewsColors.darkPrimary,
      brightness: Brightness.dark,
    ).copyWith(
      surface: VeriNewsColors.darkSurface,
      surfaceContainerLowest: VeriNewsColors.darkSurfaceContainerLowest,
      surfaceContainerLow: VeriNewsColors.darkSurfaceContainerLow,
      surfaceContainer: VeriNewsColors.darkSurfaceContainer,
      surfaceContainerHigh: VeriNewsColors.darkSurfaceContainerHigh,
      surfaceContainerHighest: VeriNewsColors.darkSurfaceContainerHighest,
      primary: VeriNewsColors.darkPrimary,
      primaryContainer: VeriNewsColors.darkPrimaryContainer,
      secondary: VeriNewsColors.darkSecondary,
      secondaryContainer: VeriNewsColors.darkSecondaryContainer,
      onSurface: VeriNewsColors.darkOnSurface,
      outline: VeriNewsColors.darkOutline,
      outlineVariant: VeriNewsColors.darkOutlineVariant,
    );

    return ThemeData(
      useMaterial3: true,
      brightness: Brightness.dark,
      colorScheme: baseColorScheme,
      scaffoldBackgroundColor: VeriNewsColors.darkSurface,
      textTheme: GoogleFonts.plusJakartaSansTextTheme(
        ThemeData.dark().textTheme,
      ),
      appBarTheme: AppBarTheme(
        backgroundColor: VeriNewsColors.darkSurface,
        scrolledUnderElevation: 0,
        centerTitle: false,
        titleTextStyle: GoogleFonts.plusJakartaSans(
          fontSize: 22,
          fontWeight: FontWeight.w700,
          color: VeriNewsColors.darkOnSurface,
          letterSpacing: -0.5,
        ),
      ),
      cardTheme: CardThemeData(
        elevation: 0,
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(24),
          side: const BorderSide(
            color: VeriNewsColors.darkOutlineVariant,
            width: 1,
          ),
        ),
        color: VeriNewsColors.darkSurfaceContainer,
      ),
      chipTheme: ChipThemeData(
        shape: RoundedRectangleBorder(
          borderRadius: BorderRadius.circular(16),
        ),
        labelStyle: GoogleFonts.plusJakartaSans(
          fontSize: 13,
          fontWeight: FontWeight.w600,
        ),
      ),
      navigationBarTheme: NavigationBarThemeData(
        backgroundColor: VeriNewsColors.darkSurfaceContainerLow,
        elevation: 0,
        indicatorColor: VeriNewsColors.darkPrimaryContainer,
        labelTextStyle: WidgetStateProperty.resolveWith((states) {
          if (states.contains(WidgetState.selected)) {
            return GoogleFonts.plusJakartaSans(
              fontSize: 12,
              fontWeight: FontWeight.w700,
              color: VeriNewsColors.darkPrimary,
            );
          }
          return GoogleFonts.plusJakartaSans(
            fontSize: 12,
            fontWeight: FontWeight.w500,
            color: VeriNewsColors.darkOnSurfaceVariant,
          );
        }),
      ),
      elevatedButtonTheme: ElevatedButtonThemeData(
        style: ElevatedButton.styleFrom(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(20),
          ),
          padding: const EdgeInsets.symmetric(horizontal: 24, vertical: 14),
          textStyle: GoogleFonts.plusJakartaSans(
            fontSize: 14,
            fontWeight: FontWeight.w600,
          ),
        ),
      ),
    );
  }
}
