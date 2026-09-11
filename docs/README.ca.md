# Ypsilon per a Home Assistant

Integració local per a descalcificadors compatibles amb **Runxin F79D + BroadLink BL3372**, provada amb ATH/BWT Ypsilon G6.

- Descobriment DHCP i configuració manual per IP.
- Lectura local de cabal, consum diari, capacitat restant, fase de vàlvula, mode de regeneració, patró de treball i avisos.
- Escriptures amb lectura física posterior estricta: un ACK no es considera estat confirmat.
- Controls de duresa, sal, proteccions de cabal/temps, hora de regeneració, rellotge, vacances i regeneració forçada.
- Mode vacances amb estat separat `desactivat / preparant / actiu` i precondicions coherents amb WaterDevice.
- Diagnòstics per fases de rentat, dissolució de sal, pausa 1, errors, comunicació i manteniment.
- Traduccions CA/ES/EN i branding local per a Home Assistant 2026.3+.

## Canvis principals de la 2.6.0

- El camp 7 (`flowRateOff`) passa a little-endian, tal com indica el còdec WaterDevice; el camp 11 continua big-endian.
- Els volums 35–42 es descodifiquen segons `waterVolumeUnit`.
- La unitat 1 de cabal es corregeix a L/min.
- `vacationPattern=1 + station=8` es tracta com l'estat estable de vacances i no manté el sondeig ràpid permanentment.
- S'afegeixen els camps diagnòstics 50 i 51 i la interpretació dels motius de tancament coneguts.
- El servei avançat genèric queda limitat a configuracions reversibles i validades.

## Instal·lació

Amb HACS, afegeix `https://github.com/Danirv/ypsilon-local` com a repositori personalitzat de tipus **Integration** fins que quedi incorporat al catàleg per defecte. Manualment, copia `custom_components/ypsilon_local` a `/config/custom_components/ypsilon_local`.

## Consum d'aigua

Per al tauler d'aigua de Home Assistant, utilitza **Consum diari** com a consum acumulat. **Cabal** és una mostra instantània i pot no veure consums molt curts que quedin entre dos polls.

## Seguretat

La integració pot canviar paràmetres i iniciar moviments de vàlvula. No és un controlador de seguretat certificat ni ha de ser l'única protecció contra fuites o inundacions.

Consulta el [README principal](../README.md), [`f79d.ca.md`](f79d.ca.md), [`hardware-verification.ca.md`](hardware-verification.ca.md), [SECURITY](../SECURITY.md) i [LEGAL](../LEGAL.md).
