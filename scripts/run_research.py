"""CLI research tool."""
import argparse
import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from backend.api.app import workflow

def main():
    parser = argparse.ArgumentParser(description="Autonomous Multi-Agent Research CLI")
    parser.add_argument("--topic", type=str, required=True, help="Research topic or query")
    parser.add_argument("--scope", type=str, default="comprehensive", help="Research scope")
    parser.add_argument("--max-iters", type=int, default=2, help="Max revision loops")
    args = parser.parse_args()

    print(f"\n🧠 Initiating multi-agent research on: {args.topic}\n")

    def progress(agent: str, msg: str):
        print(f"[{agent.upper()}]: {msg}")

    state = workflow.run_sync(
        topic=args.topic,
        scope=args.scope,
        max_iterations=args.max_iters,
        progress_callback=progress,
    )

    draft = state.get("draft_report")
    critic = state.get("critic_feedback")

    if draft:
        print("\n" + "=" * 60)
        print(draft.body_markdown)
        print("=" * 60)
        score = critic.quality_score if critic else 0.0
        print(f"\n✅ Completed! Final Quality Score: {score:.1f}/10\n")

if __name__ == "__main__":
    main()
