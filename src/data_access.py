"""Share the unchanged local dataset across the story and student pages."""

from pathlib import Path

import pandas as pd
import streamlit as st

from src.preprocessing import DEFAULT_SOURCE, load_models


@st.cache_data(show_spinner=False)
def _read_source(source: str, modified_ns: int) -> tuple[pd.DataFrame, dict]:
    """A changed file modification time invalidates the cached snapshot."""
    return load_models(Path(source))


def load_source(source: Path = DEFAULT_SOURCE) -> tuple[pd.DataFrame, dict]:
    """Default to All; pass NOTABLE_SOURCE for the separate comparison sample."""
    source = Path(source)
    return _read_source(str(source), source.stat().st_mtime_ns)
