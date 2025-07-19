import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'widgets/image_picker_widget.dart';
import 'widgets/upload_progress_widget.dart';
import 'models/upload_response.dart';

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

class HomePage extends StatefulWidget {
  const HomePage({super.key});

  @override
  State<HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<HomePage> {
  List<UploadResponse> _recentPoetry = [];
  bool _isLoading = false;

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Image Poet'),
        backgroundColor: Theme.of(context).colorScheme.inversePrimary,
        elevation: 0,
        actions: [
          if (_recentPoetry.isNotEmpty)
            IconButton(
              icon: const Icon(Icons.history),
              onPressed: _showPoetryHistory,
            ),
        ],
      ),
      body: _buildBody(),
      floatingActionButton: FloatingActionButton(
        onPressed: _isLoading ? null : _handleImageSelection,
        child: _isLoading 
          ? const SizedBox(
              width: 20,
              height: 20,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                valueColor: AlwaysStoppedAnimation<Color>(Colors.white),
              ),
            )
          : const Icon(Icons.camera_alt),
      ),
    );
  }

  Widget _buildBody() {
    if (_recentPoetry.isEmpty) {
      return const Center(
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
      );
    }

    return ListView.builder(
      padding: const EdgeInsets.all(16),
      itemCount: _recentPoetry.length,
      itemBuilder: (context, index) {
        final poetry = _recentPoetry[index];
        return _buildPoetryCard(poetry);
      },
    );
  }

  Widget _buildPoetryCard(UploadResponse poetry) {
    return Card(
      margin: const EdgeInsets.only(bottom: 16),
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            if (poetry.title != null) ...[
              Text(
                poetry.title!,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 8),
            ],
            if (poetry.poetry != null) ...[
              Text(
                poetry.poetry!,
                style: Theme.of(context).textTheme.bodyMedium,
              ),
              const SizedBox(height: 12),
            ],
            if (poetry.createdAt != null)
              Text(
                _formatDate(poetry.createdAt!),
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey[600],
                ),
              ),
          ],
        ),
      ),
    );
  }

  String _formatDate(DateTime date) {
    final now = DateTime.now();
    final difference = now.difference(date);

    if (difference.inDays > 0) {
      return '${difference.inDays}일 전';
    } else if (difference.inHours > 0) {
      return '${difference.inHours}시간 전';
    } else if (difference.inMinutes > 0) {
      return '${difference.inMinutes}분 전';
    } else {
      return '방금 전';
    }
  }

  Future<void> _handleImageSelection() async {
    await showImagePickerBottomSheet(
      context,
      onImageSelected: _handleImageUpload,
      title: '이미지를 선택하세요',
      subtitle: '선택한 이미지로 아름다운 시를 만들어드립니다',
    );
  }

  Future<void> _handleImageUpload(dynamic imageFile) async {
    setState(() {
      _isLoading = true;
    });

    try {
      final result = await showUploadProgressDialog(
        context,
        imageFile: imageFile,
      );

      if (result != null && result.success) {
        setState(() {
          _recentPoetry.insert(0, result);
          if (_recentPoetry.length > 10) {
            _recentPoetry = _recentPoetry.take(10).toList();
          }
        });

        _showSuccessDialog(result);
      }
    } catch (e) {
      _showErrorSnackBar('업로드 중 오류가 발생했습니다: $e');
    } finally {
      setState(() {
        _isLoading = false;
      });
    }
  }

  void _showSuccessDialog(UploadResponse result) {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('성공!'),
        content: Text(result.message),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('확인'),
          ),
        ],
      ),
    );
  }

  void _showErrorSnackBar(String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }

  void _showPoetryHistory() {
    showDialog(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text('시 기록'),
        content: SizedBox(
          width: double.maxFinite,
          child: ListView.builder(
            shrinkWrap: true,
            itemCount: _recentPoetry.length,
            itemBuilder: (context, index) {
              final poetry = _recentPoetry[index];
              return ListTile(
                title: Text(poetry.title ?? '제목 없음'),
                subtitle: Text(
                  poetry.poetry ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                trailing: Text(_formatDate(poetry.createdAt ?? DateTime.now())),
              );
            },
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('닫기'),
          ),
        ],
      ),
    );
  }
}
