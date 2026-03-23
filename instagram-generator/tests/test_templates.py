"""Tests for content template library."""

from templates.library import TemplateLibrary, TEMPLATE_LIBRARY


class TestTemplateLibrary:
    def test_library_not_empty(self):
        assert len(TEMPLATE_LIBRARY) >= 10

    def test_get_all(self):
        templates = TemplateLibrary.get_all()
        assert len(templates) == len(TEMPLATE_LIBRARY)

    def test_get_by_category(self):
        motivational = TemplateLibrary.get_by_category("motivational")
        assert len(motivational) >= 2
        assert all(t.category == "motivational" for t in motivational)

    def test_get_by_name(self):
        tmpl = TemplateLibrary.get_by_name("palov_recipe")
        assert tmpl is not None
        assert tmpl.category == "recipe"
        assert "palov" in tmpl.topic.lower()

    def test_get_by_name_not_found(self):
        assert TemplateLibrary.get_by_name("nonexistent") is None

    def test_get_by_type(self):
        reels = TemplateLibrary.get_by_type("reel")
        assert len(reels) >= 5
        assert all(t.content_type == "reel" for t in reels)

    def test_render(self):
        tmpl = TemplateLibrary.get_by_name("morning_motivation")
        assert tmpl is not None
        rendered = tmpl.render()
        assert rendered["topic"] == tmpl.topic
        assert rendered["category"] == "motivational"
        assert rendered["content_type"] == "reel"
        assert rendered["hashtags"] == tmpl.hashtags

    def test_all_templates_have_required_fields(self):
        for t in TEMPLATE_LIBRARY:
            assert t.name, f"Template missing name"
            assert t.topic, f"{t.name} missing topic"
            assert t.category, f"{t.name} missing category"
            assert t.content_type, f"{t.name} missing content_type"
            assert t.hashtags, f"{t.name} missing hashtags"

    def test_display(self):
        output = TemplateLibrary.display()
        assert "Template Library" in output
        assert "MOTIVATIONAL" in output
        assert "RECIPE" in output

    def test_display_filtered(self):
        output = TemplateLibrary.display("travel")
        assert "TRAVEL" in output

    def test_categories_covered(self):
        categories = {t.category for t in TEMPLATE_LIBRARY}
        assert "motivational" in categories
        assert "recipe" in categories
        assert "travel" in categories
        assert "lifestyle" in categories
