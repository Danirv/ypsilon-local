# Auditoria de WaterDevice antic / F79D

Aquest document recull l'evidència utilitzada per Ypsilon Local per separar **coneixement del còdec**, **estat observat del controlador** i **escriptures verificades físicament**. L'objectiu és evitar que un camp recuperat de l'aplicació es confongui amb un control segur en firmware actual.

## Política d'evidència

Les etiquetes de `runxin/fields.py` signifiquen:

- `LEGACY_APP_CODEC`: camp/codificació recuperat del còdec antic;
- `DEVICE_STATE_OBSERVED`: camp observat en estat real del controlador;
- `HARDWARE_WRITE_VERIFIED`: una escriptura local ha estat confirmada amb una lectura fresca posterior;
- `CLOUD_WRITE_OBSERVED`: el mateix ajust també s'ha observat canviant per la via del fabricant.

Un ACK de transport, per si sol, **no** és una verificació física. Quan la interpretació del còdec antic entra en conflicte amb el controlador real, preval l'evidència física del maquinari provat.

## Còdec F79D

El perfil recuperat utilitza opcode de consulta `0x09` i control `0x19`. Resultats rellevants:

- camp 7 `flowRateOff`: **16 bits big-endian al Ypsilon G6 provat**, verificat amb escriptura/read-back físics;
- camp 11 `flowRate`: 16 bits big-endian al cable;
- camp 33: dos flags de recordatori;
- camps 35/37/39/41: valors de volum de tres bytes repartits en dos TLV i dependents de `waterVolumeUnit`;
- camps 50/51: minuts restants de dissolució de sal i pausa 1;
- camp 52: interval de servei del material filtrant, consultat per separat per la integració.

### Camp 7: discrepància del còdec antic resolta pel maquinari

El camí recuperat de WaterDevice semblava tractar el camp 7 amb un helper little-endian. El G6 físic ho contradiu de manera concloent:

```text
bytes al fil: 03 E8
big-endian:    0x03E8 = 1000 -> 10,00 m³/h
little-endian: 0xE803 = 59395 -> 593,95 m³/h
```

L'app oficial mostrava 10,00 m³/h mentre Ypsilon 2.6.2, després de canviar el camp 7 a LE, mostrava 593,95 m³/h. Per tant aquest controlador és BE.

La via d'escriptura ho corrobora independentment. Una petició de 2,00 m³/h és raw 200 (`0x00C8`) i s'ha d'enviar com `00 C8`. La regressió LE enviava `C8 00`; el controlador retornava ACK de transport/protocol però les lectures fresques no confirmaven el valor demanat. La reconciliació estricta de Ypsilon mostrava correctament `Write ACKed but not confirmed`.

Versions anteriors del projecte amb BE ja havien completat correctament el SET/read-back local del camp 7. Per això es restaura `HARDWARE_WRITE_VERIFIED` i es conserva documentada la discrepància amb el còdec antic.

## Volums, aigua i estadístiques

Per unitats 0/1 els volums 35/37/39/41 es reconstrueixen com un enter LE de 24 bits. Per unitat 2 s'utilitza empaquetat decimal base-100 i la magnitud en m³ es mostra dividida per 100. Si falta la unitat o el TLV de continuació, la integració retorna `None`.

**37–38 Consum diari** és el comptador acumulat del dia i les dades reals confirmen que es reinicia al canvi de dia; Home Assistant utilitza `TOTAL_INCREASING`.

**39–40 Consum setmanal mitjà del controlador** no és el total setmanal de les barres històriques de l'app oficial i no té `state_class`.

**41–42 Capacitat de tractament per cicle** és una magnitud de capacitat/configuració, no un comptador acumulatiu, i tampoc té `state_class`.

## Sal

El camp 43 `addSalt` és una **quantitat de sal afegida** de 0 a 100 kg. L'escriptura local ha estat verificada físicament i també s'ha observat el canvi per la via del fabricant. No és un sensor físic de sal restant i Ypsilon Local no el decrementa després d'una regeneració.

## Vacances

La UI antiga modela les vacances amb el camp 49 i la progressió `0 -> 3 -> 7 -> 2 -> 8`. Al G6 provat, una escriptura local directa del camp 49 va rebre ACK però les lectures fresques van continuar retornant `vacationPattern=false`. Per tant el camp es continua llegint i codificant per a recerca/interoperabilitat, però no és `HARDWARE_WRITE_VERIFIED` i no s'exposa cap switch d'escriptura a Home Assistant.

## Camp 52

La consulta normal continua sent 1..51. El camp 52 es consulta i cacheja per separat perquè és un interval de servei que canvia lentament. És una política de polling de la integració, no una limitació del protocol.

## Regla de publicació

Un control nou només s'ha d'exposar quan estiguin resolts: codificació, precondicions, acceptació física, read-back i comportament davant timeout/reinici. Conèixer només el còdec és suficient per implementar-lo, però no per exposar-lo com a control d'usuari.
