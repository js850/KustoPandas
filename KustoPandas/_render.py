import pandas as pd
import numpy as np

class RenderArgs:
    xcolumn = None
    ycolumns = None

    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            self.__setattr__(k, v)

def render(w, visualization, **kwargs):
    args = RenderArgs(**kwargs)

    if args.xcolumn is None:
        args.xcolumn = w.df.columns[0]
    if args.ycolumns is None:
        args.ycolumns = w.df.columns[1:]

    if visualization == "timechart":
        return render_timechart(w, args)
    else:
        raise Exception("render visualization method not implemented yet: " + visualization)

    

def render_timechart(w, args):
    df = w.df.copy()
    # df[xcolumn] = pd.to_datetime(df[xcolumn])
    return df.plot(x=args.xcolumn, y=args.ycolumns)

