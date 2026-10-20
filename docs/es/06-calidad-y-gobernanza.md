# DOC-06 — Calidad y gobernanza

| Campo | Valor |
| --- | --- |
| Estado | Borrador |
| Versión | 1.0.0 |
| Producto objetivo | WorkForge 2.5.x |
| Última actualización | 2026-10-19 |

## 1. Estrategia

WorkForge evoluciona mediante capacidades neutrales pequeñas implementadas en
todos los proveedores. Las escrituras externas requieren autorización explícita
y las releases parten de `main` después de validación automatizada.

## 2. Definición de terminado

Un cambio está terminado cuando:

- implementa el comportamiento solicitado en el límite que lo posee;
- preserva neutralidad y compatibilidad pública;
- valida configuración antes de efectos cuando sea posible;
- incluye pruebas observables proporcionales al riesgo;
- supera pruebas focales y el equivalente local de CI;
- actualiza README, contratos, diseños y ejemplos afectados;
- no contiene credenciales, archivos ajenos ni afirmaciones no verificadas;
- entrega un resumen listo para PR con riesgos y verificación real.

## 3. Estrategia de pruebas

- Pruebas de parser y modelos para comportamiento neutral.
- Pruebas de workspace para configuración y aislamiento del entorno.
- Pruebas de helpers CLI para matching, rutas, artefactos y contexto.
- Pruebas de proveedores con `httpx.MockTransport` para peticiones, mapeos, paginación, fallos, ambigüedad y redacción.
- Ejecución completa de `pytest` en Python 3.11, 3.12 y 3.13 en CI.
- Validación de wheel y distribución fuente antes de release.

Las pruebas automatizadas excluyen llamadas reales. No existe objetivo porcentual
de cobertura; efectos, errores y cambios de contrato distintos requieren evidencia.

## 4. Compatibilidad y versionado

- Releases patch corrigen sin cambiar contratos públicos.
- Releases minor agregan comandos, capacidades, proveedores o campos compatibles.
- Releases major pueden cambiar contratos y requieren guía de migración.
- La automatización de release posee los cambios de versión y changelog generado.
- Cambios en APIs remotas que no alteren el contrato público pueden ser internos.

## 5. Gobernanza documental

1. Inglés es canónico y español se sincroniza en el mismo cambio.
2. Ambos idiomas preservan IDs, estados, versiones y significado normativo.
3. Un cambio de comportamiento revisa DOC-02, DOC-03, DOC-05 y el proveedor.
4. Un cambio arquitectónico revisa DOC-01, DOC-04 y la necesidad de ADR.
5. El historial registra cambios normativos, no correcciones tipográficas.
6. Documentos aprobados no se reescriben silenciosamente para cambiar decisiones.

## 6. Política de ADRs

Se requiere ADR para una decisión durable que cambie:

- límites neutrales al proveedor;
- contratos persistentes del workspace o artefactos;
- límites de confianza o credenciales;
- semántica de consistencia y reintentos;
- modelo de empaquetado o despliegue;
- una alternativa rechazada que probablemente reaparezca.

Los ADR usan `Proposed`, `Accepted`, `Rejected`, `Superseded` o `Retired` y
declaran contexto, opciones, decisión, consecuencias, validación y condiciones
de revisión. Los retrospectivos indican que formalizan una base implementada.

## 7. Riesgos

| ID | Riesgo | Impacto | Tratamiento |
| --- | --- | ---: | --- |
| RSK-001 | Comportamiento divergente detrás de un comando neutral | Alto | Contrato compartido y pruebas cruzadas |
| RSK-002 | Creación parcial produce duplicados al reintentar | Alto | Preview, ejecución explícita y límites documentados |
| RSK-003 | Credenciales aparecen en errores o artefactos | Alto | Entorno aislado y pruebas de redacción |
| RSK-004 | Formatos guardados cambian sin migración | Alto | DOC-05 y gate SemVer |
| RSK-005 | Cambios de API remota rompen un adaptador | Medio | Pruebas de contrato y verificación de release |
| RSK-006 | Traducciones divergen | Medio | Sincronización en el mismo cambio e IDs estables |
| RSK-007 | Salida generada se confunde con estado autoritativo | Medio | Lecturas en vivo y guía de recuperación |
| RSK-008 | La CLI acumula lógica del proveedor | Medio | Mantener payloads y API en adaptadores |

## 8. Proceso de cambio

1. Comenzar desde un requisito acotado o issue rastreado.
2. Previsualizar cambios externos antes de ejecutarlos.
3. Reclamar el item y moverlo a `doing` al iniciar implementación.
4. Completar tareas solo después de su verificación relevante.
5. Mantener el issue abierto mientras el pull request está en revisión.
6. Permitir que el PR integrado cierre el issue y la automatización finalice estado.

Los detalles operativos para agentes y commits permanecen en `AGENTS.md`; este
documento define calidad y gobernanza a nivel producto.

## 9. Gates de revisión

- **Contrato:** ningún cambio de CLI, workspace, modelo o artefacto sin documentar.
- **Proveedor:** cada proveedor concreto satisface la capacidad compartida.
- **Seguridad:** sin salida o fixtures con secretos y sin tráfico real en pruebas.
- **Release:** pruebas, build, metadatos, tag y artefactos coinciden.
- **Documentación:** línea base canónica y traducción permanecen sincronizadas.

## 10. Historial del documento

| Versión | Fecha | Cambio |
| --- | --- | --- |
| 1.0.0 | 2026-10-19 | Línea base inicial de calidad y gobernanza |

