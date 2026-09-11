[English](protocol.md) | [Español](protocol.es.md) | [Català](protocol.ca.md)

# Capes del protocol i evidència

Ypsilon separa explícitament les capes:

```text
Política Home Assistant -> client/còdec F79D -> trama Runxin crua
                                               -> transport -> dispositiu
```

El paquet `runxin/` no depèn de Home Assistant ni de BroadLink. `transport/broadlink_bl3372.py` concentra autenticació, sessió, xifratge i política de reintents BroadLink.

## Trama i còdecs F79D

El controlador provat utilitza una trama exterior `5A 5C ... A5` amb una trama interior `DF FD ... DE`. Les dues capes porten checksum additiu de 8 bits.

Opcodes observats:

- `0x09` — consulta de camps;
- `0x19` — control/escriptura;
- respostes `0xC9` i `0xD9` respectivament.

Cada camp viatja com `[field_id, byte_1, byte_2]`. No hi ha una endianitat global: `runxin/fields.py` és l'autoritat per camp.

El còdec WaterDevice confirma:

- camp 7 (`flowRateOff`) — `u16_le`;
- camp 11 (`flowRate`) — `u16_be`, perquè l'app inverteix explícitament aquest camp;
- els volums 35/37/39/41 depenen de `waterVolumeUnit`.

Vegeu [`f79d.ca.md`](f79d.ca.md).

## Model d'evidència

- `legacy_app_codec` — recuperat del còdec WaterDevice;
- `device_state_observed` — observat en dades reals;
- `hardware_write_verified` — SET local + GET físic nou + validació semàntica;
- `cloud_write_observed` — canvi observat a la via del fabricant;
- `inferred` — interpretació encara no confirmada directament.

Un ACK no és evidència física. Conèixer el còdec i demostrar que el firmware actual executa l'acció són coses diferents.

El camp 7 va perdre l'antiga marca `HW` perquè la implementació anterior podia autoconfirmar una endianitat incorrecta. El camp 49 mostra l'altre cas: el còdec antic pot serialitzar vacances, però al G6 provat el SET local directe va donar ACK i les lectures fresques van continuar sense canviar. Aquest mètode no és un control verificat.

## Semàntica de les escriptures

Les lectures es poden reintentar de forma limitada perquè són idempotents. Les escriptures no es dupliquen cegament:

1. enviar SET una vegada;
2. si la resposta és ambigua, no reenviar;
3. fer un GET físic nou;
4. reconciliar l'estat;
5. confirmar només quan el valor real coincideix.

Les accions mecàniques també han de confirmar la transició física esperada.

## Superfície Home Assistant

Que el còdec sàpiga serialitzar un camp no implica que sigui segur exposar-lo. `write_fields` queda limitat a configuracions reversibles i valida rangs/unitats.

Els camps mecànics 34 i 49 queden fora del servei genèric. El camp 34 només s'utilitza en operacions específiques conegudes. **El camp 49 no té escriptor a Home Assistant 2.6.1**: es conserva la lectura, però es retira el mètode directe que va fallar en maquinari en lloc d'inventar una seqüència alternativa.

## Vacances

La UI WaterDevice antiga usa el camp 49 com a flag i el 34 com a mode físic. Entra des del mode 0, arriba a l'estat estable 8 i revela la progressió antiga `0 -> 3 -> 7 -> 2 -> 8`.

Ypsilon manté un estat semàntic només de lectura sense ocultar `station`:

- `off`: flag fals;
- `preparing`: flag cert i station diferent de 8;
- `active`: flag cert i station 8.

Al G6 actual provat, però, `field49=1` va donar ACK sense modificar el read-back. L'app actual del fabricant també disposa d'operacions dedicades d'entrada/sortida de vacances. Per tant no s'exposa cap acció local de vacances fins verificar físicament una seqüència correcta.

## Aigua, estadístiques i sal

L'històric real confirma que el camp 37 és un comptador acumulat dins del dia que es reinicia al canvi de dia; per això usa `TOTAL_INCREASING`.

El camp 39 és una mitjana setmanal del controlador i no és el mateix que les barres històriques setmanals de l'app. El camp 41 és capacitat de tractament per cicle, no un comptador acumulatiu. Cap dels dos declara `state_class`.

El camp 43 és una quantitat de sal afegida/registrada pel controlador, no un nivell físic de sal.

## Transport BL3372

El BL3372 anteposa una longitud little-endian de dos bytes a la trama Runxin i l'envia mitjançant la comanda BroadLink `0x6A`. Xifratge, autenticació, outer errors i reintents són responsabilitat del transport.

## Límit de compatibilitat

L'evidència forta correspon al conjunt ATH/BWT Ypsilon G6 + Runxin F79D + BroadLink BL3372 provat. Altres controladors o firmwares han de validar de nou framing, camps, endianitat, escalat, escriptures i màquina d'estats.

Vegeu [`f79d.ca.md`](f79d.ca.md), [`waterdevice-audit.ca.md`](waterdevice-audit.ca.md) i [`hardware-verification.ca.md`](hardware-verification.ca.md).
