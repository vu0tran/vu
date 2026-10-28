# Does a model write correct Vu from the spec?

Ten tasks (`task_*.txt`), each reading standard input; `tasks.py` has a Python reference for each and
makes the test inputs. For each model, one agent wrote all ten in Vu given only `SPEC.md` (`vu/` for
Opus, `vu_sonnet/`, `vu_haiku/`), and another wrote them in Rust (`rs*/`). Neither could run anything:
one attempt per task. `python3 run.py vu rs` builds and tests a pair of folders and prints a table.

Results and what they mean: CHANGELOG.md, round 20. The `results_*.json` files are the runs recorded
there (`_sonnet` and `_haiku` with the compiler of the time, `_after` after the two fixes it led to).

Round 22 ran it again with a revised spec (new agents, same tasks, the same Rust programs): the Vu
programs are in `v2_vu/`, `v2_vu_sonnet/`, `v2_vu_haiku/`, their results in `results_v2_*.json`.
