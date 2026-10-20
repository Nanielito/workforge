# DOC-01 — Visión y alcance

| Campo | Valor |
| --- | --- |
| Estado | Borrador |
| Versión | 1.0.0 |
| Producto objetivo | WorkForge 2.5.x |
| Última actualización | 2026-10-19 |

## 1. Propósito

Definir el problema que resuelve WorkForge, sus usuarios, el límite actual del
producto y sus principios. Los compromisos verificables se encuentran en
[DOC-02](02-especificacion-de-requisitos.md).

## 2. Problema

Los equipos suelen describir trabajo en Markdown, pero gestionan la entrega en
sistemas específicos de un proveedor. Recrear manualmente issues, tarjetas,
listas de tareas, estados y contexto para agentes duplica esfuerzo y hace que la
automatización dependa de un solo proveedor.

## 3. Visión

WorkForge es una CLI local-first que convierte requisitos legibles en elementos
de planificación neutrales al proveedor y sincroniza su estado operativo con
Trello, GitHub Projects y Jira.

**Promesa actual:** el mismo requisito y flujo de CLI puede previsualizarse,
crearse, descubrirse, inspeccionarse y progresar sin filtrar conceptos del
proveedor al dominio compartido ni a los artefactos del workspace.

## 4. Usuarios

| Actor | Necesidad |
| --- | --- |
| Mantenedor | Convertir requisitos revisados en elementos del proveedor de forma segura |
| Contribuidor | Reclamar un elemento, comprender sus tareas y reportar progreso |
| Agente de automatización | Consumir contexto estable y completar tareas rastreadas |
| Equipo | Cambiar de proveedor de planificación sin cambiar el modelo de requisitos |

## 5. Alcance actual

- CLI para Python 3.11+ distribuida mediante PyPI.
- Workspaces locales al proyecto o compartidos con credenciales aisladas.
- Requisitos Markdown con metadatos y listas de tareas.
- Previsualización antes de escrituras externas.
- Proveedores Trello, GitHub Projects v2 personales y Jira Cloud.
- Creación, descubrimiento, estado, comentarios, asignación, movimiento y finalización de tareas.
- Artefactos JSON y Markdown neutrales al proveedor para rastreo local y contexto de agentes.
- Sincronización de listas de tareas desde requisitos hacia elementos existentes.

## 6. Fuera de alcance

- Alojar un servicio de planificación, base de datos o almacén de credenciales.
- Sincronización continua, polling o webhooks.
- Crear o administrar proyectos, tableros, workflows, campos, etiquetas o hitos del proveedor.
- Garantizar atomicidad en operaciones del proveedor que requieren múltiples peticiones.
- Sincronización bidireccional arbitraria del contenido del proveedor.
- Usar múltiples proveedores dentro del mismo conjunto de elementos guardados.
- Tratar la salida generada como fuente de verdad remota.

## 7. Principios

1. Contratos neutrales al proveedor antes que comportamiento específico.
2. Previsualización antes de mutaciones externas.
3. Las credenciales permanecen limitadas a un workspace.
4. El estado remoto es autoritativo; la salida local es estado de rastreo recuperable.
5. El contenido administrado de tareas se modifica de forma limitada; el resto se preserva.
6. CLI, configuración y formatos guardados conservan compatibilidad dentro de una versión mayor.
7. Las abstracciones nuevas siguen necesidades demostradas por proveedores reales.

## 8. Indicadores de éxito

- Un contribuidor puede inicializar un workspace y validar la configuración de su proveedor siguiendo el README.
- Un requisito revisado crea elementos equivalentes en los proveedores soportados.
- Discovery reconstruye el rastreo local si se elimina la salida generada.
- Completar una tarea modifica únicamente la tarea administrada correspondiente.
- Las pruebas de proveedores se ejecutan sin servicios externos ni credenciales reales.
- Los errores y artefactos no exponen secretos del workspace.

## 9. Futuro no comprometido

Proveedores adicionales, GitHub Projects de organizaciones, formatos de
requisitos más ricos, sincronización continua y protocolos para máquinas
requieren evidencia y un cambio explícito de contrato antes de adoptarse.

## 10. Historial del documento

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Línea base técnica retrospectiva inicial |
