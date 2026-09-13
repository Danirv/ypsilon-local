[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificación de escrituras sobre hardware

Un campo solo se marca `HARDWARE_WRITE_VERIFIED` cuando la integración local ha probado toda la ruta de escritura y lectura posterior contra un controlador físico. Un ACK o un códec autoconsistente no son suficientes.

La corrección del modo vacaciones en la 2.6.1 sigue siendo un ejemplo deliberado de esta regla: el campo 49 es codificable según la aplicación antigua, pero el G6 probado respondió con ACK a la escritura local directa sin cambiar el estado en lecturas frescas. Por eso Home Assistant expone el estado de vacaciones únicamente como lectura.

## Secuencia requerida

Para un campo de configuración reversible:

1. **GET inicial** — leer el valor actual localmente.
2. **SET candidato** — enviar una única escritura con el códec que se quiere validar.
3. **GET independiente** — volver a consultar físicamente el controlador.
4. **Validación física/semántica** — confirmar que el estado observado significa lo esperado.
5. **Restauración** — volver a escribir el valor inicial.
6. **GET de restauración** — verificar que el estado original se ha recuperado.

No se debe utilizar estado cacheado del coordinator como evidencia. Para una acción mecánica también debe comprobarse la fase o transición física esperada.

## Entrega ambigua

Si el SET ya se ha enviado pero se pierde la respuesta o hay timeout, **no se reenvía a ciegas**. El controlador podría haberlo ejecutado. Primero debe hacerse un GET nuevo y reconciliar el estado físico.

## Niveles de evidencia

- códec de la app → `LEGACY_APP_CODEC`;
- valor observado en el dispositivo → `DEVICE_STATE_OBSERVED`;
- cambio observado en cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura física independiente completa → `HARDWARE_WRITE_VERIFIED`.

## Estado actual Ypsilon G6 / F79D

Verificados localmente de extremo a extremo:

- campo 4 — reloj / sincronización;
- campo 6 — límite de consumo continuo;
- **campo 7 — umbral de cierre por caudal, u16 big-endian**;
- campo 10 — hora de regeneración;
- campo 43 — cantidad de sal añadida;
- campo 47 — dureza del agua de entrada.

Pendientes o deliberadamente no verificados:

- **campo 34** — escrituras mecánicas/máquina de estados más allá del comportamiento específico ya probado;
- **campo 49** — el control local directo `1/0` de vacaciones está explícitamente no verificado en el G6 probado y no se expone como control de HA.

## Evidencia del campo 7

El G6 físico resuelve el orden de bytes del campo 7 independientemente de la interpretación de la aplicación antigua:

```text
bytes en el cable: 03 E8
big-endian:    0x03E8 = 1000 -> 10,00 m³/h
little-endian: 0xE803 = 59395 -> 593,95 m³/h
```

La app oficial mostraba 10,00 m³/h mientras Ypsilon 2.6.2, con la regresión LE, mostraba 593,95 m³/h. La vía de escritura aporta una segunda prueba: 2,00 m³/h son raw 200 (`0x00C8`) y deben enviarse como `00 C8`; la regresión LE enviaba `C8 00`, recibía ACK pero el read-back físico no cambiaba y el coordinator generaba `Write ACKed but not confirmed`.

Versiones anteriores del proyecto con BE ya habían completado correctamente el SET/read-back físico del campo 7. Sumando aquella verificación a la evidencia actual independiente, el campo 7 vuelve a estar `HARDWARE_WRITE_VERIFIED`. La discrepancia con el códec antiguo se conserva documentada, pero para el G6 probado prevalece el controlador real.

## Evidencia del fallo del campo 49

La UI antigua modela la entrada en vacaciones desde station 0, la progresión `0 -> 3 -> 7 -> 2 -> 8` y el estado estable como campo 49 verdadero + station 8. En el G6 probado, sin embargo, un SET local directo del campo 49 recibió ACK y lecturas locales independientes repetidas siguieron devolviendo `vacationPattern=false` hasta el timeout. Por tanto ese método concreto no funciona en el hardware probado y Ypsilon no inventa una secuencia mecánica alternativa.

## Evidencia de agua y sal

El histórico real confirma que `dailyWaterConsumption` aumenta durante el día y se reinicia al cambiar de día, lo que respalda `TOTAL_INCREASING` para el campo 37. Las capturas de la app oficial muestran que el campo 39 no es la misma magnitud que las barras de totales semanales históricos, por lo que los campos 39 y 41 no tienen `state_class`.

El campo 43 tiene SET/read-back local verificado y cambio observado por cloud. Su semántica es «sal añadida» en kg, no un sensor físico de nivel.

## Campo 52

El campo 52 queda intencionadamente fuera del bloque normal 1..51. La capa Ypsilon lo consulta y cachea por separado porque es un intervalo de servicio que cambia lentamente.

## Regla de generalización

La evidencia de un controlador o firmware no debe generalizarse automáticamente a todos los dispositivos Runxin. Antes de ampliar soporte a otro transporte, rebrand o firmware, deben verificarse de forma independiente el códec y el comportamiento físico.

Consulta también [`waterdevice-audit.es.md`](waterdevice-audit.es.md).
