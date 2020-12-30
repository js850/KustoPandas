import uuid
import pandas as pd
import numpy as np

from . import expression_parser as ep

def _is_groupby(g):
    return isinstance(g, pd.core.groupby.SeriesGroupBy) or isinstance(g, pd.core.groupby.DataFrameGroupBy )

class SimpleAgg:
    """
    An aggregate function needs to define the following methods

    columns_needed => returns list of expression
    
    apply

    """
    def __init__(self, output_column_name, args, all_columns):
        self.args = args
        self.output_column_name = output_column_name

        # Get the definitions of the columns needed for the aggregate.
        # Each entry can be a simple column name, or a more complex expression, e.g. A+B.
        # The expressions will be evaluated before the groupby is done, so the inputs to this aggregate 
        # are the results of the expressions, e.g. A+B
        self.input_column_definitions = self._get_input_column_definitions(all_columns)
        # use a random name for the column to avoid conflicting names from different 
        # aggregate functions operatoring on the same groupby object
        self.input_column_names = [str(uuid.uuid1()) for a in self.input_column_definitions]

    def _get_input_column_definitions(self, all_columns):
        return self.args

    def columns_needed(self):
        return zip(self.input_column_names, self.input_column_definitions)

    def _get_method_name(self):
        return self.__class__.__name__.lower()
    
    def _get_arg_name_or_default(self, arg, default):
        if isinstance(arg, ep.Var):
            return str(arg)
        return default

    def _default_name(self):
        names = [self._get_arg_name_or_default(arg, "") for arg in self.args]
        names = [n for n in names if n != ""]
        suffix = "_".join(names)
        return self._get_method_name() + "_" + suffix

    def _get_output_column_name(self):
        if self.output_column_name:
            return self.output_column_name
        else:
            return self._default_name()
    
    def apply(self, grouped):
        names = self.input_column_names
        if len(names) == 1:
            # operate on a SeriesGroupBy
            grouped = grouped[names[0]]
        elif len(names) > 1:
            # operate on a DataFrameGroupBy
            grouped = grouped[self.input_column_names]
        
        return self.apply1(grouped)

    def apply1(self, grouped):
        output_column_name = self._get_output_column_name()
        
        if _is_groupby(grouped):
            series = self.apply_aggregate(grouped)
        else:
            result = self.apply_aggregate_series(grouped)
            series = pd.Series([result])

        return [(output_column_name, series)]
    
    def apply_aggregate(self, grouped):
        raise NotImplementedError()

    def apply_aggregate_series(self, series):
        # often the same method will work on both a series and a groupby e.g.
        # grouped.max() returns a series with one max value per group
        # series.max() just returns a single value
        return self.apply_aggregate(series)

class NoArgAgg(SimpleAgg):
    def validate(self, df):
        if self.args:
            raise Exception("{0} can't take an arg: {1}".format(self._get_method_name(), str(self.args)))

class AggOneArg(SimpleAgg):
    def validate(self, df):
        if len(self.args) != 1:
            raise Exception("{0} can only take one argument: {1}".format(self._get_method_name(), str(self.args)))

class AggTwoArgs(SimpleAgg):
    def validate(self, df):
        if len(self.args) != 2:
            raise Exception("{0} must have two arguments: {1}".format(self._get_method_name(), str(self.args)))

class Count(NoArgAgg):
    def apply_aggregate(self, grouped):
        return grouped.size()

    def apply_aggregate_series(self, series):
        # this is actually a dataframe
        return series.shape[0]
    
class DCount(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.nunique()

class CountIf(AggOneArg):
    def apply_aggregate(self, grouped):
        # the countif predicate was precomputed into a new column
        # sum returns the number of true values in that column
        return grouped.sum()

class Sum(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.sum()

class Avg(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.mean()

class AvgIf(AggTwoArgs):
    def apply_aggregate(self, grouped):
        series = grouped.apply(self.apply_aggregate_series)
        return series
    
    def apply_aggregate_series(self, df):
        predicate = df[self.input_column_names[1]]
        values = df[self.input_column_names[0]].loc[predicate]
        return values.mean()

class StDev(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.std()

class Variance(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.var()

class Min(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.min()

class Max(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.max()

class ArgMin(AggTwoArgs):
    def apply_aggregate(self, grouped):
        series = grouped.apply(self.apply_aggregate_series)
        return series
    
    def apply_aggregate_series(self, series):
        # find the index of the min of arg0
        idx = series[self.input_column_names[0]].idxmin()
        # return the value of arg1 at that index
        return series[self.input_column_names[1]].loc[idx]

class ArgMax(AggTwoArgs):
    def apply_aggregate(self, grouped):
        series = grouped.apply(self.apply_aggregate_series)
        return series
    
    def apply_aggregate_series(self, series):
        # find the index of the max of arg0
        idx = series[self.input_column_names[0]].idxmax()
        # return the value of arg1 at that index
        return series[self.input_column_names[1]].loc[idx]

def _all_non_null_if_possible_mask(s, mask):
    if mask is None:
        mask = np.ones(len(s), dtype=bool)
    
    old_mask = mask
    mask = mask & (~s.isnull())

    if np.any(mask):
        return mask
    
    return old_mask

def _all_non_null_if_possible(df):
    mask = None
    for c in df.columns:
        mask = _all_non_null_if_possible_mask(df[c], mask)
    return mask

def _any(df, return_df):
    mask = _all_non_null_if_possible(df)
    df = df[mask]
    if return_df:
        # return a dataframe object with only one row
        return df.iloc[0:1]
    else:
        # return a series object where the index is the columns of df
        return df.iloc[0]


class Any(SimpleAgg):
    def validate(self, df):
        pass

    def _get_input_column_definitions(self, all_columns):
        if isinstance(self.args[0], ep.Star):
            # .args is used to generate variable names
            self.orig_args = self.args
            return [ep.Var(c) for c in all_columns]

        return self.args

    def apply(self, df):
        df = df[self.input_column_names]

        if _is_groupby(df):
            def _any2(x):
                return _any(x, False)
            df_nonull = df.apply(_any2)
        else:
            df_nonull = _any(df, True)

        if len(self.input_column_names) == 0:
            output_col_names = [self._get_output_column_name()]
        else:
            output_col_names = []
            prefix = self._get_method_name()
            for arg in self.input_column_definitions:
                suffix = self._get_arg_name_or_default(arg, "")
                col_name = prefix + "_" + suffix
                output_col_names.append(col_name)
        
        result = []
        for output_col_name, c in zip(output_col_names, self.input_column_names):
            result.append((output_col_name, df_nonull[c]))
        return result

class Percentiles(SimpleAgg):
    def validate(self, df):
        if len(self.args) < 2:
            raise Exception("Percentiles requires at least two args: " + str(self.args))

    def _get_input_column_definitions(self, all_columns):
        return self.args[:1]

    def apply1(self, grouped):
        percentiles = [int(a.evaluate(None)) for a in self.args[1:]]
        for p in percentiles:
            if p > 100 or p < 0:
                raise Exception("Percentile must be between 0 and 100")
        
        quantiles = [1.0*p / 100 for p in percentiles]
        
        if self.output_column_name is not None:
            basename = self.output_column_name + "_"
        else:
            basename = self._get_method_name() + "_"
        
        names = [basename + str(p) for p in percentiles]

        result = grouped.quantile(quantiles)

        if _is_groupby(grouped):
            # result is a multi-index.  we need to flatten it
            flattened = [result[:,q] for q in quantiles]
        elif isinstance(result, pd.DataFrame):
            # not a multi-index so we need to access the results in a different way
            flattened = [result.loc[q] for q in quantiles]
        else: # Series
            # need to convert the result to a Series
            flattened = [pd.Series(result.loc[q]) for q in quantiles]

        return zip(names, flattened)


def get_method_name(type):
    return type.__name__.lower()

aggregate_methods = [Count, DCount, CountIf, Sum, Avg, AvgIf, StDev, Variance, Min, Max,
                     ArgMin, ArgMax, Any, Percentiles]

aggregate_map = dict([(get_method_name(t), t) for t in aggregate_methods])

def create_aggregate(parsed, all_columns):
    new_col = None

    if isinstance(parsed, ep.Assignment):
        new_col = str(parsed.left)
        method = parsed.right
    else:
        method = parsed

    if not isinstance(method, ep.Method):
        raise Exception("expected method but got: " + str(method))

    method_name = str(method.name)

    try:
        agg_method = aggregate_map[method_name]
    except KeyError:
        raise KeyError("Unknown aggregate method: {0}".format(method_name))


    return agg_method(new_col, method.args.args, all_columns)
