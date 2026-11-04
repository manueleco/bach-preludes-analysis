from __future__ import annotations

from collections import Counter
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

from bach_preludes_analysis.io import ensure_directory
from bach_preludes_analysis.models import ComparisonResult, PieceAnalysis


def _finalize_figure(output_path: Path | None) -> None:
    plt.tight_layout()
    if output_path is not None:
        ensure_directory(output_path.parent)
        plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()


def plot_tonal_timeline(analysis: PieceAnalysis, output_path: Path | None = None) -> None:
    if not analysis.key_regions:
        return

    labels = [region.key for region in analysis.key_regions]
    starts = [region.start_measure for region in analysis.key_regions]
    widths = [region.end_measure - region.start_measure + 1 for region in analysis.key_regions]

    plt.figure(figsize=(12, 2.8))
    plt.barh(["zonas tonales"], widths, left=starts, color="#4C78A8")
    for start, width, label in zip(starts, widths, labels):
        plt.text(start + width / 2, 0, label, ha="center", va="center", color="white", fontsize=9)
    plt.xlabel("Compases")
    plt.title(f"Mapa tonal: {analysis.piece_id}")
    _finalize_figure(output_path)


def plot_harmonic_activity(analysis: PieceAnalysis, output_path: Path | None = None) -> None:
    counter = Counter(segment.measure_number for segment in analysis.segments if segment.measure_number is not None)
    if not counter:
        return

    measures = sorted(counter)
    values = [counter[measure] for measure in measures]

    plt.figure(figsize=(12, 3.4))
    plt.bar(measures, values, color="#72B7B2")
    plt.xlabel("Compas")
    plt.ylabel("Segmentos")
    plt.title(f"Actividad armonica por compas: {analysis.piece_id}")
    _finalize_figure(output_path)


def plot_similarity_heatmap(comparison: ComparisonResult, output_path: Path | None = None) -> None:
    if not comparison.similarity_matrix:
        return

    matrix = pd.DataFrame(comparison.similarity_matrix).T
    plt.figure(figsize=(6.5, 5.5))
    plt.imshow(matrix.values, cmap="Blues", vmin=-1, vmax=1)
    plt.colorbar(label="Similitud")
    plt.xticks(range(len(matrix.columns)), matrix.columns, rotation=45, ha="right")
    plt.yticks(range(len(matrix.index)), matrix.index)
    plt.title("Similitud entre piezas")
    for row_index, row_label in enumerate(matrix.index):
        for col_index, col_label in enumerate(matrix.columns):
            plt.text(col_index, row_index, f"{matrix.loc[row_label, col_label]:.2f}", ha="center", va="center", fontsize=8)
    _finalize_figure(output_path)
