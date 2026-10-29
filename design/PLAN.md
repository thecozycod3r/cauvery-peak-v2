# Cauvery Peak — rework plan (29 Oct 2026)

Method: `~/Desktop/Website Master Design` (brief → outline → lock → slice → complete → enhance → QA).
Sources of truth: the live store for facts (memory: project-cauvery-peak), client-confirmed contacts (16 Aug), the **official Packaging Identity 1.0** for brand, the **Oct 26 shoot + client library** for imagery.

## 1. Brief
| | |
|---|---|
| Thesis | **A destination that sells coffee**, not a coffee brand with an estate. Semrush: Yercaud tourism ≈ 1000× coffee-ecommerce demand, near-zero competition; the destination itself is absent from those SERPs. |
| Audiences | (1) Yercaud visitors planning a day — mobile, Google/Instagram; (2) coffee buyers — shop; (3) café walk-ins; (4) B2B. |
| **Primary action** | **Book the Coffee Experience Tour** — ₹600/person, 75 min, guide, 5 stops (wet mill, dry mill, roasting & grinding, museum, café), own vehicle on all-weather roads (store copy). Booking stays the store's product + phone/WhatsApp **+91 94874 58387**. |
| Secondary | Shop coffee (store checkout) · Find a café (live open/closed; all close Tuesdays) |
| Proof | BBC News Tamil feature; press scans; archive from 1867 onward; real people from the shoot (founders, team). No invented reviews. |
| Out of scope | Shopify commerce (products, prices, checkout) — unchanged. |

## 2. What changes vs the current review build
1. **Brand, tightened**: the build already uses the packaging palette (petrol #00313B, gold, estate codes) and Lane Narrow; reconcile to the identity PDF's exact values (Deep Blue #002D3E; Shevaroys #795159 in the PDF vs #99573C in the build — check against the printed 2025 labels before changing).
2. **Photography-led**: graded Oct-26 shoot + client library replace CC0 stand-ins and cropped store composites.
3. **Signature film**: graded 4K landscape/sunrise footage (S-Log3 → Rec.709 + house grade).
4. **Homepage cut from ~21 phone screens to ~10**, ordered by the thesis: visit first, coffee second.
5. Master Design rules applied: one primary action per screen, local scrims (no blanket overlays), content visible without JS, reduced-motion fallbacks, R12 budgets, provenance.
6. The proven bits stay: build.py fragment system, all routes, schema, policies import, catalog sync, redirects, content-hashed assets.

## 3. Design lock (draft)
- **Deep Blue `#002D3E`** — structure, dark bands, primary buttons (brand-adopted option 1).
- **Estate codes** used exactly as on packs/tabs: Cauvery Peak `#394951`, Shevaroys `#795159`, Glenfell `#00808C`.
- **Kraft** (pouch) — sampled from pack photography; hairlines/small accents only, never large fills.
- **Paper** — a light neutral sampled from label stock (not the generic cream); body ink near-black with a blue bias.
- **Type**: Lane Narrow (brand wordmark face, from the client) for wordmark/eyebrows/nav only — web-embedding licence to confirm; display serif + humanist sans for reading (finalise in slice; current build ships Fraunces + Archivo).
- **Signature effect (1)**: the hero film. The three-estate elevation sequence is an explanatory scroll (R15 allowance: "explains something"), desktop-first, stills on phones.
- **Decorative (≤2)**: line/fade reveals; image unveil.
- Budgets: R12 (initial ≤1 MB on mobile, video deferred until after load, poster first).

## 4. Home outline (each section has a job)
1. **Hero film** — where/what in one line + *Book the tour* (primary) + *Shop coffee* + live "Open today 7:30–5 · closed Tuesdays". Job: orient the Yercaud visitor and convert.
2. **Proof strip** — BBC News Tamil · press · since 1867 · 4,600 ft. Job: credibility in the first scroll.
3. **The tour, stop by stop** — 5 stops with graded clips (wet mill → café). Job: show what ₹600 buys → Book.
4. **Three estates by altitude** — Glenfell → Shevaroys → Cauvery Peak; "higher is brighter, lower is rounder" (client-approved framing). Job: the terroir story a non-expert follows → shop each estate.
5. **Shop** — 3–4 coffees with real product photography. Job: purchase path.
6. **Cafés** — three locations, live open/closed, directions, photos. Job: walk-in footfall.
7. **Heritage & people** — archive, museum, founders/team from the shoot. Job: trust + story.
8. **Plan your visit** — how to reach, timings, what to expect (only verified facts). Job: capture Yercaud tourism search.
9. Footer — contacts as confirmed.
Inner pages (visit, tour PDP, estate, story/history, cafés ×3, coffee, press, shop/PDPs) get the same media + system.

## 5. Media pipeline (drive is read-only; outputs go to `assets/media/`)
1. **Index** every real file (skip `._*` stubs): path, type, size, dims, capture time, camera, gamma (S-Log3 vs Rec.709 from XML).
2. **Score stills**: sharpness (Laplacian variance), exposure/clipping, burst de-dupe (perceptual hash), keep the best of each burst.
3. **Video thumbnails**: one mid-clip frame per clip → contact sheets per shooter folder.
4. **Select** by eye from contact sheets (~60 stills, ~20 clips), mapped to sections.
5. **Grade** — "Shevaroy morning": correct S-Log3/S-Gamut3.Cine → Rec.709 with a filmic tone curve; house look = cool, slightly blue-biased shadows (toward Deep Blue), deep natural greens (no neon yellow-green), protected skin, warm low-sun highlights, gentle contrast. Same look baked into stills (RAW developed via LibRaw where an ARW exists) so stills and film match.
6. **Export**: stills WebP 2400/1600/800 (q80, eyeballed); hero/section loops 1080p + 720p H.264 (6–12 s, no audio, faststart) + posters; 100p clips conformed to slow motion. Provenance in `CREDITS.md`.

## 6. Order of work
1. Plan (this) → 2. media index + scoring (background) → 3. design lock + homepage slice on placeholders → 4. curate + grade → 5. attach media, complete inner pages → 6. QA (budgets, a11y, no-JS, mobile, Codex visual review) → 7. preview on the review URL for Dhruv → client.

## 7. Open questions (non-blocking)
- Lane Narrow web licence · consent for people in the shoot folders (Founders, Prajwal, Krithika, Subanu, Sanjith, Shwetha) · exact founding year wording · tour booking flow (still a shippable Shopify product).
