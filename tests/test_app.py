import json
import shutil
import tempfile
import unittest
from pathlib import Path

from streamlit.testing.v1 import AppTest


def verification(app):
    return next(section for section in app.expander if section.proto.label == "Verify a displayed number")


def evidence(app):
    return verification(app).dataframe[0].value


def denominator(app):
    return verification(app).dataframe[1].value


def open_app():
    return AppTest.from_file(
        str(Path(__file__).resolve().parents[1] / "app.py"), default_timeout=30
    ).run()


class ChartAppTests(unittest.TestCase):
    def test_story_is_home_and_navigation_returns_to_it(self):
        app = open_app()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "Who is driving the rise of AI?")
        self.assertEqual(len(app.get("plotly_chart")), 0)
        self.assertEqual(len(app.slider), 0)
        self.assertTrue(any("Industry vs Academia dashboard" in link.proto.label for link in app.get("page_link")))

        app.switch_page("dashboards/1_Industry_vs_Academia.py").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "Industry vs Academia")
        self.assertEqual(len(app.get("plotly_chart")), 3)

        app.switch_page("views/story.py").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.title[0].value, "Who is driving the rise of AI?")
        self.assertEqual(len(app.get("plotly_chart")), 0)

    def test_filtering_and_evidence_match_chart(self):
        app = open_app()
        app.switch_page("dashboards/1_Industry_vs_Academia.py").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(len(app.get("plotly_chart")), 3)
        self.assertEqual(app.selectbox[0].value, 2025)
        self.assertEqual(app.radio[0].value, "All")
        self.assertEqual(len(evidence(app)), int(app.metric[0].value.split()[0]))
        self.assertFalse(app.expander[0].proto.expanded)
        share_spec = json.loads(app.get("plotly_chart")[1].proto.spec)
        self.assertEqual(
            [trace["name"] for trace in share_spec["data"]],
            ["Industry", "Academia", "Collaboration", "Other", "Unknown"],
        )
        self.assertFalse(share_spec["layout"]["legend"]["itemclick"])
        for trace in share_spec["data"]:
            self.assertEqual(trace["type"], "scatter")
            self.assertTrue(trace["stackgroup"])
            self.assertNotIn("groupnorm", trace)
        for year_values in zip(*(trace["y"] for trace in share_spec["data"])):
            self.assertAlmostEqual(sum(year_values), 100)
        latest_industry = share_spec["data"][0]["customdata"][-1]
        self.assertEqual(latest_industry[1], len(evidence(app)))
        self.assertEqual(latest_industry[2], len(denominator(app)))
        self.assertAlmostEqual(latest_industry[0], latest_industry[1] / latest_industry[2] * 100)

        app.slider[0].set_value((2014, 2020)).run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(2014 <= app.selectbox[0].value <= 2020)
        spec = json.loads(app.get("plotly_chart")[0].proto.spec)
        self.assertEqual([trace["name"] for trace in spec["data"]], ["Industry", "Academia", "Collaboration"])
        share_spec = json.loads(app.get("plotly_chart")[1].proto.spec)
        for trace in share_spec["data"]:
            self.assertEqual(trace["x"], list(range(2014, 2021)))
        app.selectbox[0].select(2014).run()
        app.selectbox[1].select("Academia").run()
        matching = evidence(app)
        self.assertTrue(matching["Publication date"].str.startswith("2014").all())
        self.assertTrue(matching["Sector"].eq("Academia").all())
        self.assertTrue(denominator(app)["Publication date"].str.startswith("2014").all())
        compare_spec = json.loads(app.get("plotly_chart")[2].proto.spec)
        self.assertEqual([trace["name"] for trace in compare_spec["data"]], ["All", "Notable"])
        self.assertTrue(all(trace["x"] == list(range(2014, 2021)) for trace in compare_spec["data"]))

        app.slider[0].set_value((2003, 2003)).run()
        self.assertEqual(len(app.exception), 0)
        share_spec = json.loads(app.get("plotly_chart")[1].proto.spec)
        zero_sector = next(trace["name"] for trace in share_spec["data"] if trace["y"] == [0])
        app.selectbox[1].select(zero_sector).run()
        self.assertTrue(evidence(app).empty)
        self.assertTrue(any("at least two years" in item.value for item in app.info))
        share_spec = json.loads(app.get("plotly_chart")[1].proto.spec)
        self.assertTrue(all(trace["type"] == "bar" for trace in share_spec["data"]))

        app.slider[0].set_value((2025, 2025)).run()
        app.selectbox[1].select("Unknown").run()
        self.assertEqual(len(app.exception), 0)
        self.assertTrue(evidence(app)["Organization categorization"].eq("").all())

    def test_notable_verification_changes_sample_without_changing_main_charts(self):
        app = open_app()
        app.switch_page("dashboards/1_Industry_vs_Academia.py").run()
        all_count = app.metric[0].value
        compare_spec = json.loads(app.get("plotly_chart")[2].proto.spec)
        all_latest, notable_latest = [trace["customdata"][-1] for trace in compare_spec["data"]]
        self.assertEqual(all_latest, [len(evidence(app)), len(denominator(app))])
        app.radio[0].set_value("Notable").run()
        self.assertEqual(len(app.exception), 0)
        self.assertEqual(app.metric[0].value, all_count)
        self.assertEqual(notable_latest, [len(evidence(app)), len(denominator(app))])
        self.assertTrue(any("notable_ai_models.csv" in item.value for item in verification(app).caption))
        self.assertFalse(verification(app).proto.expanded)

    def test_new_student_page_is_discovered_without_changing_entry_point(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as directory:
            fixture = Path(directory)
            shutil.copyfile(root / "app.py", fixture / "app.py")
            (fixture / "views").mkdir()
            (fixture / "dashboards").mkdir()
            (fixture / "views/story.py").write_text(
                'import streamlit as st\nst.title("Story fixture")\n', encoding="utf-8"
            )
            # Simulate a second student adding a standalone page to the shared project.
            (fixture / "dashboards/2_Organisation_Concentration.py").write_text(
                'import streamlit as st\nst.title("Second student contribution")\n', encoding="utf-8"
            )
            app = AppTest.from_file(str(fixture / "app.py"), default_timeout=30).run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.title[0].value, "Story fixture")
            app.switch_page("dashboards/2_Organisation_Concentration.py").run()
            self.assertEqual(len(app.exception), 0)
            self.assertEqual(app.title[0].value, "Second student contribution")


if __name__ == "__main__":
    unittest.main()
