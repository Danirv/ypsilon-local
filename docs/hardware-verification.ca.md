[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificació d'escriptures amb maquinari real

Un camp només es marca com `HARDWARE_WRITE_VERIFIED` quan la integració local
demostra el recorregut complet contra un controlador físic. Un ACK del protocol
per si sol no és suficient.

## Seqüència obligatòria

Per a un paràmetre reversible:

1. **GET inicial** — llegir localment el valor actual i guardar-lo.
2. **SET de prova** — enviar una única escriptura local amb la integració/codec.
3. **GET independent** — tornar a consultar físicament el controlador.
4. **Comprovació física/semàntica** — confirmar que l'estat observat significa
   realment el que s'espera, no només que hi ha hagut ACK.
5. **Restaurar** — tornar a escriure el valor inicial.
6. **GET de restauració** — verificar que l'estat original ha quedat restaurat.

L'estat en memòria del coordinador no serveix com a evidència: la confirmació ha
de provenir d'una lectura física nova.

## Lliurament ambigu

Si el transport fa timeout o perd la resposta després d'enviar un SET, **no
s'ha de reenviar l'ordre a cegues**. El controlador ja podria haver-la executat.
Primer es fa un GET independent i es reconcilia l'estat físic. És especialment
important en accions mecàniques com forçar una regeneració.

## Nivells d'evidència

- només codec de l'app → `LEGACY_APP_CODEC`;
- valor observat en estat real → `DEVICE_STATE_OBSERVED`;
- canvi observat per cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura independent completa → `HARDWARE_WRITE_VERIFIED`.

## Estat actual Ypsilon G6 / F79D

Verificats localment de punta a punta: camps **4, 6, 7, 10, 43 i 47**. El camp 7
s'ha validat amb `waterVolumeUnit=2`.

Pendents: **34 (forçar regeneració)** i **49 (mode vacances)**.

L'evidència d'un model, firmware, rebrand o transport no s'ha de generalitzar
silenciosament a tots els dispositius Runxin.
