sealed class AppException implements Exception {
  final String message;
  final int? statusCode;

  const AppException(this.message, [this.statusCode]);

  factory AppException.network(String message) = NetworkException;
  factory AppException.unauthorized(String message) = UnauthorizedException;
  factory AppException.forbidden(String message) = ForbiddenException;
  factory AppException.notFound(String message) = NotFoundException;
  factory AppException.badRequest(String message) = BadRequestException;
  factory AppException.validation(String message) = ValidationException;
  factory AppException.conflict(String message) = ConflictException;
  factory AppException.rateLimited(String message) = RateLimitedException;
  factory AppException.server(String message) = ServerException;
  factory AppException.unknown(String message) = UnknownException;

  @override
  String toString() => message;
}

class NetworkException extends AppException {
  const NetworkException(String message) : super(message, 0);
}

class UnauthorizedException extends AppException {
  const UnauthorizedException(String message) : super(message, 401);
}

class ForbiddenException extends AppException {
  const ForbiddenException(String message) : super(message, 403);
}

class NotFoundException extends AppException {
  const NotFoundException(String message) : super(message, 404);
}

class BadRequestException extends AppException {
  const BadRequestException(String message) : super(message, 400);
}

class ValidationException extends AppException {
  const ValidationException(String message) : super(message, 422);
}

class ConflictException extends AppException {
  const ConflictException(String message) : super(message, 409);
}

class RateLimitedException extends AppException {
  const RateLimitedException(String message) : super(message, 429);
}

class ServerException extends AppException {
  const ServerException(String message) : super(message, 500);
}

class UnknownException extends AppException {
  const UnknownException(String message) : super(message);
}
