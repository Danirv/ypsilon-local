# Auditoría de WaterDevice antiguo / F79D

Este documento recoge la evidencia utilizada por Ypsilon Local para separar **conocimiento del códec**, **estado observado del controlador** y **escrituras verificadas físicamente**. El objetivo es evitar que un campo recuperado de la aplicación se confunda con un control seguro en firmware actual.

## Política de evidencia

Las etiquetas de `runxin/fields.py` significan:

- `LEGACY_APP_CODEC`: campo/codificación recuperado del códec antiguo;
- `DEVICE_STATE_OBSERVED`: campo observado en estado real del controlador;
- `HARDWARE_WRITE_VERIFIED`: una escritura local ha sido confirmada mediante una lectura fresca posterior;
- `CLOUD_WRITE_OBSERVED`: el mismo ajuste también se ha observado cambiando por la vía del fabricante.

Un ACK de transporte, por sí solo, **no** es una verificación física. Cuando la interpretación del códec antiguo entra en conflicto con el controlador real, prevalece la evidencia física del hardware probado.

## Códec F79D

El perfil recuperado utiliza opcode de consulta `0x09` y control `0x19`. Resultados relevantes:

- campo 7 `flowRateOff`: **16 bits big-endian en el Ypsilon G6 probado**, verificado con escritura/read-back físicos;
- campo 11 `flowRate`: 16 bits big-endian en el cable;
- campo 33: dos flags de recordatorio;
- campos 35/37/39/41: valores de volumen de tres bytes repartidos entre dos TLV y dependientes de `waterVolumeUnit`;
- campos 50/51: minutos restantes de disolución de sal y pausa 1;
- campo 52: intervalo de servicio del material filtrante, consultado por separado por la integración.

### Campo 7: discrepancia del códec antiguo resuelta por el hardware

El camino recuperado de WaterDevice parecía tratar el campo 7 con un helper little-endian. El G6 físico lo contradice de forma concluyente:

```text
bytes en el cable: 03 E8
big-endian:    0x03E8 = 1000 -> 10,00 m³/h
little-endian: 0xE803 = 59395 -> 593,95 m³/h
```

La app oficial mostraba 10,00 m³/h mientras Ypsilon 2.6.2, después de cambiar el campo 7 a LE, mostraba 593,95 m³/h. Por tanto este controlador es BE.

La vía de escritura lo corrobora de forma independiente. Una petición de 2,00 m³/h es raw 200 (`0x00C8`) y debe enviarse como `00 C8`. La regresión LE enviaba `C8 00`; el controlador devolvía ACK de transporte/protocolo pero las lecturas frescas no confirmaban el valor solicitado. La reconciliación estricta de Ypsilon mostraba correctamente `Write ACKed but not confirmed`.

Versiones anteriores del proyecto con BE ya habían completado correctamente el SET/read-back local del campo 7. Por ello se restaura `HARDWARE_WRITE_VERIFIED` y se conserva documentada la discrepancia con el códec antiguo.

## Volúmenes, agua y estadísticas

Para unidades 0/1 los volúmenes 35/37/39/41 se reconstruyen como un entero LE de 24 bits. Para unidad 2 se utiliza empaquetado decimal base-100 y la magnitud en m³ se muestra dividida por 100. Si falta la unidad o el TLV de continuación, la integración devuelve `None`.

**37–38 Consumo diario** es el contador acumulado del día y los datos reales confirman que se reinicia al cambiar de día; Home Assistant utiliza `TOTAL_INCREASING`.

**39–40 Consumo semanal medio del controlador** no es el total semanal de las barras históricas de la app oficial y no tiene `state_class`.

**41–42 Capacidad de tratamiento por ciclo** es una magnitud de capacidad/configuración, no un contador acumulativo, y tampoco tiene `state_class`.

## Sal

El campo 43 `addSalt` es una **cantidad de sal añadida** de 0 a 100 kg. La escritura local se ha verificado físicamente y también se ha observado el cambio por la vía del fabricante. No es un sensor físico de sal restante y Ypsilon Local no lo decrementa después de una regeneración.

## Vacaciones

La UI antigua modela las vacaciones con el campo 49 y la progresión `0 -> 3 -> 7 -> 2 -> 8`. En el G6 probado, una escritura local directa del campo 49 recibió ACK pero las lecturas frescas siguieron devolviendo `vacationPattern=false`. Por tanto el campo se sigue leyendo y codificando para investigación/interoperabilidad, pero no está `HARDWARE_WRITE_VERIFIED` y no se expone ningún switch de escritura en Home Assistant.

## Campo 52

La consulta normal sigue siendo 1..51. El campo 52 se consulta y cachea por separado porque es un intervalo de servicio que cambia lentamente. Es una política de polling de la integración, no una limitación del protocolo.

## Regla de publicación

Un control nuevo solo debe exponerse cuando estén resueltos: codificación, precondiciones, aceptación física, read-back y comportamiento ante timeout/reinicio. Conocer únicamente el códec es suficiente para implementarlo, pero no para exponerlo como control de usuario.
