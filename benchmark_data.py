from __future__ import annotations

from urllib.parse import urlparse

import pandas as pd


REQUIRED_COLUMNS = {
    "model",
    "benchmark",
    "benchmark_version",
    "score",
    "score_unit",
    "higher_is_better",
    "evaluated_on",
    "source_url",
}

OPTIONAL_COLUMNS = {"input_usd_per_1m_tokens"}
BOOLEAN_VALUES = {
    "true": True,
    "yes": True,
    "1": True,
    "false": False,
    "no": False,
    "0": False,
}


class DataValidationError(ValueError):
    """Raised when benchmark input does not match the expected schema."""


def _parse_boolean(value: object) -> bool | None:
    if isinstance(value, bool):
        return value

    normalized = str(value).strip().lower()
    return BOOLEAN_VALUES.get(normalized)


def load_and_validate(frame: pd.DataFrame) -> pd.DataFrame:
    """Validate and normalize benchmark observations from a CSV dataframe."""
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise DataValidationError(
            "Missing required columns: " + ", ".join(sorted(missing))
        )

    data = frame.copy()

    for column in REQUIRED_COLUMNS - {"score", "evaluated_on", "higher_is_better"}:
        data[column] = data[column].astype("string").str.strip()

    empty_required = [
        column
        for column in REQUIRED_COLUMNS
        if column not in {"score", "evaluated_on", "higher_is_better"}
        and data[column].isna().any()
    ]
    if empty_required:
        raise DataValidationError(
            "Required text fields cannot be blank: "
            + ", ".join(sorted(empty_required))
        )

    data["score"] = pd.to_numeric(data["score"], errors="coerce")
    if data["score"].isna().any() or not data["score"].map(
        lambda value: pd.notna(value) and abs(value) != float("inf")
    ).all():
        raise DataValidationError("Scores must be finite numeric values.")

    data["evaluated_on"] = pd.to_datetime(
        data["evaluated_on"], errors="coerce", utc=True
    )
    if data["evaluated_on"].isna().any():
        raise DataValidationError(
            "Every evaluated_on value must be a valid date, such as 2026-04-15."
        )
    data["evaluated_on"] = data["evaluated_on"].dt.strftime("%Y-%m-%d")

    data["higher_is_better"] = data["higher_is_better"].map(_parse_boolean)
    if data["higher_is_better"].isna().any():
        raise DataValidationError(
            "higher_is_better must be true/false, yes/no, or 1/0."
        )

    invalid_urls = []
    for row_number, value in enumerate(data["source_url"], start=2):
        parsed = urlparse(str(value))
        if parsed.scheme not in {"http", "https"} or not parsed.netloc:
            invalid_urls.append(row_number)
    if invalid_urls:
        rows = ", ".join(map(str, invalid_urls[:10]))
        raise DataValidationError(
            f"source_url must be an http or https URL. Check CSV row(s): {rows}."
        )

    consistency_columns = ["score_unit", "higher_is_better"]
    for column in consistency_columns:
        inconsistent = (
            data.groupby(["benchmark", "benchmark_version"])[column]
            .nunique(dropna=False)
            .gt(1)
        )
        if inconsistent.any():
            raise DataValidationError(
                f"{column} must be consistent within each benchmark version."
            )

    if "input_usd_per_1m_tokens" not in data.columns:
        data["input_usd_per_1m_tokens"] = pd.NA
    else:
        original = data["input_usd_per_1m_tokens"]
        converted = pd.to_numeric(original, errors="coerce")
        invalid = original.notna() & original.astype("string").str.strip().ne("") & converted.isna()
        if invalid.any():
            raise DataValidationError(
                "input_usd_per_1m_tokens must contain non-negative numbers or blanks."
            )
        if (converted.dropna() < 0).any():
            raise DataValidationError(
                "input_usd_per_1m_tokens must be non-negative."
            )
        data["input_usd_per_1m_tokens"] = converted

    return data
