[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificació d'escriptures sobre maquinari

Un camp només es marca `HARDWARE_WRITE_VERIFIED` quan la integració local ha provat tota la ruta d'escriptura i lectura posterior contra un controlador físic. Un ACK o un còdec autocoherent no són suficients.

## Seqüència requerida

Per a un camp de configuració reversible:

1. **GET inicial** — llegir el valor actual localment.
2. **SET candidat** — enviar una única escriptura amb el còdec que es vol validar.
3. **GET independent** — tornar a consultar físicament el controlador.
4. **Validació física/semàntica** — confirmar que l'estat observat significa el que s'espera.
5. **Restauració** — tornar a escriure el valor inicial.
6. **GET de restauració** — verificar que l'estat original s'ha recuperat.

No s'ha d'utilitzar estat cachejat del coordinator com a evidència.

## Lliurament ambigu

Si el SET ja s'ha enviat però es perd la resposta o hi ha timeout, **no es reenvia cegament**. El controlador podria haver-lo executat. Primer s'ha de fer un GET nou i reconciliar l'estat físic.

Aquesta regla és especialment important per a regeneracions i transicions de vacances.

## Nivells d'evidència

- còdec de l'app → `LEGACY_APP_CODEC`;
- valor observat al dispositiu → `DEVICE_STATE_OBSERVED`;
- canvi observat al cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura física independent completa → `HARDWARE_WRITE_VERIFIED`.

## Estat actual Ypsilon G6 / F79D

Verificats localment de punta a punta:

- camp 4 — rellotge;
- camp 6 — límit de consum continu;
- camp 10 — hora de regeneració;
- camp 43 — sal afegida;
- camp 47 — duresa de l'aigua d'entrada.

Pendents o a revalidar:

- **camp 7 — llindar de tancament per cabal:** WaterDevice confirma que el còdec correcte és little-endian. Les versions anteriors a 2.6 utilitzaven BE tant en escriptura com en lectura, de manera que el read-back podia autoconfirmar una endianitat incorrecta. Per això es retira l'antiga marca `HW` fins que el camí LE corregit es provi al controlador físic;
- camp 34 — regeneració forçada;
- camp 49 — mode vacances.

## Verificació d'estats mecànics

Per als camps 34 i 49 no n'hi ha prou amb comprovar un únic bit. Cal validar també la transició física esperada.

Per vacances, la semàntica recuperada de l'aplicació antiga és:

- entrar només des de station/system mode 0;
- el camp 49 passa a cert;
- el controlador recorre la preparació mecànica;
- vacances estables = camp 49 cert + station 8;
- la sortida s'inicia des de station 8 i s'ha de reconciliar amb l'estat físic posterior.

Només després d'observar aquest flux complet el camp 49 es podrà marcar `HARDWARE_WRITE_VERIFIED`.

L'evidència d'un controlador o firmware no s'ha de generalitzar automàticament a tots els dispositius Runxin.
