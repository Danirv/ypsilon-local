[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capes del protocol i evidència

Ypsilon separa explícitament les capes:

```text
Política Home Assistant -> client/còdec F79D -> trama Runxin crua
                                               -> transport -> dispositiu
```

El paquet `runxin/` no depèn de Home Assistant ni de BroadLink. `transport/broadlink_bl3372.py` concentra autenticació, sessió, xifratge i política de reintents BroadLink.

## Trama i còdecs F79D

El controlador provat utilitza una trama exterior `5A 5C ... A5` amb una trama interior `DF FD ... DE`, amb checksum additiu de 8 bits. Els opcodes observats són `0x09` per consulta i `0x19` per control/escriptura; les respostes són `0xC9` i `0xD9`.

Cada camp viatja com `[field_id, byte_1, byte_2]`. No hi ha una endianitat global: `runxin/fields.py` és l'autoritat per camp.

Al Ypsilon G6 físic provat:

- camp 7 (`flowRateOff`) — `u16_be` en lectura i escriptura;
- camp 11 (`flowRate`) — `u16_be`;
- camps 12, 25, 47 i 52 — `u16_le`;
- els volums 35/37/39/41 depenen de `waterVolumeUnit`.

El camp 7 conserva documentada una discrepància amb el camí recuperat de WaterDevice, que semblava usar un helper LE. L'evidència física és concloent:

```text
03 E8 -> BE 1000 -> 10,00 m³/h
03 E8 -> LE 59395 -> 593,95 m³/h
```

L'app oficial mostrava 10,00 m³/h mentre la regressió LE de Ypsilon 2.6.2 mostrava 593,95 m³/h. Una escriptura de 2,00 m³/h és raw 200 i s'ha d'enviar com `00 C8`; la regressió LE enviava `C8 00`, rebia ACK de transport però fallava el read-back físic. Versions anteriors amb BE ja havien passat SET/read-back real, de manera que el camp 7 torna a ser `HARDWARE_WRITE_VERIFIED`.

## Model d'evidència

- `legacy_app_codec` — recuperat del còdec WaterDevice;
- `device_state_observed` — observat en dades reals;
- `hardware_write_verified` — SET local + GET físic nou + validació semàntica;
- `cloud_write_observed` — canvi observat a la via del fabricant;
- `inferred` — interpretació encara no confirmada directament.

Un ACK no és evidència física. Quan una interpretació de l'app entra en conflicte amb bytes/read-back independents del controlador, preval l'evidència física per al maquinari provat i la discrepància es documenta.

El camp 49 és l'exemple negatiu complementari: el còdec antic pot serialitzar vacances, però al G6 provat el SET local directe va donar ACK i les lectures fresques van continuar sense canviar. Aquest mètode no és un control verificat.

## Semàntica de les escriptures

Les lectures es poden reintentar perquè són idempotents. Les escriptures no es dupliquen cegament:

1. enviar SET una vegada;
2. si la resposta és ambigua, no reenviar;
3. fer un GET físic nou;
4. reconciliar l'estat;
5. confirmar només quan el valor real coincideix.

La regressió LE del camp 7 demostra que aquesta arquitectura funciona: l'ACK no es va convertir en un fals èxit perquè el read-back no coincidia.

## Superfície Home Assistant

`write_fields` queda limitat a configuracions reversibles i valida rangs/unitats. Els camps mecànics 34 i 49 queden fora del servei genèric. El camp 49 continua només en lectura fins que una seqüència local correcta es verifiqui físicament.

## Aigua, estadístiques i sal

L'històric real confirma que el camp 37 és un comptador acumulat dins del dia que es reinicia al canvi de dia; per això usa `TOTAL_INCREASING`. El camp 39 és una mitjana setmanal del controlador i no és el mateix que les barres històriques setmanals de l'app. El camp 41 és capacitat de tractament per cicle, no un comptador acumulatiu. Cap dels dos declara `state_class`.

El camp 43 és una quantitat de sal afegida/registrada pel controlador, no un nivell físic de sal.

## Camp 52

El bloc normal continua sent 1..51. El camp 52 es consulta i cacheja per separat perquè és un interval de servei que canvia lentament. És política de polling de la capa Ypsilon, no una limitació del còdec F79D.

## Transport BL3372

El BL3372 anteposa una longitud little-endian de dos bytes a la trama Runxin i l'envia mitjançant la comanda BroadLink `0x6A`. Xifratge, autenticació, outer errors i reintents són responsabilitat del transport.

## Límit de compatibilitat

L'evidència forta correspon al conjunt ATH/BWT Ypsilon G6 + Runxin F79D + BroadLink BL3372 provat. Altres controladors o firmwares han de validar de nou framing, camps, endianitat, escalat, escriptures i màquina d'estats.

Vegeu [`f79d.ca.md`](f79d.ca.md), [`waterdevice-audit.ca.md`](waterdevice-audit.ca.md) i [`hardware-verification.ca.md`](hardware-verification.ca.md).
