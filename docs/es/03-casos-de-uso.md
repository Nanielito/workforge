# DOC-03 — Casos de uso

| Campo | Valor |
| --- | --- |
| Estado | Borrador |
| Versión | 1.0.0 |
| Producto objetivo | WorkForge 2.5.x |
| Última actualización | 2026-10-19 |

## 1. Actores

- **Mantenedor:** configura un workspace y autoriza escrituras externas.
- **Contribuidor:** reclama y progresa un elemento de planificación existente.
- **Agente de automatización:** consume contexto guardado y realiza trabajo acotado.
- **Proveedor de planificación:** almacena elementos remotos y es un sistema externo no confiable.
- **Sistema de archivos:** almacena requisitos versionados, secretos locales y artefactos generados.

## 2. Catálogo

| ID | Caso de uso | Requisitos |
| --- | --- | --- |
| CU-001 | Inicializar y validar un workspace | RF-001–003, RF-024, RF-042 |
| CU-002 | Previsualizar y crear elementos | RF-010–012, RF-020–024, RF-045 |
| CU-003 | Descubrir y continuar elementos existentes | RF-030–034, RNF-004 |
| CU-004 | Sincronizar tareas del requisito | RF-035–036 |
| CU-005 | Progresar un elemento rastreado | RF-032–034, RF-037–038 |
| CU-006 | Generar contexto para agentes | RF-032–034 |
| CU-007 | Diagnosticar configuración o fallos del proveedor | RF-023–024, RF-042–045, RNF-007 |

## 3. CU-001 — Inicializar y validar un workspace

1. El mantenedor ejecuta `workforge init` con proveedor y namespace.
2. WorkForge crea solo archivos faltantes salvo que se use `--force`.
3. El mantenedor copia `.env.example` a `.env` e incorpora credenciales.
4. `providers test` carga únicamente ese workspace y valida configuración y,
   cuando se soporta, acceso remoto sin mutar.

**Alternativa:** configuración inválida o ausente produce un fallo útil; ningún elemento se modifica.

## 4. CU-002 — Previsualizar y crear elementos

1. El mantenedor escribe una o más secciones de requisitos Markdown.
2. `preview`, o `create` en dry-run, emite requisitos neutrales.
3. El mantenedor revisa título, metadatos, descripción y tareas.
4. Un `create` ejecutado explícitamente envía cada requisito al proveedor.
5. Con `--save`, WorkForge guarda IDs, títulos, URLs y nombres de proveedor.

**Alternativas:** el dry-run del workspace impide la mutación; un fallo del proveedor detiene el comando. La creación en varios pasos puede dejar un elemento remoto parcial recuperable.

## 5. CU-003 — Descubrir y continuar elementos existentes

1. El contribuidor ejecuta `discover` con filtros opcionales.
2. El proveedor retorna elementos abiertos dentro de su alcance configurado.
3. Con `--save`, WorkForge crea `items.json` bajo el nombre de salida elegido.
4. El contribuidor usa esa referencia con comandos de estado y mutación.

**Alternativa:** discovery puede repetirse para reconstruir rastreo local; no recrea elementos remotos.

## 6. CU-004 — Sincronizar tareas del requisito

1. El mantenedor edita tareas en el documento de requisitos.
2. `update` empareja cada requisito con un elemento guardado por título exacto.
3. Sin `--execute`, WorkForge imprime la lista propuesta.
4. Con `--execute`, el proveedor reemplaza solo su contenido administrado.
5. El estado se conserva para títulos sin cambios cuando el proveedor lo soporta.

**Alternativas:** títulos ausentes o duplicados fallan antes de mutar; el contenido externo queda fuera de la propiedad de WorkForge.

## 7. CU-005 — Progresar un elemento rastreado

1. El contribuidor selecciona por ID, título exacto o substring único.
2. `claim-item` lo asigna, normalmente a `@me`.
3. `move-item` cambia su estado o lista.
4. `comment-item` registra una nota cuando sea necesario.
5. Tras implementar y verificar una tarea, `complete-task` la marca terminada.
6. WorkForge actualiza estado y contexto guardados por defecto.

**Alternativas:** referencias ambiguas fallan sin elegir arbitrariamente; workflows del proveedor pueden rechazar transiciones no disponibles.

## 8. CU-006 — Generar contexto para agentes

1. WorkForge lee elementos guardados y obtiene su estado remoto en vivo.
2. `agent-context` agrupa tareas pendientes y terminadas de todos los elementos.
3. `item-context` selecciona un elemento y emite guía de implementación enfocada.
4. Con `--save`, el Markdown queda junto a sus artefactos de rastreo.

## 9. CU-007 — Diagnosticar un fallo

1. WorkForge valida workspace y proveedor tan pronto como la operación permita.
2. Reporta el recurso, campo u operación que falló.
3. Omite credenciales y material de autorización.
4. Si existe un elemento remoto parcial, identifica un objetivo seguro de recuperación cuando esté disponible.

## 10. Historial del documento

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Casos de uso iniciales para WorkForge 2.5.x |
