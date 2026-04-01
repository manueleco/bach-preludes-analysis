from __future__ import annotations

from collections import Counter

from bach_preludes_analysis.models import PreludeAnalysis


def _format_key_regions(analysis: PreludeAnalysis, limit: int = 5) -> str:
    if not analysis.key_regions:
        return analysis.global_key
    regions = analysis.key_regions[:limit]
    summary = ", ".join(f"mm. {region.start_measure}-{region.end_measure}: {region.key}" for region in regions)
    if len(analysis.key_regions) > limit:
        summary += ", ..."
    return summary


def build_musician_summary(analysis: PreludeAnalysis) -> dict[str, str]:
    cadence_counter = Counter(cadence.cadence_type for cadence in analysis.cadences)
    most_common_nct = Counter(item.classification for item in analysis.non_chord_tones).most_common(3)
    nct_summary = ", ".join(f"{label} ({count})" for label, count in most_common_nct) or "sin casos claros todavia"
    bass_moves = ", ".join(f"{label} ({count})" for label, count in analysis.voice_leading.get("common_bass_moves", []))
    texture_mode = analysis.texture_profile.get("inference_strategy", "literal_verticality")
    is_implied = bool(analysis.texture_profile.get("is_implied_harmony", False))

    overview = (
        f"Tonalidad global estimada: {analysis.global_key}. "
        f"Se detectan {len(analysis.key_regions)} zonas tonales locales: {_format_key_regions(analysis)}. "
        f"Modo de lectura armonica: {'implicita por vecindad' if is_implied else 'verticalidad literal'}."
    )

    harmony = (
        f"El preludio se divide en {len(analysis.segments)} segmentos armonicos. "
        f"El ritmo armonico promedio es de {analysis.harmonic_rhythm.get('changes_per_measure', 0.0)} "
        f"cambios por compas, con {len(analysis.secondary_functions)} eventos de tonicizacion o funcion secundaria. "
        f"La textura presenta un promedio de {analysis.texture_profile.get('average_observed_pitch_classes', 0.0)} "
        f"clases de altura observadas por segmento."
    )

    cadences = (
        f"Cadencias detectadas: {len(analysis.cadences)} en total. "
        f"Distribucion principal: PAC {cadence_counter.get('PAC', 0)}, "
        f"IAC {cadence_counter.get('IAC', 0)}, semicadencias {cadence_counter.get('half', 0)}, "
        f"rotas {cadence_counter.get('deceptive', 0)}."
    )

    surface = (
        f"Cromatismo: densidad {analysis.chromaticism.get('chromatic_density', 0.0)}; "
        f"densidad disonante {analysis.chromaticism.get('dissonance_density', 0.0)}. "
        f"Notas no armonicas mas frecuentes: {nct_summary}."
    )

    voice_leading = (
        f"Conduccion de voces: tasa de movimiento contrario {analysis.voice_leading.get('contrary_motion_rate', 0.0)} "
        f"y {analysis.voice_leading.get('parallel_perfects', 0)} posibles paralelismos perfectos. "
        f"Movimientos de bajo mas comunes: {bass_moves or 'sin datos suficientes'}. "
        f"{'En cello solo estos indicadores son aproximaciones registrales y no equivalen a una polifonia completa.' if is_implied else ''}"
    )

    return {
        "overview": overview,
        "harmony": harmony,
        "cadences": cadences,
        "surface": surface,
        "voice_leading": voice_leading,
    }


def harmonic_table_rows(analysis: PreludeAnalysis, limit: int = 24) -> list[dict[str, object]]:
    rows = []
    for segment in analysis.segments[:limit]:
        rows.append(
            {
                "measure": segment.measure_number,
                "beat": segment.beat,
                "key": segment.key,
                "roman": segment.roman_numeral,
                "function": segment.harmonic_function,
                "chord": segment.chord_figure,
                "bass": segment.bass,
                "observed": ", ".join(segment.observed_pitch_names),
                "strategy": segment.inference_strategy,
            }
        )
    return rows
