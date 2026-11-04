# Development

## Conventions

- preferir nombres genericos como `piece_id` y `case_study_id`
- mantener compatibilidad razonable con el pasado cuando no cueste demasiado
- cualquier heuristica debe dejar trazabilidad en reportes o summaries

## Technical Debt

- algunos scripts legacy siguen nombrados en funcion del caso Bach
- el paquete aun se llama `bach_preludes_analysis`
- falta un segundo caso de estudio que fuerce la abstraccion

## Near-Term Dev Tasks

- ejecutar pruebas despues de la migracion a `piece_id`
- decidir si el nombre del paquete se mantiene o cambia en una futura version mayor
- revisar notebook para que no dependa de rutas viejas
