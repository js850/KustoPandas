import expression_parser as ep
import uuid


class SimpleAgg:
    """
    An aggregate function needs to define the following methods

    columns_needed => returns list of expression
    
    apply

    """
    def __init__(self, output_column_name, args):
        self.args = args
        self.output_column_name = output_column_name

    def _columns_neded_internal(self):
        return self.args

    def columns_needed(self):
        args = self._columns_neded_internal()

        self.arg_names = [str(uuid.uuid1()) for a in args]
        return zip(self.arg_names, args)

    def _get_method_name(self):
        return self.__class__.__name__.lower()
    
    def _get_arg_name_or_default(self, i, default):
        if len(self.args) > i and isinstance(self.args[i], ep.Var):
            return str(self.args[i])
        return default

    def _default_name(self):
        suffix = self._get_arg_name_or_default(0, "")
        return self._get_method_name() + "_" + suffix

    def _get_output_column_name(self):
        if self.output_column_name:
            return self.output_column_name
        else:
            return self._default_name()
    
    def apply(self, grouped):
        names = self.arg_names
        if len(names) == 1:
            # operate on a SeriesGroupBy
            grouped = grouped[names[0]]
        elif len(names) > 1:
            # operate on a DataFrameGroupBy
            grouped = grouped[self.arg_names]
        return self.apply1(grouped)


    def apply1(self, grouped):
        output_column_name = self._get_output_column_name()
        series = self.apply_aggregate(grouped)
        return [(output_column_name, series)]
    
    def apply_aggregate(self, grouped):
        raise NotImplementedError()

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
            raise Exception("{0} can only take one argument: {1}".format(self._get_method_name(), str(self.args)))

class Count(NoArgAgg):
    def apply_aggregate(self, grouped):
        return grouped.size()

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
        def argmin(g):
            # find the index of the min of arg0
            idx = g[self.arg_names[0]].idxmin()
            # return the value of arg1 at that index
            return g[self.arg_names[1]].loc[idx]
        series = grouped.apply(lambda g: argmin(g))
        return series

class ArgMax(AggTwoArgs):
    def apply_aggregate(self, grouped):
        def argmax(g):
            # find the index of the min of arg0
            idx = g[self.arg_names[0]].idxmax()
            # return the value of arg1 at that index
            return g[self.arg_names[1]].loc[idx]
        series = grouped.apply(lambda g: argmax(g))
        return series

class Percentiles(SimpleAgg):
    def validate(self, df):
        if len(self.args) < 2:
            raise Exception("Percentiles requires at least two args: " + str(self.args))

    def _columns_neded_internal(self):
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

        # series = self.args[0].evaluate(grouped)

        result = grouped.quantile(quantiles)

        # result is a multi-index.  we need to flatten it
        flattened = [result[:,q] for q in quantiles]

        return zip(names, flattened)


def get_method_name(type):
    return type.__name__.lower()

aggregate_methods = [Count, DCount, CountIf, Sum, Avg, StDev, Variance, Min, Max,
                     ArgMin, ArgMax, Percentiles]

aggregate_map = dict([(get_method_name(t), t) for t in aggregate_methods])

def create_aggregate(text):
    new_col = None

    parsed = ep.parse_statement(text)

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


    return agg_method(new_col, method.args.args)
