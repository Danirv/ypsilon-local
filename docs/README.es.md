# Ypsilon para Home Assistant

Integración local para descalcificadores compatibles con **Runxin F79D + BroadLink BL3372**, probada con ATH/BWT Ypsilon G6.

- Descubrimiento DHCP y configuración manual por IP.
- Lectura local de caudal, consumo diario, capacidad restante, fase de válvula, modo de regeneración, patrón de trabajo y avisos.
- Escrituras con lectura física posterior estricta: un ACK no se considera estado confirmado.
- Controles de dureza, sal, protecciones de caudal/tiempo, hora de regeneración, reloj, vacaciones y regeneración forzada.
- Modo vacaciones con estado separado `desactivado / preparando / activo` y precondiciones coherentes con WaterDevice.
- Diagnósticos para fases de lavado, disolución de sal, pausa 1, errores, comunicación y mantenimiento.
- Traducciones CA/ES/EN y branding local para Home Assistant 2026.3+.

## Cambios principales de la 2.6.0

- El campo 7 (`flowRateOff`) pasa a little-endian, tal como indica el códec WaterDevice; el campo 11 sigue siendo big-endian.
- Los volúmenes 35–42 se decodifican según `waterVolumeUnit`.
- La unidad 1 de caudal se corrige a L/min.
- `vacationPattern=1 + station=8` se trata como el estado estable de vacaciones y no mantiene el sondeo rápido permanentemente.
- Se añaden los campos diagnósticos 50 y 51 y la interpretación de motivos de cierre conocidos.
- El servicio avanzado genérico queda limitado a configuraciones reversibles y validadas.

## Instalación

Con HACS, añade `https://github.com/Danirv/ypsilon-local` como repositorio personalizado de tipo **Integration** hasta que quede incorporado al catálogo por defecto. Manualmente, copia `custom_components/ypsilon_local` a `/config/custom_components/ypsilon_local`.

## Consumo de agua

Para el panel de agua de Home Assistant, utiliza **Consumo diario** como consumo acumulado. **Caudal** es una muestra instantánea y puede no reflejar consumos muy cortos que queden entre dos sondeos.

## Seguridad

La integración puede cambiar parámetros e iniciar movimientos de válvula. No es un controlador de seguridad certificado ni debe ser la única protección contra fugas o inundaciones.

Consulta el [README principal](../README.md), [`f79d.es.md`](f79d.es.md), [`hardware-verification.es.md`](hardware-verification.es.md), [SECURITY](../SECURITY.md) y [LEGAL](../LEGAL.md).
