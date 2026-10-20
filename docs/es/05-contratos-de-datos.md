# DOC-05 — Contratos de datos

| Campo | Valor |
| --- | --- |
| Estado | Borrador |
| Versión | 1.0.0 |
| Producto objetivo | WorkForge 2.5.x |
| Última actualización | 2026-10-19 |

## 1. Convenciones

- Nombres y opciones de CLI, campos del workspace y artefactos guardados son contratos.
- Los campos Pydantic omitidos usan sus valores documentados.
- La configuración específica es un mapa abierto validado por el adaptador.
- Los artefactos JSON usan nombres de campos del modelo y texto UTF-8.
- La salida se agrupa usando el stem de la referencia de entrada.

## 2. DAT-001 — Documento Markdown de requisitos

Cada línea que comienza exactamente con `## ` inicia un requisito. El contenido
anterior al primero se ignora. Dentro del requisito, líneas vacías se ignoran y
los metadatos reconocidos usan sintaxis `Key: value`.

| Entrada | Cardinalidad | Mapeo |
| --- | --- | --- |
| `## Title` | Exactamente uno por sección | `Requirement.title` |
| `Source:` | Cero o un valor efectivo | `source`; default del workspace si se omite |
| `Namespace:` | Cero o un valor efectivo | `namespace`; default del workspace si se omite |
| `Priority:` | Cero o un valor efectivo | low, medium, high, urgent; de otro modo medium |
| `Milestone:` | Cero o un valor efectivo | Hito lógico neutral |
| `Labels:` | Cero o un valor efectivo | Etiquetas lógicas separadas por comas |
| `- Task` | Cero o más | Entradas `WorkTask` ordenadas |
| Otra línea no vacía | Cero o más | Descripción unida con saltos de línea |

Una aparición posterior del mismo metadato reemplaza la anterior. La sintaxis
de checkbox Markdown no tiene significado especial; las tareas usan `- `.

## 3. DAT-002 — Requirement y WorkTask

| Campo | Tipo | Requerido | Default/regla |
| --- | --- | ---: | --- |
| `Requirement.title` | string | Sí | Encabezado de sección |
| `description` | string | No | Cadena vacía |
| `source` | string | No | `manual` o default del workspace |
| `namespace` | string | No | `default` o default del workspace |
| `priority` | enum | No | `medium` |
| `milestone` | string/null | No | null |
| `labels` | list[string] | No | Lista vacía |
| `tasks` | list[WorkTask] | No | Lista vacía |
| `WorkTask.title` | string | Sí | Texto de la tarea |
| `WorkTask.done` | boolean | No | false |

Source, namespace y priority son metadatos. Cada proveedor decide qué otros
campos tienen representación remota.

## 4. DAT-003 — Configuración del workspace

```yaml
name: my-project
default_provider: github
providers:
  github: {}
defaults:
  source: manual
  namespace: organization/repository
  dry_run: true
```

| Campo | Tipo | Requerido | Default/regla |
| --- | --- | ---: | --- |
| `name` | string | Sí | Identidad del workspace |
| `default_provider` | string | No | `trello` |
| `providers` | map[string,map] | No | Mapa vacío |
| `defaults.source` | string | No | `manual` |
| `defaults.namespace` | string | No | `default` |
| `defaults.dry_run` | boolean | No | true |

El `.env` adyacente se parsea en un mapa de strings en memoria y se entrega
solo al proveedor seleccionado. `.env.example` documenta claves sin valores.

## 5. DAT-004 — CreatedItem

| Campo | Tipo | Requerido | Descripción |
| --- | --- | ---: | --- |
| `provider` | string | Sí | Nombre del adaptador |
| `id` | string | Sí | Identificador usado por operaciones posteriores |
| `url` | string/null | No | URL humana del proveedor |
| `title` | string | Sí | Título usado para mostrar y hacer matching exacto |

`items.json` es un arreglo JSON de `CreatedItem`. La carga filtra entradas por
el proveedor seleccionado actualmente.

## 6. DAT-005 — ItemStatus y TaskStatus

| Campo | Tipo | Requerido | Descripción |
| --- | --- | ---: | --- |
| `ItemStatus.provider` | string | Sí | Nombre del adaptador |
| `id` | string | Sí | Identificador del item |
| `url` | string/null | No | URL humana |
| `title` | string | Sí | Título en vivo o de respaldo |
| `closed` | boolean | No | false si no se reporta cerrado |
| `tasks` | list[TaskStatus] | No | Estado de tareas administradas |
| `TaskStatus.id` | string/null | No | Referencia del proveedor o determinista |
| `TaskStatus.title` | string | Sí | Texto de la tarea |
| `TaskStatus.done` | boolean | No | false |

`completed_tasks` es un conteo derivado y no se serializa como campo.

## 7. DAT-006 — Artefactos guardados

Para `inbox/release.md`, los artefactos viven en `output/release/`. Discovery
sin entrada usa `--output-name`, cuyo default es `discovered`.

| Artefacto | Productor | Contrato |
| --- | --- | --- |
| `preview.json` | preview o create dry-run con `--save` | Arreglo de Requirement |
| `items.json` | create ejecutado o discovery con `--save` | Arreglo de CreatedItem |
| `status.json` | status o actualización posterior a mutación | Arreglo de ItemStatus en vivo |
| `agent-context.md` | agent-context o actualización posterior a mutación | Items agrupados por tareas pendientes/completadas |
| `items/<slug>.md` | item-context | Contexto enfocado de un item |

Los slugs son texto tipo ASCII en minúsculas derivado del título; secuencias no
alfanuméricas se reemplazan por `-` y un resultado vacío se convierte en `item`.

## 8. Matching de referencias

| Objetivo | Matching aceptado |
| --- | --- |
| Operaciones generales | ID, título exacto sin distinguir mayúsculas o substring único |
| Update requisito-item | Solo título exacto sin distinguir mayúsculas |
| Tarea administrada | ID del proveedor, título exacto o substring único |

Cero coincidencias falla. Múltiples coincidencias fallan en vez de elegir una.

## 9. Compatibilidad

Dentro de la versión mayor 2, campos y significados existentes deben continuar
siendo legibles. Campos opcionales aditivos pueden llegar en una versión menor.
Renombres, eliminaciones, cambios de defaults, directorios o matching requieren
revisión explícita y pueden necesitar una versión mayor.

## 10. Historial del documento

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Contratos iniciales de entrada, modelos, workspace y artefactos |

