# External Source Profiles

Esta carpeta contiene solo fuentes externas publicas o reproducibles.

## Principio de trabajo

- `data/case_studies/<case_id>/` contiene el corpus del caso de estudio
- `data/sources/symbolic/` contiene corpus externos para contraste
- el audio privado no vive aqui
- los artefactos intermedios de OMR tampoco viven aqui

## Perfiles definidos

- `symbolic/kern/`: referencia en formato `**kern` o Humdrum
- `symbolic/mutopia/`: referencia abierta desde Mutopia
- `symbolic/musopen/`: referencia abierta desde Musopen

## Ingestion Scripts

- `scripts/ingest_kern_sources.py`
- `scripts/ingest_mutopia_sources.py`
- `scripts/ingest_musopen_sources.py`
- `scripts/ingest_all_source_profiles.py`

Cada perfil simbolico tiene un `manifest.csv` versionado con:

- que pieza se espera
- de que URL o pagina fuente viene
- que estado tiene la disponibilidad upstream
- que politica de seleccion usar

Los archivos descargados se mantienen ignorados por git. Los manifiestos no.

## Politica de fiabilidad

- usa el corpus curado del caso de estudio para armonia, numerales romanos, modulaciones y cadencias
- usa los corpus externos para contraste editorial o para cubrir huecos
- no mezcles estos materiales con assets privados locales
