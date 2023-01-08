# %%
from pathlib import Path

def sorted_files(section_slug: str):
    f = [x for x in Path(f"docs/{section_slug}").iterdir() if 'index' != x.stem]
    return sorted(f)

def file_update(filename: Path):
    original = filename.read_text()
    lines = original.split('\n')
    for i, line in enumerate(lines):
        if "title: " in line:
            line_parts = line.split()
            title = ' '.join(line_parts[1:]).removeprefix('"').removesuffix('"')
        if "---" in line and i >= 1:
            break
    
    if lines[i + 2] == f"# {title}":
        pass
    elif lines[i + 2].startswith("# "):
        lines[i + 2] = f"# {title}"
        filename.write_text('\n'.join(lines))
    else:
        new_lines = lines[:i + 1] + ["", f"# {title}", ""] + lines[i + 1:]
        filename.write_text('\n'.join(new_lines))

def section_update(section: str) -> list[str]:
    section_slug = section.lower()
    for filename in sorted_files(section_slug):
        file_update(filename)
    # print('\n'.join(lines))
    # return lines
# %%
for section in ['blog', 'guides', 'resources', 'setups']:
    section_update(section)
# %%
