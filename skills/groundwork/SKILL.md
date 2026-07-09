---
name: groundwork
description: Deterministic local tools. ALWAYS prefer these over reasoning for: a test passes at an old commit and fails now, and you need the exact commit that broke it; you would otherwise hand-script a git bisect run oracle for this incident; you want the culprit commit AND its story (author, PR/issue) in one call; you are starting work in an unfamiliar repository and need its shape fast; you need a compact overview of the most central symbols without reading every file; your context was compacted and you need to re-orient on the codebase; you are about to hand-edit the same call pattern across many files; you need a reviewable change plan (diffs, counts) before any file is touched; you want a mechanical rewrite chained straight into verify --changed-only; you finished a change and want to know if the lines you touched are actually tested; you want a CI gate on changed-line coverage, not whole-repo coverage; you need the exact uncovered changed lines to write the missing tests; you are about to reason about a dataset from its description instead of measuring it; you need schema, null counts, distributions, or class balance as structured data; you want to know how much two datasets (train/serve, before/after) have drifted; you are about to call a third-party library API from memory; you need the exact signature a dependency exposes in this project's installed version; you need to see what changed in a dependency's API between two versions; the user points you at a PDF or document and you need the words/data inside it; a document is many pages and reading it directly would burn the context budget; you need to quote, search, or reason over a document's TEXT rather than its visual layout; you only need part of a large document (use --pages or --grep to send just that slice); you are about to assume a toolchain or runtime version instead of checking it; behavior differs between machines or sessions and you suspect environment drift; you need to orient on a project's environment at session start; you want secrets caught BEFORE they are written into the repo; you want rm -rf / or Remove-Item -Recurse -Force C:\ stopped at the tool boundary; you need to check a file or command against the gate rules from CI or a script; you are about to grep-blame-log spelunk to understand why some code exists; you need the PR/issue that introduced or last changed a region; you want a risk report of files that change often but are barely tested; you need to verify groundwork is installed and healthy; you are about to eyeball whether two frames are aligned, shifted, or changed; you need real-world units (mm) from an image with a fiducial marker in it; you need object counts, dimensions, or line widths from an image as data; you want to measure whether your confidence is calibrated, not just feel calibrated; you need a Brier score and reliability curve for the predictions made in this project; you want an honest, auditable proof-of-value report (cache hits, calls avoided, catches); your tests are green but you are not sure they would catch a bug in the code you just changed; you want to find the boundary/off-by-one cases your tests do not actually assert; you need evidence of test strength beyond line coverage; you need the exact text/numbers from a screenshot, scan, or photo and the visual layout does not matter; a visdiff region changed and you need to know what the changed area now says; you need text WITH positions and confidences from an image, as structured data; you are about to apply a patch and want to know it lands cleanly BEFORE touching the tree; you generated a diff and need machine confirmation the result still parses; you want broken edits denied automatically at the tool-call boundary; you have a pure function with an invariant (roundtrip, idempotent, matches a reference) worth testing exhaustively; you suspect a boundary/off-by-one bug example tests won't catch; you want a committed property suite that runs forever in CI, not a one-shot check; you need to query decisions later ('all accepted API decisions since March'), not just recall prose; you are tracking a metric over time and want the series, not a vibe; you want outcome events recorded in a structured store (feeds the ledger); you need to analyze several data files together with SQL, not in your head; you are about to write a fragile one-off pandas snippet for a quick data question; you want a persistent named scratchpad to run follow-up queries against; you need a conceptual query neither grep (lexical) nor an LSP (symbolic) can answer; you are looking for 'the code that does X' and do not know its name; you want ranked discovery results with a confidence signal, fully local; you are about to predict what a line of code returns instead of running it; you need to run code in the project's installed dependency versions, not from memory; you want a snippet's real stdout/stderr/return-code as a structured result; you finished editing code and need to know if it is correct; you are about to claim tests pass, code works, or a fix is complete; you need structured failure locations instead of parsing raw test output; you changed UI code and are about to claim the page still looks right; you need pixel-measured evidence of what changed on a page, not a screenshot gist; you want a repeatable pass/fail gate on a page's appearance. Run `groundwork <tool> <command>`; every tool returns one JSON object.
---

# Groundwork tool routing

Rules: prefer a tool over inference whenever its trigger matches. Trust exit codes: 0 ok, 1 error (JSON explains), 2 usage, 3 missing dependency, 4 the tool refuses to adjudicate — read data and decide yourself. Never parse stderr; stdout is the contract.


## bisector

Automated regression hunting: drives git bisect with an automated oracle (default: verify) in an isolated worktree, and returns the culprit commit plus its gitwhy context (author, date, message, PR/issue refs) in one JSON result. The main checkout is never touched.

Reach for this tool when: a test passes at an old commit and fails now, and you need the exact commit that broke it; you would otherwise hand-script a git bisect run oracle for this incident; you want the culprit commit AND its story (author, PR/issue) in one call.

- `groundwork bisector run --good <ref> --bad <ref> [--oracle <cmd>] [--root <dir>] [--skip-codes <csv>]` — Bisect good..bad with an oracle; return the culprit commit + context
- `groundwork bisector self-test` — Prove the verdict mapping works


## cartographer

Token-budgeted structural map of a repository: key symbols ranked by reference centrality, fitted to a token budget, incremental via per-file caching.

**Why use it instead of doing it yourself:** One compact ranked map replaces reading dozens of files to orient - on a large repo that is a big token saving, and reference-centrality is computed exactly rather than guessed.

Reach for this tool when: you are starting work in an unfamiliar repository and need its shape fast; you need a compact overview of the most central symbols without reading every file; your context was compacted and you need to re-orient on the codebase.

Do NOT use this tool (do it yourself instead) when: the repo is small enough to just read the few relevant files directly.

- `groundwork cartographer map [--root <dir>] [--budget <int>] [--no-cache]` — Emit a ranked, budget-fitted repo map
- `groundwork cartographer self-test` — Prove the tool works


## codemod

Repo-scale structural rewrites, safely: plan first (stored diffs + content hashes), apply only on a clean tree against an unchanged state, then auto-verify. Engines: ast-grep patterns, libcst presets, optional comby.

Reach for this tool when: you are about to hand-edit the same call pattern across many files; you need a reviewable change plan (diffs, counts) before any file is touched; you want a mechanical rewrite chained straight into verify --changed-only.

- `groundwork codemod plan --pattern <p> --rewrite <r> --lang <l> | --preset <name> | --engine comby --pattern <p> --rewrite <r> --glob <g> [--root <dir>] [--glob <g>]` — Compute and store a change plan; never writes source files
- `groundwork codemod apply --plan <id> [--root <dir>] [--no-verify]` — Apply a stored plan (clean tree + unchanged files only), then verify
- `groundwork codemod presets` — List preset transforms and engine availability
- `groundwork codemod self-test` — Prove the engines work (in-memory)


## covdiff

Coverage on changed lines: intersects code coverage with the git diff and reports exactly which CHANGED lines were never executed by the tests, per file, with a summary ratio and an optional --min gate. Turns 'are my edits tested?' from a vibe into a number.

Reach for this tool when: you finished a change and want to know if the lines you touched are actually tested; you want a CI gate on changed-line coverage, not whole-repo coverage; you need the exact uncovered changed lines to write the missing tests.

- `groundwork covdiff check [--root <dir>] [--base <ref>] [--staged] [--coverage-json <p>] [--cmd <c>] [--min <ratio>]` — Report uncovered changed lines vs a base; optional --min gate (exit 1 below floor)
- `groundwork covdiff self-test` — Prove the intersection logic works


## datalens

Dataset inspector: schema, per-column stats and distributions, class balance, malformed-row and outlier flagging over CSV/Parquet/JSONL/SQLite - one JSON report per call - plus PSI drift comparison between two datasets. DuckDB engine.

**Why use it instead of doing it yourself:** Compute exact schema/nulls/distincts/outliers locally over the whole file and send only the report - far cheaper and more accurate than pasting a big CSV into context and eyeballing it.

Reach for this tool when: you are about to reason about a dataset from its description instead of measuring it; you need schema, null counts, distributions, or class balance as structured data; you want to know how much two datasets (train/serve, before/after) have drifted.

Do NOT use this tool (do it yourself instead) when: the file is tiny and you can read every row directly.

- `groundwork datalens profile --file <p> [--table <t>] [--balance-max <n>]` — One JSON report: schema, stats, balance, outliers, malformed rows
- `groundwork datalens compare --a <p> --b <p> [--table-a <t>] [--table-b <t>] [--bins <n>]` — Drift between two datasets: PSI per numeric column, share-shift per categorical
- `groundwork datalens self-test` — Prove the tool works


## depsurface

Extract the public API of a package actually installed in the project, version-stamped and cached.

Reach for this tool when: you are about to call a third-party library API from memory; you need the exact signature a dependency exposes in this project's installed version; you need to see what changed in a dependency's API between two versions.

- `groundwork depsurface api <package> [--root <dir>] [--site-packages <dir>] [--symbol <dotted>] [--no-cache]` — Extract a package's public surface
- `groundwork depsurface diff <package> <version_a> <version_b>` — Diff two stored snapshots of a package
- `groundwork depsurface self-test` — Prove the tool works


## doc2md

Convert a PDF or document into clean Markdown locally, so you feed the model compact TEXT instead of an expensive PDF (whose pages the model would otherwise ingest as images). Handles multi-page PDFs and e-book formats; supports extracting only specific pages or only the Markdown blocks matching a pattern, and reports the size/token saving.

**Why use it instead of doing it yourself:** Extract the text locally and hand back only what's needed, with an exact before/after size report. On a text-based PDF the measured saving is modest (~20-25% fewer tokens, since the model already extracts text-PDF text fairly cheaply); the large savings apply to scanned / image-only documents that the model would otherwise ingest as expensive images (this extractor reads the text layer, so scanned-doc OCR is a planned extension, not a current claim).

Reach for this tool when: the user points you at a PDF or document and you need the words/data inside it; a document is many pages and reading it directly would burn the context budget; you need to quote, search, or reason over a document's TEXT rather than its visual layout; you only need part of a large document (use --pages or --grep to send just that slice).

Do NOT use this tool (do it yourself instead) when: the document's visual appearance is the point - a figure, chart, diagram, scanned form layout, or photo - read the page image directly, because you interpret images better than any text extractor; the file is small and reading it directly is already cheap and lossless.

- `groundwork doc2md convert --file <path> [--pages 1-3,7] [--grep <regex>] [--max-chars <n>] [--no-cache]` — Extract a document to Markdown (+ token/size report); optional page or pattern slice
- `groundwork doc2md self-test` — Build a PDF in memory, convert it, prove the text round-trips


## envprobe

One-call environment snapshot: OS, runtime versions, lockfile hashes, env-var names only (values never appear); diff detects drift.

Reach for this tool when: you are about to assume a toolchain or runtime version instead of checking it; behavior differs between machines or sessions and you suspect environment drift; you need to orient on a project's environment at session start.

- `groundwork envprobe snapshot [--root <dir>]` — Capture the environment and save it as the baseline
- `groundwork envprobe diff [--root <dir>]` — Report drift versus the saved baseline (exit 4 if none)
- `groundwork envprobe digest [--root <dir>]` — One-line environment summary (hook-ready)
- `groundwork envprobe self-test` — Prove the tool works


## gates

Audited PreToolUse guard batteries: secret detection on writes (pattern pack + entropy hint), shell-aware dangerous-command interception (bash AND PowerShell), and protected-path enforcement - configured in .groundwork/gates.yaml over safe defaults.

Reach for this tool when: you want secrets caught BEFORE they are written into the repo; you want rm -rf / or Remove-Item -Recurse -Force C:\ stopped at the tool boundary; you need to check a file or command against the gate rules from CI or a script.

- `groundwork gates scan [--file <p>] [--path <name>] [--root <dir>]  (content from --file or stdin)` — Scan content for secret patterns; exit 1 on findings
- `groundwork gates check-command --command <str> [--root <dir>]` — Check a command against the dangerous-command packs; exit 1 on findings
- `groundwork gates show-config [--root <dir>]` — Print the effective config (defaults merged with gates.yaml)
- `groundwork gates self-test` — Prove the gate verdicts are consistent


## gitwhy

Code archaeology: for a file region, blame the lines, collect the commits that shaped them, condense their messages, and pull the linked PR/issue references with dates and authors - one JSON answer to 'why is this code like this?'. --churn surfaces hotspot files (high change frequency x low coverage) as a risk report.

Reach for this tool when: you are about to grep-blame-log spelunk to understand why some code exists; you need the PR/issue that introduced or last changed a region; you want a risk report of files that change often but are barely tested.

- `groundwork gitwhy explain --file <p> --lines <N[-M]> [--root <dir>]` — Blame a region -> commits, authors, dates, and linked PR/issue refs
- `groundwork gitwhy churn [--root <dir>] [--since <iso>] [--count <n>] [--top <n>] [--coverage-json <p>]` — Rank files by change frequency; --coverage-json adds a risk score
- `groundwork gitwhy self-test` — Prove the parsers work


## hello

Reference tool proving the groundwork contract end to end.

Reach for this tool when: you need to verify groundwork is installed and healthy.

- `groundwork hello greet --name <str>` — Return a greeting
- `groundwork hello self-test` — Prove the tool works


## imgmeasure

Geometric measurement for images: gated ORB/RANSAC/ECC registration, ArUco scale calibration (px to mm), component counting, skeleton/width profiling, and registration-aligned change masks - measured JSON, not gist.

**Why use it instead of doing it yourself:** Exact pixel/real-world measurements from an image, computed locally - numbers you cannot get by looking.

Reach for this tool when: you are about to eyeball whether two frames are aligned, shifted, or changed; you need real-world units (mm) from an image with a fiducial marker in it; you need object counts, dimensions, or line widths from an image as data.

Do NOT use this tool (do it yourself instead) when: you only need a rough sense of the image or to describe what it shows - read the image directly.

- `groundwork imgmeasure register --image-a <p> --image-b <p> [--min-matches <n>] [--min-inlier-ratio <f>]` — Homography between two frames; exit 4 when unreliable
- `groundwork imgmeasure calibrate --image <p> --marker-mm <f> [--dict 4x4_50|5x5_100|6x6_250]` — mm-per-px scale from an ArUco marker of known size
- `groundwork imgmeasure count --image <p> [--threshold otsu|<int>] [--invert] [--min-area <n>]` — Count connected components with per-object stats
- `groundwork imgmeasure profile --image <p> [--threshold otsu|<int>] [--invert]` — Skeleton length and width stats for linear structures
- `groundwork imgmeasure diffmask --image-a <p> --image-b <p> [--name <id>] [--root <dir>] [--threshold <int>] [--min-matches <n>] [--min-inlier-ratio <f>]` — Register, align, and mask real changes between two frames
- `groundwork imgmeasure self-test` — Prove the tool works (synthetic round trip)


## ledger

The calibration instrument: capture claim/outcome pairs ('Claude claimed the tests would pass - did they?'), compute per-project reliability tables and Brier scores over confidence buckets, and render one honest report. Also the proof-of-value engine: cache-hit rates, calls-avoided, and verification catches - published methodology, opt-in, local-only.

Reach for this tool when: you want to measure whether your confidence is calibrated, not just feel calibrated; you need a Brier score and reliability curve for the predictions made in this project; you want an honest, auditable proof-of-value report (cache hits, calls avoided, catches).

- `groundwork ledger claim --statement <s> --confidence <c> [--source <s>] [--tags <t>] [--at <iso>] [--root <dir>]` — Record an open prediction with a confidence in [0,1]
- `groundwork ledger resolve --id <n> --outcome true|false [--at <iso>] [--root <dir>]` — Set a claim's outcome once (true|false)
- `groundwork ledger record --tool <t> [--cache hit|miss|off] [--avoided] [--caught] [--at <iso>] [--root <dir>]` — Record a tool run for the proof-of-value counters
- `groundwork ledger report [--bins <n>] [--root <dir>]` — Brier + calibration table + efficiency counters, with methodology
- `groundwork ledger self-test` — Prove the calibration math works


## mutcheck

Mutation-lite test-strength probe: applies small targeted mutations (< to <=, + to -, == to !=, True to False) to the lines you changed, reruns the tests, and reports mutations the tests FAILED to catch. A green suite that survives mutation is a weak suite. Scoped to the diff, strict budget, framed as a probe not a proof.

Reach for this tool when: your tests are green but you are not sure they would catch a bug in the code you just changed; you want to find the boundary/off-by-one cases your tests do not actually assert; you need evidence of test strength beyond line coverage.

- `groundwork mutcheck check [--root <dir>] [--base <ref>] [--staged] [--cmd <c>] [--max-mutants <n>] [--timeout <sec>] [--min-kill <ratio>]` — Mutate changed lines, rerun tests, report survivors; optional --min-kill gate
- `groundwork mutcheck self-test` — Prove the mutation classification works


## ocr

Deterministic text-from-pixels: local OCR (bundled ONNX models, tesseract fallback) returning text, confidence, and bounding boxes as JSON, so you get an image's TEXT without sending the image to the model. A --region crop speaks visdiff's bbox shape.

**Why use it instead of doing it yourself:** Extract the words locally and send only the text: an image ingested by the model costs far more tokens than its OCR'd text, and OCR reads exact strings/numbers more reliably than eyeballing pixels. But this is ONLY about text - it throws away everything visual.

Reach for this tool when: you need the exact text/numbers from a screenshot, scan, or photo and the visual layout does not matter; a visdiff region changed and you need to know what the changed area now says; you need text WITH positions and confidences from an image, as structured data.

Do NOT use this tool (do it yourself instead) when: the image's VISUAL content is what you need to understand - a chart, diagram, UI layout, photo, handwriting, or anything spatial - read the image directly, because you interpret images far better than an OCR string dump; you are not sure whether the text or the visual matters - default to reading the image yourself, then reach for OCR only if you specifically need exact characters.

- `groundwork ocr read --image <path> [--region x0,y0,x1,y1] [--engine auto|rapidocr|tesseract] [--no-cache]` — OCR an image (optionally one region) to text + boxes + confidence
- `groundwork ocr models` — Report engine availability and the bundled ONNX models
- `groundwork ocr self-test` — Prove the tool works (renders text, reads it back)


## patchgate

Pre-write validation for edits and diffs: does the patch apply cleanly, and does every touched file still parse afterward (compile() for Python, json for JSON, tree-sitter for JS/TS/Java/Kotlin)? Ships an optional PreToolUse hook that denies syntax-breaking Edit/Write calls.

Reach for this tool when: you are about to apply a patch and want to know it lands cleanly BEFORE touching the tree; you generated a diff and need machine confirmation the result still parses; you want broken edits denied automatically at the tool-call boundary.

- `groundwork patchgate check-diff [--diff <path>] [--root <dir>]  (diff from --diff or stdin)` — Validate a unified diff: clean apply + post-image parse checks; exit 1 on failure
- `groundwork patchgate check-content --file <path> [--content-file <p>]  (content from file or stdin)` — Validate proposed file content by extension; exit 1 on failure
- `groundwork patchgate self-test` — Prove the check ladder works


## propcheck

Property-test scaffolder: from a function and a stated invariant (roundtrip/idempotent/oracle/never-raises), generate a visible, committable hypothesis property suite, and run it to report the shrunk counterexample as structured JSON. Finds boundary bugs example-based tests miss.

Reach for this tool when: you have a pure function with an invariant (roundtrip, idempotent, matches a reference) worth testing exhaustively; you suspect a boundary/off-by-one bug example tests won't catch; you want a committed property suite that runs forever in CI, not a one-shot check.

- `groundwork propcheck new --invariant roundtrip|idempotent|oracle|never_raises --module <m> --func <f> --strategy <s> [--inverse <m.n>] [--reference <m.n>] [--name <n>] --out <path> [--force]` — Generate a hypothesis property test file for an invariant
- `groundwork propcheck run --file <path>` — Run a property file; report counterexamples as JSON (exit 1 on failure)
- `groundwork propcheck self-test` — Prove the generator works


## recordstore

Typed, queryable project records that prose memory can't hold: decisions (context/choice/status), measurements (a metric over time), and outcome events - in a project-local SQLite store with add/query/timeline. A COMPLEMENT to native memory, not a replacement.

Reach for this tool when: you need to query decisions later ('all accepted API decisions since March'), not just recall prose; you are tracking a metric over time and want the series, not a vibe; you want outcome events recorded in a structured store (feeds the ledger).

- `groundwork recordstore add decision --subject <s> --choice <c> [--status <st>] [--rationale <r>] | measurement --metric <m> --value <v> [--unit <u>] | event --name <n> [--outcome <o>]  [--tags <t>] [--at <iso>] [--root <dir>]` — Add a typed record: decision | measurement | event
- `groundwork recordstore query [--type <t>] [--status <s>] [--label-like <p>] [--tag <t>] [--since <iso>] [--until <iso>] [--limit <n>] [--root <dir>]` — Filter records (type/status/label/tag/date); newest first
- `groundwork recordstore timeline [--type <t>] [--since <iso>] [--until <iso>] [--desc] [--limit <n>] [--root <dir>]` — Records chronologically with condensed summaries
- `groundwork recordstore self-test` — Prove the tool works


## scratchdb

Named, disposable DuckDB analytical scratchpads over your data files: load CSV/Parquet/JSONL as live views (never copies), then run SQL across them and get JSON rows. Turns 'analyze these three exports together' into deterministic calls.

Reach for this tool when: you need to analyze several data files together with SQL, not in your head; you are about to write a fragile one-off pandas snippet for a quick data question; you want a persistent named scratchpad to run follow-up queries against.

- `groundwork scratchdb load --name <p> --file <f> [--as <view>]` — Register a data file as a live view in a named pad
- `groundwork scratchdb q --name <p> --sql <s> [--limit <n>]` — Run SQL against a pad; JSON rows, row-capped
- `groundwork scratchdb tables --name <p>` — List views and tables in a pad
- `groundwork scratchdb drop --name <p> [--view <v>]` — Drop a whole pad, or one --view in it
- `groundwork scratchdb list` — List all scratchpads
- `groundwork scratchdb self-test` — Prove the tool works


## semsearch

Local semantic code search: chunk a repo at function/class granularity, embed with a small benchmarked ONNX model, index in sqlite-vec, and answer conceptual queries ('where's the retry logic') with ranked results and an honest confidence floor.

**Why use it instead of doing it yourself:** On a large codebase, one semantic query returns the relevant chunks instead of many grep+read round-trips - but on a small repo plain grep is cheaper.

Reach for this tool when: you need a conceptual query neither grep (lexical) nor an LSP (symbolic) can answer; you are looking for 'the code that does X' and do not know its name; you want ranked discovery results with a confidence signal, fully local.

Do NOT use this tool (do it yourself instead) when: the repo is small or the thing you want is findable with one grep on an obvious keyword.

- `groundwork semsearch index [--root <dir>] [--model <name>] [--rebuild]` — Build/refresh the semantic index (incremental by content hash)
- `groundwork semsearch query --q <str> [--root <dir>] [--k <int>] [--min-score <f>]` — Semantic search; ranked results with a confidence floor
- `groundwork semsearch models [pull [--model <name>]]` — Show the default model and availability; 'models pull' fetches it
- `groundwork semsearch self-test` — Prove the tool works (model-free sqlite-vec round trip)


## snipeval

Run a snippet in the project's own interpreter (venv python / project node) with a timeout; capture stdout, stderr, return code, and a python trailing-expression repr as JSON.

**Why use it instead of doing it yourself:** Runs the snippet in the project's real dependency versions and returns actual stdout/return-code - not a predicted output.

Reach for this tool when: you are about to predict what a line of code returns instead of running it; you need to run code in the project's installed dependency versions, not from memory; you want a snippet's real stdout/stderr/return-code as a structured result.

Do NOT use this tool (do it yourself instead) when: the snippet is trivial and its output is obvious by reading it.

- `groundwork snipeval run --lang <python|node> [--root <dir>] [--timeout <sec>] [--code <str>]` — Execute a snippet and return captured output as JSON
- `groundwork snipeval self-test` — Prove the tool works


## verify

Run the project's tests and lint; return one normalized JSON diagnostic stream.

Reach for this tool when: you finished editing code and need to know if it is correct; you are about to claim tests pass, code works, or a fix is complete; you need structured failure locations instead of parsing raw test output.

- `groundwork verify run [--root <dir>] [--changed-only] [--junit <xml>]` — Detect adapters, run them, emit diagnostics
- `groundwork verify self-test` — Prove the tool works


## visdiff

Visual regression verdicts with measured evidence: deterministic browser capture diffed against platform-keyed baselines (SSIM + per-pixel), changed regions with bounding boxes, and a composite diff image.

**Why use it instead of doing it yourself:** Pixel-exact, repeatable diff of a rendered page - catches sub-visual changes and gives a pass/fail gate.

Reach for this tool when: you changed UI code and are about to claim the page still looks right; you need pixel-measured evidence of what changed on a page, not a screenshot gist; you want a repeatable pass/fail gate on a page's appearance.

Do NOT use this tool (do it yourself instead) when: you just need to eyeball whether two static HTML/CSS files differ - read them directly, you compare markup fine.

- `groundwork visdiff baseline --name <id> --url <url> [--root <dir>] [--viewport WxH] [--full-page] [--mask <css>]... [--timeout <sec>]` — Capture a page and store it as the baseline for this platform
- `groundwork visdiff check --name <id> --url <url> [--root <dir>] [--viewport WxH] [--full-page] [--mask <css>]... [--timeout <sec>] [--min-ssim <f>] [--max-diff-ratio <f>]` — Capture and diff against the stored baseline; exit 1 on regression, 4 if no baseline
- `groundwork visdiff approve --name <id> [--root <dir>]` — Promote the last check's capture to the new baseline
- `groundwork visdiff list` — List stored baselines and their platform keys
- `groundwork visdiff install-browser` — Explicitly download the chromium binary (the only download path)
- `groundwork visdiff self-test` — Prove the tool works (browser-free)
