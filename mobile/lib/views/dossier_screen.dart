import 'package:cached_network_image/cached_network_image.dart';
import 'package:flutter/material.dart';
import 'package:google_fonts/google_fonts.dart';
import 'package:share_plus/share_plus.dart';
import 'package:url_launcher/url_launcher.dart';
import '../../core/theme.dart';
import '../../models/verification.dart';
import '../../services/api_service.dart';
import 'widgets/radial_truth_meter.dart';
import 'widgets/verdict_badge.dart';

class DossierScreen extends StatelessWidget {
  final VerificationResponse dossier;
  final ApiService apiService;

  const DossierScreen({
    super.key,
    required this.dossier,
    required this.apiService,
  });

  Future<void> _launchUrl(String url) async {
    final uri = Uri.tryParse(url);
    if (uri != null && await canLaunchUrl(uri)) {
      await launchUrl(uri, mode: LaunchMode.externalApplication);
    }
  }

  void _shareDebunk(BuildContext context) {
    final debunkUrl = apiService.getDebunkCardFullUrl(dossier.debunkCardUrl);
    final bulletsFormatted = dossier.explanationBullets.map((b) => '• $b').join('\n');

    final shareText = '''
🔍 [VeriNews Fact-Check Dossier]
Claim: "${dossier.claimText}"

Verdict: ${dossier.verdictDisplay} (${dossier.truthScore}% Truth Score)

Key Facts:
$bulletsFormatted

${debunkUrl != null ? 'Debunk Card: $debunkUrl\n' : ''}Checked by VeriNews AI Fact-Checking Engine.
''';

    SharePlus.instance.share(
      ShareParams(
        text: shareText,
        subject: 'VeriNews Fact Check: ${dossier.verdictDisplay}',
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final isDark = theme.brightness == Brightness.dark;
    final debunkCardFullUrl = apiService.getDebunkCardFullUrl(dossier.debunkCardUrl);

    return Scaffold(
      appBar: AppBar(
        title: const Text('Truth Dossier'),
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_rounded),
          onPressed: () => Navigator.pop(context),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_rounded),
            tooltip: 'Share Debunk',
            onPressed: () => _shareDebunk(context),
          ),
        ],
      ),
      body: SingleChildScrollView(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Hero Verdict Card with Radial Meter
            Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        VerdictBadge(verdict: dossier.verdict, isLarge: true),
                        if (dossier.cached)
                          Container(
                            padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
                            decoration: BoxDecoration(
                              color: theme.colorScheme.primaryContainer.withValues(alpha: 0.5),
                              borderRadius: BorderRadius.circular(12),
                            ),
                            child: Row(
                              children: [
                                Icon(Icons.bolt_rounded, size: 14, color: theme.colorScheme.primary),
                                const SizedBox(width: 4),
                                Text(
                                  'Cached',
                                  style: GoogleFonts.plusJakartaSans(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: theme.colorScheme.primary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                      ],
                    ),
                    const SizedBox(height: 24),

                    // Animated Radial Truth Meter
                    Center(
                      child: RadialTruthMeter(
                        score: dossier.truthScore,
                        verdict: dossier.verdict,
                        size: 160,
                      ),
                    ),
                    const SizedBox(height: 16),

                    Text(
                      'Automated multi-source NLI verification',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize: 12,
                        color: isDark ? Colors.white54 : Colors.black45,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Original Claim Box
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.chat_bubble_outline_rounded,
                          size: 18,
                          color: theme.colorScheme.primary,
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'INVESTIGATED CLAIM',
                          style: GoogleFonts.plusJakartaSans(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                            color: theme.colorScheme.primary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 12),
                    Text(
                      '"${dossier.claimText}"',
                      style: GoogleFonts.plusJakartaSans(
                        fontSize: 16,
                        fontWeight: FontWeight.w600,
                        fontStyle: FontStyle.italic,
                        height: 1.4,
                      ),
                    ),
                    const SizedBox(height: 10),
                    Text(
                      'Hash: ${dossier.claimHash.substring(0, 16)}...',
                      style: GoogleFonts.robotoMono(
                        fontSize: 11,
                        color: isDark ? Colors.white38 : Colors.black38,
                      ),
                    ),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Key Factual Breakdown
            Card(
              child: Padding(
                padding: const EdgeInsets.all(20),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      children: [
                        Icon(
                          Icons.fact_check_outlined,
                          size: 18,
                          color: VeriNewsColors.getVerdictColor(dossier.verdict, isDark: isDark),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          'FACTUAL EXPLANATION',
                          style: GoogleFonts.plusJakartaSans(
                            fontSize: 12,
                            fontWeight: FontWeight.w700,
                            letterSpacing: 0.8,
                            color: VeriNewsColors.getVerdictColor(dossier.verdict, isDark: isDark),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),
                    ...dossier.explanationBullets.map((bullet) => Padding(
                          padding: const EdgeInsets.only(bottom: 10),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                margin: const EdgeInsets.only(top: 7, right: 10),
                                width: 6,
                                height: 6,
                                decoration: BoxDecoration(
                                  shape: BoxShape.circle,
                                  color: VeriNewsColors.getVerdictColor(dossier.verdict, isDark: isDark),
                                ),
                              ),
                              Expanded(
                                child: Text(
                                  bullet,
                                  style: GoogleFonts.plusJakartaSans(
                                    fontSize: 14,
                                    height: 1.45,
                                    color: isDark ? Colors.white.withValues(alpha: 0.88) : Colors.black87,
                                  ),
                                ),
                              ),
                            ],
                          ),
                        )),
                  ],
                ),
              ),
            ),
            const SizedBox(height: 16),

            // Evidence Citations
            if (dossier.evidenceSources.isNotEmpty) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.link_rounded,
                            size: 18,
                            color: theme.colorScheme.primary,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'CITATION GRAPH & EVIDENCE',
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.8,
                              color: theme.colorScheme.primary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      ...dossier.evidenceSources.map((source) => Container(
                            margin: const EdgeInsets.only(bottom: 12),
                            padding: const EdgeInsets.all(12),
                            decoration: BoxDecoration(
                              color: isDark ? Colors.white.withValues(alpha: 0.04) : Colors.black.withValues(alpha: 0.03),
                              borderRadius: BorderRadius.circular(16),
                              border: Border.all(
                                color: isDark ? Colors.white12 : Colors.black12,
                              ),
                            ),
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Row(
                                  children: [
                                    Expanded(
                                      child: Text(
                                        source.sourceName,
                                        style: GoogleFonts.plusJakartaSans(
                                          fontWeight: FontWeight.w700,
                                          fontSize: 13,
                                          color: theme.colorScheme.primary,
                                        ),
                                      ),
                                    ),
                                    Container(
                                      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
                                      decoration: BoxDecoration(
                                        color: Colors.green.withValues(alpha: 0.15),
                                        borderRadius: BorderRadius.circular(8),
                                      ),
                                      child: Text(
                                        '${(source.credibilityScore * 100).toInt()}% trust',
                                        style: GoogleFonts.plusJakartaSans(
                                          fontSize: 10,
                                          fontWeight: FontWeight.w700,
                                          color: Colors.green,
                                        ),
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 6),
                                Text(
                                  source.title,
                                  style: GoogleFonts.plusJakartaSans(
                                    fontWeight: FontWeight.w600,
                                    fontSize: 14,
                                  ),
                                ),
                                if (source.snippet.isNotEmpty) ...[
                                  const SizedBox(height: 6),
                                  Text(
                                    source.snippet,
                                    maxLines: 3,
                                    overflow: TextOverflow.ellipsis,
                                    style: GoogleFonts.plusJakartaSans(
                                      fontSize: 12,
                                      color: isDark ? Colors.white60 : Colors.black54,
                                      height: 1.35,
                                    ),
                                  ),
                                ],
                                const SizedBox(height: 8),
                                InkWell(
                                  onTap: () => _launchUrl(source.url),
                                  child: Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      Text(
                                        'Open accredited source',
                                        style: GoogleFonts.plusJakartaSans(
                                          fontSize: 12,
                                          fontWeight: FontWeight.w700,
                                          color: theme.colorScheme.primary,
                                        ),
                                      ),
                                      const SizedBox(width: 4),
                                      Icon(
                                        Icons.open_in_new_rounded,
                                        size: 14,
                                        color: theme.colorScheme.primary,
                                      ),
                                    ],
                                  ),
                                ),
                              ],
                            ),
                          )),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 16),
            ],

            // Branded Debunk Card PNG Preview
            if (debunkCardFullUrl != null) ...[
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(20),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Row(
                        children: [
                          Icon(
                            Icons.image_outlined,
                            size: 18,
                            color: theme.colorScheme.primary,
                          ),
                          const SizedBox(width: 8),
                          Text(
                            'SHAREABLE DEBUNK CARD',
                            style: GoogleFonts.plusJakartaSans(
                              fontSize: 12,
                              fontWeight: FontWeight.w700,
                              letterSpacing: 0.8,
                              color: theme.colorScheme.primary,
                            ),
                          ),
                        ],
                      ),
                      const SizedBox(height: 14),
                      ClipRRect(
                        borderRadius: BorderRadius.circular(16),
                        child: CachedNetworkImage(
                          imageUrl: debunkCardFullUrl,
                          width: double.infinity,
                          fit: BoxFit.contain,
                          placeholder: (context, url) => Container(
                            height: 240,
                            color: isDark ? Colors.white10 : Colors.black12,
                            child: const Center(
                              child: CircularProgressIndicator(strokeWidth: 2),
                            ),
                          ),
                          errorWidget: (context, url, err) => Container(
                            height: 100,
                            color: isDark ? Colors.white10 : Colors.black12,
                            child: const Center(child: Text('Debunk card preview unavailable')),
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
              const SizedBox(height: 24),
            ],

            // Share to WhatsApp / Socials Button
            SizedBox(
              width: double.infinity,
              height: 56,
              child: ElevatedButton.icon(
                onPressed: () => _shareDebunk(context),
                icon: const Icon(Icons.share_rounded, size: 20),
                label: Text(
                  'Share Debunk to WhatsApp',
                  style: GoogleFonts.plusJakartaSans(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: theme.colorScheme.primary,
                  foregroundColor: theme.colorScheme.onPrimary,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(20),
                  ),
                  elevation: 2,
                ),
              ),
            ),
            const SizedBox(height: 32),
          ],
        ),
      ),
    );
  }
}
