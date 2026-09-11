[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capas del protocolo y evidencia

Ypsilon separa explícitamente las capas:

```text
Política Home Assistant -> cliente/códec F79D -> trama Runxin cruda
                                                -> transporte -> dispositivo
```

El paquete `runxin/` no depende de Home Assistant ni de BroadLink. `transport/broadlink_bl3372.py` concentra autenticación, sesión, cifrado y política de reintentos BroadLink.

## Trama F79D

El controlador probado utiliza una trama exterior que empieza por `5A 5C` y termina en `A5`, con una trama interior `DF FD ... DE`. Ambas capas llevan checksum aditivo de 8 bits.

Opcodes observados:

- `0x09` — consulta de campos;
- `0x19` — control/escritura;
- respuestas `0xC9` y `0xD9` respectivamente.

Cada campo viaja como:

```text
[field_id, byte_1, byte_2]
```

No existe una endianidad global. El catálogo de `runxin/fields.py` es la autoridad por campo.

## Correcciones 2.6.0

El códec WaterDevice confirma una asimetría importante:

- campo 7 (`flowRateOff`) — `u16_le`;
- campo 11 (`flowRate`) — `u16_be`, porque la aplicación invierte explícitamente este campo antes del decodificador genérico.

Los campos de volumen por parejas también dependen de `waterVolumeUnit`; no existe una fórmula universal. Véase [`f79d.es.md`](f79d.es.md).

## Modelo de evidencia

- `legacy_app_codec` — recuperado del códec WaterDevice;
- `device_state_observed` — observado en datos reales;
- `hardware_write_verified` — SET local + GET físico nuevo + validación semántica;
- `cloud_write_observed` — cambio observado en la app cloud;
- `inferred` — interpretación todavía no confirmada directamente.

Un ACK no es evidencia física. En la 2.6 se retira `hardware_write_verified` del campo 7 porque la implementación anterior podía autoconfirmar una endianidad incorrecta.

## Semántica de las escrituras

Las lecturas pueden reintentarse de forma limitada porque son idempotentes. Las escrituras no se duplican a ciegas:

1. enviar SET una sola vez;
2. si la respuesta es ambigua, no reenviar;
3. hacer un GET físico nuevo;
4. reconciliar el estado;
5. confirmar únicamente cuando el valor real coincide.

## Superficie Home Assistant

Que el códec sepa serializar un campo no implica que sea seguro exponerlo. `write_fields` queda limitado a configuraciones reversibles y valida rangos/unidades.

Los campos mecánicos 34 y 49 quedan fuera del servicio genérico y deben controlarse mediante las vías específicas de regeneración y vacaciones.

## Vacaciones

WaterDevice usa el campo 49 como flag de vacaciones y el 34 como modo físico. La UI normal entra en vacaciones desde el modo 0 y sale desde el modo estable 8. Ypsilon separa flag, transición mecánica y estado estable, manteniendo siempre visible el `station` bruto.

## Transporte BL3372

El BL3372 antepone una longitud little-endian de dos bytes a la trama Runxin y la envía mediante el comando BroadLink `0x6A`. Cifrado, autenticación, outer errors y reintentos son responsabilidad del transporte.

## Límite de compatibilidad

La evidencia fuerte corresponde al conjunto ATH/BWT Ypsilon G6 + Runxin F79D + BroadLink BL3372 probado. Otros controladores o firmwares deben volver a validar framing, campos, endianidad, escalado, escrituras y máquina de estados.
