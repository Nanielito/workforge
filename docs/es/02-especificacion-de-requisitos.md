# DOC-02 — Especificación de requisitos de software

| Campo | Valor |
| --- | --- |
| Estado | Borrador |
| Versión | 1.0.0 |
| Producto objetivo | WorkForge 2.5.x |
| Última actualización | 2026-10-19 |

## 1. Convenciones

**DEBE**, **NO DEBE**, **DEBERÍA** y **PUEDE** expresan la fuerza del requisito.
Los IDs son estables. Las realizaciones específicas de cada proveedor se
documentan en sus diseños y no se repiten aquí.

## 2. Requisitos de workspace y parsing

| ID | Requisito | Verificación |
| --- | --- | --- |
| RF-001 | `init` DEBE crear configuración, plantilla de credenciales, README para contribuidores, inbox y directorio de salida sin sobrescribir archivos existentes salvo que se use `--force`. | Unitaria |
| RF-002 | Un workspace DEBE cargar `workforge.yaml` y su `.env` local sin modificar el entorno del proceso. | Unitaria |
| RF-003 | El proveedor seleccionado DEBE usar `default_provider` por defecto y PUEDE ser reemplazado por el comando. | Unitaria/integración |
| RF-010 | El parser DEBE convertir cada sección `##` en un `Requirement`. | Unitaria |
| RF-011 | DEBE reconocer Source, Namespace, Priority, Milestone, Labels, texto descriptivo y líneas `- Task`. | Unitaria |
| RF-012 | Source y namespace ausentes DEBEN usar valores del workspace; prioridades no soportadas DEBEN normalizarse a `medium`. | Unitaria |

## 3. Requisitos de ejecución segura

| ID | Requisito | Verificación |
| --- | --- | --- |
| RF-020 | `preview` DEBE parsear e imprimir requisitos sin contactar un proveedor. | Unitaria/manual |
| RF-021 | `create` DEBE evitar escrituras externas con `--dry-run` o cuando `dry_run` sea verdadero sin `--execute`. | Unitaria/integración |
| RF-022 | La creación ejecutada DEBE retornar valores `CreatedItem` neutrales y PUEDE guardarlos como `items.json`. | Pruebas de proveedor |
| RF-023 | La configuración del proveedor DEBE validarse antes de la primera mutación cuando pueda validarse localmente. | Pruebas de proveedor |
| RF-024 | Credenciales y autorización NO DEBEN aparecer en salida, artefactos, fixtures ni errores traducidos por WorkForge. | Seguridad/revisión |

## 4. Requisitos de rastreo y sincronización

| ID | Requisito | Verificación |
| --- | --- | --- |
| RF-030 | `discover` DEBE retornar elementos abiertos y PUEDE filtrarlos por etiqueta, asignado y estado. | Pruebas de proveedor |
| RF-031 | Discovery guardado DEBE crear un `items.json` utilizable por comandos de estado y mutación. | Unitaria/proveedor |
| RF-032 | `status` DEBE mapear estado remoto y tareas administradas a valores neutrales `ItemStatus`. | Pruebas de proveedor |
| RF-033 | `agent-context` e `item-context` DEBEN distinguir tareas pendientes y completadas. | Unitaria |
| RF-034 | Las referencias de items DEBEN aceptar ID, título exacto o substring único y rechazar referencias ambiguas. | Unitaria |
| RF-035 | `update` DEBE emparejar por título exacto y previsualizar antes de mutar salvo que se use `--execute`. | Unitaria/proveedor |
| RF-036 | La sincronización DEBERÍA retener el estado de títulos sin cambios y preservar contenido no administrado. | Pruebas de proveedor |
| RF-037 | `complete-task` DEBE aceptar ID de tarea, título exacto o substring único y rechazar ambigüedad. | Pruebas de proveedor |
| RF-038 | Mutaciones exitosas DEBERÍAN actualizar por defecto el estado y contexto guardados. | Unitaria/proveedor |

## 5. Requisitos de proveedores

| ID | Requisito | Verificación |
| --- | --- | --- |
| RF-040 | Cada proveedor DEBE implementar el contrato completo `PlanningProvider`. | Tipos/registro |
| RF-041 | Identificadores y payloads específicos DEBEN permanecer en módulos y configuración del proveedor. | Revisión arquitectónica |
| RF-042 | `check` DEBE ser solo lectura y retornar un resultado neutral. | Pruebas de proveedor |
| RF-043 | Los métodos de red DEBEN usar timeouts limitados. | Revisión/pruebas |
| RF-044 | Las pruebas DEBEN inyectar `httpx.MockTransport` y NO DEBEN llamar servicios reales. | Revisión de pruebas |
| RF-045 | Fallos parciales de creación DEBEN aportar información no secreta para recuperación y no reportar éxito silencioso. | Pruebas de proveedor |

## 6. Requisitos no funcionales

| ID | Categoría | Requisito | Verificación |
| --- | --- | --- | --- |
| RNF-001 | Compatibilidad | CLI, opciones, campos del workspace, contratos de proveedor y artefactos DEBEN ser compatibles dentro de la versión mayor 2. | Revisión de release |
| RNF-002 | Portabilidad | El paquete DEBE soportar Python 3.11, 3.12 y 3.13. | CI |
| RNF-003 | Seguridad | Las credenciales DEBEN permanecer locales y protegidas de filtraciones. | Pruebas unitarias/proveedor |
| RNF-004 | Recuperación | Los artefactos de rastreo DEBERÍAN poder reconstruirse mediante discovery y estado en vivo. | Revisión de casos |
| RNF-005 | Mantenibilidad | El código compartido DEBE ser neutral y los proveedores usar el contrato común. | Revisión arquitectónica |
| RNF-006 | Distribución | Las releases DEBEN construir wheel y distribución fuente válidos antes de publicar. | Workflow de release |
| RNF-007 | Observabilidad | Los errores DEBERÍAN identificar configuración u operación fallida sin revelar secretos. | Pruebas de proveedor |

## 7. Notas de conformidad del borrador

La implementación 2.5.x tiene brechas conocidas respecto a esta línea base:

- `init --provider jira` aún no genera configuración ni claves específicas de Jira.
- `providers test` de Trello valida valores locales, pero no acceso remoto.
- La redacción de fallos HTTP de Trello no tiene cobertura regresiva explícita contra filtración del token.

Estas notas son entradas de seguimiento, no excepciones a los requisitos.

## 8. Reglas de trazabilidad

- Cada caso de uso referencia sus requisitos RF y RNF.
- DOC-04 asigna responsabilidades sin redefinir requisitos.
- Todo dato persistente o intercambiado aparece en DOC-05.
- Los diseños de proveedor explican RF-040 a RF-045.

## 9. Historial del documento

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Requisitos iniciales reconstruidos desde WorkForge 2.5.x |
