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
  const NetworkException(super.message) : super(0);
}

class UnauthorizedException extends AppException {
  const UnauthorizedException(super.message) : super(401);
}

class ForbiddenException extends AppException {
  const ForbiddenException(super.message) : super(403);
}

class NotFoundException extends AppException {
  const NotFoundException(super.message) : super(404);
}

class BadRequestException extends AppException {
  const BadRequestException(super.message) : super(400);
}

class ValidationException extends AppException {
  const ValidationException(super.message) : super(422);
}

class ConflictException extends AppException {
  const ConflictException(super.message) : super(409);
}

class RateLimitedException extends AppException {
  const RateLimitedException(super.message) : super(429);
}

class ServerException extends AppException {
  const ServerException(super.message) : super(500);
}

class UnknownException extends AppException {
  const UnknownException(super.message);
}
