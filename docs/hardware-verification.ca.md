[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificació d'escriptures sobre maquinari

Un camp només es marca `HARDWARE_WRITE_VERIFIED` quan la integració local ha provat tota la ruta d'escriptura i lectura posterior contra un controlador físic. Un ACK o un còdec autocoherent no són suficients.

La correcció de vacances de la 2.6.1 és un exemple deliberat d'aquesta regla: el camp 49 és codificable segons l'app antiga, però el G6 actual provat va donar ACK a l'escriptura local directa sense canviar l'estat en lectures fresques. Per això Home Assistant només exposa l'estat de vacances com a lectura.

## Seqüència requerida

Per a un camp de configuració reversible:

1. **GET inicial** — llegir el valor actual localment.
2. **SET candidat** — enviar una única escriptura amb el còdec que es vol validar.
3. **GET independent** — tornar a consultar físicament el controlador.
4. **Validació física/semàntica** — confirmar que l'estat observat significa el que s'espera.
5. **Restauració** — tornar a escriure el valor inicial.
6. **GET de restauració** — verificar que l'estat original s'ha recuperat.

No s'ha d'utilitzar estat cachejat del coordinator com a evidència.

Per a una acció mecànica, també cal validar la fase/transició física esperada. Un bit coincident sense el moviment o estat esperat no és suficient.

## Lliurament ambigu

Si el SET ja s'ha enviat però es perd la resposta o hi ha timeout, **no es reenvia cegament**. El controlador podria haver-lo executat. Primer s'ha de fer un GET nou i reconciliar l'estat físic.

Aquesta regla és especialment important per a regeneracions i transicions de vacances.

## Nivells d'evidència

- còdec de l'app → `LEGACY_APP_CODEC`;
- valor observat al dispositiu → `DEVICE_STATE_OBSERVED`;
- canvi observat al cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura física independent completa → `HARDWARE_WRITE_VERIFIED`.

Conèixer el còdec i demostrar que el maquinari accepta l'acció són evidències independents. Un camp pot conservar un write codec a `runxin/fields.py` per interoperabilitat i, alhora, no formar part de la superfície d'escriptura de Home Assistant.

## Estat actual Ypsilon G6 / F79D

Verificats localment de punta a punta:

- camp 4 — rellotge / sincronització;
- camp 6 — límit de consum continu;
- camp 10 — hora de regeneració;
- camp 43 — valor de quantitat de sal afegida;
- camp 47 — duresa de l'aigua d'entrada.

Pendents o a revalidar:

- **camp 7 — llindar de tancament per cabal:** WaterDevice confirma que el còdec correcte és little-endian. Les versions anteriors a 2.6 utilitzaven BE tant en escriptura com en lectura i podien autoconfirmar l'error. Es retira l'antiga marca `HW` fins provar físicament el camí LE corregit;
- **camp 34 — escriptures mecàniques/màquina d'estats:** només s'han d'exposar accions específicament observades i provades; el còdec per si sol no autoritza tots els valors;
- **camp 49 — vacances:** el control local directe `1/0` està explícitament **no verificat** al G6 actual provat i no s'exposa a Home Assistant 2.6.1.

## Evidència del falliment del camp 49

La UI WaterDevice antiga indica aquesta semàntica:

- entrada només des de station/system mode 0;
- establir el flag de vacances;
- progressió antiga de preparació `0 -> 3 -> 7 -> 2 -> 8`;
- vacances estables = camp 49 cert + station 8;
- la fase 2 de vacances utilitza el 25% del temps normal de rentat lent per al progrés de la UI;
- sortida iniciada des de station 8.

Al G6 físic actual del projecte, la 2.6.0 va fer la comprovació crítica:

1. lectura inicial amb `vacationPattern=false` i vàlvula en servei;
2. SET local directe del camp 49;
3. ACK de transport/protocol;
4. lectures locals independents repetides que continuaven retornant `vacationPattern=false`;
5. timeout sense confirmació física.

Això descarta el mètode d'escriptura directa del camp 49 utilitzat a la 2.6.0 com a control d'usuari per a aquest firmware. La conclusió és més forta que «pendent»: **aquest mètode concret no funciona al maquinari provat**.

L'app actual del fabricant també conté operacions dedicades d'entrada/sortida de vacances separades del control genèric. Per tant Ypsilon no ha d'inventar una seqüència multi-camp o mecànica alternativa.

La 2.6.1 conserva:

- lectura/descodificació del camp 49;
- codificació legacy del camp 49 a la capa F79D reutilitzable per recerca/interoperabilitat;
- sensor semàntic d'estat de vacances només de lectura;

I elimina:

- el switch de Mode vacances de Home Assistant;
- qualsevol mètode del coordinator que escrigui directament el camp 49.

## Evidència d'aigua i estadístiques

Un export real d'històric del G6 confirma que `dailyWaterConsumption` augmenta durant el dia i es reinicia al canvi de dia. Això dona suport a `TOTAL_INCREASING` per al camp 37.

Les mateixes dades, juntament amb captures de l'app oficial, mostren que el valor viu del camp 39 no és el mateix que les barres de totals setmanals històrics de l'app. Per això els camps 39 i 41 no tenen `state_class`.

## Evidència de sal

El camp 43 té SET/read-back local verificat i canvi observat també per la via cloud. La semàntica antiga és «sal afegida» en kg: valida un valor de configuració/registre, no un sensor físic de nivell. La integració no ha d'inferir ni decrementar «sal restant» a partir d'aquest camp.

## Regla de generalització

L'evidència d'un controlador o firmware no s'ha de generalitzar automàticament a tots els dispositius Runxin. Abans d'ampliar suport a un altre transport, rebrand o firmware, cal verificar independentment còdec i comportament físic.

Consulta també [`waterdevice-audit.ca.md`](waterdevice-audit.ca.md).
