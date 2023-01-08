# %%
from pathlib import Path
NAV_KEY = "# NAV"

def sorted_files(section_slug: str):
    f = [x for x in Path(f"docs/{section_slug}").iterdir() if 'index' != x.stem]
    return sorted(f)

def section_nav(section: str) -> list[str]:
    section_slug = section.lower()
    lines = [f"  - {section.title()}:", f"    - {section_slug}/index.md"]
    for filename in sorted_files(section_slug):
        title = filename.stem.replace("-", " ").replace("_", " ").title()
        lines.append(f"    - '{title}': {section_slug}/{filename.stem}")
    print('\n'.join(lines))
    return lines
nav_lines = [NAV_KEY, "nav:"]
# %%
for section in ['blog', 'guides', 'resources', 'setups']:
    nav_lines.extend(section_nav(section))
nav_lines
# %%
mkdocs = Path('mkdocs.yml')
original = mkdocs.read_text()
Path('.bak.mkdocs.yml').write_text(original)
# %%
start_nav_index = original.find(NAV_KEY)
updated = original[:start_nav_index] + '\n'.join(nav_lines)
mkdocs.write_text(updated)
# %%
