KustoPandas is a wrapper around a Pandas DataFrame which allows you to use the syntax of the 
[Kusto Query Language](https://docs.microsoft.com/en-us/azure/data-explorer/kusto/query/) to transform the data frame.  Under the hood the commands are transformed in the corresponding Pandas method, so you get all the performance of Pandas, but with the nice syntax of Kusto.

See the following jupyter notebook for example usage
[Trump approval ratings](https://github.com/js850/KustoPandas/blob/master/examples/trump_approval_ratings.ipynb)

(This package is still a work in progress.  Many kusto commands are not yet mapped to the corresponding Pandas command.  I will add more and more functionality as time goes on.  Please feel free to contribute.)





