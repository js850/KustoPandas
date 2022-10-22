import pandas as pd

from IPython.core.magic import register_line_cell_magic, needs_local_scope

from kusto_pandas import Wrap

def _is_table(t):
    return isinstance(t, pd.DataFrame) or isinstance(t, Wrap)

def _get_tables(namespace):
    if namespace is None:
        return dict()
    return dict((k, v) for k, v in namespace.items() if _is_table(v))
    
@register_line_cell_magic
@needs_local_scope
def kusto(line, cell=None, local_ns=None):
    """
    This enalbes IPython magics

    Cell magic:  The rest of the cell will be interpreted as a kusto command

    `import Kusto.magic`

    ```
    %kusto
    w
    | where A > 1
    | take 10
    ```

    w must be a variable in the local namespace

    line magic: The rest of the line will be interpreted as a Kusto command

    ```
    %kusto w | where A > 1 | take 10
    ```

    With line magic you can capture the output in a new variable

    ```
    wnew = %kusto w | where A > 1 | take 10
    print(wnew)
    ```
    
    """

    local_tables = _get_tables(local_ns)
    
    cell = cell or ""
    kusto_query = line + " " + cell
    
    wnew = Wrap(pd.DataFrame())
    wnew = wnew.let(**local_tables)
    wnew = wnew.execute(kusto_query)
    return wnew