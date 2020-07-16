import expression_parser as ep

class AggMethod:
    dname = None


class SimpleAgg:
    dname = None
    def __init__(self, name, args):
        self.args = args
        self.name = name
    
    def default_name(self):
        suffix = ""
        if len(self.args) > 0:
            suffix = str(self.args[0])
        return self.name + "_" + suffix

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

class Count(SimpleAgg):
    dname = "count"
    
    def validate(self, df):
        if self.args:
            raise Exception("count can't take an arg: " +  str(self.args))
    
    def apply_aggregate(self, grouped):
        return grouped.size()

class Sum(SimpleAgg):
    dname = "sum"

    def validate(self, df):
        if len(self.args) != 1:
            raise Exception("Sum can only take one argument: " + str(self.args))
        for arg in self.args:
            if str(arg) not in df.columns:
                raise Exception("sum argument is not a column: ", str(arg))
    
    def apply_aggregate(self, grouped):
        return self.args[0].evaluate(grouped).sum()

class Percentiles(SimpleAgg):
    dname = "percentiles"

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
            basename = self.dname + "_"
        
        names = [basename + str(p) for p in percentiles]

        series = self.args[0].evaluate(grouped)

        result = series.quantile(quantiles)

        # result is a multi-index.  we need to flatten it
        flattened = [result[:,q] for q in quantiles]

        return zip(names, flattened)




aggregate_methods = [Count, Sum, Percentiles]

aggregate_map = dict([(t.dname, t) for t in aggregate_methods])

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