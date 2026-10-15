# AI Coding Benchmark Infographics

A small Streamlit app for comparing AI models on coding benchmarks and
exporting two shareable interactive infographics:

1. **Benchmark scores** — scores for the selected benchmark and version.
2. **Score-point gap from the leader** — each model's difference from the
   highest- or lowest-scoring model, depending on the benchmark's direction.

The app does not fetch, verify, or generate benchmark results. Upload sourced
data to make a real comparison. The included demo values are synthetic and
must not be presented as real model results.

## Features

- CSV upload with input validation.
- Select a benchmark and version before comparing models.
- Uses each model's latest observation for the selected benchmark version.
- Supports benchmarks where either higher or lower scores are better.
- Displays evaluation dates and source URLs.
- Downloads both charts as standalone HTML and the comparison as CSV.
- No API keys or external model integrations required.

## Requirements

- Python 3.10 or later
- Bash for the setup scripts

## Quick start

```bash
chmod +x scripts/setup.sh scripts/run.sh
./scripts/setup.sh
./scripts/run.sh

The app opens in your browser. Upload a results CSV, or use the synthetic demo
to preview the charts.

CSV format
Download the template from the app. Required columns:

Column	Description
model	Model name as reported by the source
benchmark	Benchmark name
benchmark_version	Benchmark version or evaluation configuration
score	Numeric benchmark score
score_unit	Unit or scale used by the benchmark
higher_is_better	true or false
evaluated_on	Evaluation date, for example 2026-04-15
source_url	HTTP or HTTPS link to the result source
input_usd_per_1m_tokens	Optional input-token price; blank if unavailable
For a fair comparison, use the same benchmark version, score unit, and
score direction for every model in the comparison. Include enough context in
the source links for readers to understand how the results were obtained.

To compare Argon, add it as a model row and provide its benchmark score,
evaluation date, and source URL. The app does not assume or supply Argon's
benchmark results.

Run tests
bash


source .venv/bin/activate
python -m unittest discover -s tests -v
Repository layout
text


app.py                 Streamlit interface and chart generation
benchmark\_data.py      CSV validation and normalization
data/demo.csv          Clearly synthetic example rows
tests/                 Unit tests
scripts/setup.sh       Virtual environment and dependency setup
scripts/run.sh         Local app launcher