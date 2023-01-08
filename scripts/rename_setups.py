# %%
from pathlib import Path
# %%
fs = Path('docs/setups').iterdir()
fs
# %%
fs = list(fs)
fs
# %%
for f in fs:
    newf = f.with_name(f.name.removeprefix("setup_"))
    newf.write_text(f.read_text())
# %%
