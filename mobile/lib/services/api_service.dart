import 'dart:io';
import 'package:flutter/foundation.dart';
import 'package:dio/dio.dart';
import 'package:image_picker/image_picker.dart';
import 'package:path/path.dart' as path;
import '../models/upload_response.dart';

class ApiService {
  static final ApiService _instance = ApiService._internal();
  factory ApiService() => _instance;
  ApiService._internal() {
    _initializeDio();
  }

  late Dio _dio;
  
  // 개발 환경에서는 localhost, 프로덕션에서는 실제 서버 주소 사용
  static const String _baseUrl = 'http://localhost:8000';

  void _initializeDio() {
    _dio = Dio(BaseOptions(
      baseUrl: _baseUrl,
      connectTimeout: const Duration(seconds: 30),
      receiveTimeout: const Duration(seconds: 30),
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'application/json',
      },
    ));

    // 요청/응답 로깅 (개발 모드에서만)
    _dio.interceptors.add(LogInterceptor(
      requestBody: true,
      responseBody: true,
      logPrint: (obj) => print(obj),
    ));
  }

  /// 서버 연결 상태 확인
  Future<bool> checkServerConnection() async {
    try {
      final response = await _dio.get('/health');
      return response.statusCode == 200;
    } catch (e) {
      return false;
    }
  }

  /// 이미지 업로드 및 시 생성 요청
  Future<UploadResponse> uploadImageAndGeneratePoetry(
    dynamic imageFile, {
    Function(double)? onProgress,
  }) async {
    try {
      String fileName;
      MultipartFile multipartFile;
      
      if (kIsWeb && imageFile is XFile) {
        // 웹에서는 XFile 처리
        fileName = imageFile.name;
        final bytes = await imageFile.readAsBytes();
        multipartFile = MultipartFile.fromBytes(
          bytes,
          filename: fileName,
        );
      } else if (imageFile is File) {
        // 모바일에서는 File 처리
        fileName = path.basename(imageFile.path);
        multipartFile = await MultipartFile.fromFile(
          imageFile.path,
          filename: fileName,
        );
      } else {
        throw Exception('지원하지 않는 파일 타입입니다.');
      }
      
      // FormData 생성
      final formData = FormData.fromMap({
        'image': multipartFile,
        'timestamp': DateTime.now().millisecondsSinceEpoch.toString(),
      });

      // 업로드 진행률 콜백 설정
      final response = await _dio.post(
        '/api/upload-image',
        data: formData,
        onSendProgress: (sent, total) {
          if (onProgress != null && total > 0) {
            final progress = sent / total;
            onProgress(progress);
          }
        },
      );

      if (response.statusCode == 200) {
        return UploadResponse.fromJson(response.data);
      } else {
        throw ApiException('업로드 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('예상치 못한 오류가 발생했습니다: $e');
    }
  }

  /// 이미지만 업로드 (시 생성 없이)
  Future<UploadResponse> uploadImageOnly(
    dynamic imageFile, {
    Function(double)? onProgress,
  }) async {
    try {
      String fileName;
      MultipartFile multipartFile;
      
      if (kIsWeb && imageFile is XFile) {
        // 웹에서는 XFile 처리
        fileName = imageFile.name;
        final bytes = await imageFile.readAsBytes();
        multipartFile = MultipartFile.fromBytes(
          bytes,
          filename: fileName,
        );
      } else if (imageFile is File) {
        // 모바일에서는 File 처리
        fileName = path.basename(imageFile.path);
        multipartFile = await MultipartFile.fromFile(
          imageFile.path,
          filename: fileName,
        );
      } else {
        throw Exception('지원하지 않는 파일 타입입니다.');
      }
      
      final formData = FormData.fromMap({
        'image': multipartFile,
      });

      final response = await _dio.post(
        '/api/upload',
        data: formData,
        onSendProgress: (sent, total) {
          if (onProgress != null && total > 0) {
            onProgress(sent / total);
          }
        },
      );

      if (response.statusCode == 200) {
        return UploadResponse.fromJson(response.data);
      } else {
        throw ApiException('업로드 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('예상치 못한 오류가 발생했습니다: $e');
    }
  }

  /// 업로드된 이미지로 시 생성 요청
  Future<UploadResponse> generatePoetryFromImageId(String imageId) async {
    try {
      final response = await _dio.post(
        '/api/generate-poetry',
        data: {'image_id': imageId},
      );

      if (response.statusCode == 200) {
        return UploadResponse.fromJson(response.data);
      } else {
        throw ApiException('시 생성 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('예상치 못한 오류가 발생했습니다: $e');
    }
  }

  /// 업로드 기록 조회
  Future<List<UploadResponse>> getUploadHistory({
    int page = 1,
    int limit = 20,
  }) async {
    try {
      final response = await _dio.get(
        '/api/uploads',
        queryParameters: {
          'page': page,
          'limit': limit,
        },
      );

      if (response.statusCode == 200) {
        final List<dynamic> data = response.data['uploads'];
        return data.map((json) => UploadResponse.fromJson(json)).toList();
      } else {
        throw ApiException('업로드 기록 조회 실패: ${response.statusMessage}');
      }
    } on DioException catch (e) {
      throw _handleDioException(e);
    } catch (e) {
      throw ApiException('예상치 못한 오류가 발생했습니다: $e');
    }
  }

  /// Dio 예외 처리
  ApiException _handleDioException(DioException e) {
    switch (e.type) {
      case DioExceptionType.connectionTimeout:
        return ApiException('연결 시간이 초과되었습니다.');
      case DioExceptionType.sendTimeout:
        return ApiException('요청 전송 시간이 초과되었습니다.');
      case DioExceptionType.receiveTimeout:
        return ApiException('응답 수신 시간이 초과되었습니다.');
      case DioExceptionType.badResponse:
        final statusCode = e.response?.statusCode;
        final message = e.response?.data?['message'] ?? '서버 오류';
        return ApiException('서버 오류 ($statusCode): $message');
      case DioExceptionType.cancel:
        return ApiException('요청이 취소되었습니다.');
      case DioExceptionType.connectionError:
        return ApiException('네트워크 연결을 확인해주세요.');
      default:
        return ApiException('알 수 없는 오류가 발생했습니다: ${e.message}');
    }
  }

  /// 베이스 URL 설정 (테스트용)
  void setBaseUrl(String url) {
    _dio.options.baseUrl = url;
  }

  /// 요청 취소를 위한 CancelToken 생성
  CancelToken createCancelToken() {
    return CancelToken();
  }
}

class ApiException implements Exception {
  final String message;
  final int? statusCode;
  
  ApiException(this.message, [this.statusCode]);
  
  @override
  String toString() => 'ApiException: $message';
}