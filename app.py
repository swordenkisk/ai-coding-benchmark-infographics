from __future__ import annotations

import io

import pandas as pd
import plotly.express as px
import streamlit as st

from benchmark_data import DataValidationError, load_and_validate


st.set_page_config(
    page_title="AI Coding Benchmark Infographics",
    page_icon="📊",
    layout="wide",
)

st.title("AI Coding Benchmark Infographics")
st.write(
    "Compare models on the same benchmark and version. Upload sourced results "
    "or explore the clearly labeled synthetic demo."
)

with st.sidebar:
    st.header("Data")
    uploaded_file = st.file_uploader(
        "Upload benchmark results",
        type=["csv"],
        help="Use the CSV template to check the required columns.",
    )

    template = (
        "model,benchmark,benchmark_version,score,score_unit,"
        "higher_is_better,evaluated_on,source_url,input_usd_per_1m_tokens\n"
    )
    st.download_button(
        "Download CSV template",
        data=template.encode("utf-8"),
        file_name="benchmark-template.csv",
        mime="text/csv",
    )

    st.caption(
        "No API keys are required. Results are not fetched or verified by this app."
    )

if uploaded_file is None:
    st.info(
        "Showing synthetic demo data—not real benchmark results. "
        "Upload sourced results to make a factual comparison."
    )
    raw_data = pd.read_csv("data/demo.csv")
else:
    try:
        raw_data = pd.read_csv(uploaded_file)
    except (pd.errors.ParserError, UnicodeDecodeError, ValueError) as exc:
        st.error(f"Could not read that CSV: {exc}")
        st.stop()

try:
    data = load_and_validate(raw_data)
except DataValidationError as exc:
    st.error(str(exc))
    st.stop()

benchmark_names = sorted(data["benchmark"].unique())
selected_benchmark = st.selectbox("Benchmark", benchmark_names)

benchmark_data = data[data["benchmark"] == selected_benchmark]
versions = sorted(benchmark_data["benchmark_version"].unique())
selected_version = st.selectbox("Benchmark version", versions)

comparison = benchmark_data[
    benchmark_data["benchmark_version"] == selected_version
].copy()

# Keep the most recent observation for each model in this benchmark version.
comparison = (
    comparison.sort_values("evaluated_on")
    .drop_duplicates(subset=["model"], keep="last")
    .copy()
)

if comparison.empty:
    st.warning("There are no observations for this benchmark version.")
    st.stop()

if comparison["score_unit"].nunique() != 1:
    st.error("Scores use inconsistent units; this comparison cannot be plotted.")
    st.stop()

higher_is_better = bool(comparison["higher_is_better"].iloc[0])
score_unit = comparison["score_unit"].iloc[0]

if higher_is_better:
    leader_row = comparison.loc[comparison["score"].idxmax()]
    comparison["gap_from_leader"] = leader_row["score"] - comparison["score"]
    comparison = comparison.sort_values("score", ascending=True)
    direction_label = "Higher score is better"
else:
    leader_row = comparison.loc[comparison["score"].idxmin()]
    comparison["gap_from_leader"] = comparison["score"] - leader_row["score"]
    comparison = comparison.sort_values("score", ascending=False)
    direction_label = "Lower score is better"

leader_name = str(leader_row["model"])
latest_date = comparison["evaluated_on"].max()

metric_columns = st.columns(3)
metric_columns[0].metric("Models compared", len(comparison))
metric_columns[1].metric("Best observed result", leader_name)
metric_columns[2].metric("Most recent evaluation", latest_date)

st.caption(
    f"{selected_benchmark} · {selected_version} · {direction_label}. "
    "Only the latest observation per model is shown."
)

# Infographic 1: raw benchmark scores.
score_chart_data = comparison.sort_values(
    "score", ascending=higher_is_better
)
score_figure = px.bar(
    score_chart_data,
    x="score",
    y="model",
    orientation="h",
    text="score",
    title=f"{selected_benchmark}: benchmark scores",
    labels={"score": f"Score ({score_unit})", "model": ""},
    hover_data=["evaluated_on", "source_url"],
)
score_figure.update_traces(textposition="outside", cliponaxis=False)
score_figure.update_layout(yaxis={"categoryorder": "total ascending"})

# Infographic 2: each model's score-point gap from the leader.
gap_chart_data = comparison.sort_values(
    "gap_from_leader", ascending=False
)
gap_figure = px.bar(
    gap_chart_data,
    x="gap_from_leader",
    y="model",
    orientation="h",
    text="gap_from_leader",
    title=f"Score-point gap from leader: {leader_name}",
    labels={
        "gap_from_leader": f"Gap from leader ({score_unit})",
        "model": "",
    },
    hover_data=["score", "evaluated_on", "source_url"],
)
gap_figure.update_traces(textposition="outside", cliponaxis=False)
gap_figure.update_layout(yaxis={"categoryorder": "total ascending"})

left, right = st.columns(2)
with left:
    st.plotly_chart(score_figure, use_container_width=True)
    st.download_button(
        "Download score infographic (HTML)",
        data=score_figure.to_html(full_html=True, include_plotlyjs=True).encode(
            "utf-8"
        ),
        file_name="benchmark-scores.html",
        mime="text/html",
    )

with right:
    st.plotly_chart(gap_figure, use_container_width=True)
    st.download_button(
        "Download leader-gap infographic (HTML)",
        data=gap_figure.to_html(full_html=True, include_plotlyjs=True).encode(
            "utf-8"
        ),
        file_name="leader-gap.html",
        mime="text/html",
    )

st.subheader("Observations and sources")
display_columns = [
    "model",
    "score",
    "score_unit",
    "evaluated_on",
    "source_url",
    "input_usd_per_1m_tokens",
]
st.dataframe(
    comparison[display_columns].reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)

st.download_button(
    "Download compared data (CSV)",
    data=comparison[display_columns].to_csv(index=False).encode("utf-8"),
    file_name="benchmark-comparison.csv",
    mime="text/csv",
)

st.caption(
    "A benchmark score is not a guarantee of real-world coding performance. "
    "Check each linked source for its testing setup and date. The optional "
    "input-price field is included in the data export but does not affect ranking."
)
