from pathlib import Path
from typing import Any

from docutils import nodes
from docutils.parsers.rst import Directive, directives  # type:ignore
from jinja2 import Template
from sphinx.application import Sphinx


from .. import _utils

STLITE_VERSION = "0.73.0"

page_template = Template((Path(__file__).parent / "page.html.jinja").read_text())
view_template = Template("""
  <div id="{{ id }}__div" style="position: relative;">
    <iframe id="{{ id }}__iframe" src="{{ url }}" frameborder="0"></iframe>
  </div>
  <script>
    const iframe = document.getElementById('{{ id }}__iframe');
    const div = document.getElementById('{{ id }}__div');
    iframe.style.width = `${div.scrollWidth}px`;
    window.addEventListener("message", (event, origin) => {
      const url = new URL('{{ url }}', location);
      if (event.source.location.toString() !== url.toString()) {
        return;
      }
      const { height } = event.data;
      if (height) {
        div.style.height = `${height}px`;
        iframe.style.height = `${height}px`;
      }
    });
  </script>
""")


class stlite(nodes.Element, nodes.General):
    pass


def visit_stlite(self, node: stlite):
    """Inject br tag (html only)."""
    app: Sphinx = self.builder.app
    widget_uri = f"_widgets/{node['id']}"
    out = app.outdir / widget_uri / "index.html"
    print(node.document)
    docname = app.env.path2doc(node.document["source"])
    widget_url = app.builder.get_relative_uri(docname, widget_uri)
    out.parent.mkdir(exist_ok=True, parents=True)
    out.write_text(page_template.render(node.attributes))
    self.body.append(view_template.render(node.attributes, url=widget_url))


class Stlite(Directive):
    option_spec = {
        "id": directives.unchanged,
        "requirements": directives.unchanged,
    }
    has_content = True

    def run(self):
        node = stlite()
        node.attributes = self.options
        node.attributes["requirements"] = [
            f'"{r}"' for r in self.options["requirements"].split(",")
        ]
        node.attributes["code"] = "\n".join(self.content)
        return [
            node,
        ]


def inject_stlite_assets(
    app: Sphinx,
    pagename: str,
    templatename: str,
    context: dict[str, Any],
    doctree: nodes.document | None = None,
):
    if not doctree:
        return
    if not doctree.findall(stlite):
        return

    context["script_files"].append(
        f"https://cdn.jsdelivr.net/npm/@stlite/mountable@{STLITE_VERSION}/build/stlite.js"
    )
    context["css_files"].append(
        f"https://cdn.jsdelivr.net/npm/@stlite/mountable@{STLITE_VERSION}/build/stlite.css"
    )


def setup(app: Sphinx):
    app.add_node(stlite, html=(visit_stlite, _utils.skip_departing))
    app.add_directive("stlite", Stlite)
    app.connect("html-page-context", inject_stlite_assets)
    return {}
