[English](hardware-verification.md) | [Español](hardware-verification.es.md) | [Català](hardware-verification.ca.md)

# Verificación de escrituras sobre hardware

Un campo solo se marca `HARDWARE_WRITE_VERIFIED` cuando la integración local ha probado toda la ruta de escritura y lectura posterior contra un controlador físico. Un ACK o un códec autoconsistente no son suficientes.

## Secuencia requerida

Para un campo de configuración reversible:

1. **GET inicial** — leer el valor actual localmente.
2. **SET candidato** — enviar una única escritura con el códec que se quiere validar.
3. **GET independiente** — volver a consultar físicamente el controlador.
4. **Validación física/semántica** — confirmar que el estado observado significa lo esperado.
5. **Restauración** — volver a escribir el valor inicial.
6. **GET de restauración** — verificar que el estado original se ha recuperado.

No se debe utilizar estado cacheado del coordinator como evidencia.

## Entrega ambigua

Si el SET ya se ha enviado pero se pierde la respuesta o hay timeout, **no se reenvía a ciegas**. El controlador podría haberlo ejecutado. Primero debe hacerse un GET nuevo y reconciliar el estado físico.

Esta regla es especialmente importante para regeneraciones y transiciones de vacaciones.

## Niveles de evidencia

- códec de la app → `LEGACY_APP_CODEC`;
- valor observado en el dispositivo → `DEVICE_STATE_OBSERVED`;
- cambio observado en cloud → `CLOUD_WRITE_OBSERVED`;
- SET local + lectura física independiente completa → `HARDWARE_WRITE_VERIFIED`.

## Estado actual Ypsilon G6 / F79D

Verificados localmente de extremo a extremo:

- campo 4 — reloj;
- campo 6 — límite de consumo continuo;
- campo 10 — hora de regeneración;
- campo 43 — sal añadida;
- campo 47 — dureza del agua de entrada.

Pendientes o a revalidar:

- **campo 7 — umbral de cierre por caudal:** WaterDevice confirma que el códec correcto es little-endian. Las versiones anteriores a 2.6 utilizaban BE tanto al escribir como al leer, por lo que el read-back podía autoconfirmar una endianidad incorrecta. Por ello se retira la antigua marca `HW` hasta probar físicamente el camino LE corregido;
- campo 34 — regeneración forzada;
- campo 49 — modo vacaciones.

## Verificación de estados mecánicos

Para los campos 34 y 49 no basta con comprobar un único bit. También hay que validar la transición física esperada.

Para vacaciones, la semántica recuperada de la aplicación antigua es:

- entrar solo desde station/system mode 0;
- el campo 49 pasa a verdadero;
- el controlador recorre la preparación mecánica;
- vacaciones estables = campo 49 verdadero + station 8;
- la salida se inicia desde station 8 y debe reconciliarse con el estado físico posterior.

Solo después de observar este flujo completo el campo 49 podrá marcarse `HARDWARE_WRITE_VERIFIED`.

La evidencia de un controlador o firmware no debe generalizarse automáticamente a todos los dispositivos Runxin.
