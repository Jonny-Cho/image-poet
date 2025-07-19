import 'package:flutter/material.dart';

void main() {
  runApp(const ImagePoetApp());
}

class ImagePoetApp extends StatelessWidget {
  const ImagePoetApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Image Poet',
      theme: ThemeData(
        colorScheme: ColorScheme.fromSeed(seedColor: Colors.indigo),
        useMaterial3: true,
      ),
      home: const HomePage(),
      debugShowCheckedModeBanner: false,
    );
  }
}

class HomePage extends StatelessWidget {
  const HomePage({super.key});

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Image Poet'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        elevation: 0,
      ),
      body: const Center(
        child: Column(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            Icon(
              Icons.photo_camera,
              size: 80,
              color: Colors.indigo,
            ),
            SizedBox(height: 24),
            Text(
              'Welcome to Image Poet',
              style: TextStyle(
                fontSize: 28,
                fontWeight: FontWeight.bold,
                color: Colors.indigo,
              ),
            ),
            SizedBox(height: 16),
            Text(
              'Transform your images into beautiful poetry',
              style: TextStyle(
                fontSize: 16,
                color: Colors.grey,
              ),
              textAlign: TextAlign.center,
            ),
            SizedBox(height: 48),
            Text(
              'Tap the camera button to get started',
              style: TextStyle(
                fontSize: 14,
                color: Colors.grey,
              ),
            ),
          ],
        ),
      ),
      floatingActionButton: FloatingActionButton(
        onPressed: () {
          // TODO: Implement image picker and poetry generation
          ScaffoldMessenger.of(context).showSnackBar(
            const SnackBar(
              content: Text('Image selection coming soon!'),
            ),
          );
        },
        child: const Icon(Icons.camera_alt),
      ),
    );
  }
}
