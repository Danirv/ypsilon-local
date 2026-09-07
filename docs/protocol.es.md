[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capas del protocolo y evidencia

Este documento describe lo observado por el proyecto para interoperabilidad. No es documentación del fabricante ni implica que todos los controladores Runxin usen el mismo protocolo.

## Capas en el dispositivo probado

Una transacción local normal contiene dos protocolos independientes:

1. una trama de producto Runxin/F79D en bruto;
2. una envolvente de transporte BroadLink BL3372 que transporta esa trama.

La arquitectura 2.4.x mantiene ambas capas separadas.

### Trama Runxin en bruto

El F79D probado usa una trama exterior que empieza por `5A 5C` y termina en `A5`, con una trama interior que empieza por `DF FD` y termina en `DE`. Ambas capas incluyen un checksum aditivo de 8 bits. El opcode de petición es `0x09` para consultas de campos y `0x19` para escrituras de control. Las respuestas observadas usan `0xC9` y `0xD9` respectivamente.

Los datos de campos se representan en grupos de tres bytes:

```text
[field_id, byte_1, byte_2]
```

El significado de los bytes depende del campo. `runxin/fields.py` registra explícitamente los codecs conocidos de lectura/escritura y su evidencia.

### Envolvente BL3372

El BL3372 antepone una longitud little-endian de dos bytes a la trama Runxin antes de enviarla mediante el comando BroadLink `0x6A`. Autenticación, cifrado, errores externos, política de reintentos y este prefijo de longitud pertenecen al transporte.

`protocol.py` mantiene `pack_tfb()` / `unpack_tfb()` solo por compatibilidad con scripts antiguos de investigación. El código nuevo de protocolo debe vivir en `runxin/`.

## Codecs de campos F79D

Los codecs observados incluyen:

- `u8`;
- `u16_le`;
- `u16_be`;
- `time_hm` — hora del día, hora/minuto;
- `duration_min_sec` — duración, minuto/segundo;
- `bool`;
- `volume_pair` — campo base más continuación;
- `reminder_flags` — campo 33 dividido en dos flags booleanos.

Las escrituras de hora y duración usan codecs semánticamente distintos aunque ocupen dos bytes. Esto evita tratar una duración como hora del día solo porque su forma en el cable sea parecida.

Los cuatro valores de volumen de agua usan dos IDs consecutivos. Si falta la continuación se devuelve `None`, nunca un cero falso plausible.

## Niveles de evidencia

`runxin/fields.py` usa etiquetas conservadoras:

- `legacy_app_codec`: recuperado del codec de la antigua app WaterDevice;
- `device_state_observed`: observado en estado/capturas reales del Ypsilon/F79D;
- `hardware_write_verified`: SET local probado de extremo a extremo y confirmado mediante lectura física independiente;
- `cloud_write_observed`: cambio observado mediante la aplicación cloud antigua;
- `inferred`: interpretación todavía no confirmada directamente.

Un ACK de protocolo no basta para `hardware_write_verified`. Consulta [`hardware-verification.es.md`](hardware-verification.es.md).

La existencia de un campo en la app antigua no demuestra que todos los modelos/firmwares Runxin lo implementen igual. La capacidad de escritura del codec también es distinta de la lista más restringida de escrituras seguras expuestas por Home Assistant.

## Semántica de entrega de lecturas y escrituras

Las lecturas son idempotentes y un transport puede aplicar reintentos limitados. Las escrituras no se consideran idempotentes. Si la entrega de un SET queda ambigua, el transport no debe duplicarlo ciegamente; primero debe consultar y reconciliar el estado físico.

## Límite de compatibilidad

El proyecto tiene evidencia fuerte para el perfil F79D y el Ypsilon G6 probado. Las aplicaciones antiguas contienen comportamiento dependiente del modelo; eso justifica facilitar la reutilización, no llamar al mapa actual de 52 campos una API universal de Runxin.

Para otro controlador, primero hay que establecer:

- si comparte realmente el framing `5A 5C` / `DF FD`;
- su valor de modelo;
- qué IDs de campo existen;
- byte order y escalado de lectura;
- encoding y rangos seguros de escritura;
- semántica de fases/máquina de estados.

Consulta [`adding-a-device-profile.es.md`](adding-a-device-profile.es.md).

## Seguridad e higiene de investigación

Aquí solo deben entrar hechos de interoperabilidad y código escrito de forma independiente. No subas APK, firmware, binarios propietarios, claves de emparejamiento, credenciales, tokens privados ni capturas sin sanear con secretos.
