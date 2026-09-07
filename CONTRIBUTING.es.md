[English](CONTRIBUTING.md) | [Español](CONTRIBUTING.es.md) | [Català](CONTRIBUTING.ca.md)

# Contribuir

Las contribuciones son bienvenidas. El proyecto prioriza control local fiable, reconciliación explícita del estado, escrituras mecánicas conservadoras y conocimiento de interoperabilidad reutilizable.

## Antes de abrir un pull request

1. Ejecuta `python scripts/audit.py`.
2. Ejecuta `python scripts/publication_check.py` en un clon público configurado.
3. Ejecuta `python -m compileall -q custom_components/ypsilon_local scripts`.
4. Mantén los textos visibles para el usuario en los archivos de traducción (`en`, `es`, `ca`).
5. Prefiere cambios pequeños y revisables y conserva los unique ids de entidades/config entries salvo que exista una migración.
6. En escrituras, distingue transporte del comando, ACK de protocolo y estado físico confirmado.

## Límites de arquitectura

Lee [`docs/architecture.es.md`](docs/architecture.es.md) antes de trabajar con el protocolo.

- `runxin/` debe seguir siendo independiente de Home Assistant y BroadLink.
- Los transports transportan tramas Runxin en bruto y no deben decodificar campos F79D.
- Paquetes, cifrado y sesión pertenecen a la implementación del transport.
- IDs de campo, codecs y evidencia pertenecen al perfil de dispositivo.
- Home Assistant decide qué escrituras conocidas son seguras de exponer.
- `protocol.py` es una fachada de compatibilidad, no el lugar para lógica nueva.

## Investigación del protocolo y datos de prueba

No publiques APK del fabricante, firmware, scripts/binarios propietarios, credenciales, claves privadas o de emparejamiento, tokens de cuenta ni capturas sin sanear con identificadores de usuario/dispositivo.

Los fixtures pequeños y saneados necesarios para probar código escrito de forma independiente son aceptables si no contienen secretos ni partes sustanciales de código/contenido del fabricante.

Al documentar un hecho de ingeniería inversa, diferencia evidencia recuperada de la app antigua, comportamiento observado en un dispositivo real, una escritura físicamente verificada y una inferencia. Es preferible marcar algo como `inferred` que presentarlo como certeza falsa.

## Nuevos transports

Consulta [`docs/adding-a-transport.es.md`](docs/adding-a-transport.es.md). Un transport debe implementar el contrato `transact(frame: bytes) -> bytes` y retirar únicamente su propia envolvente antes de devolver la respuesta.

## Nuevos dispositivos Runxin

Consulta [`docs/adding-a-device-profile.es.md`](docs/adding-a-device-profile.es.md). Incluye marca/modelo, controlador/válvula, identidad del transport/módulo si se conoce y qué campos/comandos se han verificado realmente.

## Posible librería independiente

La capa pura de protocolo está preparada para poder extraerse más adelante a una librería pública de PyPI si aparecen varios consumidores reales. Hasta entonces, no introduzcas dependencias runtime entre integraciones HACS importando un `custom_components.ypsilon_local` instalado.

## Licencia

Al contribuir aceptas que tu contribución se publica bajo la licencia Apache 2.0 del repositorio.
