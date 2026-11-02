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
3. To test memory usage: `/usr/bin/time -v python -m unittest tests.testCreatorWithSimulator.TestCreatorWithSimulator.test_15_player`
4. To profile: `python -m cProfile -o profile10player.prof tests/testCreatorWithSimulator.py`

## Benchmarking workflow
`python -m bench run --tier smoke --label "..."`      # after a change
`python -m bench compare`                             # vs. baseline
`python -m bench compare --game 10p-0003`             # drill into one game
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

Make the latest run the new baseline (copied to `bench/baseline.json`, which is committed):
`python -m bench baseline`

### Other bench compare options
- `python -m bench compare <A> <B>`: compare any two runs. Each can be a path, `baseline`, `latest`, or part of a run's file name (e.g. `cache-clones`)
- `--game 10p-0003`: step by step world counts and times for one game in both runs
- `--force`: compare runs that use different scenario versions
- `python -m bench baseline <run>`: make a specific run the baseline instead of the latest

### Other bench run options
- `--no-csv`: don't append the run to `bench/results.csv`, e.g. while experimenting
- `--players 5 10`: only run some of the tier's player counts
- `--repeat 3`: run each game 3 times and keep the fastest time, to reduce timing noise
- `--timeout 15=3600`: per game timeout in seconds for a player count (defaults: 5=60, 10=300, 15=1800)
- `--memory-gb 16`: memory limit per worker process (default 12). Games that run out are recorded as `oom` and the run continues
- `--asserts`: keep asserts on (benchmarks run with `python -O` by default)
- `--version v2`: use a different scenario version

### Generating scenarios
The benchmark games are saved in `bench/scenarios/<version>/` so that changes to the simulator can't change the workload. You only need to generate them when creating a new scenario version:
`python -m bench.scenarios generate --version v2`
- Existing files are never overwritten; use a new version, or `--force` to replace them
- `--players 15`: only generate some player counts
- Generate from a committed working tree so the files record which commit produced them
- `tests/test_bench_scenarios.py` fails if the simulator no longer matches the saved `v1` games; that means it's time for a new version, not that `v1` should be overwritten
