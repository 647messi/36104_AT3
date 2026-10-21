"""Shared entry point: Story first, with automatically discovered student pages."""

from pathlib import Path

import streamlit as st


ROOT = Path(__file__).resolve().parent


def main() -> None:
    st.set_page_config(page_title="The Rise of AI", layout="wide")
    story = st.Page(
        "views/story.py",
        title="Story",
        icon=":material/auto_stories:",
        default=True,
    )
    # Number prefixes determine reading order; underscores become spaces in the label.
    # New student pages are discovered without editing this shared entry point.
    student_pages = [
        st.Page(str(path.relative_to(ROOT)))
        for path in sorted((ROOT / "dashboards").glob("*.py"))
        if not path.name.startswith("_")
    ]
    page = st.navigation([story, *student_pages], expanded=True)
    page.run()


if __name__ == "__main__":
    main()
