# Theophysics Research Search Layer

This directory defines the Theophysics customization layer over Marginalia Search.
The upstream engine remains attributable and updateable; Theophysics-specific behavior
is added through isolated profiles, services, event contracts, and interface components.

## Governing boundaries

1. Preserve `upstream/master` and record the upstream commit for every release.
2. Do not silently change Marginalia's ranking logic. Theophysics weights are additive,
   named, inspectable, and individually disableable.
3. Browsing behavior produces preference evidence, not truth grades.
4. Saving, downloading, or crawling a page does not canonize its contents.
5. Private behavioral history stays local unless David explicitly exports it.
6. Crawlers preserve source URL, capture time, content hash, and extraction receipt.
7. Alternate engines are separately labeled; results never masquerade as native index hits.

## Product shape

The first interface keeps the Marginalia result surface and adds two narrow research rails.

### Left rail: query construction

- Search profiles: small web, academia, vintage, forums, plain text, and Theophysics.
- Stackable query operators: exact phrase, site/domain, title, file type, exclusions,
  date constraints, and reusable query recipes.
- Alternate providers: Marginalia, local index, SearXNG, Exa, Brave, and manually
  configured OpenAI-compatible research services.
- A visible final-query preview before submission.

### Right rail: source actions

- Preserve page with Crawl4AI.
- Add domain or URL to the native crawl queue.
- Save to research intake.
- Download media through the existing URL-capture integration.
- Mark useful, irrelevant, hostile-control, primary-source, or return-later.
- Show why the result ranked and which preference signals affected it.

## Preference model

The model observes explicit research behavior:

- result impression;
- result opened;
- result position;
- click depth from the search result;
- active dwell time;
- back-to-results latency;
- repeated visit;
- saved/bookmarked;
- preserved by crawler;
- media downloaded;
- explicit useful/not-useful judgment;
- query reformulation after visiting.

These events update a local transition graph. A Markov-style transition model describes
navigation tendencies; Personalized PageRank propagates preference over the domain graph.
Neither score measures truth. Both must be resettable and explainable per result.

## System boundaries

```text
Query composer
  -> provider adapters
  -> Marginalia query/index services
  -> result merger with provider provenance
  -> explicit ranking explanation
  -> browser event ledger
  -> local preference graph
  -> Personalized PageRank seed set

Result action
  -> preserve/crawl request
  -> Crawl4AI or Marginalia crawl queue
  -> immutable capture receipt
  -> research intake
  -> separate claim/canonization pipeline (never automatic)
```

## Implementation order

1. Run the existing `paperDoll` UI against mock data.
2. Add a Theophysics search profile without changing existing profiles.
3. Add the query-construction rail and final-query preview.
4. Add a local-only browser event ledger and explicit feedback controls.
5. Connect events to a preference projection and existing Personalized PageRank.
6. Add Crawl4AI and native crawl-queue actions with receipts.
7. Add alternate-provider adapters and provenance-preserving result merging.
8. Connect the existing media URL-capture integration.

## Current upstream baseline

- Repository: `https://github.com/MarginaliaSearch/MarginaliaSearch`
- Commit: `5b5f7aeb9b917126c8caf2b1fedd71e91bca8aaa`
- Working branch: `theophysics-workbench`
- Primary license: AGPL-3.0 with documented exceptions
- Runtime target: x86-64 Linux, Docker, JDK 25, and `liburing`

