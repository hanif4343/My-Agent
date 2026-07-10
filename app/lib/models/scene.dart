// lib/models/scene.dart

class Scene {
  final String id;
  final String title;
  final int durationSeconds;
  final String imagePath;

  Scene({
    required this.id,
    required this.title,
    required this.durationSeconds,
    required this.imagePath,
  });

  /// Creates a [Scene] object from a JSON object.
  factory Scene.fromJson(Map<String, dynamic> json) {
    return Scene(
      id: json['id'] as String,
      title: json['title'] as String,
      durationSeconds: json['durationSeconds'] as int,
      imagePath: json['imagePath'] as String,
    );
  }

  /// Converts a [Scene] object to a JSON object.
  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'title': title,
      'durationSeconds': durationSeconds,
      'imagePath': imagePath,
    };
  }
}
