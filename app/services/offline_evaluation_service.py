from __future__ import annotations

import csv
from pathlib import Path

from ..schemas.analytics import (
    MetricLeader,
    OfflineEvaluationResponse,
    OfflineModelEvaluationRow,
)

_OUTPUTS_DIR = Path(__file__).resolve().parents[2] / "outputs"
_FINAL_COMPARISON_FILE = _OUTPUTS_DIR / "model_comparison_final.csv"


def load_offline_evaluation() -> OfflineEvaluationResponse:
    rows = _load_rows()
    leaders = _build_leaders(rows)
    return OfflineEvaluationResponse(
        source_file=str(_FINAL_COMPARISON_FILE),
        rows=rows,
        leaders=leaders,
    )


def _load_rows() -> list[OfflineModelEvaluationRow]:
    if not _FINAL_COMPARISON_FILE.exists():
        return []

    with _FINAL_COMPARISON_FILE.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        return [
            OfflineModelEvaluationRow(
                model=row["model"],
                precision_at_10=float(row["precision@10"]),
                hit_rate_at_10=float(row["hit_rate@10"]),
                ndcg_at_10=float(row["ndcg@10"]),
                auc=float(row["auc"]),
                coverage=float(row["coverage"]),
                user_coverage=float(row["user_coverage"]),
                diversity=float(row["diversity"]),
                evaluated_rows=int(float(row["evaluated_rows"])),
            )
            for row in reader
        ]


def _build_leaders(rows: list[OfflineModelEvaluationRow]) -> list[MetricLeader]:
    metric_extractors = {
        "precision_at_10": lambda row: row.precision_at_10,
        "hit_rate_at_10": lambda row: row.hit_rate_at_10,
        "ndcg_at_10": lambda row: row.ndcg_at_10,
        "auc": lambda row: row.auc,
        "coverage": lambda row: row.coverage,
        "diversity": lambda row: row.diversity,
    }
    leaders: list[MetricLeader] = []
    for metric, extractor in metric_extractors.items():
        if not rows:
            continue
        best_row = max(rows, key=extractor)
        leaders.append(
            MetricLeader(
                metric=metric,
                model=best_row.model,
                value=extractor(best_row),
            )
        )
    return leaders
