import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path_provider/path_provider.dart';
import 'package:path/path.dart' as path;

class ImageService {
  static final ImageService _instance = ImageService._internal();
  factory ImageService() => _instance;
  ImageService._internal();

  final ImagePicker _picker = ImagePicker();

  /// 카메라에서 이미지 촬영
  Future<dynamic> pickImageFromCamera() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.camera,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      if (image != null) {
        if (kIsWeb) {
          return image; // 웹에서는 XFile 반환
        } else {
          return File(image.path); // 모바일에서는 File 반환
        }
      }
      return null;
    } catch (e) {
      throw ImagePickerException('카메라에서 이미지를 가져올 수 없습니다: $e');
    }
  }

  /// 갤러리에서 이미지 선택
  Future<dynamic> pickImageFromGallery() async {
    try {
      final XFile? image = await _picker.pickImage(
        source: ImageSource.gallery,
        maxWidth: 1920,
        maxHeight: 1080,
        imageQuality: 85,
      );

      if (image != null) {
        if (kIsWeb) {
          return image; // 웹에서는 XFile 반환
        } else {
          return File(image.path); // 모바일에서는 File 반환
        }
      }
      return null;
    } catch (e) {
      throw ImagePickerException('갤러리에서 이미지를 가져올 수 없습니다: $e');
    }
  }

  /// 이미지 선택 옵션 표시
  Future<File?> showImageSourceDialog({
    required Future<void> Function() onCameraPressed,
    required Future<void> Function() onGalleryPressed,
  }) async {
    // UI 컴포넌트에서 처리할 예정
    return null;
  }

  /// 이미지를 임시 디렉토리에 저장
  Future<File> saveImageToTemp(File imageFile) async {
    try {
      final Directory tempDir = await getTemporaryDirectory();
      final String fileName = 'image_${DateTime.now().millisecondsSinceEpoch}.jpg';
      final String tempPath = path.join(tempDir.path, fileName);
      
      return await imageFile.copy(tempPath);
    } catch (e) {
      throw ImageProcessingException('이미지 저장 중 오류가 발생했습니다: $e');
    }
  }

  /// 이미지 파일 크기 확인 (MB 단위) - 플랫폼별 처리
  Future<double> getImageSizeMB(dynamic imageFile) async {
    if (kIsWeb && imageFile is XFile) {
      final Uint8List bytes = await imageFile.readAsBytes();
      return bytes.length / (1024 * 1024);
    } else if (imageFile is File) {
      final int sizeInBytes = imageFile.lengthSync();
      return sizeInBytes / (1024 * 1024);
    }
    return 0.0;
  }

  /// 이미지 파일 유효성 검사 - 플랫폼별 처리
  Future<bool> isValidImageFile(dynamic imageFile) async {
    String extension;
    String filePath;
    
    if (kIsWeb && imageFile is XFile) {
      extension = path.extension(imageFile.name).toLowerCase();
      filePath = imageFile.name;
    } else if (imageFile is File) {
      extension = path.extension(imageFile.path).toLowerCase();
      filePath = imageFile.path;
    } else {
      return false;
    }
    
    const List<String> validExtensions = ['.jpg', '.jpeg', '.png', '.webp'];
    final double sizeMB = await getImageSizeMB(imageFile);
    
    print('🔍 Image validation debug:');
    print('  - File path: $filePath');
    print('  - Extension: $extension');
    print('  - Size: ${sizeMB.toStringAsFixed(2)} MB');
    print('  - Valid extension: ${validExtensions.contains(extension)}');
    print('  - Size OK: ${sizeMB <= 10}');
    print('  - Platform: ${kIsWeb ? "Web" : "Mobile"}');
    
    final isValid = validExtensions.contains(extension) && sizeMB <= 10;
    print('  - Final result: $isValid');
    
    return isValid;
  }

  /// 임시 파일 정리
  Future<void> cleanupTempFiles() async {
    try {
      final Directory tempDir = await getTemporaryDirectory();
      final List<FileSystemEntity> files = tempDir.listSync();
      
      for (final file in files) {
        if (file is File && file.path.contains('image_')) {
          await file.delete();
        }
      }
    } catch (e) {
      // 정리 실패는 치명적이지 않음
      print('임시 파일 정리 중 오류: $e');
    }
  }
}

class ImagePickerException implements Exception {
  final String message;
  ImagePickerException(this.message);
  
  @override
  String toString() => 'ImagePickerException: $message';
}

class ImageProcessingException implements Exception {
  final String message;
  ImageProcessingException(this.message);
  
  @override
  String toString() => 'ImageProcessingException: $message';
}