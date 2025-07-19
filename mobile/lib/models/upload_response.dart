class UploadResponse {
  final bool success;
  final String message;
  final String? imageId;
  final String? imageUrl;
  final String? poetry;
  final String? title;
  final DateTime? createdAt;
  final Map<String, dynamic>? metadata;

  UploadResponse({
    required this.success,
    required this.message,
    this.imageId,
    this.imageUrl,
    this.poetry,
    this.title,
    this.createdAt,
    this.metadata,
  });

  factory UploadResponse.fromJson(Map<String, dynamic> json) {
    return UploadResponse(
      success: json['success'] ?? false,
      message: json['message'] ?? '',
      imageId: json['image_id'],
      imageUrl: json['image_url'],
      poetry: json['poetry'],
      title: json['title'],
      createdAt: json['created_at'] != null 
          ? DateTime.parse(json['created_at'])
          : null,
      metadata: json['metadata'],
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'success': success,
      'message': message,
      if (imageId != null) 'image_id': imageId,
      if (imageUrl != null) 'image_url': imageUrl,
      if (poetry != null) 'poetry': poetry,
      if (title != null) 'title': title,
      if (createdAt != null) 'created_at': createdAt!.toIso8601String(),
      if (metadata != null) 'metadata': metadata,
    };
  }

  UploadResponse copyWith({
    bool? success,
    String? message,
    String? imageId,
    String? imageUrl,
    String? poetry,
    String? title,
    DateTime? createdAt,
    Map<String, dynamic>? metadata,
  }) {
    return UploadResponse(
      success: success ?? this.success,
      message: message ?? this.message,
      imageId: imageId ?? this.imageId,
      imageUrl: imageUrl ?? this.imageUrl,
      poetry: poetry ?? this.poetry,
      title: title ?? this.title,
      createdAt: createdAt ?? this.createdAt,
      metadata: metadata ?? this.metadata,
    );
  }

  @override
  String toString() {
    return 'UploadResponse(success: $success, message: $message, imageId: $imageId, poetry: $poetry)';
  }

  @override
  bool operator ==(Object other) {
    if (identical(this, other)) return true;
    return other is UploadResponse &&
        other.success == success &&
        other.message == message &&
        other.imageId == imageId &&
        other.imageUrl == imageUrl &&
        other.poetry == poetry &&
        other.title == title &&
        other.createdAt == createdAt;
  }

  @override
  int get hashCode {
    return Object.hash(
      success,
      message,
      imageId,
      imageUrl,
      poetry,
      title,
      createdAt,
    );
  }
}