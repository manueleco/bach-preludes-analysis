# TODO

## In Progress

- reestructurar el repo de un caso puntual a un framework por caso de estudio
- separar corpus publico reproducible de assets privados locales
- validar score y audio por emparejamiento canonico y perfil cromatico

## Done

- base de analisis simbolico para tonalidad, acordes, numerales, cadencias, secuencias, cromatismo y conduccion
- capa de audio para tempo, rubato, dinamica, densidad espectral y articulacion aproximada
- perfiles de corpus para `official_curated`, `kern`, `mutopia`, `musopen`, `audiveris` y audio de un solo interprete
- pipeline de OMR con Audiveris
- ingestores para `kern`, `Mutopia` y `Musopen`
- organizacion inicial del caso de estudio `bach_cello_suites`
- notebook dedicado de caso de estudio para Bach, separado del motor generico

## To Do

- poblar `symbolic/official_curated/` con los `MusicXML` ya revisados
- revisar y promover los mejores `MusicXML` provenientes de OMR
- ejecutar la validacion score-audio sobre los 6 preludios
- mejorar explicaciones del notebook para audiencias musicales no tecnicas
- afinar heuristicas de cadencias y notas no armonicas para cello solo

## Future Work

- agregar un segundo caso de estudio, por ejemplo nocturnos de Chopin
- crear importadores especificos por fuente y por formato
- soportar comparacion entre ediciones del mismo corpus
- incorporar validaciones ritmicas y de alineacion score-audio mas finas
- explorar `kern` cuando exista mejor cobertura upstream

## Roadmap

1. cerrar el corpus oficial de Bach con score curado y audio privado organizado
2. estabilizar notebook y reportes para lectura musicologica
3. validar reproducibilidad del flujo sin depender de archivos privados
4. agregar un nuevo caso de estudio para probar la generalidad de la arquitectura
