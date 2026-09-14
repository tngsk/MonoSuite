import unittest
from src.registry import (
    ComponentRegistry,
    get_all_components,
    get_components_by_status,
    get_components_by_category,
    is_web_component,
    get_component_meta
)

class TestComponentRegistry(unittest.TestCase):
    def setUp(self):
        self.registry = ComponentRegistry()

    def test_singleton(self):
        r2 = ComponentRegistry()
        self.assertIs(self.registry, r2)

    def test_status_categorization(self):
        active = get_components_by_status("active")
        frozen = get_components_by_status("frozen")
        wip = get_components_by_status("wip")
        
        # Verify active components
        self.assertIn("mono-layout", active)
        self.assertIn("mono-zoom", active)
        self.assertIn("mono-section", active)
        self.assertIn("mono-connector", active)
        self.assertEqual(len(active), 10)
        
        # Verify wip components
        self.assertEqual(len(wip), 0)
        
        # Verify frozen components
        self.assertIn("mono-clock", frozen)
        self.assertIn("mono-countdown", frozen)
        self.assertIn("mono-dice", frozen)
        self.assertEqual(len(frozen), 7)

    def test_category_filtering(self):
        interactive = get_components_by_category("interactive")
        self.assertIn("mono-poll", interactive)
        self.assertIn("mono-reaction", interactive)
        self.assertIn("mono-account", interactive)
        self.assertEqual(len(interactive), 9)

    def test_web_component_detection(self):
        self.assertFalse(is_web_component("mono-image"))
        self.assertTrue(is_web_component("mono-layout"))
        self.assertTrue(is_web_component("mono-zoom"))

if __name__ == "__main__":
    unittest.main()
