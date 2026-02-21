import unittest
from md_to_pdf_tui import _process_alerts

class TestAlertProcessing(unittest.TestCase):
    def setUp(self):
        self.alert_styles = {
            "NOTE": {"color": "#0969da", "bg": "#f6f8fa", "icon": "ℹ️"},
            "TIP": {"color": "#1f883d", "bg": "#f6f8fa", "icon": "💡"}
        }
        self.txt_color = "#1b1f23"

    def test_no_alerts(self):
        md = "This is a normal paragraph.\n> This is a normal blockquote.\n\nAnother paragraph."
        result = _process_alerts(md, self.alert_styles, self.txt_color)
        self.assertEqual(md, result)

    def test_single_alert(self):
        md = "> [!NOTE]\n> This is a note."
        result = _process_alerts(md, self.alert_styles, self.txt_color)

        # We expect an HTML table
        self.assertIn('<table style="width:100%; border-left: 5px solid #0969da', result)
        self.assertIn('ℹ️ NOTE - </strong><br/>This is a note.</td>', result)

    def test_alert_with_multiline_content(self):
        md = "> [!TIP]\n> Line 1.\n> Line 2."
        result = _process_alerts(md, self.alert_styles, self.txt_color)

        self.assertIn('<table', result)
        self.assertIn('Line 1.<br/>Line 2.', result)

    def test_mixed_content(self):
        md = "Start.\n\n> [!NOTE]\n> Alert.\n\nEnd."
        result = _process_alerts(md, self.alert_styles, self.txt_color)

        self.assertIn("Start.", result)
        self.assertIn("<table", result)
        self.assertIn("End.", result)

    def test_nested_blockquote_behavior(self):
        # The logic treats any `> ` inside an alert as continuation.
        # It does not parse nested blockquotes as Markdown blockquotes, but as text.
        md = "> [!NOTE]\n> > Nested quote"
        result = _process_alerts(md, self.alert_styles, self.txt_color)
        self.assertIn("> Nested quote", result)

    def test_optimization_edge_case(self):
        # Line with > but not at start
        md = "Check this -> arrow."
        result = _process_alerts(md, self.alert_styles, self.txt_color)
        self.assertEqual(md, result)

    def test_malformed_alert(self):
        # Missing space or bracket
        md = ">[!NOTE] No space."
        # The regex is `^\s*>\s*\[!(NOTE|...`
        # It handles `>[!NOTE]`.
        result = _process_alerts(md, self.alert_styles, self.txt_color)
        self.assertIn("<table", result)

        md2 = "> [NOTE] Not an alert."
        result2 = _process_alerts(md2, self.alert_styles, self.txt_color)
        self.assertEqual(md2, result2)

if __name__ == "__main__":
    unittest.main()
