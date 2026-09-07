[English](architecture.md) | [Español](architecture.es.md) | [Català](architecture.ca.md)

# Arquitectura

Ypsilon es ante todo una integración de Home Assistant, pero el conocimiento
reverse-engineered del dispositivo se mantiene por debajo de la capa HA para que
pueda reutilizarse y, si aparecen más consumidores, extraerse a una librería Python.

## Dirección de dependencias

```text
Home Assistant (entidades / config flow / servicios)
                 |
                 v
          política Ypsilon
       (api.py + coordinator.py)
                 |
        +--------+---------+
        |                  |
        v                  v
   cliente/codec       transporte
   Runxin F79D        concreto
        |                  |
        +--------+---------+
                 |
                 v
              hardware
```

Ruta probada:

```text
Home Assistant
 -> YpsilonLocalClient
 -> F79DClient
 -> codec F79D
 -> trama Runxin cruda
 -> BroadlinkBL3372Transport
 -> BL3372 0x6A/cifrado/TFB
 -> válvula Runxin F79D
```

## Responsabilidades

`runxin/`
: protocolo independiente de Home Assistant y BroadLink: framing observado,
  catálogo F79D, encode/decode y `F79DClient`. Puede usar hooks estructurales
  opcionales como `transact_write()` sin importar un transporte concreto.

`transport/`
: lleva una trama Runxin cruda al controlador. El BL3372 concentra autenticación,
  cifrado, `0x6A`, TFB, errores externos y sesiones. Las lecturas pueden tener
  reintentos acotados; una escritura ambigua se envía como máximo una vez.

`api.py`
: adapta el perfil Ypsilon G6 y compone `F79DClient` con el transporte BL3372.
  Mantiene las fachadas de compatibilidad y la caché específica del campo 52.

`coordinator.py`
: polling HA, tolerancia stale, cadencia adaptativa, reloj y reconciliación. La
  mutación completa `SET -> GET estricto -> reconciliación` está serializada. Un
  ACK nunca equivale a estado físico y un ACK perdido no provoca reenvío ciego.

Entidades
: presentan datos y controles seguros; no construyen paquetes.

## Reglas de arquitectura

- `runxin/` no importa Home Assistant ni BroadLink.
- El framing Runxin no conoce TFB/cifrado/sesión BL3372.
- `transport/base.py` no conoce campos F79D.
- Un transporte devuelve tramas Runxin crudas, no diccionarios decodificados.
- `api.py` compone capas; no contiene lógica de paquete/cifrado/codec de campos.
- Refactors internos no cambian ids de entidades, versión de config entry ni la
  estrategia de identidad por MAC.
- Los reintentos respetan la idempotencia: un SET ambiguo se reconcilia antes de
  cualquier posible reenvío.

## Reutilización y extensión

El código está preparado para extraerse a una librería independiente cuando
exista un segundo consumidor real, pero hoy mantener otro paquete sería coste sin
beneficio. No hagas que otra integración custom dependa en runtime de
`custom_components.ypsilon_local`.

Un segundo transporte para el mismo F79D debe implementar el contrato de trama
cruda sin modificar el codec F79D. Otro controlador Runxin debe añadir un perfil
nuevo y solo compartir framing si las capturas lo demuestran. No se deben
considerar universales los 52 campos actuales.

## Compatibilidad

La arquitectura 2.4.x conserva `ypsilon_local`, config-entry v2, unique ids por
MAC, unique ids de entidades y las fachadas `protocol.py`/`api.py`. La integración
HA sigue soportando únicamente la combinación verificada F79D model 9 + BroadLink
BL3372 devtype `0x520F`.
