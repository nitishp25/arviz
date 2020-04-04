"""Bokeh Densityplot."""
from collections import defaultdict

from bokeh.models.annotations import Title, Legend
import numpy as np

from . import backend_kwarg_defaults
from .. import show_layout
from ...plot_utils import (
    make_label,
    _create_axes_grid,
    calculate_point_estimate,
)
from ....stats import hpd
from ....stats.stats_utils import histogram, _fast_kde, get_bins


def plot_density(
    ax,
    all_labels,
    to_plot,
    colors,
    bw,
    figsize,
    length_plotters,
    rows,
    cols,
    line_width,
    markersize,
    credible_interval,
    point_estimate,
    hpd_markers,
    outline,
    shade,
    data_labels,
    backend_kwargs,
    show,
):
    """Bokeh density plot."""
    if backend_kwargs is None:
        backend_kwargs = {}

    backend_kwargs = {
        **backend_kwarg_defaults(("dpi", "plot.bokeh.figure.dpi"),),
        **backend_kwargs,
    }

    if ax is None:
        _, ax = _create_axes_grid(
            length_plotters,
            rows,
            cols,
            figsize=figsize,
            squeeze=False,
            backend="bokeh",
            backend_kwargs=backend_kwargs,
        )
    else:
        ax = np.atleast_2d(ax)

    axis_map = {
        label: ax_
        for label, ax_ in zip(all_labels, (item for item in ax.flatten() if item is not None))
    }
    if data_labels is None:
        data_labels = {}

    legend_items = defaultdict(list)
    for m_idx, plotters in enumerate(to_plot):
        for var_name, selection, values in plotters:
            label = make_label(var_name, selection)

            if data_labels:
                data_label = data_labels[m_idx]
            else:
                data_label = None

            plotted = _d_helper(
                values.flatten(),
                label,
                colors[m_idx],
                bw,
                line_width,
                markersize,
                credible_interval,
                point_estimate,
                hpd_markers,
                outline,
                shade,
                axis_map[label],
            )
            if data_label is not None:
                legend_items[axis_map[label]].append((data_label, plotted))

    for ax1, legend in legend_items.items():
        legend = Legend(items=legend, location="center_right", orientation="horizontal",)
        ax1.add_layout(legend, "above")
        ax1.legend.click_policy = "hide"

    show_layout(ax, show)

    return ax


def _d_helper(
    vec,
    vname,
    color,
    bw,
    line_width,
    markersize,
    credible_interval,
    point_estimate,
    hpd_markers,
    outline,
    shade,
    ax,
):

    extra = dict()
    plotted = []

    if vec.dtype.kind == "f":
        if credible_interval != 1:
            hpd_ = hpd(vec, credible_interval, multimodal=False)
            new_vec = vec[(vec >= hpd_[0]) & (vec <= hpd_[1])]
        else:
            new_vec = vec

        density, xmin, xmax = _fast_kde(new_vec, bw=bw)
        density *= credible_interval
        x = np.linspace(xmin, xmax, len(density))
        ymin = density[0]
        ymax = density[-1]

        if outline:
            plotted.append(ax.line(x, density, line_color=color, line_width=line_width, **extra))
            plotted.append(
                ax.line(
                    [xmin, xmin],
                    [-ymin / 100, ymin],
                    line_color=color,
                    line_dash="solid",
                    line_width=line_width,
                    muted_color=color,
                    muted_alpha=0.2,
                )
            )
            plotted.append(
                ax.line(
                    [xmax, xmax],
                    [-ymax / 100, ymax],
                    line_color=color,
                    line_dash="solid",
                    line_width=line_width,
                    muted_color=color,
                    muted_alpha=0.2,
                )
            )

        if shade:
            plotted.append(
                ax.patch(
                    np.r_[x[::-1], x, x[-1:]],
                    np.r_[np.zeros_like(x), density, [0]],
                    fill_color=color,
                    fill_alpha=shade,
                    muted_color=color,
                    muted_alpha=0.2,
                    **extra
                )
            )

    else:
        xmin, xmax = hpd(vec, credible_interval, multimodal=False)
        bins = get_bins(vec)

        _, hist, edges = histogram(vec, bins=bins)

        if outline:
            plotted.append(
                ax.quad(
                    top=hist,
                    bottom=0,
                    left=edges[:-1],
                    right=edges[1:],
                    line_color=color,
                    fill_color=None,
                    muted_color=color,
                    muted_alpha=0.2,
                    **extra
                )
            )
        else:
            plotted.append(
                ax.quad(
                    top=hist,
                    bottom=0,
                    left=edges[:-1],
                    right=edges[1:],
                    line_color=color,
                    fill_color=color,
                    fill_alpha=shade,
                    muted_color=color,
                    muted_alpha=0.2,
                    **extra
                )
            )

    if hpd_markers:
        plotted.append(ax.diamond(xmin, 0, line_color="black", fill_color=color, size=markersize))
        plotted.append(ax.diamond(xmax, 0, line_color="black", fill_color=color, size=markersize))

    if point_estimate is not None:
        est = calculate_point_estimate(point_estimate, vec, bw)
        plotted.append(ax.circle(est, 0, fill_color=color, line_color="black", size=markersize))

    _title = Title()
    _title.text = vname
    ax.title = _title
    ax.title.text_font_size = "13pt"

    return plotted
