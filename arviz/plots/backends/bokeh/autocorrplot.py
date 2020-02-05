"""Bokeh Autocorrplot."""
import bokeh.plotting as bkp
import numpy as np
from bokeh.layouts import gridplot
from bokeh.models import DataRange1d
from bokeh.models.annotations import Title

from . import backend_kwarg_defaults, backend_show
from ...plot_utils import _create_axes_grid, make_label
from ....stats import autocorr
from ....rcparams import rcParams


def plot_autocorr(
    axes,
    plotters,
    max_lag,
    figsize,
    rows,
    cols,
    line_width,
    combined,
    backend_config,
    backend_kwargs,
    show,
):
    """Bokeh autocorrelation plot."""
    if backend_config is None:
        backend_config = {}

    backend_config = {
        **backend_kwarg_defaults(("bounds_y_range", "plots.bokeh.bounds_y_range"),),
        **backend_config,
    }

    if backend_kwargs is None:
        backend_kwargs = {}

    backend_kwargs = {
        **backend_kwarg_defaults(),
        **backend_kwargs,
    }

    if axes is None:
        _, axes = _create_axes_grid(
            len(plotters),
            rows,
            cols,
            figsize=figsize,
            squeeze=False,
            sharex=True,
            sharey=True,
            backend="bokeh",
            backend_kwargs=backend_kwargs,
        )
    else:
        axes = np.atleast_2d(axes)

    if "bounds_x_range" in backend_config:
        data_range_x = DataRange1d(
            start=0, end=max_lag, bounds=backend_config["bounds_x_range"], min_interval=5
        )
    else:
        len_y = plotters[0][2].size
        data_range_x = DataRange1d(start=0, end=max_lag, bounds=(0, len_y), min_interval=5)

    data_range_y = DataRange1d(
        start=-1, end=1, bounds=backend_config["bounds_y_range"], min_interval=0.1
    )

    for (var_name, selection, x), ax in zip(
        plotters, (item for item in axes.flatten() if item is not None)
    ):
        x_prime = x
        if combined:
            x_prime = x.flatten()
        y = autocorr(x_prime)

        ax.segment(
            x0=np.arange(len(y)),
            y0=0,
            x1=np.arange(len(y)),
            y1=y,
            line_width=line_width,
            line_color="black",
        )
        ax.line([0, 0], [0, max_lag], line_color="steelblue")

        title = Title()
        title.text = make_label(var_name, selection)
        ax.title = title
        ax.x_range = data_range_x
        ax.y_range = data_range_y

    if backend_show(show):
        bkp.show(gridplot(axes.tolist(), toolbar_location="above"))
    return axes
