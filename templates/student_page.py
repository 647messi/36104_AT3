"""Copy to dashboards/2_Your_Topic.py and replace with your contribution.

Set the application configuration only in app.py. Keep page-specific processing
in a separate src module, and document any changes to counting or attribution.
"""

import streamlit as st


def main() -> None:
    st.page_link("views/story.py", label="Back to the story", icon=":material/arrow_back:")
    st.title("Your analysis title")
    st.markdown("**Research question:** Replace with your individual sub-question.")
    st.write("Explain what is measured and how this contribution connects to the group story.")

    # Add your filters, charts and evidence here. Use distinctive widget keys if needed.
    # Shared local source access is available through src.data_access.load_source.
    # Its Sector field uses the Industry vs Academia attribution rules.
    # Add a separate classification for your analysis if those rules do not apply.

    with st.expander("Source and methodology"):
        st.write("Document the dataset, unit of analysis, attribution rules and limitations.")


if __name__ == "__main__":
    main()
