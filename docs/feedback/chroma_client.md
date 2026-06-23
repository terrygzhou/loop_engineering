# `feedback/chroma_client.py`

## Purpose
Provides a ChromaDB client wrapper for storing and retrieving pattern embeddings from development cycles. Enables semantic similarity search over historical patterns (metrics, feedback, tags) so the **REFLECT** node can find analogous past situations and propose informed configuration adjustments. Designed with graceful degradation — if ChromaDB is unavailable (not installed or unreachable), all operations return empty/`False` without crashing the engine.

## Public API

### Functions

#### `get_chroma_client(url: str = None)`
- **Description**: Creates and returns a ChromaDB HTTP client. Checks for the `chromadb` library availability, then resolves the connection URL from the `url` parameter or the `CHROMA_URL` environment variable (default: `http://localhost:8000`). Returns `None` if ChromaDB is unavailable or the connection fails.
- **Parameters**:
  - `url` (`str | None`): ChromaDB server URL. If `None`, reads `CHROMA_URL` env var, falling back to `http://localhost:8000`.
- **Returns**: ChromaDB `HttpClient` instance, or `None` on failure.
- **Side Effects**: Prints a warning message if ChromaDB is not installed or connection fails.

#### `init_collections(client)`
- **Description**: Initializes ChromaDB collections for the loop engine. Creates (or retrieves) three collections — `patterns`, `feedback`, and `artifacts` — each configured with cosine similarity for HNSW indexing. Returns a dictionary mapping collection names to collection objects.
- **Parameters**:
  - `client`: ChromaDB client instance (may be `None`).
- **Returns**: `dict` — Mapping of collection name (`str`) to collection object, or empty dict if client is `None`.
- **Side Effects**: Calls `client.get_or_create_collection()` for each collection. Prints warnings on individual failures.

#### `store_pattern(client, pattern_id: str, metrics: dict, feedback: list, tags: list = None) -> bool`
- **Description**: Stores a pattern in the `patterns` ChromaDB collection. Constructs an embedding document from the metrics, feedback, and tags, then adds it to the collection with the provided ID. Returns `True` on success, `False` on failure or if client is `None`.
- **Parameters**:
  - `client`: ChromaDB client instance.
  - `pattern_id` (`str`): Unique identifier for this pattern.
  - `metrics` (`dict`): Metrics dictionary from the cycle (serialized to string for embedding).
  - `feedback` (`list`): Feedback list from the cycle (serialized to string for embedding).
  - `tags` (`list`, optional): Tags for categorization. Defaults to `None`.
- **Returns**: `bool` — `True` on success, `False` on failure.
- **Side Effects**: Writes to ChromaDB. Prints warning on failure.

#### `query_patterns(client, query_metrics: dict, top_k: int = 3) -> list`
- **Description**: Queries ChromaDB for historically similar patterns based on metric similarity. Converts query metrics to text, performs a nearest-neighbor search, and returns results with document content, metadata, and distance scores.
- **Parameters**:
  - `client`: ChromaDB client instance.
  - `query_metrics` (`dict`): Metrics dictionary to search against.
  - `top_k` (`int`, default: `3`): Number of similar patterns to return.
- **Returns**: `list` of `dict` — Each dict has `document` (str), `metadata` (dict), and `distance` (float or `None`). Returns empty list on failure or if client is `None`.
- **Side Effects**: Queries ChromaDB. Prints warning on failure.

### Module-Level Variables
- `_chroma_error` (`str | None`): Stores the import error message if `chromadb` is not available. `None` if import succeeded. Used in warning messages when `get_chroma_client` is called without the library.
- `chromadb` (module or `None`): Reference to the imported `chromadb` module, or `None` if import failed.

---

## Dependencies / Used By
- **Imports**: `os`, `chromadb` (graceful import with fallback).
- **Used By**: `graph/nodes/reflect.py` (calls `get_chroma_client`, `init_collections`, `store_pattern`, `query_patterns` to persist and retrieve patterns for reflection), `graph/nodes/plan.py` (calls `get_chroma_client`, `query_patterns` to find similar past patterns for planning), `graph/nodes/define.py` (calls `get_chroma_client`, `query_patterns` for pattern lookup during specification definition).

## Notes / Caveats
- **Graceful degradation**: Every public function checks for `client is None` and returns a safe default (`None`, `{}`, `False`, `[]`) rather than raising exceptions. This ensures the engine continues to function even without ChromaDB.
- **Embedding strategy**: Patterns are stored as plain text (string concatenation of metrics, feedback, and tags). ChromaDB's built-in embedding model generates the vector embeddings — no external embedding model is required.
- **Distance metric**: Collections use `hnsw:space: cosine` for similarity computation.
- **No deduplication**: `store_pattern` will overwrite an existing pattern if the same `pattern_id` is used (ChromaDB behavior).
- **Connection handling**: `get_chroma_client` parses the URL manually (`url.split("//")[-1].split(":")`) to extract host and port. This is a simple parser that may fail with unusual URL formats.
- **Collection lifecycle**: `init_collections` calls `get_or_create_collection`, so collections persist across client restarts as long as the underlying ChromaDB server persists data.
- The `feedback` and `artifacts` collections are initialized by `init_collections` but not used by any current `store_*` or `query_*` functions — they are placeholders for future expansion.
