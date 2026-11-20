# Hamilton

[`dotdoc.hamilton`](api.md#dotdoc.hamilton) styles drawings of [Apache Hamilton](https://hamilton.apache.org/) DAGs, linking each node to the documentation of the function that defines it.
It needs the `hamilton` extra:

=== "uv"

    ```sh
    uv add "dotdoc[hamilton]"
    ```

=== "pip"

    ```sh
    pip install "dotdoc[hamilton]"
    ```

The drawing below is of a Hamilton dataflow that draws a Hamilton DAG with dotdoc, made by running it on itself when the documentation was built.
Each step is named after the function it calls, and its name links to that function's API entry, through the `link` argument of [`link_style`][dotdoc.hamilton.link_style].
Hover over a name to preview the entry.

??? example "The dataflow, `examples/draw_dag.py`"

    ```python exec="on" result="python"
    print(open("examples/draw_dag.py").read())
    ```

```python exec="on" html="1" source="tabbed-right" result="html"
import sys  # markdown-exec: hide

sys.path.insert(0, "examples")  # markdown-exec: hide
import draw_dag
from hamilton import driver

dr = driver.Builder().with_modules(draw_dag).build()
result = dr.execute(
    ["graph_html"],
    inputs={
        "dr": dr,
        "tag": "stage",
        "colours": {
            "styling": "#e7eef7",
            "rendering": "#fde9c4",
            "output": "#d9ead3",
        },
    },
)

print(result["graph_html"])
```
