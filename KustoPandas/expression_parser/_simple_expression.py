import uuid

_temp_name_base = "__tempcolumnname__"

from .expression_parser import Assignment, Var, Method, By, Comma, Mul, Asc, Desc
from .expression_tree import flatten_comma

class DefaultColumnNameGenerator:
    def __init__(self):
        self.count = 0

    def _is_temp_column_name(self, name):
        return _temp_name_base in name
    
    def _generate_default_column_name(self, existing_cols):
        self.count += 1
        new_name_base = "Column" + str(self.count)
        new_name = new_name_base
        i = 0
        while new_name in existing_cols:
            # This is not examctly what Kusto does.  If Column1 already exists in the 
            # dataframe, then kusto changes that column and keeps this default name as Column1
            i += 1
            new_name = new_name_base + "_" + str(i)
        return new_name
        
    def replace_temp_column_names(self, df):
        name_map = {}
        for c in df.columns:
            if self._is_temp_column_name(c):
                new_name = self._generate_default_column_name(df.columns)
                name_map[c] = new_name
        
        return df.rename(columns=name_map)

def _generate_temp_column_name():
    return _temp_name_base + str(uuid.uuid1())

def replace_temp_column_names(df):
    name_generator = DefaultColumnNameGenerator()
    return name_generator.replace_temp_column_names(df)

class SimpleExpression:
    """
    this class is a wrapper around a simple parsed expression.

    It makes it easier to do things like get the assigned name or default name
    and determine if there is an additional modifiers like asc or desc
    """
    def __init__(self, parsed):
        """ parsed can be an assignment or a simple expression
        A = B
        A = method(B)
        A = B + C
        method(B) => default name method_B
        B + C => default name 
        """
        self.parsed = parsed

        self.assignment_name = None
        if isinstance(parsed, Assignment):
            self.assignment_name = str(parsed.left)
            self.expression = parsed.right
        else:
            self.expression = parsed
    
    def get_name(self):
        if self.assignment_name is not None:
            return self.assignment_name
        return _get_default_name(self.parsed)

    def evaluate(self, variable_map):
        return self.expression.evaluate(variable_map)
    
    def set_name(self, name):
        self.assignment_name = name
    
    def is_asc(self):
        return isinstance(self.expression, Asc)

    def is_desc(self):
        return isinstance(self.expression, Desc)
    
    def __str__(self):
        return str(self.parsed)

def _get_method_default_name(method):
    name = str(method.name)
    suffix = ""
    if len(method.args.args) > 0:
        arg1 = method.args.args[0]
        if isinstance(arg1, Var):
            suffix = str(arg1)
    return "{0}_{1}".format(name, suffix)

def _get_default_name(parsed):
    if isinstance(parsed, Var):
        return str(parsed)
    if isinstance(parsed, Method):
        return _get_method_default_name(parsed)
    return _generate_temp_column_name()

def _evaluate_and_get_name(parsed, variable_map):
    result = parsed.evaluate(variable_map)
    if isinstance(parsed, Assignment):
        for name, value in result.items():
            return name, value
    if isinstance(parsed, Var):
        return str(parsed), result
    if isinstance(parsed, Method):
        return _get_method_default_name(parsed), result
    return _generate_temp_column_name(), result