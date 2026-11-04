# Notebooks

Los notebooks son la capa de presentacion de los **casos de estudio**.

## Convencion

- `notebooks/case_studies/<case_study_id>/`: notebook principal de un corpus concreto
- `src/`: motor generico reutilizable

## Notebook principal hoy

- Bach cello suites: `notebooks/case_studies/bach_cello_suites/bach_cello_suites_case_study.ipynb`

## Compatibilidad

`notebooks/bach_preludes_walkthrough.ipynb` se mantiene como acceso legacy mientras migramos referencias antiguas.

## Publicacion

Antes de hacer commit, limpia las salidas y los contadores de ejecucion.
Los widgets de audio incrustan grabaciones en el propio `.ipynb`, aunque sus archivos originales esten ignorados por Git.
Conserva las versiones ejecutadas solo en `.cache/` o en otra carpeta local ignorada.
