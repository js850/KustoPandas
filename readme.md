KustoPandas is a wrapper around a Pandas DataFrame which allows you to use the syntax of the 
[Kusto Query Language](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/query/) to transform the data frame.  Under the hood the commands are converted to the corresponding Pandas method, so you get all the performance of Pandas, but with the nice syntax of Kusto.

See the following jupyter notebooks for example usage

[KustoPandas walkthrough](https://github.com/js850/KustoPandas/blob/master/examples/kusto_pandas_walkthrough.ipynb)

[Trump approval ratings](https://github.com/js850/KustoPandas/blob/master/examples/trump_approval_ratings.ipynb)


Here is a very basic example usage, but please see the above notebooks for more details.

```python
import pandas as pd
from KustoPandas import Wrap
dataframe = pd.read_csv("data.csv")
w = Wrap(dataframe)

w.where("Column1 > 0").summarize("count(), AvgOfCol1 = avg(Column1) by Column2")

```

(This package is still a work in progress.  Some kusto commands are not yet mapped to the corresponding Pandas command.  I will add more and more functionality as time goes on.  Please feel free to contribute.)
