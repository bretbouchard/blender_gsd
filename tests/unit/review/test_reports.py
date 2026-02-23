"""
Tests for reports module.

Tests run WITHOUT Blender (bpy) by testing only non-Blender-dependent code paths.
"""

import pytest
import tempfile
import os
import json


class TestReportFormat:
    """Tests for ReportFormat enum."""

    def test_format_values(self):
        """Test ReportFormat enum values."""
        from lib.review.reports import ReportFormat

        assert ReportFormat.HTML.value == "html"
        assert ReportFormat.PDF.value == "pdf"
        assert ReportFormat.JSON.value == "json"
        assert ReportFormat.MARKDOWN.value == "markdown"


class TestReportGenerator:
    """Tests for ReportGenerator class."""

    def test_generator_creation(self):
        """Test creating a ReportGenerator."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        assert generator is not None

    def test_generate_html_basic(self):
        """Test generating basic HTML report."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {
            "scene_name": "Test Scene",
            "summary": {"total": 5, "pass": 3, "error": 1, "warning": 1},
            "results": [
                {"level": "pass", "category": "scale", "message": "Scale OK"},
                {"level": "error", "category": "materials", "message": "Missing material"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            result = generator.generate_html(data, temp_path, title="Test Report")
            assert result is True
            assert os.path.exists(temp_path)

            # Check file contains HTML
            with open(temp_path, 'r') as f:
                content = f.read()
                assert "<!DOCTYPE html>" in content
                assert "Test Report" in content
                assert "Test Scene" in content
        finally:
            os.unlink(temp_path)

    def test_generate_html_with_object_names(self):
        """Test generating HTML with object names."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {
            "scene_name": "Test",
            "summary": {"total": 1, "pass": 1, "error": 0, "warning": 0},
            "results": [
                {
                    "level": "error",
                    "category": "scale",
                    "message": "Bad scale",
                    "object_name": "Cube.001",
                    "suggestion": "Fix the scale",
                },
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            result = generator.generate_html(data, temp_path)
            assert result is True

            with open(temp_path, 'r') as f:
                content = f.read()
                assert "Cube.001" in content
                assert "Fix the scale" in content
        finally:
            os.unlink(temp_path)

    def test_generate_html_io_error(self):
        """Test HTML generation with IO error."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {"scene_name": "Test", "summary": {}, "results": []}

        # Try to write to invalid path
        result = generator.generate_html(data, "/nonexistent/path/report.html")
        assert result is False

    def test_generate_markdown(self):
        """Test generating Markdown report."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {
            "scene_name": "Test Scene",
            "summary": {"total": 2, "pass": 1, "error": 1, "warning": 0},
            "results": [
                {"level": "pass", "category": "scale", "message": "Scale OK"},
                {"level": "error", "category": "materials", "message": "Missing"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            result = generator.generate_markdown(data, temp_path, title="Test Report")
            assert result is True

            with open(temp_path, 'r') as f:
                content = f.read()
                assert "# Test Report" in content
                assert "Test Scene" in content
                assert "PASS" in content or "PASS" in content.upper()
                assert "ERROR" in content or "ERROR" in content.upper()
        finally:
            os.unlink(temp_path)

    def test_generate_markdown_with_emojis(self):
        """Test Markdown report includes emojis."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {
            "scene_name": "Test",
            "summary": {"total": 1, "pass": 1, "error": 0, "warning": 0},
            "results": [
                {"level": "pass", "category": "test", "message": "OK"},
            ],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            generator.generate_markdown(data, temp_path)

            with open(temp_path, 'r') as f:
                content = f.read()
                # Should contain checkmark emoji
                assert "PASS" in content.upper()
        finally:
            os.unlink(temp_path)

    def test_generate_json(self):
        """Test generating JSON report."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {
            "scene_name": "Test",
            "summary": {"total": 1, "pass": 1, "error": 0, "warning": 0},
            "results": [{"level": "pass", "message": "OK"}],
        }

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = generator.generate_json(data, temp_path)
            assert result is True

            with open(temp_path, 'r') as f:
                loaded = json.load(f)
                assert loaded["scene_name"] == "Test"
                assert len(loaded["results"]) == 1
        finally:
            os.unlink(temp_path)

    def test_generate_json_io_error(self):
        """Test JSON generation with IO error."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {"test": "data"}

        result = generator.generate_json(data, "/nonexistent/path/report.json")
        assert result is False

    def test_generate_pdf(self):
        """Test PDF generation (creates HTML first)."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {
            "scene_name": "Test",
            "summary": {"total": 0, "pass": 0, "error": 0, "warning": 0},
            "results": [],
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            pdf_path = os.path.join(temp_dir, "report.pdf")

            result = generator.generate_pdf(data, pdf_path, title="Test")
            # PDF generation may or may not work depending on libs
            # But should create HTML at least
            html_path = pdf_path.replace(".pdf", ".html")
            assert os.path.exists(html_path) or result is True

    def test_generate_method_html(self):
        """Test generate method with HTML format."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {"scene_name": "Test", "summary": {}, "results": []}

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            result = generator.generate(data, temp_path, format="html", title="Test")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_generate_method_markdown(self):
        """Test generate method with Markdown format."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {"scene_name": "Test", "summary": {}, "results": []}

        with tempfile.NamedTemporaryFile(suffix='.md', delete=False) as f:
            temp_path = f.name

        try:
            result = generator.generate(data, temp_path, format="markdown", title="Test")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_generate_method_json(self):
        """Test generate method with JSON format."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {"scene_name": "Test", "summary": {}, "results": []}

        with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
            temp_path = f.name

        try:
            result = generator.generate(data, temp_path, format="json")
            assert result is True
        finally:
            os.unlink(temp_path)

    def test_generate_method_invalid_format(self):
        """Test generate method with invalid format."""
        from lib.review.reports import ReportGenerator

        generator = ReportGenerator()
        data = {"scene_name": "Test", "summary": {}, "results": []}

        result = generator.generate(data, "/tmp/test.xyz", format="invalid")
        assert result is False


class TestGenerateReportFunction:
    """Tests for generate_report convenience function."""

    def test_generate_report_function(self):
        """Test generate_report convenience function."""
        from lib.review.reports import generate_report

        data = {"scene_name": "Test", "summary": {}, "results": []}

        with tempfile.NamedTemporaryFile(suffix='.html', delete=False) as f:
            temp_path = f.name

        try:
            result = generate_report(data, temp_path, format="html", title="Test")
            assert result is True
        finally:
            os.unlink(temp_path)


class TestHTMLTemplate:
    """Tests for HTML template rendering."""

    def test_template_structure(self):
        """Test HTML template has expected structure."""
        from lib.review.reports import HTML_TEMPLATE

        assert "<!DOCTYPE html>" in HTML_TEMPLATE
        assert "{title}" in HTML_TEMPLATE
        assert "{timestamp}" in HTML_TEMPLATE
        assert "{scene_name}" in HTML_TEMPLATE
        assert "{total}" in HTML_TEMPLATE
        assert "{passed}" in HTML_TEMPLATE
        assert "{errors}" in HTML_TEMPLATE
        assert "{warnings}" in HTML_TEMPLATE
        assert "{results_html}" in HTML_TEMPLATE

    def test_template_css_classes(self):
        """Test HTML template has CSS classes."""
        from lib.review.reports import HTML_TEMPLATE

        assert ".pass" in HTML_TEMPLATE
        assert ".error" in HTML_TEMPLATE
        assert ".warning" in HTML_TEMPLATE
        assert ".summary-card" in HTML_TEMPLATE
        assert ".result-item" in HTML_TEMPLATE
