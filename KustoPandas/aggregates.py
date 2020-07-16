import expression_parser as ep

class AggMethod:
    def get_method_name(self):
        return self.__class__.__name__.lower()

class SimpleAgg(AggMethod):
    def __init__(self, name, args):
        self.args = args
        self.name = name
    
    def default_name(self):
        suffix = ""
        if len(self.args) > 0:
            suffix = str(self.args[0])
        return self.get_method_name() + "_" + suffix

    def get_name(self):
        if self.name:
            return self.name
        else:
            return self.default_name()
    
    def apply(self, grouped):
        name = self.get_name()
        series = self.apply_aggregate(grouped)
        return [(name, series)]
    
    def apply_aggregate(self, grouped):
        raise NotImplementedError()

class NoArgAgg(SimpleAgg):
    def validate(self, df):
        if self.args:
            raise Exception("{0} can't take an arg: {1}".format(self.get_method_name(), str(self.args)))

class AggOneArg(SimpleAgg):
    def validate(self, df):
        if len(self.args) != 1:
            raise Exception("{0} can only take one argument: {1}".format(self.get_method_name(), str(self.args)))

class Count(NoArgAgg):
    def apply_aggregate(self, grouped):
        return grouped.size()

class DCount(AggOneArg):
    def apply_aggregate(self, grouped):
        return self.args[0].evaluate(grouped).nunique()

class Sum(AggOneArg):
    def apply_aggregate(self, grouped):
        return self.args[0].evaluate(grouped).sum()

class Percentiles(SimpleAgg):

    def validate(self, df):
        if len(self.args) < 2:
            raise Exception("Percentiles requires at least two args: " + str(self.args))

    def apply(self, grouped):
        percentiles = [int(a.evaluate(None)) for a in self.args[1:]]
        for p in percentiles:
            if p > 100 or p < 0:
                raise Exception("Percentile must be between 0 and 100")
        
        quantiles = [1.0*p / 100 for p in percentiles]

        
        if self.name is not None:
            basename = self.name + "_"
        else:
            basename = self.get_method_name() + "_"
        
        names = [basename + str(p) for p in percentiles]

        series = self.args[0].evaluate(grouped)

        result = series.quantile(quantiles)

        # result is a multi-index.  we need to flatten it
        flattened = [result[:,q] for q in quantiles]

        return zip(names, flattened)


def get_method_name(type):
    return type.__name__.lower()

aggregate_methods = [Count, DCount, Sum, Percentiles]

aggregate_map = dict([(get_method_name(t), t) for t in aggregate_methods])

class Aggregate:
    def __init__(self, text):
        new_col = None

        parsed = ep.parse_statement(text)

        if isinstance(parsed, ep.Assignment):
            new_col = str(parsed.left)
            method = parsed.right
        else:
            method = parsed

        if not isinstance(method, ep.Method):
            raise Exception("expected method but got: " + str(method))

        func_name = str(method.name)
        # if len(method.args.args) == 0:
        #     func_arg = ""
        # else:
        #     func_arg = str(method.args.args[0])

        self.aggregate_func = aggregate_map[func_name](new_col, method.args.args)

    def validate(self, df):
        self.aggregate_func.validate(df)
    
    def apply(self, grouped):
        return self.aggregate_func.apply(grouped)