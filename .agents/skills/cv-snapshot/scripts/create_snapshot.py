"""Create an offline application snapshot using only the existing CV Tailor CLI."""
import argparse
from datetime import date, datetime, timezone
from html import escape
import json
from pathlib import Path
import subprocess
import sys


COLORS = {"Saved": "#8b969a", "Applied": "#5487b5", "Interview": "#3b9a91", "Tech Test": "#a285bd",
          "Offer": "#73934b", "Rejected": "#d88276", "Ghosted": "#b3a69b"}


def cli(directory, *arguments):
    command = [sys.executable, "-m", "cv_tailor", "--json"]
    if directory:
        command += ["--data-dir", str(directory)]
    result = subprocess.run([*command, *arguments], capture_output=True, text=True, encoding="utf-8", timeout=60)
    if result.returncode:
        raise ValueError((result.stdout or result.stderr).strip() or "CV Tailor could not read the workspace.")
    return json.loads(result.stdout)


def flow_svg(snapshot):
    branches = [item for item in snapshot["by_status"] if item["count"]]
    total = snapshot["total"]
    height = max(450, 64 + len(branches) * 52)
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1024 {height + 150}" role="img" aria-labelledby="title desc">',
             '<title id="title">Application flow</title>',
             '<desc id="desc">Each application appears once at its current recorded status. Branch widths represent counts.</desc>',
             f'<rect width="1024" height="{height + 150}" rx="12" fill="white"/>',
             '<g font-family="Arial, sans-serif" fill="#253a43">',
             '<text x="32" y="40" font-size="21" font-weight="600">Application flow</text>',
             f'<text x="32" y="66" font-size="13" fill="#728187">Current recorded statuses · As of {escape(snapshot["as_of"])}</text>',
             '<g transform="translate(32 90)">']
    if total:
        usable = height - 64 - max(0, len(branches) - 1) * 48
        scale = usable / total
        source_top = (height - usable) / 2
        parts += [f'<text x="20" y="{height / 2 - 12}" font-size="15">Applications</text>',
                  f'<text x="20" y="{height / 2 + 31}" font-size="40" font-weight="600">{total}</text>',
                  f'<rect x="168" y="{source_top}" width="10" height="{usable}" rx="2" fill="#a4afb2"/>']
        offset = 0
        for index, branch in enumerate(branches):
            label, count = escape(branch["status"]), branch["count"]
            color = COLORS.get(branch["status"], "#8b969a")
            thickness = count * scale
            y0, y1 = source_top + offset, 32 + offset + index * 48
            path = (f'M178 {y0} C390 {y0} 505 {y1} 706 {y1} L706 {y1 + thickness} '
                    f'C505 {y1 + thickness} 390 {y0 + thickness} 178 {y0 + thickness} Z')
            parts += [f'<path d="{path}" fill="{color}" opacity="0.38"/>',
                      f'<rect x="706" y="{y1}" width="10" height="{thickness}" rx="1" fill="{color}"/>',
                      f'<text x="739" y="{y1 + thickness / 2 - 3}" font-size="16">{label}</text>',
                      f'<text x="739" y="{y1 + thickness / 2 + 20}" font-size="19" fill="{color}">{count}'
                      f'<tspan dx="12" font-size="12" fill="#728187">{count / total:.0%}</tspan></text>']
            offset += thickness
    else:
        parts += ['<text x="480" y="200" text-anchor="middle" font-size="23">No applications in this snapshot.</text>',
                  '<text x="480" y="233" text-anchor="middle" font-size="14" fill="#728187">Add a job to your tracker or include archived applications.</text>']
    scope = "Archived applications included" if snapshot["include_archived"] else f'{snapshot["archived_excluded"]} archived applications excluded'
    parts += ['</g>', f'<text x="32" y="{height + 126}" font-size="12" fill="#728187">{scope} · Snapshot of current statuses; past transitions are not recorded.</text>', '</g></svg>']
    return "\n".join(parts)


def report_html(snapshot, svg):
    def counts(items):
        return "".join(f'<div><dt>{escape(str(label))}</dt><dd>{value}</dd></div>' for label, value in items)

    workspace = snapshot["workspace"]
    summary = counts((("Tracked applications", snapshot["total"]), ("Awaiting response", snapshot["awaiting_response"]),
                      ("Interview / tech test", snapshot["interviewing"]), ("Offers", snapshot["offers"])))
    inventory = counts((("Applications", workspace["applications"]), ("Archived", workspace["archived_applications"]),
                        ("Conversations", workspace["conversations"]), ("Saved drafts", workspace["drafts"])))
    rows = "".join(f'<tr><td>{escape(item["status"])}</td><td>{item["count"]}</td></tr>' for item in snapshot["by_status"])
    sources = "".join(f'<tr><td>{escape(item["source"])}</td><td>{item["count"]}</td></tr>' for item in snapshot["by_source"])
    return f'''<!doctype html>
<html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Application snapshot · {escape(snapshot["as_of"])}</title>
<style>
*{{box-sizing:border-box}}body{{margin:0;background:#f3f5f2;color:#253a43;font:15px/1.6 Arial,sans-serif}}main{{max-width:1120px;margin:auto;padding:32px 24px}}h1{{font-size:32px;letter-spacing:-1px;margin:8px 0}}h2{{font-size:17px}}p,dt{{color:#728187}}.eyebrow{{font-size:11px;letter-spacing:2px;color:#638176}}.metrics{{display:grid;grid-template-columns:repeat(4,1fr);gap:20px;border-block:1px solid #dce3df;padding:20px 0}}dt{{font-size:12px}}dd{{margin:4px 0;font-size:28px;font-weight:600}}.chart,section{{margin:24px 0;background:white;border:1px solid #dce3df;border-radius:12px;overflow:hidden}}.chart svg{{display:block;width:100%;min-width:650px}}.chart{{overflow-x:auto}}section{{padding:20px 24px}}.columns{{display:grid;grid-template-columns:1fr 1fr;gap:24px}}.columns section{{margin-top:0}}table{{width:100%;border-collapse:collapse;font-size:13px}}td,th{{padding:8px 0;border-bottom:1px solid #edf0ed;text-align:left}}td:last-child,th:last-child{{text-align:right}}a{{color:#41756a}}@media(max-width:600px){{main{{padding:20px 14px}}.metrics{{grid-template-columns:1fr 1fr}}.columns{{display:block}}}}
</style><main>
<header><p class="eyebrow">APPLICATION SNAPSHOT</p><h1>Where things stand.</h1><p>As of {escape(snapshot["as_of"])} · Current application statuses from your local tracker.</p></header>
<dl class="metrics">{summary}</dl><div class="chart">{svg}</div>
<div class="columns"><section><h2>Current statuses</h2><table><thead><tr><th>Status</th><th>Applications</th></tr></thead><tbody>{rows}</tbody></table></section>
<section><h2>Where your jobs came from</h2><table><thead><tr><th>Source</th><th>Applications</th></tr></thead><tbody>{sources or '<tr><td>No sources recorded</td><td>0</td></tr>'}</tbody></table></section></div>
<section><h2>Inside your local workspace</h2><p>All saved records, including archived applications and earlier draft versions.</p><dl class="metrics">{inventory}</dl></section>
<p>This is a saved snapshot. Regenerate it to reflect later changes. The as-of date does not reconstruct historical statuses.</p>
<p><a href="application-flow.svg">SVG chart</a> · <a href="snapshot.json">Source data (JSON)</a></p>
</main></html>'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", type=Path)
    parser.add_argument("--output-dir", type=Path)
    parser.add_argument("--as-of", type=date.fromisoformat, default=date.today())
    parser.add_argument("--include-archived", action="store_true")
    args = parser.parse_args()
    try:
        status = cli(args.data_dir, "status")
        if not status["initialized"]:
            raise ValueError("Workspace is not initialized. Select the existing --data-dir or set up CV Tailor first.")
        directory = Path(status["data_dir"])
        command = ["applications", "insights", "--as-of", args.as_of.isoformat()]
        if args.include_archived:
            command.append("--include-archived")
        snapshot = cli(directory, *command)
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        output = (args.output_dir or directory / "snapshots" / timestamp).expanduser().resolve()
        contents = {"application-flow.svg": flow_svg(snapshot), "snapshot.json": json.dumps(snapshot, ensure_ascii=False, indent=2)}
        contents["snapshot.html"] = report_html(snapshot, contents["application-flow.svg"])
        if any((output / name).exists() for name in contents):
            raise ValueError("Snapshot files already exist here. Choose a new --output-dir to preserve earlier snapshots.")
        output.mkdir(parents=True, exist_ok=True)
        for name, content in contents.items():
            (output / name).write_text(content, encoding="utf-8")
        print(json.dumps({"as_of": snapshot["as_of"], "total": snapshot["total"],
                          "include_archived": snapshot["include_archived"], "archived_excluded": snapshot["archived_excluded"],
                          "files": {name: str(output / name) for name in contents}}, ensure_ascii=True))
        return 0
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=True), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
