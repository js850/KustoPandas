KustoPandas is a wrapper around a Pandas DataFrame which allows you to use the syntax of the 
[Kusto Query Language](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/query/) to transform the data frame.  Under the hood the commands are converted to the corresponding Pandas method, so you get all the performance of Pandas, but with the nice syntax of Kusto.

For installation use pip

```python
python -m pip install kusto_pandas
```

See the following jupyter notebooks for example usage

[KustoPandas walkthrough](https://github.com/js850/KustoPandas/blob/master/examples/kusto_pandas_walkthrough.ipynb)

[Trump approval ratings](https://github.com/js850/KustoPandas/blob/master/examples/trump_approval_ratings.ipynb)


Here are some very basic usage examples.  Please see the walkthrough above for more details.

```python
import pandas as pd
from kusto_pandas import Wrap
dataframe = pd.read_csv("data.csv")
w = Wrap(dataframe)

w.where("Column1 > 0").summarize("count(), AvgOfCol1 = avg(Column1) by Column2")

```

In the above, multiple tabular operators are chained together, however if you prefer you can enter the full Kusto query 

```python
w.execute("""
w
| where Column1 > 0
| summarize count(), AvgOfCol1 = avg(Column1) by Column2
""")
```

If you are working in a Jupyter notebook, then you may find it more convenient to use an IPython magic

![Kusto magic impage](https://github.com/js850/KustoPandas/raw/master/KustoMagic.png)


