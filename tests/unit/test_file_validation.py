"""Unit tests for file validation."""
import pytest


@pytest.mark.unit
class TestFileValidator:
    def test_validate_valid_extension(self):
        from app.files.validation import FileValidator

        validator = FileValidator()
        assert validator.validate_extension("document.pdf") is True
        assert validator.validate_extension("image.png") is True
        assert validator.validate_extension("data.xlsx") is True

    def test_validate_invalid_extension(self):
        from app.files.validation import FileValidator

        validator = FileValidator()
        assert validator.validate_extension("script.exe") is False
        assert validator.validate_extension("malware.bat") is False
        assert validator.validate_extension("hack.sh") is False

    def test_validate_double_extension(self):
        from app.files.validation import FileValidator

        validator = FileValidator()
        assert validator.validate_extension("file.pdf.exe") is False
        assert validator.validate_extension("image.jpg.php") is False

    def test_validate_file_size_within_limit(self):
        from app.files.validation import FileValidator

        validator = FileValidator(max_size_mb=10)
        assert validator.validate_size(5 * 1024 * 1024) is True

    def test_validate_file_size_exceeds_limit(self):
        from app.files.validation import FileValidator

        validator = FileValidator(max_size_mb=10)
        assert validator.validate_size(15 * 1024 * 1024) is False

    def test_validate_path_traversal(self):
        from app.files.validation import FileValidator

        validator = FileValidator()
        assert validator.validate_filename("../etc/passwd") is False
        assert validator.validate_filename("..\\windows\\system32") is False
        assert validator.validate_filename("/absolute/path.txt") is False

    def test_validate_safe_filename(self):
        from app.files.validation import FileValidator

        validator = FileValidator()
        assert validator.validate_filename("my-document.pdf") is True
        assert validator.validate_filename("report_2026.xlsx") is True


@pytest.mark.unit
class TestMimeTypeValidator:
    def test_detect_png(self):
        from app.files.validation import MimeTypeValidator

        validator = MimeTypeValidator()
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert validator.detect_mime(png_header) == "image/png"

    def test_detect_jpeg(self):
        from app.files.validation import MimeTypeValidator

        validator = MimeTypeValidator()
        jpeg_header = b"\xff\xd8\xff\xe0" + b"\x00" * 100
        assert validator.detect_mime(jpeg_header) == "image/jpeg"

    def test_detect_pdf(self):
        from app.files.validation import MimeTypeValidator

        validator = MimeTypeValidator()
        pdf_header = b"%PDF-1.4" + b"\x00" * 100
        assert validator.detect_mime(pdf_header) == "application/pdf"

    def test_validate_mime_matches_extension(self):
        from app.files.validation import MimeTypeValidator

        validator = MimeTypeValidator()
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert validator.validate(png_header, "image.png") is True

    def test_validate_mime_mismatch(self):
        from app.files.validation import MimeTypeValidator

        validator = MimeTypeValidator()
        png_header = b"\x89PNG\r\n\x1a\n" + b"\x00" * 100
        assert validator.validate(png_header, "image.jpg") is False
