# Ypsilon per a Home Assistant

Integració local per a descalcificadors compatibles amb **Runxin F79D + BroadLink BL3372**, provada amb ATH/BWT Ypsilon G6.

- Descobriment DHCP i configuració manual per IP.
- Lectura local de cabal, consum diari, capacitat restant, fase de vàlvula, mode de regeneració, patró de treball i avisos.
- Escriptures amb lectura física posterior estricta: un ACK no es considera estat confirmat.
- Controls verificats de duresa, quantitat de sal afegida, proteccions de cabal/temps, hora de regeneració, rellotge i regeneració forçada.
- Estat de vacances de només lectura; la 2.6.1 retira el switch de vacances perquè l'escriptura local directa del camp 49 no va quedar confirmada físicament al G6 provat.
- Diagnòstics per fases de rentat, dissolució de sal, pausa 1, errors, comunicació i manteniment.
- Traduccions CA/ES/EN i branding local amb icona quadrada i logo horitzontal independents.

## Canvis principals de la 2.6.1

- Vacances: el camp 49 es continua llegint i el sensor `desactivat / preparant / actiu` es manté, però no s'exposa cap escriptura fins conèixer i verificar físicament l'acció local del firmware actual.
- Consum diari: es manté com a comptador `TOTAL_INCREASING` que creix durant el dia i es reinicia al canvi de dia.
- Camp 39: passa a dir-se **Consum setmanal mitjà del controlador**. No és el total setmanal de les barres històriques de l'app oficial.
- Camp 41: **Capacitat de tractament per cicle**, no un comptador de consum.
- Camp 43: **Quantitat de sal afegida**, un valor de registre/configuració en kg; no és nivell de sal restant i no es decrementa automàticament després d'una regeneració.
- Branding regenerat: `icon` 256×256 amb marges segurs, `icon@2x`, logo horitzontal i variants 2x/dark.
- Tests i `scripts/audit.py` amplien les regressions de vacances, estadístiques d'aigua, sal i geometria del branding.

## Estadístiques antigues de Home Assistant

Versions anteriors van crear estadístiques de llarg termini per al consum mitjà setmanal i la capacitat per cicle quan encara declaraven `state_class`. Després d'actualitzar, Home Assistant pot oferir eliminar aquelles estadístiques obsoletes. És correcte eliminar-les: això no elimina l'entitat ni l'històric normal del Recorder.

## Instal·lació

Amb HACS, afegeix `https://github.com/Danirv/ypsilon-local` com a repositori personalitzat de tipus **Integration** fins que quedi incorporat al catàleg per defecte. Manualment, copia `custom_components/ypsilon_local` a `/config/custom_components/ypsilon_local`.

## Consum d'aigua

Per a consum acumulat utilitza **Consum diari**. **Cabal** és una mostra instantània i pot no veure consums molt curts entre dos polls. Per obtenir un total real de la setmana a Home Assistant, deriva'l del comptador diari/estadístiques; no utilitzis el camp 39 com si fos el total de la setmana actual.

## Seguretat

La integració pot canviar paràmetres i iniciar moviments de vàlvula. No és un controlador de seguretat certificat ni ha de ser l'única protecció contra fuites o inundacions. Un camp conegut pel còdec no es converteix en control d'usuari fins que l'acció real queda verificada físicament.

Consulta el [README principal](../README.md), [`waterdevice-audit.ca.md`](waterdevice-audit.ca.md), [`f79d.ca.md`](f79d.ca.md), [`hardware-verification.ca.md`](hardware-verification.ca.md), [SECURITY](../SECURITY.md) i [LEGAL](../LEGAL.md).
