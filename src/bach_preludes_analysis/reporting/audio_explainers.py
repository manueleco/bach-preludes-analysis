from __future__ import annotations

from bach_preludes_analysis.models import AudioAnalysis


def build_audio_summary(analysis: AudioAnalysis) -> dict[str, str]:
    key_label = " ".join(part for part in [analysis.estimated_key, analysis.estimated_scale] if part) or "desconocida"
    level_label = analysis.metering.get("integrated_loudness")
    level_text = (
        f"loudness {level_label}"
        if level_label is not None
        else f"nivel medio {analysis.metering.get('level_dbfs_mean')} dBFS"
    )
    overview = (
        f"Backend usado: {analysis.backend}. Duracion aproximada: {analysis.duration_seconds} segundos. "
        f"Tempo estimado desde audio: {analysis.tempo_bpm} BPM, con {analysis.beat_count} pulsos detectados."
    )
    tonality = f"Tonalidad estimada desde audio: {key_label}, con fuerza tonal {analysis.key_strength}."
    metering = (
        f"Perfil dinamico: {level_text}, "
        f"RMS medio {analysis.metering.get('rms_mean')}, "
        f"pico {analysis.metering.get('peak_dbfs')} dBFS, "
        f"crest factor {analysis.metering.get('crest_factor')}."
    )
    timbre = (
        f"Huella espectral: centroide medio {analysis.spectral.get('spectral_centroid_mean')} Hz "
        f"y flujo espectral medio {analysis.spectral.get('spectral_flux_mean')}."
    )
    return {
        "overview": overview,
        "tonality": tonality,
        "metering": metering,
        "timbre": timbre,
    }
