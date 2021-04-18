import uuid
import itertools
import pandas as pd
import numpy as np

from . import expression_parser as ep

from ._simple_expression import _generate_temp_column_name

def _is_groupby(g):
    return isinstance(g, pd.core.groupby.SeriesGroupBy) or isinstance(g, pd.core.groupby.DataFrameGroupBy )

class TopLevelAgg:
    """
    use this as a wrapper if the aggregate expression is not just a simple aggregate.  e.g.

    summarize("C = avg(A+1) + avg(B)")

    The logic here is complicated because we first have to do this in 3 steps
    
        1. evaluate the expressions inside the aggregate functions.  These become the inputs to the agg functions
        2. Combine them in a DataFrame and do a groupby on all of them at the same time.  This does not happen here, 
           but higher in the call stack because this is just one of potentially many aggregate functions and we only want to execute groupby once
        3. Perform the aggregation
        4. Evaluate any mathematical expressions that act on the aggregate result.
        5. Figure out what the name of the resulting column should be.

    Then the groupby is applied 
    """
    def __init__(self, new_column_name, parsed, all_columns):
        self.new_colum_name = new_column_name
        self.parsed = parsed
        self.all_columns = all_columns
        self.aggregate_instances = []
    
    def _evaluate_column_inputs_traverse(self, vars, parsed):
        """
        Traverse the expression tree to find the aggregate methods.  Once we find one, evaluate the 
        expressions that are arguments to that method.  Return those evaluated arguments as a list.
        """
        if isinstance(parsed, ep.Method) and str(parsed.name) in aggregate_map:
            aggregate_class = aggregate_map[str(parsed.name)]
            # here we instantiate the instance of the aggrege method class.
            # We attach that to the parsed object for later use because we will need to call it again.
            # This is an inelegant solution, I should find a cleaner one.
            aggregate_instance = aggregate_class(parsed.args.args, self.all_columns)
            parsed.set_aggregate_instance(aggregate_instance)
            self.aggregate_instances.append(aggregate_instance)
            return aggregate_instance.evaluate_column_inputs(vars)

        list_of_lists = [self._evaluate_column_inputs_traverse(vars, d) for d in parsed.descendents]
        # flatten lists
        return list(itertools.chain.from_iterable(list_of_lists))

    def evaluate_column_inputs(self, vars):
        return self._evaluate_column_inputs_traverse(vars, self.parsed)

    def _get_output_names(self):
        if self.new_colum_name is not None:
            return [self.new_colum_name]
        
        if isinstance(self.parsed, ep.Method) and self.parsed.has_aggregate_instance():
            return self.parsed.aggregate_instance.get_output_column_names()
        
        return [_generate_temp_column_name()]
    
    def apply(self, grouped, vars):
        """
        Evaluate the aggregate expression.  Most aggregates output exactly one series, 
        but some, e.g. percentiles(A, 90, 95) can output multiple series

        """
        # In this method we will do several things.  
        # 1. evaluate the aggregate method on the precomputed columns in the groupby 
        # 2. Evaluate any mathematical expressions operating on the output of the aggregate method
        # 3. Assign names to the output columns
        #
        # For 2. we will use self.parsed.evaluate(vars) which does not allow us to pass down the groupby object.
        # To work around this we will attache the groupby object to the aggregate method instances
        for agg in self.aggregate_instances:
            agg.set_grouped_object(grouped)

        # result can be a Series or a list of Series (E.g. percentiles returns a list of Series)
        result = self.parsed.evaluate(vars)

        output_names = self._get_output_names()

        if isinstance(result, pd.Series):
            return [(output_names[0], result)]
        
        if len(result) != len(output_names):
            # eventually this will be allowed A = percentiles(B, 50, 75) should result in columns A and percentiles_B_75
            raise Exception("Error in Aggregate output naming. Length of output names ({}) does not agree with length of result ({})".format(len(output_names), len(result)))

        return zip(output_names, result)

class SimpleAgg:
    """
    """
    def __init__(self, args, all_columns):
        self.args = args
        self._grouped_val = None

        # Get the definitions of the columns needed for the aggregate.
        # Each entry can be a simple column name, or a more complex expression, e.g. A+B.
        # The expressions will be evaluated before the groupby is done, so the inputs to this aggregate 
        # are the results of the expressions, e.g. A+B
        self.input_column_definitions = self._get_input_column_definitions(all_columns)
        # use a random name for the column to avoid conflicting names from different 
        # aggregate functions operatoring on the same groupby object
        self.input_column_names = [self._get_arg_name_or_default(a, _generate_temp_column_name()) for a in self.input_column_definitions]

    def validate(self):
        pass

    def _get_input_column_definitions(self, all_columns):
        """
        Return the columns that need to be evaluated and become part of the groupby expression

        For most aggregates this is all arguments, but not all.  e.g. for percentiles(A, 90, 95) only the first arg is a column definition
        """
        return self.args

    def evaluate_column_inputs(self, vars):
        self.validate()

        input_cols = [col.evaluate(vars) for col in self.input_column_definitions]
        return zip(self.input_column_names, input_cols)

    def _get_method_name(self):
        return self.__class__.__name__.lower()
    
    def _get_arg_name_or_default(self, arg, default):
        if isinstance(arg, ep.Var):
            return str(arg)
        return default

    def get_output_column_names(self):
        names = [self._get_arg_name_or_default(arg, "") for arg in self.args]
        names = [n for n in names if n != ""]
        suffix = "_".join(names)
        return [self._get_method_name() + "_" + suffix]
    
    def set_grouped_object(self, grouped):
        self._grouped_val = grouped

    def evaluate(self, vals):
        return self.apply(self._grouped_val)

    def apply(self, grouped):
        if len(self.input_column_names) == 1:
            # operate on a SeriesGroupBy
            grouped = grouped[self.input_column_names[0]]
        else:
            # operate on a DataFrameGroupBy
            grouped = grouped[self.input_column_names]
        
        return self.apply1(grouped)

    def apply1(self, grouped):
        if _is_groupby(grouped):
            series = self.apply_aggregate(grouped)
        else:
            result = self.apply_aggregate_series(grouped)
            series = pd.Series([result])

        return series
    
    def apply_aggregate(self, grouped):
        raise NotImplementedError()

    def apply_aggregate_series(self, series):
        # often the same method will work on both a series and a groupby e.g.
        # grouped.max() returns a series with one max value per group
        # series.max() just returns a single value
        return self.apply_aggregate(series)

class NoArgAgg(SimpleAgg):
    def validate(self):
        if self.args:
            raise Exception("{0} can't take an arg: {1}".format(self._get_method_name(), str(self.args)))

class AggOneArg(SimpleAgg):
    def validate(self):
        if len(self.args) != 1:
            raise Exception("{0} can only take one argument: {1}".format(self._get_method_name(), str(self.args)))

class AggTwoArgs(SimpleAgg):
    def validate(self):
        if len(self.args) != 2:
            raise Exception("{0} must have two arguments: {1}".format(self._get_method_name(), str(self.args)))

class SimpleIfAgg(AggTwoArgs):
    def apply_aggregate(self, grouped):
        series = grouped.apply(self.apply_aggregate_series)
        return series
    
    def apply_aggregate_series(self, df):
        predicate = df[self.input_column_names[1]]
        series = df[self.input_column_names[0]].loc[predicate]
        if len(series) == 0:
            return None
        return self._apply_aggregate_series(series)
    
    def _apply_aggregate_series(self, series):
        raise NotImplementedError()

class Count(NoArgAgg):
    def apply_aggregate(self, grouped):
        return grouped.size()

    def apply_aggregate_series(self, series):
        # this is actually a dataframe because self.input_column_names is empty
        return series.shape[0]
    
class CountIf(AggOneArg):
    def apply_aggregate(self, grouped):
        # the countif predicate was precomputed into a new column
        # sum returns the number of true values in that column
        return grouped.sum()

class DCount(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.nunique()

class DCountIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return series.nunique()

class Sum(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.sum()

class SumIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return series.sum()

class Avg(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.mean()

class AvgIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return series.mean()

class StDev(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.std()

class StDevIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return series.std()

class Variance(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.var()

class VarianceIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return series.var()

class Min(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.min()

class MinIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return series.min()

class Max(AggOneArg):
    def apply_aggregate(self, grouped):
        return grouped.max()

class MaxIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return series.max()

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
    def validate(self):
        if len(self.args) == 0:
            raise Exception("{0} must have at least one arg: {1}".format(self._get_method_name(), str(self.args)))

    def _get_input_column_definitions(self, all_columns):
        if isinstance(self.args[0], ep.Star):
            # .args is used to generate variable names
            self.orig_args = self.args
            return [ep.Var(c) for c in all_columns]

        return self.args
    
    def get_output_column_names(self):
        output_col_names = []
        prefix = self._get_method_name()
        for arg in self.input_column_definitions:
            suffix = self._get_arg_name_or_default(arg, "")
            col_name = prefix + "_" + suffix
            output_col_names.append(col_name)
        
        return output_col_names

    def apply(self, df):
        df = df[self.input_column_names]

        if _is_groupby(df):
            def _any2(x):
                return _any(x, False)
            df_nonull = df.apply(_any2)
        else:
            df_nonull = _any(df, True)

        result = [df_nonull[c] for c in self.input_column_names]

        if len(result) == 1:
            return result[0]

        return result

class AnyIf(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        mask = _all_non_null_if_possible_mask(series, None)
        s = series.loc[mask]
        return s.iloc[0]

class Percentiles(SimpleAgg):
    def validate(self):
        if len(self.args) < 2:
            raise Exception("Percentiles requires at least two args: " + str(self.args))

    def _get_input_column_definitions(self, all_columns):
        return self.args[:1]
    
    def get_output_column_names(self):
        percentiles = [int(a.evaluate(None)) for a in self.args[1:]]
        arg_name = self._get_arg_name_or_default(self.input_column_definitions[0], "")
        basename = "{}_{}_".format(self._get_method_name(), arg_name)

        names = [basename + str(p) for p in percentiles]
        return names

    def apply(self, grouped):
        grouped = grouped[self.input_column_names[0]]

        percentiles = [int(a.evaluate(None)) for a in self.args[1:]]
        for p in percentiles:
            if p > 100 or p < 0:
                raise Exception("Percentile must be between 0 and 100")
        
        quantiles = [1.0*p / 100 for p in percentiles]

        result = grouped.quantile(quantiles)

        if _is_groupby(grouped):
            flattened = []
            for q in quantiles:
                # The result has a multi-index.  
                # The first n levels of the multi-index are the group-by columns
                # The lowest level is the quantile
                # Select the rows corresponding to quantile q
                r = result.loc[result.index.get_level_values(-1) == q]
                # We now need to drop the index level corresponding to q
                r.index = r.index.droplevel(-1)
                flattened.append(r)
        elif isinstance(result, pd.Series):
            flattened = [pd.Series(result.loc[q]) for q in quantiles]
        else: 
            raise "Unexpected type for the result of quantile " + type(result)

        if len(flattened) == 1:
            return flattened[0]

        return flattened

class Make_Set(AggOneArg):
    def apply_aggregate(self, grouped):
        series = grouped.apply(self.apply_aggregate_series)
        return series
    
    def apply_aggregate_series(self, series):
        # should I convert this to a json set first?
        return set(series)

class Make_Set_If(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return set(series)

class Make_List(AggOneArg):
    def apply_aggregate(self, grouped):
        series = grouped.apply(self.apply_aggregate_series)
        return series
    
    def apply_aggregate_series(self, series):
        # should I convert this to a json set first?
        return list(series)

class Make_List_If(SimpleIfAgg):
    def _apply_aggregate_series(self, series):
        return list(series)

class Camoflage:
    def __init__(self, value):
        self.value = value

class Make_Bag(AggOneArg):
    def apply_aggregate(self, grouped):
        camo_series = grouped.apply(self.apply_aggregate_series)
        series = camo_series.apply(lambda x: x.value)
        return series
    
    def apply_aggregate_series(self, series):
        # should I convert this to a json set first?
        bag = dict()
        for s in series:
            try: 
                items = s.items()
            except:
                # skip the item if it is not a dictionary type
                continue

            for k, v in items:
                # overwrite old values
                bag[k] = v

        # If I return a dict here then the internals of pandas disassemble the dict 
        # and turn it into a multi-index Series.  
        # A simple workaround is to camoflage it as something else and then extract it later
        return Camoflage(bag)

def get_method_name(type):
    return type.__name__.lower()

aggregate_methods = [Count, DCount, DCountIf, CountIf, 
                     Sum, SumIf, Avg, AvgIf, StDev, StDevIf, Variance, VarianceIf, 
                     Min, MinIf, Max, MaxIf,
                     ArgMin, ArgMax, Any, AnyIf, Percentiles,
                     Make_Set, Make_Set_If, Make_List, Make_List_If, Make_Bag
                     ]

aggregate_map = dict([(get_method_name(t), t) for t in aggregate_methods])

def create_aggregate_old(parsed, all_columns):
    new_col = None

    if isinstance(parsed, ep.Assignment):
        new_col = str(parsed.left)
        method = parsed.right
    else:
        method = parsed

    if not isinstance(method, ep.Method):
        raise Exception("expected aggregate method but got: " + str(method))

    method_name = str(method.name)

    try:
        agg_method = aggregate_map[method_name]
    except KeyError:
        raise KeyError("Unknown aggregate method: {0}".format(method_name))


    return agg_method(new_col, method.args.args, all_columns)

def create_aggregate(parsed, all_columns):

    if isinstance(parsed, ep.Assignment):
        new_col = str(parsed.left)
        method = parsed.right
    else:
        new_col = None
        method = parsed

    return TopLevelAgg(new_col, method, all_columns)