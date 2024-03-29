import pandas as pd

from ._simple_expression import SimpleExpression, _evaluate_and_get_name, parse_column_name_or_pattern_list, remove_duplicates_maintain_order
from .aggregates import create_aggregate

def ensure_column_name_unique(df, col):
    while col in df.columns:
        col = col + "_"
    return col

TABLE_SELF = "self"

class Query:
    def __init__(self, query_statements):
        self.query_statements = query_statements
    
    def evaluate_query(self, w):
        wnew = w
        for s in self.query_statements:
            wnew = s.evaluate_query(wnew)
        return wnew

class QueryStatement:
    pass

class Pipe(QueryStatement):
    def __init__(self, tabular_operators):
        self.tabular_operators = tabular_operators
    
    def evaluate_query(self, w):
        for op in self.tabular_operators:
            w = op.evaluate_query(w)
        return w

class Let(QueryStatement):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def evaluate_query(self, w):
        left = str(self.left)
        right = self.right.evaluate(w._get_var_map())
        wnew = w.let(**{left: right})
        return wnew   

class LetTable(QueryStatement):
    def __init__(self, left, right):
        self.left = left
        self.right = right
    
    def evaluate_query(self, w):
        left = str(self.left)
        right = self.right.evaluate_query(w)
        # right is an instance of Wrap.  keep only the dataframe
        wnew = w.let(**{left: right.df})
        return wnew

class TabularOperator:
    def evaluate_query(self, w):
        newdf = self._evaluate_top(w.df, w._get_var_map())
        return w._copy(newdf)

    def _evaluate_top(self, df, vars):
        raise NotImplementedError()

class TableIdentifier(TabularOperator):
    def __init__(self, identifier):
        self.identifier = identifier

    def evaluate_query(self, w):
        wnew = w._set_active_table(str(self.identifier))
        return wnew

class As(TabularOperator):
    def __init__(self, identifier):
        self.identifier = identifier
    
    def evaluate_query(self, w):
        identifier = str(self.identifier)
        wnew = w.let(**{identifier: w.df})
        return wnew

class Take(TabularOperator):
    def __init__(self, n):
        self.n = n
    
    def _evaluate_top(self, df, vars):
        n = self.n.evaluate(vars)
        return df.head(n)   

class Where(TabularOperator):
    def __init__(self, predicate):
        self.predicate = predicate
    
    def _evaluate_top(self, df, vars):
        mask = self.predicate.evaluate(vars)

        return df[mask].copy()
class Extend(TabularOperator):
    def __init__(self, args):
        self.args = args
    
    def _evaluate_top(self, df, var_map):
        dfnew = df.copy(deep=False)
        for parsed in self.args:
            se = SimpleExpression(parsed)
            name = se.get_name()
            result = se.evaluate(var_map)
            dfnew[name] = result
        
        return dfnew

class Summarize(TabularOperator):
    def __init__(self, aggregates, by):
        self.aggregates = aggregates
        self.by = by
    
    def _evaluate_top(self, df, variable_map):
        dftemp = pd.DataFrame(index=df.index.copy())

        group_by_col_names = []
        for parsed in self.by:
            col_name, series = _evaluate_and_get_name(parsed, variable_map)
            if col_name in group_by_col_names:
                raise Exception("Column can only appear once in group by expression " + col_name)

            group_by_col_names.append(col_name)
            dftemp[col_name] = series
        
        all_columns = set(df.columns) - set(group_by_col_names)

        args = [create_aggregate(a, all_columns) for a in self.aggregates]

        for arg in args:
            for col_name, col_value in arg.evaluate_column_inputs(variable_map):
                if col_name not in dftemp.columns:
                    dftemp[col_name] = col_value

        if len(group_by_col_names) > 0:
            grouped = dftemp.groupby(group_by_col_names)
        else:
            # it's allowed to pass nothing as group by.  In which case the aggregate will 
            # operate on the entire series
            grouped = dftemp
        dfnew = pd.DataFrame()

        for arg in args:
            result = arg.apply(grouped, variable_map)
            for col, series in result:
                col = ensure_column_name_unique(dfnew, col)
                dfnew[col] = series
        
        if len(group_by_col_names) > 0:
            dfnew = dfnew.reset_index()
        
        return dfnew

def _sort(df, sort_columns, variable_map):
    dfnew = df.copy(deep=False)

    col_names = ["__tempcol_" + str(i) for i in range(len(sort_columns))]
    asc = [False] * len(sort_columns)

    var_map = variable_map
    for i, expr in enumerate(sort_columns):
        col = col_names[i]
        series = expr.evaluate(var_map)
        dfnew[col] = series
        if expr.is_asc():
            asc[i] = True
        # if expr.is_desc():
        #     asc[i] = False
    
    dfnew = dfnew.sort_values(col_names, ascending=asc)

    for c in col_names:
        del dfnew[c]
    
    return dfnew

class Sort(TabularOperator):
    def __init__(self, sort_columns):
        self.sort_columns = sort_columns
    
    def _evaluate_top(self, df, variable_map):
        return _sort(df, self.sort_columns, variable_map)

class Top(TabularOperator):
    def __init__(self, n, sort_columns):
        self.n = n
        self.sort_columns = sort_columns
    
    def evaluate_query(self, w):
        pipe = Pipe([Sort(self.sort_columns), Take(self.n)])
        return pipe.evaluate_query(w)

class Project(TabularOperator):
    def __init__(self, columns):
        self.columns = columns
    
    def _evaluate_top(self, df, variable_map):
        dfnew = pd.DataFrame()

        for parsed in self.columns:
            se = SimpleExpression(parsed)
            result = se.evaluate(variable_map)
            dfnew[se.get_name()] = result
        
        return dfnew

class ProjectAway(TabularOperator):
    def __init__(self, column_name_or_pattern_list):
        self.column_name_or_pattern_list = column_name_or_pattern_list
    
    def _evaluate_top(self, df, variable_map):
        dfnew = df.copy()
        for column in parse_column_name_or_pattern_list(self.column_name_or_pattern_list, df):
            del dfnew[column]

        return dfnew
    
class ProjectKeep(TabularOperator):
    def __init__(self, column_name_or_pattern_list):
        self.column_name_or_pattern_list = column_name_or_pattern_list
    
    def _evaluate_top(self, df, variable_map):
        columns_to_keep = set(parse_column_name_or_pattern_list(self.column_name_or_pattern_list, df))

        # maintain the original orderin of the columns
        columns = [c for c in df.columns if c in columns_to_keep]

        dfnew = df[columns].copy()

        return dfnew

class ProjectReorder(TabularOperator):
    def __init__(self, column_name_or_pattern_list):
        self.column_name_or_pattern_list = column_name_or_pattern_list
    
    def _evaluate_top(self, df, variable_map):
        specified_cols = parse_column_name_or_pattern_list(self.column_name_or_pattern_list, df)
        # unspecified columns should be put at the back of the list
        new_cols = remove_duplicates_maintain_order(specified_cols + list(df.columns))
        dfnew = df[new_cols].copy()

        return dfnew

class ProjectRename(TabularOperator):
    def __init__(self, simple_assignments):
        self.simple_assignments = simple_assignments
    
    def _evaluate_top(self, df, variable_map):
        col_map = dict()

        for simple_assignment in self.simple_assignments:
            se = SimpleExpression(simple_assignment)
            newcol = se.get_name()
            oldcol = str(se.expression)
            col_map[oldcol] = newcol
            if oldcol not in df.columns:
                raise KeyError("Could not find column: " + oldcol)
        
        dfnew = df.rename(columns=col_map).copy()
        return dfnew

class Distinct(TabularOperator):
    def __init__(self, columnsOrStar):
        self.columnsOrStar = columnsOrStar
    
    def _evaluate_top(self, df, variable_map):
        if self.columnsOrStar == "*":
            return df.drop_duplicates()
        
        # note: the arguments to kusto distinct must be either "*" or a list of column names.
        # Here we support an arbitrary expression.  e.g. distinct("A + B")
        # It would be extra work to limit it to only column names, and supporting arbitrary expressions seems nice, so I will leave it

        dfnew = pd.DataFrame()
        for parsed in self.columnsOrStar:
            se = SimpleExpression(parsed)
            name = se.get_name()
            series = se.evaluate(variable_map)
            dfnew[name] = series
        
        return dfnew.drop_duplicates()

class Count(TabularOperator):
    def _evaluate_top(self, df, variable_map):
        count = df.shape[0]

        dfnew = pd.DataFrame()
        dfnew["Count"] = [count]
        return dfnew

class GetSchema(TabularOperator):
    def _evaluate_top(self, df, variable_map):
        d2 = pd.DataFrame()
        d2["ColumnName"] = df.columns
        d2["ColumnOrdinal"] = range(len(df.columns))
        d2["DataType"] = list(df.dtypes)
        d2["ColumnType"] = list(df.dtypes)
        return d2

class Join(TabularOperator):
    def __init__(self, right, kwargs):
        self.right = right
        self.kwargs = kwargs
    
    def evaluate_query(self, w):
        right = self.right.evaluate_query(w)
        return w.join(right, **self.kwargs)

class Union(TabularOperator):
    def __init__(self, right_tables, kwargs):
        self.right_tables = right_tables
        self.kwargs = kwargs
    
    def evaluate_query(self, w):
        tables = []
        for t in self.right_tables:
            t = t.evaluate_query(w)
            tables.append(t)
        return w.union(tables, **self.kwargs)