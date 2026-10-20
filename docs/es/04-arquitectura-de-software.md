# DOC-04 — Arquitectura de software

| Campo | Valor |
| --- | --- |
| Estado | Borrador |
| Versión | 1.0.0 |
| Producto objetivo | WorkForge 2.5.x |
| Última actualización | 2026-10-19 |

## 1. Drivers

- Un flujo para diferentes proveedores de planificación.
- Inspección segura antes de mutaciones externas.
- Credenciales aisladas por workspace.
- Contratos estables de CLI y salida guardada.
- Adaptadores pequeños comprobables sin servicios externos.
- Contexto útil para contribuidores humanos y agentes.

## 2. Decisión estructural

WorkForge es un paquete Python con cuatro áreas de responsabilidad:

```text
Entrada Markdown
    │
    ▼
parser ──► modelos neutrales al proveedor
               │
workspace ─────┤
               ▼
       orquestación CLI ──► adaptador ──► API de planificación remota
               │
               └──────────────────────► artefactos locales
```

| Componente | Responsabilidad |
| --- | --- |
| `config.py` | Cargar y validar un workspace y su entorno aislado |
| `core/parser.py` | Convertir secciones Markdown en modelos `Requirement` |
| `models.py` | Definir contratos neutrales de entrada, salida y estado |
| `cli.py` | Orquestar comandos, efectos, matching, salida y persistencia |
| `providers/base.py` | Definir el contrato completo de comportamiento |
| `providers/registry.py` | Seleccionar un proveedor concreto por nombre |
| `providers/*.py` | Traducir operaciones neutrales a una API remota |

La CLI depende del contrato neutral. Los proveedores dependen de modelos
neutrales. Los modelos y parser compartidos no dependen de payloads remotos.

## 3. Flujos principales

### Requisito primero

```text
cargar workspace → parsear Markdown → preview → create explícito → guardar items
```

### Proveedor primero

```text
cargar workspace → descubrir items remotos → guardar items → leer/mutar estado
```

### Sincronización de tareas

```text
parsear Markdown → match por título exacto → preview → actualización explícita
```

`items.json` es el índice local que conecta comandos posteriores con elementos
remotos. No es un caché de todo el estado: estados y tareas se consultan en vivo.

## 4. Límites de efectos

| Operación | Lectura local | Escritura local | Lectura remota | Escritura remota |
| --- | ---: | ---: | ---: | ---: |
| `init` | Opcional | Sí | No | No |
| `preview` | Sí | Opcional | No | No |
| `create` dry-run | Sí | Opcional | No | No |
| `create` ejecutado | Sí | Opcional | Sí | Sí |
| `providers test` | Sí | No | Sí | No |
| `discover` | Sí | Opcional | Sí | No |
| `status` / contexto | Sí | Opcional | Sí | No |
| `update` en preview | Sí | No | No | No |
| Mutaciones ejecutadas | Sí | Usualmente | Sí | Sí |

La autorización externa corresponde al llamador. WorkForge aporta dry-run y
preview, pero no puede inferir aprobación organizacional.

## 5. Límites de confianza

Son entradas no confiables:

- requisitos Markdown y YAML del workspace;
- valores del `.env` local;
- JSON guardado que haya sido editado externamente;
- referencias y comentarios recibidos por CLI;
- respuestas y errores de APIs remotas;
- títulos y tareas del proveedor renderizados en contexto Markdown.

Pydantic valida modelos compartidos. Los adaptadores validan configuración,
usan clientes HTTP con timeout y traducen errores cuando es necesario. Ninguna
credencial se copia al entorno global del proceso.

## 6. Contenido administrado y propiedad

WorkForge posee únicamente la representación de tareas definida por cada
proveedor: sección `## Tasks` en GitHub, lista ADF identificada en Jira y
checklists `Tasks` en Trello. La sincronización puede reemplazar esa zona y
preserva descripciones, comentarios, campos y checklists externos.

El proveedor es autoritativo para el estado del item. Los artefactos locales son
desechables, salvo cuando el usuario versiona intencionalmente el requisito.

## 7. Consistencia y fallos

- Los comandos operan secuencialmente; no existe transacción entre items.
- La creación con múltiples peticiones puede completarse parcialmente.
- Los reintentos no son universalmente idempotentes y pueden duplicar items.
- La salida se guarda únicamente cuando el comando alcanza su etapa de guardado.
- El matching por substring solo tiene éxito cuando es único.
- Discovery es la ruta de recuperación cuando falta el índice local.

Los detalles de recuperación pertenecen al diseño de cada proveedor.

## 8. Seguridad

- Los secretos viven en `.env`, no en YAML ni ejemplos versionados.
- La carga del entorno es local y no modifica `os.environ`.
- Errores, pruebas, fixtures y salida deben evitar tokens y autorización.
- Las pruebas usan transportes simulados; no reciben credenciales reales.
- Preview y comprobaciones del proveedor no mutan sistemas remotos.

## 9. Reglas de evolución

- Un proveedor nuevo implementa juntos el contrato completo y su registro.
- Una capacidad compartida se expresa neutralmente y se implementa en todos los proveedores.
- Un cambio incompatible de CLI o formato requiere versión mayor y migración.
- Sincronización continua, base de datos o concurrencia requieren otra decisión arquitectónica.

## 10. Historial del documento

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Arquitectura inicial reconstruida desde WorkForge 2.5.x |

