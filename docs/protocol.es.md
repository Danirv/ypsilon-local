[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capas del protocolo y evidencia

Ypsilon separa explícitamente las capas:

```text
Política Home Assistant -> cliente/códec F79D -> trama Runxin cruda
                                                -> transporte -> dispositivo
```

El paquete `runxin/` no depende de Home Assistant ni de BroadLink. `transport/broadlink_bl3372.py` concentra autenticación, sesión, cifrado y política de reintentos BroadLink.

## Trama y códecs F79D

El controlador probado utiliza una trama exterior `5A 5C ... A5` con una trama interior `DF FD ... DE`, ambas con checksum aditivo de 8 bits. Los opcodes observados son `0x09` para consulta y `0x19` para control/escritura; las respuestas son `0xC9` y `0xD9`.

Cada campo viaja como `[field_id, byte_1, byte_2]`. No existe una endianidad global: `runxin/fields.py` es la autoridad por campo.

En el Ypsilon G6 físico probado:

- campo 7 (`flowRateOff`) — `u16_be` en lectura y escritura;
- campo 11 (`flowRate`) — `u16_be`;
- campos 12, 25, 47 y 52 — `u16_le`;
- los volúmenes 35/37/39/41 dependen de `waterVolumeUnit`.

El campo 7 conserva documentada una discrepancia con el camino recuperado de WaterDevice, que parecía usar un helper LE. La evidencia física es concluyente:

```text
03 E8 -> BE 1000 -> 10,00 m³/h
03 E8 -> LE 59395 -> 593,95 m³/h
```

La app oficial mostraba 10,00 m³/h mientras la regresión LE de Ypsilon 2.6.2 mostraba 593,95 m³/h. Una escritura de 2,00 m³/h es raw 200 y debe enviarse como `00 C8`; la regresión LE enviaba `C8 00`, recibía ACK de transporte pero fallaba el read-back físico. Versiones anteriores con BE ya habían pasado SET/read-back real, por lo que el campo 7 vuelve a ser `HARDWARE_WRITE_VERIFIED`.

## Modelo de evidencia

- `legacy_app_codec` — recuperado del códec WaterDevice;
- `device_state_observed` — observado en datos reales;
- `hardware_write_verified` — SET local + GET físico nuevo + validación semántica;
- `cloud_write_observed` — cambio observado por la vía del fabricante;
- `inferred` — interpretación todavía no confirmada directamente.

Un ACK no es evidencia física. Cuando una interpretación de la app entra en conflicto con bytes/read-back independientes del controlador, prevalece la evidencia física para el hardware probado y la discrepancia se documenta.

El campo 49 es el ejemplo negativo complementario: el códec antiguo puede serializar vacaciones, pero en el G6 probado el SET local directo recibió ACK y las lecturas frescas siguieron sin cambiar. Ese método no es un control verificado.

## Semántica de las escrituras

Las lecturas pueden reintentarse porque son idempotentes. Las escrituras no se duplican a ciegas:

1. enviar SET una sola vez;
2. si la respuesta es ambigua, no reenviar;
3. hacer un GET físico nuevo;
4. reconciliar el estado;
5. confirmar únicamente cuando el valor real coincide.

La regresión LE del campo 7 demuestra que esta arquitectura funciona: el ACK no se convirtió en un falso éxito porque el read-back no coincidía.

## Superficie Home Assistant

`write_fields` queda limitado a configuraciones reversibles y valida rangos/unidades. Los campos mecánicos 34 y 49 quedan fuera del servicio genérico. El campo 49 continúa solo en lectura hasta que una secuencia local correcta se verifique físicamente.

## Agua, estadísticas y sal

El histórico real confirma que el campo 37 es un contador acumulado dentro del día que se reinicia al cambiar de día; por eso usa `TOTAL_INCREASING`. El campo 39 es una media semanal del controlador y no es lo mismo que las barras históricas semanales de la app. El campo 41 es capacidad de tratamiento por ciclo, no un contador acumulativo. Ninguno declara `state_class`.

El campo 43 es una cantidad de sal añadida/registrada por el controlador, no un nivel físico de sal.

## Campo 52

El bloque normal sigue siendo 1..51. El campo 52 se consulta y cachea por separado porque es un intervalo de servicio que cambia lentamente. Es política de polling de la capa Ypsilon, no una limitación del códec F79D.

## Transporte BL3372

El BL3372 antepone una longitud little-endian de dos bytes a la trama Runxin y la envía mediante el comando BroadLink `0x6A`. Cifrado, autenticación, outer errors y reintentos son responsabilidad del transporte.

## Límite de compatibilidad

La evidencia fuerte corresponde al conjunto ATH/BWT Ypsilon G6 + Runxin F79D + BroadLink BL3372 probado. Otros controladores o firmwares deben volver a validar framing, campos, endianidad, escalado, escrituras y máquina de estados.

Véase [`f79d.es.md`](f79d.es.md), [`waterdevice-audit.es.md`](waterdevice-audit.es.md) y [`hardware-verification.es.md`](hardware-verification.es.md).
