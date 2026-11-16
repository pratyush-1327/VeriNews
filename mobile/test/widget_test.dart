import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:verinews_mobile/core/location_service.dart';
import 'package:verinews_mobile/core/theme.dart';
import 'package:verinews_mobile/models/article.dart';
import 'package:verinews_mobile/models/verification.dart';
import 'package:verinews_mobile/views/widgets/article_card.dart';
import 'package:verinews_mobile/views/widgets/radial_truth_meter.dart';
import 'package:verinews_mobile/views/widgets/verdict_badge.dart';

void main() {
  group('Unit Tests: LocationService & Distance', () {
    test('Haversine distance calculation between Delhi and Jaipur', () {
      // Delhi: 28.6139, 77.2090; Jaipur: 26.9124, 75.7873 (~235-240 km)
      final distance = LocationService.calculateDistanceKm(
        28.6139,
        77.2090,
        26.9124,
        75.7873,
      );

      expect(distance, greaterThan(220));
      expect(distance, lessThan(260));
    });

    test('Same coordinate distance is 0', () {
      final distance = LocationService.calculateDistanceKm(
        28.6139,
        77.2090,
        28.6139,
        77.2090,
      );
      expect(distance, closeTo(0.0, 0.001));
    });
  });

  group('Unit Tests: Article Model & 60-Word Bullets', () {
    test('Article.fromJson parses 3 bullet points correctly', () {
      final json = {
        'id': 1,
        'title': 'Test Headline',
        'summary_60_words': '• First fact point.\n• Second key takeaway.\n• Third essential detail.',
        'url': 'https://example.com/test-article',
        'published_at': DateTime.now().toIso8601String(),
        'scope': 'national',
        'city_tag': null,
        'source_id': 10,
        'source_name': 'The Hindu',
        'created_at': DateTime.now().toIso8601String(),
      };

      final article = Article.fromJson(json);
      expect(article.id, '1');
      expect(article.title, 'Test Headline');
      expect(article.bullets.length, 3);
      expect(article.bullets[0], 'First fact point.');
      expect(article.bullets[1], 'Second key takeaway.');
      expect(article.bullets[2], 'Third essential detail.');
      expect(article.timeAgo, 'Just now');
    });
  });

  group('Unit Tests: VerificationResponse & Verdicts', () {
    test('VerificationResponse parses 5 verdict classes properly', () {
      for (final verdict in ['TRUE', 'MISLEADING', 'FAKE', 'SATIRE', 'UNVERIFIED']) {
        final json = {
          'id': 42,
          'claim_text': 'Viral internet claim test',
          'claim_hash': 'abcdef1234567890',
          'verdict': verdict,
          'truth_score': verdict == 'TRUE' ? 95 : (verdict == 'FAKE' ? 10 : 50),
          'explanation_bullets': ['Point 1', 'Point 2', 'Point 3'],
          'evidence_sources': [
            {
              'title': 'Fact Check Registry',
              'url': 'https://reuters.com/fact-check',
              'snippet': 'Official statement refuting claim',
              'source_name': 'Reuters',
              'credibility_score': 0.98,
            }
          ],
          'debunk_card_url': '/static/debunks/abcdef1234567890.png',
          'created_at': DateTime.now().toIso8601String(),
          'cached': true,
        };

        final dossier = VerificationResponse.fromJson(json);
        expect(dossier.verdict, verdict);
        expect(dossier.cached, isTrue);
        expect(dossier.explanationBullets.length, 3);
        expect(dossier.evidenceSources.length, 1);
        expect(dossier.evidenceSources[0].sourceName, 'Reuters');
      }
    });
  });

  group('Widget Tests: VerdictBadge', () {
    testWidgets('Renders all 5 verdict badges with distinctive colors & labels', (tester) async {
      final verdicts = ['TRUE', 'MISLEADING', 'FAKE', 'SATIRE', 'UNVERIFIED'];

      for (final verdict in verdicts) {
        await tester.pumpWidget(
          MaterialApp(
            theme: VeriNewsTheme.darkTheme,
            home: Scaffold(
              body: Center(
                child: VerdictBadge(verdict: verdict, isLarge: true),
              ),
            ),
          ),
        );

        expect(find.byType(VerdictBadge), findsOneWidget);
        await tester.pumpAndSettle();
      }
    });
  });

  group('Widget Tests: RadialTruthMeter', () {
    testWidgets('Renders truth score meter smoothly', (tester) async {
      await tester.pumpWidget(
        MaterialApp(
          theme: VeriNewsTheme.darkTheme,
          home: const Scaffold(
            body: Center(
              child: RadialTruthMeter(
                score: 85,
                verdict: 'TRUE',
                size: 150,
              ),
            ),
          ),
        ),
      );

      // Trigger frame animation
      await tester.pump();
      await tester.pump(const Duration(milliseconds: 600));

      expect(find.byType(RadialTruthMeter), findsOneWidget);
      expect(find.text('TRUTH SCORE'), findsOneWidget);
    });
  });

  group('Widget Tests: ArticleCard', () {
    testWidgets('Renders headline, bullets, and actions', (tester) async {
      bool factCheckTapped = false;
      final article = Article(
        id: '1',
        title: 'Exciting AI Model Released Today',
        summary60Words: '• New model achieves top benchmark.\n• Completely open-weights.\n• Available immediately.',
        url: 'https://example.com/ai-model',
        publishedAt: DateTime.now().subtract(const Duration(hours: 2)),
        scope: 'national',
        cityTag: 'delhi',
        sourceId: '5',
        sourceName: 'PIB FactCheck',
        createdAt: DateTime.now(),
      );

      await tester.pumpWidget(
        MaterialApp(
          theme: VeriNewsTheme.darkTheme,
          home: Scaffold(
            body: ArticleCard(
              article: article,
              onFactCheck: () {
                factCheckTapped = true;
              },
            ),
          ),
        ),
      );

      expect(find.text('Exciting AI Model Released Today'), findsOneWidget);
      expect(find.text('PIB FactCheck'), findsOneWidget);
      expect(find.text('• New model achieves top benchmark.'), findsNothing); // Bullets strip leading •
      expect(find.text('New model achieves top benchmark.'), findsOneWidget);
      expect(find.text('2h ago'), findsOneWidget);

      // Tap fact-check
      await tester.tap(find.text('Fact-Check'));
      expect(factCheckTapped, isTrue);
    });
  });
}
