[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificación de escrituras sobre hardware

Un campo solo se marca `HARDWARE_WRITE_VERIFIED` cuando la integración local ha probado toda la ruta de escritura y lectura posterior contra un controlador físico. Un ACK o un códec autoconsistente no son suficientes.

La corrección del modo vacaciones en la 2.6.1 es un ejemplo deliberado de esta regla: el campo 49 es codificable según la aplicación antigua, pero el G6 actual probado respondió con ACK a la escritura local directa sin cambiar el estado en lecturas frescas. Por eso Home Assistant expone el estado de vacaciones únicamente como lectura.

## Secuencia requerida

Para un campo de configuración reversible:

1. **GET inicial** — leer el valor actual localmente.
2. **SET candidato** — enviar una única escritura con el códec que se quiere validar.
3. **GET independiente** — volver a consultar físicamente el controlador.
4. **Validación física/semántica** — confirmar que el estado observado significa lo esperado.
5. **Restauración** — volver a escribir el valor inicial.
6. **GET de restauración** — verificar que el estado original se ha recuperado.

No se debe utilizar estado cacheado del coordinator como evidencia.

Para una acción mecánica también debe comprobarse la fase o transición física esperada. Un bit coincidente sin el movimiento o estado esperado no es suficiente.

## Entrega ambigua

Si el SET ya se ha enviado pero se pierde la respuesta o hay timeout, **no se reenvía a ciegas**. El controlador podría haberlo ejecutado. Primero debe hacerse un GET nuevo y reconciliar el estado físico.

Esta regla es especialmente importante para regeneraciones y transiciones de vacaciones.

## Niveles de evidencia

- códec de la app → `LEGACY_APP_CODEC`;
- valor observado en el dispositivo → `DEVICE_STATE_OBSERVED`;
- cambio observado en cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura física independiente completa → `HARDWARE_WRITE_VERIFIED`.

Conocer el códec y demostrar que el hardware acepta la acción son evidencias independientes. Un campo puede conservar un write codec en `runxin/fields.py` para interoperabilidad y, al mismo tiempo, no formar parte de la superficie de escritura de Home Assistant.

## Estado actual Ypsilon G6 / F79D

Verificados localmente de extremo a extremo:

- campo 4 — reloj / sincronización;
- campo 6 — límite de consumo continuo;
- campo 10 — hora de regeneración;
- campo 43 — valor de cantidad de sal añadida;
- campo 47 — dureza del agua de entrada.

Pendientes o a revalidar:

- **campo 7 — umbral de cierre por caudal:** WaterDevice confirma que el códec correcto es little-endian. Las versiones anteriores a 2.6 utilizaban BE tanto al escribir como al leer y podían autoconfirmar el error. Se retira la antigua marca `HW` hasta probar físicamente el camino LE corregido;
- **campo 34 — escrituras mecánicas/máquina de estados:** solo deben exponerse acciones específicamente observadas y probadas; el códec por sí solo no autoriza todos los valores;
- **campo 49 — vacaciones:** el control local directo `1/0` está explícitamente **no verificado** en el G6 actual probado y no se expone en Home Assistant 2.6.1.

## Evidencia del fallo del campo 49

La UI WaterDevice antigua indica esta semántica:

- entrada solo desde station/system mode 0;
- establecer el flag de vacaciones;
- progresión antigua de preparación `0 -> 3 -> 7 -> 2 -> 8`;
- vacaciones estables = campo 49 verdadero + station 8;
- la fase 2 de vacaciones utiliza el 25% del tiempo normal de lavado lento para el progreso de la UI;
- salida iniciada desde station 8.

En el G6 físico actual del proyecto, la 2.6.0 realizó la comprobación crítica:

1. lectura inicial con `vacationPattern=false` y válvula en servicio;
2. SET local directo del campo 49;
3. ACK de transporte/protocolo;
4. lecturas locales independientes repetidas que continuaban devolviendo `vacationPattern=false`;
5. timeout sin confirmación física.

Esto descarta el método de escritura directa del campo 49 utilizado en la 2.6.0 como control de usuario para este firmware. La conclusión es más fuerte que «pendiente»: **este método concreto no funciona en el hardware probado**.

La aplicación actual del fabricante también contiene operaciones dedicadas de entrada/salida de vacaciones separadas del control genérico. Por tanto, Ypsilon no debe inventar una secuencia multi-campo o mecánica alternativa.

La 2.6.1 conserva:

- lectura/decodificación del campo 49;
- codificación legacy del campo 49 en la capa F79D reutilizable para investigación/interoperabilidad;
- sensor semántico de estado de vacaciones solo de lectura;

Y elimina:

- el switch de Modo vacaciones de Home Assistant;
- cualquier método del coordinator que escriba directamente el campo 49.

## Evidencia de agua y estadísticas

Un export real de histórico del G6 confirma que `dailyWaterConsumption` aumenta durante el día y se reinicia al cambiar de día. Esto respalda `TOTAL_INCREASING` para el campo 37.

Las mismas evidencias, junto con capturas de la app oficial, muestran que el valor vivo del campo 39 no es el mismo que las barras de totales semanales históricos de la app. Por ello los campos 39 y 41 no tienen `state_class`.

## Evidencia de sal

El campo 43 tiene SET/read-back local verificado y cambio observado también por la vía cloud. Su semántica antigua es «sal añadida» en kg: valida un valor de configuración/registro, no un sensor físico de nivel. La integración no debe inferir ni decrementar «sal restante» a partir de este campo.

## Regla de generalización

La evidencia de un controlador o firmware no debe generalizarse automáticamente a todos los dispositivos Runxin. Antes de ampliar soporte a otro transporte, rebrand o firmware, deben verificarse de forma independiente el códec y el comportamiento físico.

Consulta también [`waterdevice-audit.es.md`](waterdevice-audit.es.md).
