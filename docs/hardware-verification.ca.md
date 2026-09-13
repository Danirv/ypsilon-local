[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificació d'escriptures sobre maquinari

Un camp només es marca `HARDWARE_WRITE_VERIFIED` quan la integració local ha provat tota la ruta d'escriptura i lectura posterior contra un controlador físic. Un ACK o un còdec autocoherent no són suficients.

La correcció de vacances de la 2.6.1 continua sent un exemple deliberat d'aquesta regla: el camp 49 és codificable segons l'app antiga, però el G6 provat va donar ACK a l'escriptura local directa sense canviar l'estat en lectures fresques. Per això Home Assistant només exposa l'estat de vacances com a lectura.

## Seqüència requerida

Per a un camp de configuració reversible:

1. **GET inicial** — llegir el valor actual localment.
2. **SET candidat** — enviar una única escriptura amb el còdec que es vol validar.
3. **GET independent** — tornar a consultar físicament el controlador.
4. **Validació física/semàntica** — confirmar que l'estat observat significa el que s'espera.
5. **Restauració** — tornar a escriure el valor inicial.
6. **GET de restauració** — verificar que l'estat original s'ha recuperat.

No s'ha d'utilitzar estat cachejat del coordinator com a evidència. Per a una acció mecànica també cal validar la fase/transició física esperada.

## Lliurament ambigu

Si el SET ja s'ha enviat però es perd la resposta o hi ha timeout, **no es reenvia cegament**. El controlador podria haver-lo executat. Primer s'ha de fer un GET nou i reconciliar l'estat físic.

## Nivells d'evidència

- còdec de l'app → `LEGACY_APP_CODEC`;
- valor observat al dispositiu → `DEVICE_STATE_OBSERVED`;
- canvi observat al cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura física independent completa → `HARDWARE_WRITE_VERIFIED`.

## Estat actual Ypsilon G6 / F79D

Verificats localment de punta a punta:

- camp 4 — rellotge / sincronització;
- camp 6 — límit de consum continu;
- **camp 7 — llindar de tancament per cabal, u16 big-endian**;
- camp 10 — hora de regeneració;
- camp 43 — quantitat de sal afegida;
- camp 47 — duresa de l'aigua d'entrada.

Pendents o deliberadament no verificats:

- **camp 34** — escriptures mecàniques/màquina d'estats més enllà del comportament específic provat;
- **camp 49** — el control local directe `1/0` de vacances està explícitament no verificat al G6 provat i no s'exposa com a control HA.

## Evidència del camp 7

El G6 físic resol l'ordre de bytes del camp 7 independentment de la interpretació de l'app antiga:

```text
bytes al fil: 03 E8
big-endian:    0x03E8 = 1000 -> 10,00 m³/h
little-endian: 0xE803 = 59395 -> 593,95 m³/h
```

L'app oficial mostrava 10,00 m³/h mentre Ypsilon 2.6.2, amb la regressió LE, mostrava 593,95 m³/h. La via d'escriptura aporta una segona prova: 2,00 m³/h són raw 200 (`0x00C8`) i s'han d'enviar com `00 C8`; la regressió LE enviava `C8 00`, rebia ACK però el read-back físic no canviava i el coordinator generava `Write ACKed but not confirmed`.

Versions anteriors del projecte amb BE ja havien completat correctament el SET/read-back físic del camp 7. Sumant aquella verificació a l'evidència actual independent, el camp 7 torna a estar `HARDWARE_WRITE_VERIFIED`. La discrepància amb el còdec antic es conserva documentada, però per al G6 provat preval el controlador real.

## Evidència del falliment del camp 49

La UI antiga modela l'entrada de vacances des de station 0, la progressió `0 -> 3 -> 7 -> 2 -> 8` i l'estat estable com camp 49 cert + station 8. Al G6 provat, però, un SET local directe del camp 49 va rebre ACK i lectures locals independents repetides van continuar retornant `vacationPattern=false` fins al timeout. Per tant aquest mètode concret no funciona al maquinari provat i Ypsilon no inventa una seqüència mecànica alternativa.

## Evidència d'aigua i sal

L'històric real confirma que `dailyWaterConsumption` augmenta durant el dia i es reinicia al canvi de dia, cosa que dona suport a `TOTAL_INCREASING` per al camp 37. Les captures de l'app oficial mostren que el camp 39 no és el mateix que les barres de totals setmanals històrics, de manera que els camps 39 i 41 no tenen `state_class`.

El camp 43 té SET/read-back local verificat i canvi observat per cloud. La seva semàntica és «sal afegida» en kg, no un sensor físic de nivell.

## Camp 52

El camp 52 queda intencionadament fora del bloc normal 1..51. La capa Ypsilon el consulta i cacheja per separat perquè és un interval de servei que canvia lentament.

## Regla de generalització

L'evidència d'un controlador o firmware no s'ha de generalitzar automàticament a tots els dispositius Runxin. Abans d'ampliar suport a un altre transport, rebrand o firmware, cal verificar independentment còdec i comportament físic.

Consulta també [`waterdevice-audit.ca.md`](waterdevice-audit.ca.md).
