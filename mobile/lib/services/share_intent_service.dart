import 'dart:async';
import 'package:flutter/foundation.dart';
import 'package:receive_sharing_intent/receive_sharing_intent.dart';

class SharedPayload {
  final String? text;
  final String? imagePath;

  const SharedPayload({this.text, this.imagePath});
}

class ShareIntentService extends ChangeNotifier {
  static final ShareIntentService _instance = ShareIntentService._internal();
  factory ShareIntentService() => _instance;
  ShareIntentService._internal();

  StreamSubscription<List<SharedMediaFile>>? _intentSub;
  SharedPayload? _pendingPayload;

  SharedPayload? get pendingPayload => _pendingPayload;

  void clearPendingPayload() {
    _pendingPayload = null;
    notifyListeners();
  }

  /// Initialize listeners for intent sharing while app is running and on cold start
  void initShareListeners() {
    // Listen to media sharing while app is in memory
    _intentSub = ReceiveSharingIntent.instance.getMediaStream().listen(
      (List<SharedMediaFile> value) {
        _handleSharedFiles(value);
      },
      onError: (err) {
        debugPrint('[ShareIntentService] getMediaStream error: $err');
      },
    );

    // Get the media shared when the app is launched from closed state
    ReceiveSharingIntent.instance.getInitialMedia().then((List<SharedMediaFile> value) {
      if (value.isNotEmpty) {
        _handleSharedFiles(value);
      }
    }).catchError((err) {
      debugPrint('[ShareIntentService] getInitialMedia error: $err');
    });
  }

  void _handleSharedFiles(List<SharedMediaFile> files) {
    if (files.isEmpty) return;

    for (final file in files) {
      if (file.type == SharedMediaType.text || file.type == SharedMediaType.url) {
        final textContent = file.path;
        if (textContent.isNotEmpty) {
          _pendingPayload = SharedPayload(text: textContent);
          notifyListeners();
          return;
        }
      } else if (file.type == SharedMediaType.image) {
        _pendingPayload = SharedPayload(imagePath: file.path);
        notifyListeners();
        return;
      }
    }
  }

  void disposeListeners() {
    _intentSub?.cancel();
  }
}
