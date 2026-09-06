# Ypsilon para Home Assistant

Integración local para descalcificadores compatibles con **Runxin F79D + BroadLink BL3372**, probada con ATH/BWT Ypsilon G6.

- Descubrimiento DHCP y configuración manual por IP.
- Lectura local de caudal, consumo diario, capacidad restante, fase de válvula, modo de regeneración y avisos.
- Escrituras con lectura posterior estricta: un ACK no se considera estado físico confirmado.
- Controles de dureza, sal, protecciones de caudal/tiempo, hora de regeneración, reloj, vacaciones y regeneración forzada.
- Diagnósticos separados de las entidades operativas.
- Traducciones CA/ES/EN.

## Instalación

Con HACS, añade `https://github.com/Danirv/ypsilon-local` como repositorio personalizado de tipo **Integration**. Manualmente, copia `custom_components/ypsilon_local` a `/config/custom_components/ypsilon_local`.

## Consumo de agua

Para el panel de agua de Home Assistant usa **Daily consumption** como consumo acumulado. **Flow rate** es opcional y solo representa la última muestra instantánea.

## Seguridad

La integración puede mover la válvula e iniciar regeneraciones. No es un controlador de seguridad certificado ni debe ser la única protección contra fugas/inundaciones.

Consulta el [README principal](../README.md), [SECURITY](../SECURITY.md) y [LEGAL](../LEGAL.md).
