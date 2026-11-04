# Bach Cello Suites Case Study

Este es el primer caso de estudio oficial del proyecto.

## Alcance

- compositor: Johann Sebastian Bach
- coleccion: Suites para violonchelo solo `BWV 1007-1012`
- subconjunto analizado: solo los preludios

## Intencion

La arquitectura del repo ya no asume que el unico corpus posible sea este. La idea es que cualquier nueva coleccion, por ejemplo nocturnos de Chopin, pueda montarse con la misma estructura:

- `catalog/`: manifiesto canonico de piezas
- `symbolic/official_curated/`: corpus simbolico publico y reproducible
- `symbolic/raw_pdfs/`: fuentes crudas locales o restringidas
- `symbolic/converted/`: salidas intermedias de OMR
- `audio/inbox/`: dropbox local para audios aun sin normalizar
- `audio/private_reference/`: corpus privado y consistente para comparacion expresiva

## Politica

- el score curado es la fuente principal para armonia
- el audio privado sirve para expresion y para validaciones ligeras score-audio
- los raw PDFs y audios privados no van a GitHub
