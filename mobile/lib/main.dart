import 'package:flutter/material.dart';
import 'core/config.dart';
import 'core/theme.dart';
import 'services/api_service.dart';
import 'services/share_intent_service.dart';
import 'views/home_screen.dart';

void main() async {
  WidgetsFlutterBinding.ensureInitialized();

  // Load user configured backend URL if persisted
  await AppConfig.loadSavedBaseUrl();

  // Initialize Native OS Share Intent listeners
  ShareIntentService().initShareListeners();

  runApp(const VeriNewsApp());
}

class VeriNewsApp extends StatefulWidget {
  const VeriNewsApp({super.key});

  @override
  State<VeriNewsApp> createState() => _VeriNewsAppState();
}

class _VeriNewsAppState extends State<VeriNewsApp> {
  ThemeMode _themeMode = ThemeMode.dark;
  final ApiService _apiService = ApiService();

  void _toggleTheme() {
    setState(() {
      _themeMode = _themeMode == ThemeMode.dark ? ThemeMode.light : ThemeMode.dark;
    });
  }

  @override
  void dispose() {
    ShareIntentService().disposeListeners();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'VeriNews',
      debugShowCheckedModeBanner: false,
      theme: VeriNewsTheme.lightTheme,
      darkTheme: VeriNewsTheme.darkTheme,
      themeMode: _themeMode,
      home: HomeScreen(
        apiService: _apiService,
        onToggleTheme: _toggleTheme,
        isDarkMode: _themeMode == ThemeMode.dark,
      ),
    );
  }
}
