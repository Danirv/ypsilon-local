[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capes del protocol i evidència

Ypsilon separa explícitament les capes:

```text
Política Home Assistant -> client/còdec F79D -> trama Runxin crua
                                               -> transport -> dispositiu
```

El paquet `runxin/` no depèn de Home Assistant ni de BroadLink. `transport/broadlink_bl3372.py` concentra autenticació, sessió, xifratge i política de reintents BroadLink.

## Trama F79D

El controlador provat utilitza una trama exterior que comença per `5A 5C` i acaba en `A5`, amb una trama interior `DF FD ... DE`. Les dues capes porten checksum additiu de 8 bits.

Opcodes observats:

- `0x09` — consulta de camps;
- `0x19` — control/escriptura;
- respostes `0xC9` i `0xD9` respectivament.

Cada camp viatja com:

```text
[field_id, byte_1, byte_2]
```

No hi ha una endianitat global. El catàleg de `runxin/fields.py` és l'autoritat per camp.

## Correccions 2.6.0

El còdec WaterDevice confirma una asimetria important:

- camp 7 (`flowRateOff`) — `u16_le`;
- camp 11 (`flowRate`) — `u16_be`, perquè l'aplicació inverteix explícitament aquest camp abans del descodificador genèric.

Els camps de volum per parelles també depenen de `waterVolumeUnit`; no existeix una única fórmula universal. Vegeu [`f79d.ca.md`](f79d.ca.md).

## Model d'evidència

- `legacy_app_codec` — recuperat del còdec WaterDevice;
- `device_state_observed` — observat en dades reals;
- `hardware_write_verified` — SET local + GET físic nou + validació semàntica;
- `cloud_write_observed` — canvi observat a l'app cloud;
- `inferred` — interpretació encara no confirmada directament.

Un ACK no és evidència física. A la 2.6 es retira `hardware_write_verified` del camp 7 perquè la implementació anterior podia autoconfirmar una endianitat incorrecta.

## Semàntica de les escriptures

Les lectures es poden reintentar de forma limitada perquè són idempotents. Les escriptures no es dupliquen cegament:

1. enviar SET una vegada;
2. si la resposta és ambigua, no reenviar;
3. fer un GET físic nou;
4. reconciliar l'estat;
5. confirmar només quan el valor real coincideix.

## Superfície Home Assistant

Que el còdec sàpiga serialitzar un camp no implica que sigui segur exposar-lo. `write_fields` queda limitat a configuracions reversibles i valida rangs/unitats.

Els camps mecànics 34 i 49 queden fora del servei genèric i s'han de controlar per les vies específiques de regeneració i vacances.

## Vacances

WaterDevice usa el camp 49 com a flag de vacances i el 34 com a mode físic. La UI normal entra en vacances des del mode 0 i en surt des del mode estable 8. Ypsilon separa flag, transició mecànica i estat estable, mantenint sempre visible el `station` cru.

## Transport BL3372

El BL3372 anteposa una longitud little-endian de dos bytes a la trama Runxin i l'envia mitjançant la comanda BroadLink `0x6A`. Xifratge, autenticació, outer errors i reintents són responsabilitat del transport.

## Límit de compatibilitat

L'evidència forta correspon al conjunt ATH/BWT Ypsilon G6 + Runxin F79D + BroadLink BL3372 provat. Altres controladors o firmwares han de validar de nou framing, camps, endianitat, escalat, escriptures i màquina d'estats.
