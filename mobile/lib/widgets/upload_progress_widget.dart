import 'dart:io';
import 'dart:typed_data';
import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import '../services/api_service.dart';
import '../models/upload_response.dart';

enum UploadState {
  idle,
  uploading,
  processing,
  completed,
  error,
}

class UploadProgressWidget extends StatefulWidget {
  final dynamic imageFile; // File or XFile
  final Function(UploadResponse)? onSuccess;
  final Function(String)? onError;
  final VoidCallback? onCancel;
  final bool showImagePreview;

  const UploadProgressWidget({
    super.key,
    this.imageFile,
    this.onSuccess,
    this.onError,
    this.onCancel,
    this.showImagePreview = true,
  });

  @override
  State<UploadProgressWidget> createState() => _UploadProgressWidgetState();
}

class _UploadProgressWidgetState extends State<UploadProgressWidget>
    with TickerProviderStateMixin {
  UploadState _state = UploadState.idle;
  double _progress = 0.0;
  String _statusMessage = '';
  UploadResponse? _result;
  
  late AnimationController _rotationController;
  late AnimationController _pulseController;
  late Animation<double> _pulseAnimation;

  @override
  void initState() {
    super.initState();
    _initAnimations();
    if (widget.imageFile != null) {
      _startUpload();
    }
  }

  void _initAnimations() {
    _rotationController = AnimationController(
      duration: const Duration(seconds: 2),
      vsync: this,
    );
    
    _pulseController = AnimationController(
      duration: const Duration(milliseconds: 1500),
      vsync: this,
    );
    
    _pulseAnimation = Tween<double>(
      begin: 0.8,
      end: 1.2,
    ).animate(CurvedAnimation(
      parent: _pulseController,
      curve: Curves.easeInOut,
    ));
  }

  @override
  void dispose() {
    _rotationController.dispose();
    _pulseController.dispose();
    super.dispose();
  }

  Future<void> _startUpload() async {
    if (widget.imageFile == null) return;

    setState(() {
      _state = UploadState.uploading;
      _statusMessage = '이미지 업로드 중...';
      _progress = 0.0;
    });

    _rotationController.repeat();

    try {
      final apiService = ApiService();
      
      // 서버 연결 확인
      final isConnected = await apiService.checkServerConnection();
      if (!isConnected) {
        throw Exception('서버에 연결할 수 없습니다. 네트워크를 확인해주세요.');
      }

      // 이미지 업로드 및 시 생성
      final result = await apiService.uploadImageAndGeneratePoetry(
        widget.imageFile!,
        onProgress: (progress) {
          setState(() {
            _progress = progress;
          });
        },
      );

      setState(() {
        _state = UploadState.processing;
        _statusMessage = '시 생성 중...';
        _progress = 1.0;
      });

      _rotationController.stop();
      _pulseController.repeat(reverse: true);

      // 잠시 대기 (시 생성 시뮬레이션)
      await Future.delayed(const Duration(seconds: 2));

      setState(() {
        _state = UploadState.completed;
        _statusMessage = '완료!';
        _result = result;
      });

      _pulseController.stop();
      widget.onSuccess?.call(result);

    } catch (e) {
      setState(() {
        _state = UploadState.error;
        _statusMessage = e.toString().replaceFirst('Exception: ', '');
      });

      _rotationController.stop();
      _pulseController.stop();
      widget.onError?.call(_statusMessage);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.all(20),
      child: Column(
        mainAxisSize: MainAxisSize.min,
        children: [
          if (widget.showImagePreview && widget.imageFile != null) ...[
            _buildImagePreview(),
            const SizedBox(height: 24),
          ],
          _buildProgressIndicator(),
          const SizedBox(height: 16),
          _buildStatusText(),
          const SizedBox(height: 24),
          _buildActionButtons(),
        ],
      ),
    );
  }

  Widget _buildImagePreview() {
    if (kIsWeb && widget.imageFile is XFile) {
      // 웹에서는 XFile을 사용하여 미리보기
      return FutureBuilder<Uint8List>(
        future: (widget.imageFile as XFile).readAsBytes(),
        builder: (context, snapshot) {
          if (snapshot.hasData) {
            return Container(
              width: 120,
              height: 120,
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(12),
                image: DecorationImage(
                  image: MemoryImage(snapshot.data!),
                  fit: BoxFit.cover,
                ),
              ),
            );
          }
          return Container(
            width: 120,
            height: 120,
            decoration: BoxDecoration(
              borderRadius: BorderRadius.circular(12),
              color: Colors.grey[300],
            ),
            child: const Icon(Icons.image, size: 40),
          );
        },
      );
    } else {
      // 모바일에서는 File 사용
      return Container(
        width: 120,
        height: 120,
        decoration: BoxDecoration(
          borderRadius: BorderRadius.circular(12),
          image: DecorationImage(
            image: FileImage(widget.imageFile as File),
            fit: BoxFit.cover,
          ),
        ),
      );
    }
  }

  Widget _buildProgressIndicator() {
    switch (_state) {
      case UploadState.idle:
        return const Icon(
          Icons.cloud_upload,
          size: 64,
          color: Colors.grey,
        );
      
      case UploadState.uploading:
        return Stack(
          alignment: Alignment.center,
          children: [
            SizedBox(
              width: 80,
              height: 80,
              child: CircularProgressIndicator(
                value: _progress,
                strokeWidth: 6,
                backgroundColor: Colors.grey[300],
                valueColor: AlwaysStoppedAnimation<Color>(
                  Theme.of(context).primaryColor,
                ),
              ),
            ),
            RotationTransition(
              turns: _rotationController,
              child: Icon(
                Icons.cloud_upload,
                size: 32,
                color: Theme.of(context).primaryColor,
              ),
            ),
          ],
        );
      
      case UploadState.processing:
        return AnimatedBuilder(
          animation: _pulseAnimation,
          builder: (context, child) {
            return Transform.scale(
              scale: _pulseAnimation.value,
              child: Icon(
                Icons.auto_awesome,
                size: 64,
                color: Colors.orange,
              ),
            );
          },
        );
      
      case UploadState.completed:
        return const Icon(
          Icons.check_circle,
          size: 64,
          color: Colors.green,
        );
      
      case UploadState.error:
        return const Icon(
          Icons.error,
          size: 64,
          color: Colors.red,
        );
    }
  }

  Widget _buildStatusText() {
    Color textColor;
    switch (_state) {
      case UploadState.idle:
        textColor = Colors.grey;
        break;
      case UploadState.uploading:
      case UploadState.processing:
        textColor = Theme.of(context).primaryColor;
        break;
      case UploadState.completed:
        textColor = Colors.green;
        break;
      case UploadState.error:
        textColor = Colors.red;
        break;
    }

    return Column(
      children: [
        Text(
          _statusMessage,
          style: Theme.of(context).textTheme.titleMedium?.copyWith(
            color: textColor,
            fontWeight: FontWeight.bold,
          ),
          textAlign: TextAlign.center,
        ),
        if (_state == UploadState.uploading) ...[
          const SizedBox(height: 8),
          Text(
            '${(_progress * 100).toInt()}%',
            style: Theme.of(context).textTheme.bodyMedium?.copyWith(
              color: Colors.grey[600],
            ),
          ),
        ],
        if (_state == UploadState.completed && _result?.poetry != null) ...[
          const SizedBox(height: 16),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: BoxDecoration(
              color: Colors.grey[100],
              borderRadius: BorderRadius.circular(12),
            ),
            child: Column(
              children: [
                if (_result!.title != null) ...[
                  Text(
                    _result!.title!,
                    style: Theme.of(context).textTheme.titleSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                    ),
                    textAlign: TextAlign.center,
                  ),
                  const SizedBox(height: 8),
                ],
                Text(
                  _result!.poetry!,
                  style: Theme.of(context).textTheme.bodyMedium,
                  textAlign: TextAlign.center,
                ),
              ],
            ),
          ),
        ],
      ],
    );
  }

  Widget _buildActionButtons() {
    switch (_state) {
      case UploadState.uploading:
      case UploadState.processing:
        return ElevatedButton(
          onPressed: widget.onCancel,
          style: ElevatedButton.styleFrom(
            backgroundColor: Colors.grey,
          ),
          child: const Text('취소'),
        );
      
      case UploadState.error:
        return Row(
          mainAxisAlignment: MainAxisAlignment.spaceEvenly,
          children: [
            ElevatedButton(
              onPressed: _startUpload,
              child: const Text('다시 시도'),
            ),
            OutlinedButton(
              onPressed: widget.onCancel,
              child: const Text('취소'),
            ),
          ],
        );
      
      case UploadState.completed:
        return ElevatedButton(
          onPressed: widget.onCancel,
          child: const Text('확인'),
        );
      
      case UploadState.idle:
      default:
        return const SizedBox.shrink();
    }
  }
}

/// 업로드 진행 다이얼로그를 표시하는 헬퍼 함수
Future<UploadResponse?> showUploadProgressDialog(
  BuildContext context, {
  required dynamic imageFile, // File or XFile
  bool barrierDismissible = false,
}) {
  return showDialog<UploadResponse>(
    context: context,
    barrierDismissible: barrierDismissible,
    builder: (context) => Dialog(
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(16),
      ),
      child: UploadProgressWidget(
        imageFile: imageFile,
        onSuccess: (result) {
          Navigator.of(context).pop(result);
        },
        onError: (error) {
          Navigator.of(context).pop();
          ScaffoldMessenger.of(context).showSnackBar(
            SnackBar(
              content: Text(error),
              backgroundColor: Colors.red,
            ),
          );
        },
        onCancel: () {
          Navigator.of(context).pop();
        },
      ),
    ),
  );
}