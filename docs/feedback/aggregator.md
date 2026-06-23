# `feedback/aggregator.py`

## Purpose
The FeedbackAggregator collects and persists metrics, artifacts, and feedback from each phase execution across development cycles. It stores records as JSON files under `./storage/cycles/`, enabling historical analysis and pattern detection. Serves as the data foundation for the **REFLECT** node to analyze trends, identify recurring issues, and drive configuration adjustments between cycles.

## Public API

### Classes

#### `FeedbackAggregator`
- **Description**: Collects and stores feedback from workflow cycles. Creates a `storage_dir/cycles/` directory on initialization, where each cycle is stored as a JSON file named `{cycle_id}.json`.

##### `__init__(self, storage_dir: str = "./storage")`
- **Description**: Initializes the aggregator, creating the storage directory and cycles subdirectory if they don't exist.
- **Parameters**:
  - `storage_dir` (`str`, default: `"./storage"`): Base directory for all feedback storage.
- **Returns**: Nothing.
- **Side Effects**: Creates directories via `Path.mkdir(parents=True, exist_ok=True)`.

##### `record_cycle(self, cycle_id: str, phase: str, metrics: dict, artifacts: dict, feedback: list) -> dict`
- **Description**: Records a phase execution within a cycle. Truncates artifact values to 500 characters for storage efficiency. If a file for `cycle_id` already exists, appends to the existing list of records (allowing multiple phases per cycle). Returns the created record.
- **Parameters**:
  - `cycle_id` (`str`): Unique identifier for the development cycle (e.g., `"cycle-1"`, `"cycle-2"`).
  - `phase` (`str`): Phase name (e.g., `"DISCOVER"`, `"BUILD"`, `"VERIFY"`).
  - `metrics` (`dict`): Key-value metrics from the phase execution (e.g., spec confidence, review revisions, security findings).
  - `artifacts` (`dict`): Phase output artifacts (strings), truncated to 500 chars each.
  - `feedback` (`list`): List of feedback strings from the phase.
- **Returns**: `dict` — The cycle record dictionary (with truncated artifacts).
- **Side Effects**: Writes/appends to `{storage_dir}/cycles/{cycle_id}.json`.

##### `get_cycle(self, cycle_id: str) -> list`
- **Description**: Retrieves all records for a given cycle ID.
- **Parameters**:
  - `cycle_id` (`str`): Cycle identifier.
- **Returns**: `list` — List of record dictionaries for the cycle, or empty list if not found.
- **Side Effects**: Reads JSON file from disk.

##### `list_cycles(self) -> list`
- **Description**: Lists all completed cycle IDs by scanning the cycles directory for JSON files. Returns IDs sorted alphabetically.
- **Parameters**: None.
- **Returns**: `list` of `str` — Sorted list of cycle ID strings (file stems without `.json` extension).
- **Side Effects**: Scans directory via `Path.glob("*.json")`.

##### `get_historical_patterns(self, metric_name: str, threshold: float) -> list`
- **Description**: Scans all cycle files to find historical records where a specific metric exceeded a threshold. Useful for identifying recurring problem patterns (e.g., cycles where `spec_confidence` dropped below 0.5).
- **Parameters**:
  - `metric_name` (`str`): Name of the metric key to check within each record's `metrics` dict.
  - `threshold` (`float`): Threshold value; records are included where `metrics[metric_name] > threshold`.
- **Returns**: `list` of `dict` — Matching record dictionaries from all cycles.
- **Side Effects**: Reads all JSON files in the cycles directory.

### Module-Level Variables
- None (all state is encapsulated within the `FeedbackAggregator` class).

---

## Dependencies / Used By
- **Imports**: `json`, `os`, `datetime.datetime`, `pathlib.Path`.
- **Used By**: `graph/nodes/reflect.py` (creates an instance, records cycle records during the REFLECT phase).

## Notes / Caveats
- Artifact truncation to 500 characters is a hard limit applied in `record_cycle`. This prevents storage bloat but may truncate important diagnostic information.
- Multiple phases can be recorded for the same `cycle_id` by appending to the same JSON file. The file format is a list of record dicts.
- `get_historical_patterns` uses `>` (strictly greater than) for threshold comparison. For "below threshold" queries, pass a negative threshold or use a different comparison strategy.
- No locking or concurrency controls; simultaneous writes to the same cycle file may corrupt data in multi-threaded scenarios.
- Storage is purely local file-based; no database or remote persistence. For long-term retention across containers, mount the storage directory as a volume.
