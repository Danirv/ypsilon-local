[English](PUBLISHING.md) | [Español](PUBLISHING.es.md) | [Català](PUBLISHING.ca.md)

# Publicar Ypsilon a GitHub i HACS

L'arbre de codi està preparat per al repositori públic `Danirv/ypsilon-local` i la seva distribució mitjançant HACS.

## 1. Metadades del repositori

En un clon/plantilla nou, configura el propietari una sola vegada:

```bash
python scripts/configure_repository.py Danirv --repo ypsilon-local
```

Després verifica:

```bash
python scripts/publication_check.py
python scripts/audit.py
python -m pytest -q
python -m compileall -q custom_components/ypsilon_local scripts
```

## 2. Requisits del repositori

Mantén Issues habilitat i temes útils com `home-assistant`, `hacs`, `custom-component`, `water-softener`, `runxin`, `broadlink` i `ypsilon`.

El repositori inclou validació HACS, hassfest, auditoria offline de protocol/arquitectura i workflow automatitzat de releases. No ignoris errors de validació abans de publicar ni mentre hi hagi una sol·licitud d'inclusió a HACS oberta.

## 3. Publicar una GitHub Release des de la web

1. Fusiona el bump de versió i les release notes a `main` només quan HACS, hassfest i l'auditoria offline estiguin en verd.
2. Obre GitHub **Actions** → **Publish GitHub release**.
3. Prem **Run workflow** i comprova que la branca sigui `main`.
4. Executa el workflow.

El workflow llegeix la versió de `custom_components/ypsilon_local/manifest.json`, torna a validar el codi, crea el tag `v<versió>` sobre el commit exacte de `main`, construeix el ZIP i crea la GitHub Release.

### Alternativa amb Git

```bash
VERSION="$(python -c 'import json; print(json.load(open("custom_components/ypsilon_local/manifest.json"))["version"])')"
git tag -a "v${VERSION}" -m "Ypsilon ${VERSION}"
git push origin "v${VERSION}"
```

No creïs manualment una altra GitHub Release per al mateix tag.

## 4. Provar mitjançant HACS

Abans de sol·licitar inclusió per defecte, afegeix el repositori com a Integration personalitzada, instal·la/actualitza, reinicia Home Assistant i verifica el camí real contra maquinari.

## 5. Inclusió per defecte a HACS

El projecte té una sol·licitud oberta a `hacs/default#10717`. El manteniment normal i noves releases poden continuar mentre espera revisió. No obris sol·licituds duplicades ni comentis al PR de cua llevat d'informació crítica o petició del revisor.

## Disciplina de release

Per a cada release:

1. Actualitza la versió de `manifest.json`.
2. Actualitza `CHANGELOG.md` i `info.md`.
3. Executa auditoria, publication check, pytest i compileall.
4. Fusiona només amb HACS/hassfest/audit en verd.
5. Publica preferentment des d'Actions a `main`.
6. Verifica l'asset resultant i els checks de `main`.

No pugis mai APK del fabricant, firmware, binaris/scripts propietaris, credencials, claus privades/d'aparellament ni captures sense sanejar.
