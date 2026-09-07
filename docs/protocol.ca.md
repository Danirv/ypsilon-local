[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capes del protocol i evidència

Aquest document descriu allò que el projecte ha observat per interoperabilitat. No és documentació del fabricant ni implica que tots els controladors Runxin utilitzin el mateix protocol.

## Capes al dispositiu provat

Una transacció local normal conté dos protocols independents:

1. una trama de producte Runxin/F79D en brut;
2. una envolupant de transport BroadLink BL3372 que porta aquesta trama.

L'arquitectura 2.4.x manté les dues capes separades.

### Trama Runxin en brut

El F79D provat usa una trama exterior que comença per `5A 5C` i acaba en `A5`, amb una trama interior que comença per `DF FD` i acaba en `DE`. Les dues capes inclouen un checksum additiu de 8 bits. L'opcode de petició és `0x09` per a consultes de camps i `0x19` per a escriptures de control. Les respostes observades usen `0xC9` i `0xD9` respectivament.

Les dades dels camps es representen en grups de tres bytes:

```text
[field_id, byte_1, byte_2]
```

El significat dels bytes depèn del camp. `runxin/fields.py` registra explícitament els codecs coneguts de lectura/escriptura i la seva evidència.

### Envolupant BL3372

El BL3372 anteposa una longitud little-endian de dos bytes a la trama Runxin abans d'enviar-la mitjançant l'ordre BroadLink `0x6A`. Autenticació, xifrat, errors externs, política de reintents i aquest prefix de longitud pertanyen al transport.

`protocol.py` manté `pack_tfb()` / `unpack_tfb()` només per compatibilitat amb scripts antics de recerca. El codi nou de protocol ha d'anar a `runxin/`.

## Codecs de camps F79D

Els codecs observats inclouen:

- `u8`;
- `u16_le`;
- `u16_be`;
- `time_hm` — hora del dia, hora/minut;
- `duration_min_sec` — durada, minut/segon;
- `bool`;
- `volume_pair` — camp base més continuació;
- `reminder_flags` — camp 33 dividit en dos flags booleans.

Les escriptures d'hora i durada usen codecs semànticament diferents encara que ocupin dos bytes. Això evita tractar una durada com una hora del dia només perquè la forma al cable sigui semblant.

Els quatre valors de volum d'aigua usen dos IDs consecutius. Si falta la continuació es retorna `None`, mai un zero fals plausible.

## Nivells d'evidència

`runxin/fields.py` usa etiquetes conservadores:

- `legacy_app_codec`: recuperat del codec de l'antiga app WaterDevice;
- `device_state_observed`: observat en estat/captures reals del Ypsilon/F79D;
- `hardware_write_verified`: SET local provat d'extrem a extrem i confirmat mitjançant lectura física independent;
- `cloud_write_observed`: canvi observat mitjançant l'aplicació cloud antiga;
- `inferred`: interpretació encara no confirmada directament.

Un ACK de protocol no és suficient per a `hardware_write_verified`. Consulta [`hardware-verification.ca.md`](hardware-verification.ca.md).

Que un camp aparegui a l'app antiga no demostra que tots els models/firmwares Runxin l'implementin igual. La capacitat d'escriptura del codec també és diferent de la llista més restringida d'escriptures segures exposades per Home Assistant.

## Semàntica de lliurament de lectures i escriptures

Les lectures són idempotents i un transport pot aplicar reintents limitats. Les escriptures no es consideren idempotents. Si el lliurament d'un SET queda ambigu, el transport no l'ha de duplicar a cegues; primer cal consultar i reconciliar l'estat físic.

## Límit de compatibilitat

El projecte té evidència forta per al perfil F79D i el Ypsilon G6 provat. Les aplicacions antigues contenen comportament dependent del model; això justifica facilitar la reutilització, no anomenar el mapa actual de 52 camps una API universal de Runxin.

Per a un altre controlador, primer cal establir:

- si comparteix realment el framing `5A 5C` / `DF FD`;
- el seu valor de model;
- quins IDs de camp existeixen;
- byte order i escalat de lectura;
- encoding i rangs segurs d'escriptura;
- semàntica de fases/màquina d'estats.

Consulta [`adding-a-device-profile.ca.md`](adding-a-device-profile.ca.md).

## Seguretat i higiene de recerca

Aquí només hi han d'entrar fets d'interoperabilitat i codi escrit de manera independent. No pugis APK, firmware, binaris propietaris, claus d'aparellament, credencials, tokens privats ni captures sense sanejar amb secrets.
