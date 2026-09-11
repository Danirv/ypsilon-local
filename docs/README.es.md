# Ypsilon para Home Assistant

Integración local para descalcificadores compatibles con **Runxin F79D + BroadLink BL3372**, probada con ATH/BWT Ypsilon G6.

- Descubrimiento DHCP y configuración manual por IP.
- Lectura local de caudal, consumo diario, capacidad restante, fase de válvula, modo de regeneración, patrón de trabajo y avisos.
- Escrituras con lectura física posterior estricta: un ACK no se considera estado confirmado.
- Controles verificados de dureza, cantidad de sal añadida, protecciones de caudal/tiempo, hora de regeneración, reloj y regeneración forzada.
- Estado de vacaciones solo de lectura; la 2.6.1 retira el switch de vacaciones porque la escritura local directa del campo 49 no quedó confirmada físicamente en el G6 probado.
- Diagnósticos para fases de lavado, disolución de sal, pausa 1, errores, comunicación y mantenimiento.
- Traducciones CA/ES/EN y branding local con icono cuadrado y logotipo horizontal independientes.

## Cambios principales de la 2.6.1

- Vacaciones: el campo 49 se sigue leyendo y el sensor `desactivado / preparando / activo` se mantiene, pero no se expone ninguna escritura hasta conocer y verificar físicamente la acción local del firmware actual.
- Consumo diario: se mantiene como contador `TOTAL_INCREASING` que crece durante el día y se reinicia al cambio de día.
- Campo 39: pasa a llamarse **Consumo semanal medio del controlador**. No es el total semanal de las barras históricas de la app oficial.
- Campo 41: **Capacidad de tratamiento por ciclo**, no un contador de consumo.
- Campo 43: **Cantidad de sal añadida**, un valor de registro/configuración en kg; no es el nivel de sal restante y no se decrementa automáticamente después de una regeneración.
- Branding regenerado: `icon` 256×256 con márgenes seguros, `icon@2x`, logo horizontal y variantes 2x/dark.
- Tests y `scripts/audit.py` amplían las regresiones de vacaciones, estadísticas de agua, sal y geometría del branding.

## Estadísticas antiguas de Home Assistant

Versiones anteriores crearon estadísticas de largo plazo para el consumo medio semanal y la capacidad por ciclo cuando todavía declaraban `state_class`. Tras actualizar, Home Assistant puede ofrecer eliminar esas estadísticas obsoletas. Es correcto eliminarlas: esto no elimina la entidad ni el historial normal del Recorder.

## Instalación

Con HACS, añade `https://github.com/Danirv/ypsilon-local` como repositorio personalizado de tipo **Integration** hasta que quede incorporado al catálogo por defecto. Manualmente, copia `custom_components/ypsilon_local` a `/config/custom_components/ypsilon_local`.

## Consumo de agua

Para consumo acumulado utiliza **Consumo diario**. **Caudal** es una muestra instantánea y puede no reflejar consumos muy cortos entre dos sondeos. Para obtener un total real de la semana en Home Assistant, derívalo del contador diario/estadísticas; no utilices el campo 39 como si fuera el total de la semana actual.

## Seguridad

La integración puede cambiar parámetros e iniciar movimientos de válvula. No es un controlador de seguridad certificado ni debe ser la única protección contra fugas o inundaciones. Un campo conocido por el códec no se convierte en control de usuario hasta que la acción real queda verificada físicamente.

Consulta el [README principal](../README.md), [`waterdevice-audit.es.md`](waterdevice-audit.es.md), [`f79d.es.md`](f79d.es.md), [`hardware-verification.es.md`](hardware-verification.es.md), [SECURITY](../SECURITY.md) y [LEGAL](../LEGAL.md).
