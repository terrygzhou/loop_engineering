# `main.py`

## Purpose
CLI entry point for the Loop Engineering workflow engine. Parses command-line arguments, collects the project name, spec text, and optional codebase context from the user (interactively or via flags), then delegates to `WorkflowRunner.run_interactive` from the shared executor module. This design ensures CLI and Web UI run identical workflow logic — only the UX layer differs.

## Public API

### Functions

#### `parse_args() -> argparse.Namespace`
- **Parameters**: None
- **Returns**: `argparse.Namespace` — Object containing `project`, `spec`, `context`, and `auto_approve` attributes parsed from `sys.argv`.
- **Behavior**: Defines an `ArgumentParser` with four flags: `--project` (str, default ""), `--spec` (str, default ""), `--context` (str, default ""), and `--auto-approve` (store_true). Reads `sys.argv` and returns the parsed namespace.

#### `main() -> None`
- **Parameters**: None
- **Returns**: Nothing
- **Behavior**: Prints the CLI banner, calls `parse_args()`, interactively collects missing inputs (project name, spec text, context path) via `input()` when not supplied on the command line, instantiates `WorkflowRunner`, and calls `run_interactive()` with the gathered parameters. Prints a summary of the cycle result including cycle ID, phase, project name, error (if any), and feedback entry count. Exits with `sys.exit(1)` if the project name is empty.

### Module-Level Variables
- `argparse` (module): Standard library argument parsing.
- `sys` (module): Standard library system interface.
- `WorkflowRunner` (class): Imported from `graph.executor`; the shared workflow runner used by both CLI and Web UI.

---

## Dependencies / Used By
- **Imports**: `argparse`, `sys`, `graph.executor.WorkflowRunner`
- **Used By**: Terminal invocations (`python main.py ...`), Docker entrypoints

## Notes / Caveats
- When `--auto-approve` is passed, all HIL (Human-in-the-Loop) gates are skipped, making the workflow fully headless/CI-compatible.
- The `--context` flag enables "brownfield" mode where an existing codebase is scanned in the DISCOVER phase. Omitting it defaults to "greenfield" mode.
- The top-level `if __name__ == "__main__"` block catches `KeyboardInterrupt` (exit code 1) and generic `Exception` (exit code 2 with traceback), providing user-friendly error messages.
