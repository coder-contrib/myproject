class PaginatedResponse<T> {
  final List<T> items;
  final int total;
  final int page;
  final int size;
  final int pages;

  const PaginatedResponse({
    required this.items,
    required this.total,
    required this.page,
    required this.size,
    required this.pages,
  });

  bool get hasNext => page < pages;
  bool get hasPrevious => page > 1;

  factory PaginatedResponse.fromJson(
    Map<String, dynamic> json,
    T Function(Map<String, dynamic>) fromJsonT,
  ) => PaginatedResponse(
    items: (json['items'] as List<dynamic>)
        .map((e) => fromJsonT(e as Map<String, dynamic>))
        .toList(),
    total: json['total'] ?? 0,
    page: json['page'] ?? 1,
    size: json['size'] ?? 20,
    pages: json['pages'] ?? 1,
  );
}
