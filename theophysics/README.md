# Theophysics Workbench (isolated first slice)

This AGPL-compatible addition extends, but does not replace, Marginalia's search-service mock surface. Upstream commit `5b5f7aeb9b917126c8caf2b1fedd71e91bca8aaa` remains its base.

## Launch

On x86-64 Linux with JDK 25 and the repository setup data, run `./gradlew :code:services-application:search-service:paperDoll -i`, then open `http://localhost:9999/theophysics/index.html`. Alternatively run `docker compose -f theophysics/docker/compose.paperdoll.yml up` from the repository root. No crawl starts from either command.

The shell connects only to Marginalia through its ordinary local `/search?query=...&profile=theophysics` URL. Other provider controls are provenance-preserving placeholders. Browser events are disabled by default and, when enabled, remain in namespaced `localStorage`; no network event sink exists. Clearing, JSON export/import, and a readable viewer are provided.

`PersonalizedPageRank` is documented as a future extension point only. The projection in the UI never changes rankings and is always labeled **PERSONAL RELEVANCE — NOT A TRUTH OR QUALITY GRADE**. Saving, judging, or requesting preservation never changes canonical standing. Crawl4AI is contract-only: the verified Duke receipt and ledger were unavailable in this Linux workspace, so no local adapter was invented and no crawl occurred.

## Machine inspection

The requested Windows/UNC dashboard and Duke paths were not mounted in `/workspace` or `/mnt`; their contracts could not be verified here. Marginalia documents x86-64 Linux, Docker, JDK 25, `liburing`, and setup/model data requirements. The Docker profile addresses the OS/JDK launch shape but still requires Docker and setup data on the host.

## URL → Markdown

Run `python3 theophysics/markdown_service.py`, then open `http://127.0.0.1:8765/theophysics/index.html`. The local server accepts unauthenticated public HTTP(S) URLs, blocks private/link-local destinations, limits captures to 5 MB, and performs no JavaScript execution. Preview and download do not write research files. Batch saves require an explicit checkbox review for each successful preview.

Reviewed saves are written beneath ignored `theophysics/captures/<destination>/<url-hash>/<retrieval-time>-<content-hash>/`. Every save uses a new immutable directory (`exist_ok=False`) containing `capture.md`, `source.html`, and `receipt.json`; it cannot overwrite an earlier version. “Claim extraction/canonization” writes only to `claim-extraction-staging` with `canonized: false`. Admission to canon is intentionally outside this slice.

Local HTTP extraction is the default. Crawl4AI, Jina Reader, and ScreenshotOne are visibly separate optional fallbacks and remain `NOT CONNECTED` until their server-side contracts can be verified. ScreenshotOne is not required. No API-key field exists in the browser interface.
