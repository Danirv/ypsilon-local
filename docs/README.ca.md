# Ypsilon per a Home Assistant

Integració local per a descalcificadors compatibles amb **Runxin F79D + BroadLink BL3372**, provada amb ATH/BWT Ypsilon G6.

- Descobriment DHCP i configuració manual per IP.
- Lectura local de cabal, consum diari, capacitat restant, fase de vàlvula, mode de regeneració i avisos.
- Escriptures amb lectura posterior estricta: un ACK no es considera estat físic confirmat.
- Controls de duresa, sal, proteccions de cabal/temps, hora de regeneració, rellotge, vacances i regeneració forçada.
- Diagnòstics separats de les entitats operatives.
- Traduccions CA/ES/EN.

## Instal·lació

Amb HACS, afegeix `https://github.com/Danirv/ypsilon-local` com a repositori personalitzat de tipus **Integration**. Manualment, copia `custom_components/ypsilon_local` a `/config/custom_components/ypsilon_local`.

## Consum d'aigua

Per al tauler d'aigua de Home Assistant, utilitza **Daily consumption** com a consum acumulat. **Flow rate** és opcional i només representa l'última mostra instantània.

## Seguretat

La integració pot moure la vàlvula i iniciar regeneracions. No és un controlador de seguretat certificat ni ha de ser l'única protecció contra fuites/inundacions.

Consulta el [README principal](../README.md), [SECURITY](../SECURITY.md) i [LEGAL](../LEGAL.md).
