"""Generate lightweight Claude entrypoints from the canonical skill pack."""
import argparse
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    different = []
    for source in sorted((root / ".agents/skills").glob("cv-*/SKILL.md")):
        name = source.parent.name
        header = source.read_text(encoding="utf-8").split("---", 2)[1].strip()
        expected = f"---\n{header}\n---\n\nRead [the canonical skill](../../../.agents/skills/{name}/SKILL.md) and follow it. Supporting instructions live in that canonical skill so all harnesses use the same workflow.\n"
        destination = root / ".claude/skills" / name / "SKILL.md"
        if not destination.exists() or destination.read_text(encoding="utf-8") != expected:
            different.append(name)
            if not args.check:
                destination.parent.mkdir(parents=True, exist_ok=True)
                destination.write_text(expected, encoding="utf-8")
    if args.check and different:
        raise SystemExit("Run python scripts/sync_skills.py: " + ", ".join(different))
    print("Skill entrypoints are synchronized.")


if __name__ == "__main__":
    main()
