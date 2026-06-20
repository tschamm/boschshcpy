# Releasing

## boschshcpy (this repo → PyPI)
1. Make sure `master` is green (the **Tests** workflow runs on every push/PR).
2. Bump `version=` in `setup.py`.
3. Commit `Release X.Y.Z` to `master`.
4. Tag it and push the tag:
   ```sh
   git tag vX.Y.Z && git push origin vX.Y.Z
   ```
   The **Publish to PyPI** workflow builds and publishes automatically via PyPI
   Trusted Publishing (OIDC) — no API token is stored anywhere.
5. Create the GitHub release with notes (`gh release create vX.Y.Z --notes-file ...`).

**One-time PyPI setup** (required before the first OIDC publish): on
`https://pypi.org/manage/project/boschshcpy/settings/publishing/` add a GitHub
trusted publisher — owner `tschamm`, repo `boschshcpy`, workflow `publish.yml`.

Manual fallback (only if the workflow is unavailable):
```sh
python -m build && twine upload -r boschshcpy dist/*   # needs a boschshcpy-scoped token in ~/.pypirc
```

## boschshc-hass (the HA integration → HACS)
1. Bump `version` in `custom_components/bosch_shc/manifest.json`.
2. Commit `Release X.Y.Z` to `master`, tag `vX.Y.Z`, and create a GitHub release
   with notes — HACS picks the release up automatically.

## Coordination rules
- **Never pin an unreleased library.** Only bump the `boschshcpy==` requirement
  in `manifest.json` after that boschshcpy version is published to PyPI.
- A new device that needs library support ships as a pair: release boschshcpy
  first → bump the integration's pin → release the integration.
- Use `Closes #N` in the squash/merge message only when the fix actually ships
  in the tagged release, so issues don't close before users can update.
- Keep release notes user-facing: what changed + which issues, grouped by area.
