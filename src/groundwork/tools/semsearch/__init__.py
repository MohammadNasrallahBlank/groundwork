# Benchmark-selected defaults (plan 13 Task 1, 2026-07-08, this machine).
# Fixture: 8 labelled code chunks, 8 conceptual queries. MRR@10 / query latency:
#   BAAI/bge-small-en-v1.5              MRR 1.000   2.0 ms   <- WINNER
#   sentence-transformers/all-MiniLM-L6-v2  MRR 1.000   6.8 ms  (ties, 3x slower)
#   snowflake/snowflake-arctic-embed-xs     MRR 0.938   1.1 ms  (lower quality)
# bge-small wins: perfect ranking and second-fastest. Re-run
# tests/semsearch/test_benchmark.py to reproduce.
#
# _MIN_SCORE is the confidence floor on the index's distance->similarity score
# ((1+cos)/2); tuned in Task 5 against real index queries to separate correct
# answers (sim ~0.80+) from the distractor tail (sim ~0.70).
_DEFAULT_MODEL = "BAAI/bge-small-en-v1.5"
_MIN_SCORE = 0.78
