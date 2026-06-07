import unittest

import app
import town


class RenderTest(unittest.TestCase):
    def test_god_power_event_escapes_html_tags(self):
        state = town.TownState()
        town.inject(state, '<script>alert("x")</script> <img onerror=x>')

        rendered = app._render(state)

        self.assertIn("&lt;script&gt;", rendered)
        self.assertIn("&lt;/script&gt;", rendered)
        self.assertIn("&lt;img onerror=x&gt;", rendered)
        self.assertNotIn("<script>", rendered)
        self.assertNotIn("<img onerror=x>", rendered)
        self.assertIn("<div class='ev'>", rendered)

    def test_speaker_and_model_text_are_escaped(self):
        state = town.TownState(feed=[("<b>Stranger</b>", "<img src=x onerror=x>")])

        rendered = app._render(state)

        self.assertIn("&lt;b&gt;Stranger&lt;/b&gt;", rendered)
        self.assertIn("&lt;img src=x onerror=x&gt;", rendered)
        self.assertNotIn("<b>Stranger</b>", rendered)
        self.assertNotIn("<img src=x onerror=x>", rendered)


if __name__ == "__main__":
    unittest.main()
