# Architecture

## North Star

El repo debe funcionar como un analizador de colecciones musicales por compositor o por corpus, no como un script monouso para un solo set de preludios.

## Current Pattern

- `src/`: motor generico de analisis simbolico, audio y comparacion
- `data/case_studies/<case_id>/`: datos y manifests del caso de estudio activo
- `data/sources/`: corpus externos publicos de referencia
- `outputs/`: reportes y figuras generados

## Separation Of Concerns

- score simbolico curado: armonia y estructura
- audio privado: expresion y validacion auxiliar
- corpus externos: contraste, no verdad absoluta
- OMR: solo staging

## Important Constraint

En repertorio monodico o arpegiado, la armonia puede ser implicita. El sistema debe exponer inferencias explicables, no fingir certeza absoluta.
