[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificación de escrituras con hardware real

Un campo solo se marca como `HARDWARE_WRITE_VERIFIED` cuando la integración
local demuestra el recorrido completo contra un controlador físico. Un ACK del
protocolo por sí solo no es suficiente.

## Secuencia obligatoria

Para un parámetro reversible:

1. **GET inicial** — leer localmente el valor actual y guardarlo.
2. **SET de prueba** — enviar una única escritura local con la integración/codec.
3. **GET independiente** — volver a consultar físicamente el controlador.
4. **Comprobación física/semántica** — confirmar que el estado observado significa
   realmente lo esperado, no solo que hubo ACK.
5. **Restaurar** — volver a escribir el valor inicial.
6. **GET de restauración** — verificar que el estado original ha quedado restaurado.

El estado cacheado del coordinador no sirve como evidencia: la confirmación debe
proceder de una lectura física nueva.

## Entrega ambigua

Si el transporte agota el tiempo o pierde la respuesta después de enviar un SET,
**no se debe reenviar la orden a ciegas**. El controlador podría haberla ejecutado.
Primero se realiza un GET independiente y se reconcilia el estado físico. Esto
es especialmente importante en acciones mecánicas como forzar una regeneración.

## Niveles de evidencia

- solo codec de la app → `LEGACY_APP_CODEC`;
- valor observado en estado real → `DEVICE_STATE_OBSERVED`;
- cambio observado por cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura independiente completa → `HARDWARE_WRITE_VERIFIED`.

## Estado actual Ypsilon G6 / F79D

Verificados localmente de extremo a extremo: campos **4, 6, 7, 10, 43 y 47**.
El campo 7 se ha validado con `waterVolumeUnit=2`.

Pendientes: **34 (forzar regeneración)** y **49 (modo vacaciones)**.

La evidencia de un modelo, firmware, rebrand o transporte no debe generalizarse
silenciosamente a todos los dispositivos Runxin.
