"""Builds the site's pages from the Markdown files in src/.

Run `python3 build.py` after editing a file in src/, then commit both.
Handles only what the pages use: headings, paragraphs, lists, rules,
bold, links and <autolinks>.
"""
import html
import pathlib
import re

ROOT = pathlib.Path(__file__).resolve().parent
PAGES = {
    "PRIVACY_POLICY.md": ("privacy", "Privacy Policy"),
    "TERMS_OF_USE.md": ("terms", "Terms of Use"),
    "SUPPORT.md": ("support", "Support"),
    "DATA.md": ("data", "Open Data"),
}


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", r'<a href="\2">\1</a>', text)

    def autolink(match):
        target = match.group(1)
        href = target if target.startswith("http") else "mailto:" + target
        return f'<a href="{href}">{target}</a>'

    return re.sub(r"&lt;((?:https?://|[\w.+-]+@)[^&\s]+)&gt;", autolink, text)


def render(markdown):
    out, paragraph, items = [], [], []

    def flush():
        if paragraph:
            out.append(f"<p>{inline(' '.join(paragraph))}</p>")
            paragraph.clear()
        if items:
            out.append("<ul>" + "".join(f"<li>{inline(i)}</li>" for i in items) + "</ul>")
            items.clear()

    for line in markdown.splitlines():
        stripped = line.strip()
        heading = re.match(r"(#{1,3}) (.+)", stripped)
        if not stripped:
            flush()
        elif heading:
            flush()
            level = len(heading.group(1))
            out.append(f"<h{level}>{inline(heading.group(2))}</h{level}>")
        elif stripped == "---":
            flush()
            out.append("<hr>")
        elif stripped.startswith("- "):
            if paragraph:
                flush()
            items.append(stripped[2:])
        elif items and line.startswith("  "):
            items[-1] += " " + stripped
        else:
            paragraph.append(stripped)
    flush()
    return "\n".join(out)


def page(title, body):
    template = (ROOT / "template.html").read_text()
    return template.replace("{{title}}", html.escape(title)).replace("{{body}}", body)


def build():
    for source, (folder, title) in PAGES.items():
        body = render((ROOT / "src" / source).read_text())
        target = ROOT / folder / "index.html"
        target.parent.mkdir(exist_ok=True)
        target.write_text(page(f"{title} — Sadeem", body))
        print("built", target.relative_to(ROOT))


if __name__ == "__main__":
    build()
