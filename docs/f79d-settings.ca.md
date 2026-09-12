# Semàntica dels ajustos F79D recuperats

Aquest document recull els ajustos recuperats de la pantalla avançada de l'antiga WaterDevice i deixa explícita la seva representació a Home Assistant. Complementa `f79d.ca.md`; que el còdec pugui codificar un camp no implica que sigui segur exposar-lo com a control d'escriptura.

## Camps enum

| Camp | Nom del protocol | Valors crus | Estats de Home Assistant | Política HA |
|---:|---|---|---|---|
| 2 | `language` | 0 xinès, 1 anglès, 2 espanyol, 3 francès, 4 rus, 5 italià, 6 alemany, 7 polonès | `chinese` … `polish` | enum de diagnòstic, deshabilitat per defecte |
| 3 | `deviceTimeScheme` | 0 12 hores, 1 24 hores | `12_hour`, `24_hour` | enum de diagnòstic, deshabilitat per defecte |
| 24 | `outRelayMode` | 0 `b-01`, 1 `b-02` | `b_01`, `b_02` | enum de diagnòstic, deshabilitat per defecte |
| 48 | `absorbSaltMode` | 0 aspiració inversa (`逆吸`), 1 aspiració directa (`顺吸`) | `reverse`, `forward` | enum de diagnòstic, deshabilitat per defecte |

Les claus d'estat estables de Home Assistant no utilitzen text traduït. El codi cru original es conserva a l'atribut `raw_code` de l'entitat.

## Camps numèrics recuperats de la mateixa UI

| Camp | Nom del protocol | Rang WaterDevice | Representació HA |
|---:|---|---:|---|
| 13 | `washingIncreaseNumber` | 0–20 | sensor de diagnòstic només lectura, deshabilitat per defecte |
| 14 | `backWashIntervalNumber` | 0–20 | sensor de diagnòstic només lectura, deshabilitat per defecte |
| 25 | `regenerationAlarmNumber` | 5–1200 | sensor de diagnòstic només lectura, habilitat per defecte |

WaterDevice etiqueta el camp 25 com el recompte de regeneracions usat per al recordatori. Al Ypsilon G6 provat el valor observat és 700. És útil com a llindar natiu per calcular el manteniment de la resina; **no** és el comptador actual de regeneracions.

## Ajustos d'escriptura existents: límits recuperats de la UI

WaterDevice limita el camp 6 (`continuousWaterTime`) a 0–120 minuts. Home Assistant replica aquest rang.

El camp 7 (`flowRateOff`) depèn de la unitat. La integració només habilita el `number` escrivible per a la família validada en metres cúbics (codi d'unitat 2), on WaterDevice limita la visualització a 10,00 m³/h. El protocol desa centèsimes, per tant el rang cru segur corresponent és 0–1000.

Els altres límits d'escriptura exposats es mantenen:

- camp 43 `saltAddition`: 0–100 kg;
- camp 47 `rawWaterHardness`: 50–1500 mg/L.

Aquests rangs de la UI són independents de la política d'evidència d'escriptura. El camp 7 continua sense evidència `HARDWARE_WRITE_VERIFIED` després de corregir l'endianness fins que es torni a validar físicament al maquinari actual.

## Font de l'evidència

Els mapatges i rangs anteriors provenen de la configuració i dels mòduls d'enums recuperats del JavaScript de l'antiga WaterDevice. `tests/test_recovered_settings_semantics.py` els protegeix contra regressions: un enum no pot tornar silenciosament a ser un sensor enter cru i els estats traduïts han de ser complets en anglès, castellà i català.
