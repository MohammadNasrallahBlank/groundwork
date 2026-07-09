# Groundwork A/B — with vs without

_46 graded runs across 23 tasks. Columns: **without** (control) and **with** (Groundwork) are means over repeated runs; **Δ%** is with-vs-without. ✅ = Groundwork better, ⚠️ = worse. Lower is better for speed/cost/effort; higher for quality._

## Overall

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.5487 | 0.5726 | +4.4% ⚠️ |
| api_requests | 6.1739 | 5.3043 | -14.1% ✅ |
| tool_calls | 7.6087 | 5.1304 | -32.6% ✅ |
| total_tokens | 658705.3043 | 548780 | -16.7% ✅ |
| billable_tokens | 98056.2609 | 78820.7391 | -19.6% ✅ |
| estimated_usd | 0.6431 | 0.4624 | -28.1% ✅ |
| groundwork_invocations | 0 | 1.1739 | n/a ✅ |
| check_pass | 0.9565 | 0.9565 | +0.0% |
| check_accuracy | 0.9203 | 0.9312 | +1.2% ✅ |
| rubric_mean | 4.8406 | 4.5942 | -5.1% ⚠️ |

## Per task

### bigmap

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.82 | 0.71 | -13.4% ✅ |
| api_requests | 7 | 5 | -28.6% ✅ |
| tool_calls | 6 | 4 | -33.3% ✅ |
| total_tokens | 609246 | 619980 | +1.8% ⚠️ |
| billable_tokens | 74524 | 132746 | +78.1% ⚠️ |
| estimated_usd | 0.5051 | 0.6998 | +38.5% ⚠️ |
| groundwork_invocations | 0 | 1 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 4.333 | 4 | -7.7% ⚠️ |

### bigsearch

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.15 | 0.21 | +40.0% ⚠️ |
| api_requests | 3 | 2 | -33.3% ✅ |
| tool_calls | 2 | 1 | -50.0% ✅ |
| total_tokens | 234113 | 127744 | -45.4% ✅ |
| billable_tokens | 48297 | 39270 | -18.7% ✅ |
| estimated_usd | 0.2335 | 0.1712 | -26.7% ✅ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### bisectorbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.48 | 1.08 | +125.0% ⚠️ |
| api_requests | 8 | 9 | +12.5% ⚠️ |
| tool_calls | 7 | 10 | +42.9% ⚠️ |
| total_tokens | 708900 | 1071914 | +51.2% ⚠️ |
| billable_tokens | 69279 | 134841 | +94.6% ⚠️ |
| estimated_usd | 0.4681 | 0.8556 | +82.8% ⚠️ |
| groundwork_invocations | 0 | 1 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 0.5 | 1.0 | +100.0% ✅ |
| rubric_mean | 4 | 5 | +25.0% ✅ |

### codemodbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 1.65 | 1.18 | -28.5% ✅ |
| api_requests | 13 | 14 | +7.7% ⚠️ |
| tool_calls | 53 | 14 | -73.6% ✅ |
| total_tokens | 3411200 | 1710547 | -49.9% ✅ |
| billable_tokens | 822377 | 114386 | -86.1% ✅ |
| estimated_usd | 5.6734 | 0.9932 | -82.5% ✅ |
| groundwork_invocations | 0 | 5 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### covdiffbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.41 | 0.7 | +70.7% ⚠️ |
| api_requests | 6 | 10 | +66.7% ⚠️ |
| tool_calls | 6 | 10 | +66.7% ⚠️ |
| total_tokens | 527453 | 1015028 | +92.4% ⚠️ |
| billable_tokens | 63057 | 80033 | +26.9% ⚠️ |
| estimated_usd | 0.3855 | 0.6133 | +59.1% ⚠️ |
| groundwork_invocations | 0 | 2 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### datalensbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.84 | 0.43 | -48.8% ✅ |
| api_requests | 8 | 6 | -25.0% ✅ |
| tool_calls | 7 | 5 | -28.6% ✅ |
| total_tokens | 647777 | 544262 | -16.0% ✅ |
| billable_tokens | 63134 | 74251 | +17.6% ⚠️ |
| estimated_usd | 0.4857 | 0.4328 | -10.9% ✅ |
| groundwork_invocations | 0 | 4 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 0.75 | 0.75 | +0.0% |
| rubric_mean | 4 | 4.333 | +8.3% ✅ |

### depsurfacebig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.53 | 0.61 | +15.1% ⚠️ |
| api_requests | 5 | 6 | +20.0% ⚠️ |
| tool_calls | 11 | 10 | -9.1% ✅ |
| total_tokens | 732712 | 870705 | +18.8% ⚠️ |
| billable_tokens | 115841 | 112310 | -3.0% ✅ |
| estimated_usd | 0.6656 | 0.7049 | +5.9% ⚠️ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 4.333 | -13.3% ⚠️ |

### doc2mdbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.32 | 0.38 | +18.8% ⚠️ |
| api_requests | 3 | 6 | +100.0% ⚠️ |
| tool_calls | 2 | 5 | +150.0% ⚠️ |
| total_tokens | 275320 | 537548 | +95.2% ⚠️ |
| billable_tokens | 116642 | 88789 | -23.9% ✅ |
| estimated_usd | 0.4886 | 0.4796 | -1.8% ✅ |
| groundwork_invocations | 0 | 3 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### gatesbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.4 | 0.38 | -5.0% ✅ |
| api_requests | 2 | 3 | +50.0% ⚠️ |
| tool_calls | 1 | 4 | +300.0% ⚠️ |
| total_tokens | 160320 | 366891 | +128.8% ⚠️ |
| billable_tokens | 40130 | 77230 | +92.4% ⚠️ |
| estimated_usd | 0.214 | 0.4033 | +88.5% ⚠️ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### gitwhybig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.3 | 0.27 | -10.0% ✅ |
| api_requests | 5 | 3 | -40.0% ✅ |
| tool_calls | 4 | 2 | -50.0% ✅ |
| total_tokens | 318268 | 226042 | -29.0% ✅ |
| billable_tokens | 44284 | 59663 | +34.7% ⚠️ |
| estimated_usd | 0.2459 | 0.2779 | +13.0% ⚠️ |
| groundwork_invocations | 0 | 1 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### hellobig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.71 | 0.19 | -73.2% ✅ |
| api_requests | 7 | 3 | -57.1% ✅ |
| tool_calls | 10 | 3 | -70.0% ✅ |
| total_tokens | 865062 | 275654 | -68.1% ✅ |
| billable_tokens | 120006 | 76852 | -36.0% ✅ |
| estimated_usd | 0.7231 | 0.3538 | -51.1% ✅ |
| groundwork_invocations | 0 | 2 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 3 | -40.0% ⚠️ |

### imgmeasurebig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.35 | 2.4 | +585.7% ⚠️ |
| api_requests | 6 | 6 | +0.0% |
| tool_calls | 5 | 5 | +0.0% |
| total_tokens | 369826 | 590848 | +59.8% ⚠️ |
| billable_tokens | 47337 | 71218 | +50.4% ⚠️ |
| estimated_usd | 0.279 | 0.4339 | +55.5% ⚠️ |
| groundwork_invocations | 0 | 1 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### ledgerbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.24 | 0.12 | -50.0% ✅ |
| api_requests | 1 | 1 | +0.0% |
| tool_calls | 0 | 0 | n/a |
| total_tokens | 80294 | 78620 | -2.1% ✅ |
| billable_tokens | 22924 | 21250 | -7.3% ✅ |
| estimated_usd | 0.124 | 0.0945 | -23.8% ✅ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 0.5 | 0.5 | +0.0% |
| rubric_mean | 4.667 | 2.667 | -42.9% ⚠️ |

### mutcheckbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.41 | 1.35 | +229.3% ⚠️ |
| api_requests | 5 | 11 | +120.0% ⚠️ |
| tool_calls | 4 | 12 | +200.0% ⚠️ |
| total_tokens | 375422 | 1280500 | +241.1% ⚠️ |
| billable_tokens | 44701 | 130310 | +191.5% ⚠️ |
| estimated_usd | 0.291 | 0.9627 | +230.8% ⚠️ |
| groundwork_invocations | 0 | 2 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### ocrbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.13 | 0.41 | +215.4% ⚠️ |
| api_requests | 3 | 5 | +66.7% ⚠️ |
| tool_calls | 2 | 4 | +100.0% ⚠️ |
| total_tokens | 158654 | 436024 | +174.8% ⚠️ |
| billable_tokens | 31050 | 71080 | +128.9% ⚠️ |
| estimated_usd | 0.1461 | 0.38 | +160.1% ⚠️ |
| groundwork_invocations | 0 | 1 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### patchgatebig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.07 | 0.2 | +185.7% ⚠️ |
| api_requests | 1 | 3 | +200.0% ⚠️ |
| tool_calls | 0 | 2 | n/a ⚠️ |
| total_tokens | 38939 | 159971 | +310.8% ⚠️ |
| billable_tokens | 10254 | 32401 | +216.0% ⚠️ |
| estimated_usd | 0.0444 | 0.1559 | +251.1% ⚠️ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### propcheckbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.27 | 0.23 | -14.8% ✅ |
| api_requests | 4 | 3 | -25.0% ✅ |
| tool_calls | 3 | 2 | -33.3% ✅ |
| total_tokens | 285331 | 200689 | -29.7% ✅ |
| billable_tokens | 47246 | 41657 | -11.8% ✅ |
| estimated_usd | 0.2533 | 0.2044 | -19.3% ✅ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 4.333 | -13.3% ⚠️ |

### recordstorebig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.73 | 0.48 | -34.2% ✅ |
| api_requests | 11 | 8 | -27.3% ✅ |
| tool_calls | 10 | 7 | -30.0% ✅ |
| total_tokens | 826465 | 643039 | -22.2% ✅ |
| billable_tokens | 61701 | 72547 | +17.6% ⚠️ |
| estimated_usd | 0.5048 | 0.4586 | -9.2% ✅ |
| groundwork_invocations | 0 | 4 | n/a ✅ |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 0.6667 | 0.6667 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### scratchdbbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.18 | 0.46 | +155.6% ⚠️ |
| api_requests | 3 | 5 | +66.7% ⚠️ |
| tool_calls | 3 | 6 | +100.0% ⚠️ |
| total_tokens | 281316 | 499861 | +77.7% ⚠️ |
| billable_tokens | 51572 | 65395 | +26.8% ⚠️ |
| estimated_usd | 0.2663 | 0.3913 | +46.9% ⚠️ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 0.0 | 0.0 | n/a |
| check_accuracy | 0.75 | 0.5 | -33.3% ⚠️ |
| rubric_mean | 4.333 | 4.667 | +7.7% ✅ |

### skillgenbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 2.9 | 0.59 | -79.7% ✅ |
| api_requests | 28 | 3 | -89.3% ✅ |
| tool_calls | 27 | 2 | -92.6% ✅ |
| total_tokens | 3094974 | 321346 | -89.6% ✅ |
| billable_tokens | 192976 | 77163 | -60.0% ✅ |
| estimated_usd | 1.8647 | 0.4042 | -78.3% ✅ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 3.333 | -33.3% ⚠️ |

### snipevalbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.18 | 0.21 | +16.7% ⚠️ |
| api_requests | 3 | 2 | -33.3% ✅ |
| tool_calls | 2 | 1 | -50.0% ✅ |
| total_tokens | 240516 | 158130 | -34.3% ✅ |
| billable_tokens | 42596 | 38606 | -9.4% ✅ |
| estimated_usd | 0.2172 | 0.1855 | -14.6% ✅ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### verifybig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.35 | 0.31 | -11.4% ✅ |
| api_requests | 7 | 5 | -28.6% ✅ |
| tool_calls | 7 | 5 | -28.6% ✅ |
| total_tokens | 669747 | 481088 | -28.2% ✅ |
| billable_tokens | 77647 | 82973 | +6.9% ⚠️ |
| estimated_usd | 0.4749 | 0.4326 | -8.9% ✅ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

### visdiffbig

| metric | without | with | Δ% |
| --- | --- | --- | --- |
| wall_clock_min | 0.2 | 0.27 | +35.0% ⚠️ |
| api_requests | 3 | 3 | +0.0% |
| tool_calls | 3 | 4 | +33.3% ⚠️ |
| total_tokens | 238367 | 405509 | +70.1% ⚠️ |
| billable_tokens | 47719 | 117906 | +147.1% ⚠️ |
| estimated_usd | 0.2373 | 0.5473 | +130.6% ⚠️ |
| groundwork_invocations | 0 | 0 | n/a |
| check_pass | 1.0 | 1.0 | +0.0% |
| check_accuracy | 1.0 | 1.0 | +0.0% |
| rubric_mean | 5 | 5 | +0.0% |

## Reading this

- **total_tokens / estimated_usd** — cost. Token counts are exact; $ uses `eval/pricing.json` (edit to your rates).
- **wall_clock_min / api_requests / tool_calls** — speed & effort.
- **check_pass / check_accuracy** — automated correctness (0–1).
- **rubric_mean** — human/LLM 1–5 quality (blank until scored).
- **groundwork_invocations** — sanity check that the *with* arm actually used the tools (should be >0 with, 0 without).