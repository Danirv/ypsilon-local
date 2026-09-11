# Auditoria de WaterDevice antic / F79D

Aquest document recull l'evidència utilitzada per Ypsilon Local per separar **coneixement del còdec**, **estat observat del controlador** i **escriptures verificades físicament**. L'objectiu és evitar que un camp recuperat de l'aplicació es confongui amb un control segur en firmware actual.

## Política d'evidència

Les etiquetes de `runxin/fields.py` signifiquen:

- `LEGACY_APP_CODEC`: camp/codificació recuperat del còdec antic;
- `DEVICE_STATE_OBSERVED`: camp observat en estat real del controlador;
- `HARDWARE_WRITE_VERIFIED`: una escriptura local ha estat confirmada amb una lectura fresca posterior;
- `CLOUD_WRITE_OBSERVED`: el mateix ajust també s'ha observat canviant per la via del fabricant.

Un ACK de transport, per si sol, **no** és una verificació física.

## Còdec F79D

El perfil recuperat utilitza opcode de consulta `0x09` i control `0x19`. Resultats rellevants:

- camp 7 `flowRateOff`: 16 bits little-endian;
- camp 11 `flowRate`: big-endian al cable perquè el codi antic inverteix explícitament el parell;
- camp 33: dos flags de recordatori;
- camps 35/37/39/41: valors de volum de tres bytes repartits en dos TLV i dependents de `waterVolumeUnit`;
- camps 50/51: minuts restants de dissolució de sal i pausa 1;
- camp 52: dies de servei del material filtrant.

Per unitats 0/1 els volums es reconstrueixen com un enter LE de 24 bits. Per unitat 2 s'utilitza empaquetat decimal base-100 i la magnitud en m³ es mostra dividida per 100. Si falta la unitat o el TLV de continuació, la integració retorna `None` en lloc d'inventar un valor.

## Aigua i estadístiques

**37–38 Consum diari** és el comptador acumulat del dia. Les dades reals del G6 mostren que puja durant el dia i es reinicia al canvi de dia. Per això Home Assistant utilitza `TOTAL_INCREASING`: un descens per reinici inicia un nou cicle de comptador i no representa consum negatiu.

**39–40 Consum setmanal mitjà del controlador** correspon a `averageUsedWater` del còdec antic. No és el total de la setmana que mostra el gràfic històric de l'app oficial. Aquest gràfic utilitza una via estadística separada. El sensor no té `state_class`.

**41–42 Capacitat de tractament per cicle** és una magnitud de capacitat/configuració del controlador, no un comptador acumulatiu. Tampoc té `state_class`.

Versions anteriors van crear estadístiques de llarg termini per als camps 39 i 41. Després de l'actualització, Home Assistant pot oferir eliminar aquestes estadístiques antigues. És una migració esperada i no elimina l'entitat ni l'històric normal.

## Sal

El camp 43 `addSalt` és una **quantitat de sal afegida**, de 0 a 100 kg, que l'app antiga permet configurar. L'escriptura local ha estat verificada físicament i també s'ha observat el canvi per la via del fabricant.

No és un sensor físic de sal restant i Ypsilon Local no el decrementa després d'una regeneració. Els avisos físics de sal són separats:

- camp 31: concentració de salmorra baixa;
- camp 33: recordatori de comprovar/afegir sal.

## Vacances: decisió de seguretat de la 2.6.1

La UI antiga conté la semàntica següent:

- entrada: `holidayMode=1` des de servei;
- sortida: `holidayMode=0` quan s'ha arribat a l'estació 8;
- progressió antiga: `0 -> 3 -> 7 -> 2 -> 8`;
- durant la fase 2 en vacances, el progrés utilitza el 25% del temps normal de rentat lent.

Això prova el comportament de la **UI/còdec antic**, però no que qualsevol firmware actual executi una escriptura local directa del camp 49.

Al G6 provat, la 2.6.0 va enviar el camp 49, va rebre ACK, però les lectures fresques posteriors van continuar retornant `vacationPattern=false`. Per tant, a la 2.6.1:

- el camp 49 es continua llegint;
- el còdec conserva la seva codificació per a recerca/interoperabilitat;
- no es marca com `HARDWARE_WRITE_VERIFIED`;
- s'elimina el switch d'escriptura de vacances;
- es manté el sensor d'estat de vacances només de lectura;
- no s'envia cap seqüència mecànica deduïda o no verificada.

L'app actual del fabricant també disposa d'operacions dedicades d'entrada/sortida de vacances, fet que reforça aquesta decisió conservadora.

## Regla de publicació

Un control nou només s'ha d'exposar quan estiguin resolts: codificació, precondicions, acceptació física, read-back i comportament davant timeout/reinici. Conèixer només el còdec és suficient per implementar-lo, però no per exposar-lo com a control d'usuari.
