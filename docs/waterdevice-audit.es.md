# Auditoría de WaterDevice antiguo / F79D

Este documento recoge la evidencia utilizada por Ypsilon Local para separar **conocimiento del códec**, **estado observado del controlador** y **escrituras verificadas físicamente**. El objetivo es evitar que un campo recuperado de la aplicación se confunda con un control seguro en firmware actual.

## Política de evidencia

Las etiquetas de `runxin/fields.py` significan:

- `LEGACY_APP_CODEC`: campo/codificación recuperado del códec antiguo;
- `DEVICE_STATE_OBSERVED`: campo observado en estado real del controlador;
- `HARDWARE_WRITE_VERIFIED`: una escritura local ha sido confirmada mediante una lectura fresca posterior;
- `CLOUD_WRITE_OBSERVED`: el mismo ajuste también se ha observado cambiando por la vía del fabricante.

Un ACK de transporte, por sí solo, **no** es una verificación física.

## Códec F79D

El perfil recuperado utiliza opcode de consulta `0x09` y control `0x19`. Resultados relevantes:

- campo 7 `flowRateOff`: 16 bits little-endian;
- campo 11 `flowRate`: big-endian en el cable porque el código antiguo invierte explícitamente el par;
- campo 33: dos flags de recordatorio;
- campos 35/37/39/41: valores de volumen de tres bytes repartidos entre dos TLV y dependientes de `waterVolumeUnit`;
- campos 50/51: minutos restantes de disolución de sal y pausa 1;
- campo 52: días de servicio del material filtrante.

Para unidades 0/1 los volúmenes se reconstruyen como un entero LE de 24 bits. Para unidad 2 se utiliza empaquetado decimal base-100 y la magnitud en m³ se muestra dividida por 100. Si falta la unidad o el TLV de continuación, la integración devuelve `None` en lugar de inventar un valor.

## Agua y estadísticas

**37–38 Consumo diario** es el contador acumulado del día. Los datos reales del G6 muestran que aumenta durante el día y se reinicia al cambiar de día. Por eso Home Assistant utiliza `TOTAL_INCREASING`: un descenso por reinicio inicia un nuevo ciclo de contador y no representa consumo negativo.

**39–40 Consumo semanal medio del controlador** corresponde a `averageUsedWater` del códec antiguo. No es el total de la semana que muestra el gráfico histórico de la app oficial. Ese gráfico utiliza una vía estadística separada. El sensor no tiene `state_class`.

**41–42 Capacidad de tratamiento por ciclo** es una magnitud de capacidad/configuración del controlador, no un contador acumulativo. Tampoco tiene `state_class`.

Versiones anteriores crearon estadísticas de largo plazo para los campos 39 y 41. Tras actualizar, Home Assistant puede ofrecer eliminar esas estadísticas antiguas. Es una migración esperada y no elimina la entidad ni el histórico normal.

## Sal

El campo 43 `addSalt` es una **cantidad de sal añadida**, de 0 a 100 kg, que la app antigua permite configurar. La escritura local se ha verificado físicamente y también se ha observado el cambio por la vía del fabricante.

No es un sensor físico de sal restante y Ypsilon Local no lo decrementa después de una regeneración. Los avisos físicos de sal son independientes:

- campo 31: concentración de salmuera baja;
- campo 33: recordatorio de comprobar/añadir sal.

## Vacaciones: decisión de seguridad de la 2.6.1

La UI antigua contiene la siguiente semántica:

- entrada: `holidayMode=1` desde servicio;
- salida: `holidayMode=0` cuando se ha alcanzado la estación 8;
- progresión antigua: `0 -> 3 -> 7 -> 2 -> 8`;
- durante la fase 2 en vacaciones, el progreso usa el 25% del tiempo normal de lavado lento.

Esto prueba el comportamiento de la **UI/códec antiguo**, pero no que cualquier firmware actual ejecute una escritura local directa del campo 49.

En el G6 probado, la 2.6.0 envió el campo 49, recibió ACK, pero las lecturas frescas posteriores siguieron devolviendo `vacationPattern=false`. Por tanto, en la 2.6.1:

- el campo 49 se sigue leyendo;
- el códec conserva su codificación para investigación/interoperabilidad;
- no se marca como `HARDWARE_WRITE_VERIFIED`;
- se elimina el switch de escritura de vacaciones;
- se mantiene el sensor de estado de vacaciones solo de lectura;
- no se envía ninguna secuencia mecánica deducida o no verificada.

La app actual del fabricante también dispone de operaciones dedicadas de entrada/salida de vacaciones, lo que refuerza esta decisión conservadora.

## Regla de publicación

Un control nuevo solo debe exponerse cuando estén resueltos: codificación, precondiciones, aceptación física, read-back y comportamiento ante timeout/reinicio. Conocer únicamente el códec es suficiente para implementarlo, pero no para exponerlo como control de usuario.
