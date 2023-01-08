# %%
from pathlib import Path
from nbconvert import MarkdownExporter
from traitlets.config import Config
from nbconvert.preprocessors import TagRemovePreprocessor, ConvertFiguresPreprocessor

# Setup config
c = Config()

# Configure tag removal - be sure to tag your cells to remove  using the
# words remove_cell to remove cells. You can also modify the code to use
# a different tag word
c.TagRemovePreprocessor.remove_cell_tags = ("remove_cell",)
c.TagRemovePreprocessor.remove_all_outputs_tags = ('remove_output',)
c.TagRemovePreprocessor.remove_input_tags = ('remove_input',)
c.TagRemovePreprocessor.enabled = True


class PNGToB64Converter(ConvertFiguresPreprocessor):
    from_format = "image/png"
    to_format = "text/html"

    def convert_figure(self, data_format: str, data: str):
        return f"![Cell Output](data:image/png;base64,{data})"


md_exporter = MarkdownExporter(config=c)
md_exporter.register_preprocessor(TagRemovePreprocessor(config=c),True)
md_exporter.register_preprocessor(PNGToB64Converter(),True)

blog_dir = Path('docs/blog')

fs = Path('docs/notebooks').glob('*.ipynb')
fs = list(fs)
fs
# %%
for f in fs:
    body, resources = md_exporter.from_file(f)
    newf = blog_dir / f"{f.stem}.md"
    newf.write_text(body)
    print(str(newf))
# %%