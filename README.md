## Prerequisites: 
- git
- docker ([docker install](https://docs.docker.com/desktop/setup/install/windows-install/))

## Steps to run the application:
1. Clone the project into a directory by using the command: `git clone https://github.com/MagnusBane05/bloodontheclocktowersolver.git`
2. Navigate to the project directory: `cd bloodontheclocktowersolver`
3. Make sure Docker Desktop is running on your machine
4. Run the project with the command: `docker compose up --build`
5. Navigate to `http://localhost` in your browser

## Steps to run development application:
1. Navigate to frontend `cd fronend` and start application `npm run dev`
2. Create venv if not present `python -m venv` and activate venv `source .venv/bin/activate`
3. Install dependencies `pip install -r backend_requirements.txt`
4. Run app `python app.py`

## Running tests
1. `cd bloodontheclocktowersolver`
2. `unittest-parallel -t . -s tests`
3. To test memory usage: `/usr/bin/time -v python -m unittest tests.testCreatorWithSimulator.TestCreatorWithSimulator.test_5_player`
4. To profile: see [Profiling](#profiling) below

## Benchmarking workflow
`python -m bench run --tier smoke --label "..."`      # after a change
`python -m bench compare`                             # vs. baseline
`python -m bench compare --game 10p-0003`             # drill into one game
`python -m bench worlds`                              # when final world counts changed
`python -m bench baseline`                            # when a change is accepted

## Benchmarking
Commit the code before running a benchmark you want to keep; runs from a working tree with uncommitted changes are marked as `dirty` in the results.
Run these from the project root with the venv active. 

Quick check after a change (~10 seconds):
`python -m bench run --tier smoke --label "Describe the change"`

Before committing a performance change (~5 minutes):
`python -m bench run --tier standard --label "Describe the change"`

Occasional full run (10 player and 15 player games take much longer):
`python -m bench run --tier full --label "Describe the change"`

Compare the latest run against the baseline (exits with an error if any game stopped finishing or lost the true grim):
`python -m bench compare`

Check which final worlds changed against the baseline, and whether any possibly valid worlds were lost (exits with an error if a removed world passes every validator):
`python -m bench worlds`

Make the latest run the new baseline (copied to `bench/baseline.json` and `bench/baseline.worlds/`, which are committed):
`python -m bench baseline`

### Other bench compare options
- `python -m bench compare <A> <B>`: compare any two runs. Each can be a path, `baseline`, `latest`, or part of a run's file name (e.g. `cache-clones`)
- `--game 10p-0003`: step by step world counts and times for one game in both runs
- `--force`: compare runs that use different scenario versions
- `python -m bench baseline <run>`: make a specific run the baseline instead of the latest

### Other bench worlds options
- `python -m bench worlds <A> <B>`: compare the worlds of any two runs, chosen the same way as for `compare`
- `--game 5p-0074`: list every world that differs for one game

Removed worlds are sorted into:
- **dropped poison**: a kept world is the same apart from having no extra poison, so the poison wasn't needed to explain anything. Only counted unless you use `--game`
- **merged**: covered by a more general world
- **invalid**: fails a validator
- **rejected**: finalizing it again finds it impossible, for example a conflict between pages. Listed with the reason
- **refined**: finalizing it again gives a world that was kept, so it's the same world with more detail
- **unexplained**: none of these, so possibly a valid world that was lost. The command exits 1 if there are any

Rejected and refined use the solver's own finalize with the code that's currently checked out, so a bug in it could hide a lost world: check the rejected reasons. Each unexplained world is re-run as if it were the true grim to show the step that drops it, or `not dropped` if a loosely matching world survives every step. Added worlds are sorted into **generalized**, **refined**, **known invalid** and **other**. Merged, refined and generalized worlds are only listed with `--game`.

### Other bench run options
- `--no-csv`: don't append the run to `bench/results.csv`, e.g. while experimenting
- `--players 5 10`: only run some of the tier's player counts
- `--repeat 3`: run each game 3 times and keep the fastest time, to reduce timing noise
- `--timeout 15=3600`: per game timeout in seconds for a player count (defaults: 5=60, 10=300, 15=1800)
- `--memory-gb 16`: memory limit per worker process (default 12). Games that run out are recorded as `oom` and the run continues
- `--asserts`: keep asserts on (benchmarks run with `python -O` by default)
- `--version v2`: use a different scenario version
- `--worlds 5`: player counts whose final worlds are saved for `bench worlds` (default 5 10); `--no-worlds` saves none

### Generating scenarios
The benchmark games are saved in `bench/scenarios/<version>/` so that changes to the simulator can't change the workload. You only need to generate them when creating a new scenario version:
`python -m bench.scenarios generate --version v2`
- Existing files are never overwritten; use a new version, or `--force` to replace them
- `--players 15`: only generate some player counts
- Generate from a committed working tree so the files record which commit produced them
- `tests/test_bench_scenarios.py` fails if the simulator no longer matches the saved `v1` games; that means it's time for a new version, not that `v1` should be overwritten

## Profiling
Profiles the benchmark games with cProfile, so you see the same games the benchmark runs. Each player count runs in its own process with a memory limit, so a game that runs out of memory is recorded as `oom` (with a profile of the part that ran) and the rest still run.

`python -m bench profile --players 5 10 15`           # 100 5p games, 3 10p games, 1 15p game
`python -m bench profile --game 10p-0003`             # one game
`python -m bench profile --game 5p-0074 15p-0001`     # specific games
`python -m bench profile --players 10 --count 20`     # the first 20 10p games
`python -m bench profile --players 5 --games 100-199` # a range of games (or e.g. 1,4,9)
`python -m bench profile --tier smoke`                # the same games as a benchmark tier

Results go to `bench/profiles/<time>_<label>/` (not committed):
- `5p.prof`, `10p.prof`, `15p.prof`: all of a player count's games merged into one profile. Open with `snakeviz bench/profiles/<run>/10p.prof`, or add `--open`
- `summary.txt` (also printed):
  - each game's time under the profiler next to its time in `bench/baseline.json`
  - time and worlds by kind of step (claim, empath, demon kill, death, ...) over all of the games
  - the top functions by own time (`tottime`) and by time including what they call (`cumtime`)
- `meta.json`: every game's status and step by step world counts, times and memory

Times under cProfile are roughly twice the benchmark's, so use `python -m bench run` to measure speed and this to find where the time goes.

### Other bench profile options
- `--label "..."`: name for the output directory
- `--filter grimoire/`: only show functions whose `path:line(name)` matches this regex in the tables, e.g. `validators` or `grimoire_page.py`
- `--top 50`: number of functions in each table (default 30)
- `--sort tottime` or `--sort cumtime`: only show one table
- `--per-game`: also keep each game's own profile in `<players>p_games/`
- `--memory`: also trace memory with tracemalloc. Shows each game's peak memory, the step after which it held the most, and the lines that allocated most of that memory. Makes games about 5 times slower than normal
- `--timeout 15=7200`, `--memory-gb 16`, `--asserts`, `--version v2`: as for `bench run` (timeouts default to twice the benchmark's)
