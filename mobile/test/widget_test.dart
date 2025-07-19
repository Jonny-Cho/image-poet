// This is a basic Flutter widget test.
//
// To perform an interaction with a widget in your test, use the WidgetTester
// utility in the flutter_test package. For example, you can send tap and scroll
// gestures. You can also use WidgetTester to find child widgets in the widget
// tree, read text, and verify that the values of widget properties are correct.

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';

import 'package:image_poet/main.dart';

void main() {
  testWidgets('Image Poet app smoke test', (WidgetTester tester) async {
    // Build our app and trigger a frame.
    await tester.pumpWidget(const ImagePoetApp());

    // Verify that welcome message is displayed.
    expect(find.text('Welcome to Image Poet'), findsOneWidget);
    expect(find.text('Transform your images into beautiful poetry'), findsOneWidget);

    // Verify that camera icon is present.
    expect(find.byIcon(Icons.photo_camera), findsOneWidget);

    // Tap the camera button and verify snackbar appears.
    await tester.tap(find.byIcon(Icons.camera_alt));
    await tester.pump();

    // Verify that snackbar message appears.
    expect(find.text('Image selection coming soon!'), findsOneWidget);
  });
}
