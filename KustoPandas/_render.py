import pandas as pd
from pandas.api.types import is_datetime64_any_dtype

import numpy as np

class RenderArgs:
    xcolumn = None
    ycolumns = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

def render(w, visualization=None, **kwargs):
    args = RenderArgs(**kwargs)

    if args.xcolumn is None:
        args.xcolumn = w.df.columns[0]
    if args.ycolumns is None:
        args.ycolumns = w.df.columns[1:]

    if visualization is None:
        return render_plot(w, args)
    if visualization == "timechart":
        return render_timechart(w, args)
    if visualization == "barchart":
        return render_barchart(w, args)
    else:
        raise Exception("render visualization method not implemented yet: " + visualization)

def render_plot(w, args):
    return w.df.plot(x=args.xcolumn, y=args.ycolumns)

def render_timechart(w, args):
    if not pd.api.types.is_datetime64_any_dtype(w.df[args.xcolumn]):
        w = w.project_rename("{0}=datetime({0})".format(args.xcolumn))
    return render_plot(w, args)

def render_barchart(w, args):
    return w.df.plot.bar(x=args.xcolumn, y=args.ycolumns)

