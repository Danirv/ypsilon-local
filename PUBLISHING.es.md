[English](PUBLISHING.md) | [Español](PUBLISHING.es.md) | [Català](PUBLISHING.ca.md)

# Publicar Ypsilon en GitHub y HACS

El árbol de código está preparado para el repositorio público `Danirv/ypsilon-local` y su distribución mediante HACS.

## 1. Metadatos del repositorio

En un clon/plantilla nuevo, configura el propietario una sola vez:

```bash
python scripts/configure_repository.py Danirv --repo ypsilon-local
```

Después verifica:

```bash
python scripts/publication_check.py
python scripts/audit.py
python -m pytest -q
python -m compileall -q custom_components/ypsilon_local scripts
```

## 2. Requisitos del repositorio

Mantén Issues habilitado y temas útiles como `home-assistant`, `hacs`, `custom-component`, `water-softener`, `runxin`, `broadlink` y `ypsilon`.

El repositorio incluye validación HACS, hassfest, auditoría offline de protocolo/arquitectura y workflow automatizado de releases. No ignores fallos de validación antes de publicar ni mientras haya una solicitud de inclusión en HACS abierta.

## 3. Publicar una GitHub Release desde la web

1. Fusiona el bump de versión y las release notes en `main` solo cuando HACS, hassfest y la auditoría offline estén en verde.
2. Abre GitHub **Actions** → **Publish GitHub release**.
3. Pulsa **Run workflow** y comprueba que la rama sea `main`.
4. Ejecuta el workflow.

El workflow lee la versión de `custom_components/ypsilon_local/manifest.json`, vuelve a validar el código, crea el tag `v<versión>` sobre el commit exacto de `main`, construye el ZIP y crea la GitHub Release.

### Alternativa con Git

```bash
VERSION="$(python -c 'import json; print(json.load(open("custom_components/ypsilon_local/manifest.json"))["version"])')"
git tag -a "v${VERSION}" -m "Ypsilon ${VERSION}"
git push origin "v${VERSION}"
```

No crees manualmente otra GitHub Release para el mismo tag.

## 4. Probar mediante HACS

Antes de solicitar inclusión por defecto, añade el repositorio como Integration personalizada, instala/actualiza, reinicia Home Assistant y verifica el camino real contra hardware.

## 5. Inclusión por defecto en HACS

El proyecto tiene una solicitud abierta en `hacs/default#10717`. El mantenimiento normal y nuevas releases pueden continuar mientras espera revisión. No abras solicitudes duplicadas ni comentes en el PR de cola salvo información crítica o petición del revisor.

## Disciplina de release

Para cada release:

1. Actualiza la versión de `manifest.json`.
2. Actualiza `CHANGELOG.md` e `info.md`.
3. Ejecuta auditoría, publication check, pytest y compileall.
4. Fusiona solo con HACS/hassfest/audit en verde.
5. Publica preferentemente desde Actions en `main`.
6. Verifica el asset resultante y los checks de `main`.

Nunca subas APK del fabricante, firmware, binarios/scripts propietarios, credenciales, claves privadas/de emparejamiento ni capturas sin sanear.
