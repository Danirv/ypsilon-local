[English](architecture.md) | [Español](architecture.es.md) | [Català](architecture.ca.md)

# Arquitectura

Ypsilon és primer de tot una integració de Home Assistant, però el coneixement
reverse-engineered del dispositiu es manté per sota de la capa HA perquè es
pugui reutilitzar i, si apareixen més consumidors, extreure a una llibreria Python.

## Direcció de dependències

```text
Home Assistant (entitats / config flow / serveis)
                 |
                 v
          política Ypsilon
       (api.py + coordinator.py)
                 |
        +--------+---------+
        |                  |
        v                  v
   client/codec         transport
   Runxin F79D         concret
        |                  |
        +--------+---------+
                 |
                 v
              maquinari
```

Ruta provada:

```text
Home Assistant
 -> YpsilonLocalClient
 -> F79DClient
 -> codec F79D
 -> trama Runxin crua
 -> BroadlinkBL3372Transport
 -> BL3372 0x6A/xifrat/TFB
 -> vàlvula Runxin F79D
```

## Responsabilitats

`runxin/`
: protocol independent de Home Assistant i BroadLink: framing observat, catàleg
  F79D, encode/decode i `F79DClient`. Pot usar hooks estructurals opcionals com
  `transact_write()` sense importar cap transport concret.

`transport/`
: porta una trama Runxin crua al controlador. El BL3372 concentra autenticació,
  xifrat, `0x6A`, TFB, errors externs i sessions. Les lectures poden tenir
  reintents acotats; una escriptura amb lliurament ambigu s'envia com a màxim un cop.

`api.py`
: adapta el perfil Ypsilon G6 i compon `F79DClient` amb el transport BL3372.
  Manté les façanes de compatibilitat i la memòria cau específica del camp 52.

`coordinator.py`
: polling HA, tolerància stale, cadència adaptativa, rellotge i reconciliació. La
  mutació completa `SET -> GET estricte -> reconciliació` està serialitzada. Un
  ACK mai equival a estat físic i un ACK perdut no provoca un reenviament cec.

Entitats
: presenten dades i controls segurs; no construeixen paquets.

## Regles d'arquitectura

- `runxin/` no importa Home Assistant ni BroadLink.
- El framing Runxin no coneix TFB/xifrat/sessió BL3372.
- `transport/base.py` no coneix camps F79D.
- Un transport retorna trames Runxin crues, no diccionaris descodificats.
- `api.py` compon capes; no conté lògica de paquet/xifrat/codec de camps.
- Refactors interns no canvien ids d'entitats, versió de config entry ni
  l'estratègia d'identitat per MAC.
- Els reintents respecten la idempotència: un SET ambigu es reconcilia abans de
  qualsevol possible reenviament.

## Reutilització i extensió

El codi està preparat per extreure's a una llibreria independent quan existeixi
un segon consumidor real, però avui mantenir un altre paquet seria cost sense
benefici. No facis que una altra integració custom depengui en runtime de
`custom_components.ypsilon_local`.

Un segon transport per al mateix F79D ha d'implementar el contracte de trama crua
sense modificar el codec F79D. Un altre controlador Runxin ha d'afegir un perfil
nou i només compartir framing si les captures ho demostren. No s'han de considerar
universals els 52 camps actuals.

## Compatibilitat

L'arquitectura 2.4.x conserva `ypsilon_local`, config-entry v2, unique ids per MAC,
unique ids d'entitats i les façanes `protocol.py`/`api.py`. La integració HA
continua suportant únicament la combinació verificada F79D model 9 + BroadLink
BL3372 devtype `0x520F`.
