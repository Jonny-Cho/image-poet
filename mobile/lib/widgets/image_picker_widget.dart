import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/image_service.dart';

class ImagePickerWidget extends StatelessWidget {
  final Function(dynamic) onImageSelected;
  final String? title;
  final String? subtitle;

  const ImagePickerWidget({
    super.key,
    required this.onImageSelected,
    this.title,
    this.subtitle,
  });

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (title != null) ...[
            Text(
              title!,
              style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                fontWeight: FontWeight.bold,
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
          ],
          if (subtitle != null) ...[
            Text(
              subtitle!,
              style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                color: Colors.grey[600],
              ),
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 24),
          ],
          Row(
            children: [
              Expanded(
                child: _buildOptionCard(
                  context,
                  icon: Icons.camera_alt,
                  title: '카메라',
                  subtitle: '사진 촬영',
                  onTap: () => _pickFromCamera(context),
                ),
              ),
              const SizedBox(width: 16),
              Expanded(
                child: _buildOptionCard(
                  context,
                  icon: Icons.photo_library,
                  title: '갤러리',
                  subtitle: '사진 선택',
                  onTap: () => _pickFromGallery(context),
                ),
              ),
            ],
          ),
        ],
      ),
    );
  }

  Widget _buildOptionCard(
    BuildContext context, {
    required IconData icon,
    required String title,
    required String subtitle,
    required VoidCallback onTap,
  }) {
    return Card(
      elevation: 2,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(12),
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                icon,
                size: 48,
                color: Theme.of(context).primaryColor,
              ),
              const SizedBox(height: 12),
              Text(
                title,
                style: Theme.of(context).textTheme.titleMedium?.copyWith(
                  fontWeight: FontWeight.bold,
                ),
              ),
              const SizedBox(height: 4),
              Text(
                subtitle,
                style: Theme.of(context).textTheme.bodySmall?.copyWith(
                  color: Colors.grey[600],
                ),
                textAlign: TextAlign.center,
              ),
            ],
          ),
        ),
      ),
    );
  }

  Future<void> _pickFromCamera(BuildContext context) async {
    try {
      final imageService = ImageService();
      final dynamic imageFile = await imageService.pickImageFromCamera();
      
      if (imageFile != null) {
        final bool isValid = await imageService.isValidImageFile(imageFile);
        if (!isValid) {
          _showErrorSnackBar(context, '이미지 파일이 유효하지 않거나 크기가 너무 큽니다 (최대 10MB)');
          return;
        }
        
        Navigator.of(context).pop(); // 다이얼로그 닫기
        onImageSelected(imageFile);
      }
    } catch (e) {
      _showErrorSnackBar(context, '카메라에서 이미지를 가져올 수 없습니다: $e');
    }
  }

  Future<void> _pickFromGallery(BuildContext context) async {
    try {
      final imageService = ImageService();
      final dynamic imageFile = await imageService.pickImageFromGallery();
      
      if (imageFile != null) {
        final bool isValid = await imageService.isValidImageFile(imageFile);
        if (!isValid) {
          _showErrorSnackBar(context, '이미지 파일이 유효하지 않거나 크기가 너무 큽니다 (최대 10MB)');
          return;
        }
        
        Navigator.of(context).pop(); // 다이얼로그 닫기
        onImageSelected(imageFile);
      }
    } catch (e) {
      _showErrorSnackBar(context, '갤러리에서 이미지를 가져올 수 없습니다: $e');
    }
  }

  void _showErrorSnackBar(BuildContext context, String message) {
    ScaffoldMessenger.of(context).showSnackBar(
      SnackBar(
        content: Text(message),
        backgroundColor: Colors.red,
        duration: const Duration(seconds: 3),
      ),
    );
  }
}

/// 이미지 선택 다이얼로그를 표시하는 헬퍼 함수
Future<void> showImagePickerDialog(
  BuildContext context, {
  required Function(dynamic) onImageSelected,
  String? title,
  String? subtitle,
}) {
  return showDialog(
    context: context,
    builder: (context) => Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: ImagePickerWidget(
        onImageSelected: onImageSelected,
        title: title ?? '이미지 선택',
        subtitle: subtitle ?? '카메라로 촬영하거나 갤러리에서 선택하세요',
      ),
    ),
  );
}

/// 바텀시트로 이미지 선택 옵션을 표시하는 헬퍼 함수
Future<void> showImagePickerBottomSheet(
  BuildContext context, {
  required Function(dynamic) onImageSelected,
  String? title,
  String? subtitle,
}) {
  return showModalBottomSheet(
    context: context,
    shape: const RoundedRectangleBorder(
      borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
    ),
    builder: (context) => SafeArea(
      child: ImagePickerWidget(
        onImageSelected: onImageSelected,
        title: title ?? '이미지 선택',
        subtitle: subtitle ?? '카메라로 촬영하거나 갤러리에서 선택하세요',
      ),
    ),
  );
}