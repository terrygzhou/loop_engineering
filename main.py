"""
Loop Engineering CLI entry point.

Delegates to the shared executor so CLI and Web UI run identical workflow logic.
Usage:
    python main.py                      # interactive mode (asks for project name + spec)
    python main.py --project NAME       # auto-approve with given project name
    python main.py --project NAME --spec "text"  # with inline spec
    python main.py --project NAME --context /path  # scan existing codebase
"""
import argparse
import sys

from graph.executor import WorkflowRunner


def parse_args():
    parser = argparse.ArgumentParser(description="Loop Engineering CLI")
    parser.add_argument("--project", type=str, default="", help="Project name")
    parser.add_argument("--spec", type=str, default="", help="Initial spec/idea text")
    parser.add_argument("--context", type=str, default="", help="Path to existing codebase for discovery")
    parser.add_argument("--auto-approve", action="store_true", help="Skip all HIL gates")
    return parser.parse_args()


def main():
    print("=== Loop Engineering — CLI ===")
    args = parse_args()

    if not args.project:
        name = input("Project name: ").strip()
    else:
        name = args.project

    if not name:
        print("✗ Project name is required. Use --project NAME or answer the prompt.")
        sys.exit(1)

    spec = args.spec
    if not spec:
        spec = input("Brief description (or Enter to skip): ").strip()

    context = args.context
    if not context and not args.auto_approve:
        context = input("Existing codebase path for discovery (or Enter for greenfield): ").strip()

    runner = WorkflowRunner()
    result = runner.run_interactive(
        project_name=name,
        spec_text=spec,
        context_folder=context,
        auto_approve=args.auto_approve,
    )

    print(f"\n=== Cycle {result.get('cycle_id', '?')} complete ===")
    print(f"Phase: {result.get('phase')}")
    print(f"Project: {result.get('artifacts', {}).get('project_name', 'unknown')}")
    if result.get("error"):
        print(f"Error: {result['error']}")
    print(f"Feedback entries: {len(result.get('feedback', []))}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n⚠ Interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Workflow failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(2)
