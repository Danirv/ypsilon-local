[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capas del protocolo y evidencia

Ypsilon separa explícitamente las capas:

```text
Política Home Assistant -> cliente/códec F79D -> trama Runxin cruda
                                                -> transporte -> dispositivo
```

El paquete `runxin/` no depende de Home Assistant ni de BroadLink. `transport/broadlink_bl3372.py` concentra autenticación, sesión, cifrado y política de reintentos BroadLink.

## Trama y códecs F79D

El controlador probado utiliza una trama exterior `5A 5C ... A5` con una trama interior `DF FD ... DE`. Ambas capas llevan checksum aditivo de 8 bits.

Opcodes observados:

- `0x09` — consulta de campos;
- `0x19` — control/escritura;
- respuestas `0xC9` y `0xD9` respectivamente.

Cada campo viaja como `[field_id, byte_1, byte_2]`. No existe una endianidad global: `runxin/fields.py` es la autoridad por campo.

El códec WaterDevice confirma:

- campo 7 (`flowRateOff`) — `u16_le`;
- campo 11 (`flowRate`) — `u16_be`, porque la app invierte explícitamente este campo;
- los volúmenes 35/37/39/41 dependen de `waterVolumeUnit`.

Véase [`f79d.es.md`](f79d.es.md).

## Modelo de evidencia

- `legacy_app_codec` — recuperado del códec WaterDevice;
- `device_state_observed` — observado en datos reales;
- `hardware_write_verified` — SET local + GET físico nuevo + validación semántica;
- `cloud_write_observed` — cambio observado por la vía del fabricante;
- `inferred` — interpretación todavía no confirmada directamente.

Un ACK no es evidencia física. Conocer el códec y demostrar que el firmware actual ejecuta la acción son hechos distintos.

El campo 7 perdió la antigua marca `HW` porque la implementación anterior podía autoconfirmar una endianidad incorrecta. El campo 49 muestra el caso complementario: el códec antiguo puede serializar vacaciones, pero en el G6 probado el SET local directo recibió ACK y las lecturas frescas siguieron sin cambiar. Ese método no es un control verificado.

## Semántica de las escrituras

Las lecturas pueden reintentarse de forma limitada porque son idempotentes. Las escrituras no se duplican a ciegas:

1. enviar SET una sola vez;
2. si la respuesta es ambigua, no reenviar;
3. hacer un GET físico nuevo;
4. reconciliar el estado;
5. confirmar únicamente cuando el valor real coincide.

Las acciones mecánicas también deben confirmar la transición física esperada.

## Superficie Home Assistant

Que el códec sepa serializar un campo no implica que sea seguro exponerlo. `write_fields` queda limitado a configuraciones reversibles y valida rangos/unidades.

Los campos mecánicos 34 y 49 quedan fuera del servicio genérico. El campo 34 solo se utiliza en operaciones específicas conocidas. **El campo 49 no tiene escritor en Home Assistant 2.6.1**: se conserva la lectura, pero se retira el método directo que falló en hardware en lugar de inventar una secuencia alternativa.

## Vacaciones

La UI WaterDevice antigua usa el campo 49 como flag y el 34 como modo físico. Entra desde el modo 0, llega al estado estable 8 y revela la progresión antigua `0 -> 3 -> 7 -> 2 -> 8`.

Ypsilon mantiene un estado semántico solo de lectura sin ocultar `station`:

- `off`: flag falso;
- `preparing`: flag verdadero y station distinto de 8;
- `active`: flag verdadero y station 8.

En el G6 actual probado, sin embargo, `field49=1` recibió ACK sin modificar el read-back. La app actual del fabricante también dispone de operaciones dedicadas de entrada/salida de vacaciones. Por tanto no se expone ninguna acción local de vacaciones hasta verificar físicamente una secuencia correcta.

## Agua, estadísticas y sal

El histórico real confirma que el campo 37 es un contador acumulado dentro del día que se reinicia al cambiar de día; por eso usa `TOTAL_INCREASING`.

El campo 39 es una media semanal del controlador y no es lo mismo que las barras históricas semanales de la app. El campo 41 es capacidad de tratamiento por ciclo, no un contador acumulativo. Ninguno declara `state_class`.

El campo 43 es una cantidad de sal añadida/registrada por el controlador, no un nivel físico de sal.

## Transporte BL3372

El BL3372 antepone una longitud little-endian de dos bytes a la trama Runxin y la envía mediante el comando BroadLink `0x6A`. Cifrado, autenticación, outer errors y reintentos son responsabilidad del transporte.

## Límite de compatibilidad

La evidencia fuerte corresponde al conjunto ATH/BWT Ypsilon G6 + Runxin F79D + BroadLink BL3372 probado. Otros controladores o firmwares deben volver a validar framing, campos, endianidad, escalado, escrituras y máquina de estados.

Véase [`f79d.es.md`](f79d.es.md), [`waterdevice-audit.es.md`](waterdevice-audit.es.md) y [`hardware-verification.es.md`](hardware-verification.es.md).
