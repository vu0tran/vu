# Do models write correct Vu?

100 programming tasks, each asked of a model in Vu, Rust, Go and Python, and judged by the same tests.

- **The tasks** (`tasks.py`): programs that read standard input and write standard output: text
  processing, number crunching, parsing, data structures and graph algorithms, formats (JSON, CSV,
  INI, dates), simulations, big-number arithmetic. Each has a prompt, a few edge-case inputs, a
  generator of random inputs, and a Python reference that gives the right output. Every task has
  about six tests (624 in all), and `run.py --self-test` checks that the reference passes them all.
- **The run** (`run.py`): for each model, language and task, the model writes the whole program. It's
  built (`vu build`, `rustc -O`, `go build`, `python3`) and run on every test. If it doesn't build, or
  a test fails, the model sees the compiler's errors or the failing input with the expected and
  actual output, and tries again, up to 3 attempts. For Vu the system prompt carries `llms.txt`, the
  language in brief (models have seen little Vu, and a user would hand them that page); the other
  languages get no documentation.
- **The measures** (`report.py`): how often the first program compiles, how often it passes every
  test first time, how often it passes within 3 attempts, and the median output tokens of a passing
  program. Every request, reply, build error and test failure is kept in `results/`, so each number
  can be traced.

```
export ANTHROPIC_API_KEY=... OPENAI_API_KEY=...
python3 eval/run.py --self-test
python3 eval/run.py --model anthropic:claude-sonnet-5-5 --model openai:gpt-5 --jobs 8
python3 eval/report.py --markdown
```

Needs `rustc`, `go` and the Vu compiler (`./vu`). 100 tasks times 4 languages is 400 programs per
model, up to 1,200 requests with retries.

## Limits, said up front

- The tasks are small (10 to 80 lines in Python). They test whether a model can write correct
  everyday code in Vu, not large systems.
- They were written by the same AI that wrote most of Vu. The tests are mechanical (outputs compared
  byte for byte against a reference that passes them), but the choice of tasks isn't neutral; anyone
  can add tasks to `tasks.py`.
- Vu gets a page of documentation in the prompt; the others don't need one. That's the honest setting
  for a new language, and the report should say so beside the numbers.
- No results are published here yet: running it needs API keys.
