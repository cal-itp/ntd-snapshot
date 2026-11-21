import altair as alt
import numpy as np
import pandas as pd

# Chart Colors
from snapshot_utils._color_palette import (
    BRAND_COLORS,
    CALITP_CATEGORY_BRIGHT_COLORS,
    DIVERGING_COLORS,
    NEUTRAL_COLORS,
    PASTEL_COLORS,
)

# Chart Typography
CHART_FONT = "Century Gothic, Helvetica, Arial, sans-serif"
AXIS_FONT = "Arial"
CHART_FONTS = {
    "primary": CHART_FONT,
    "axis": AXIS_FONT,
}

ALT_TEXT_CONFIG = {
    "font": CHART_FONT,
    "fontSize": 13,
    "fontWeight": 500,
    "color": NEUTRAL_COLORS["axis_label"],
    "align": "left",
    "dx": 8,
}

# Axis Styling
ALT_AXIS_CONFIG = {
    "labelFont": AXIS_FONT,
    "titleFont": AXIS_FONT,
    "labelFontSize": 13,
    "titleFontSize": 15,
    "labelColor": NEUTRAL_COLORS["axis_label"],
    "titleColor": NEUTRAL_COLORS["axis_title"],
    "labelFontWeight": 500,
    "titleFontWeight": 600,
    "domainColor": NEUTRAL_COLORS["axis_line"],
    "tickColor": NEUTRAL_COLORS["axis_line"],
    "grid": False,
    "labelPadding": 6,
    "titlePadding": 10,
}
# Grid Styling
ALT_GRID_CONFIG = {
    "grid": True,
    "gridColor": "#E5E7EB",
    "gridOpacity": 0.8,
}

# Legend Styling
ALT_LEGEND_CONFIG = {
    "labelFont": CHART_FONT,
    "titleFont": CHART_FONT,
    "labelFontSize": 13,
    "titleFontSize": 13,
    "labelColor": NEUTRAL_COLORS["axis_label"],
    "titleColor": NEUTRAL_COLORS["axis_title"],
}


######################################################### Mode Report Charts #########################################################
# Composition Chart
def composition_by_year(df, cols, chart_title=None, colors=None, width=650, height=140):
    colors = colors or PASTEL_COLORS
    d = df[["ntd_id", "year"] + list(cols)].drop_duplicates()
    charts = []
    for col, title in cols.items():
        x = d.groupby(["year", col])["ntd_id"].nunique().reset_index(name="n")
        x[col] = x[col].fillna("Missing").astype(str)
        x["pct"] = x["n"] / x.groupby("year")["n"].transform("sum") * 100
        cats = x[col].unique().tolist()
        scale = alt.Scale(domain=cats, range=colors[: len(cats)])

        bars = (
            alt.Chart(x)
            .mark_bar()
            .encode(
                x=alt.X("year:O", title="Year", axis=alt.Axis(**ALT_AXIS_CONFIG)),
                y=alt.Y(
                    "pct:Q",
                    title="Share of Agencies",
                    scale=alt.Scale(domain=[0, 100]),
                    axis=alt.Axis(**ALT_AXIS_CONFIG),
                ),
                color=alt.Color(f"{col}:N", scale=scale, legend=None),
                tooltip=[
                    "year:O",
                    alt.Tooltip(f"{col}:N", title=title),
                    alt.Tooltip("n:Q", title="Agencies", format=","),
                    alt.Tooltip("pct:Q", title="Share", format=".1f"),
                ],
            )
            .properties(width=width, height=height, title=title)
        )
        ld = pd.DataFrame({"category": cats, "y": range(len(cats))})
        legend = (
            alt.Chart(ld)
            .mark_square(size=80)
            .encode(
                y=alt.Y("y:O", axis=None),
                color=alt.Color("category:N", scale=scale, legend=None),
            )
            + alt.Chart(ld)
            .mark_text(**ALT_TEXT_CONFIG)
            .encode(y=alt.Y("y:O", axis=None), text="category:N")
        ).properties(width=150, height=max(40, len(cats) * 22))
        charts.append(alt.hconcat(bars, legend, spacing=8))

    chart = alt.vconcat(*charts, spacing=20).configure_view(strokeWidth=0)
    return chart.properties(title=chart_title) if chart_title else chart


# Mode Trend Charts
def mode_trend_chart(df, value_column, title=None, y_title=None, width=400, height=300):
    trend_df = df.groupby(["year", "mode_group"])[value_column].sum().reset_index()
    trend_df[value_column] = trend_df[value_column].round(0).astype(int)
    title = title or f"{value_column.replace('_', ' ').title()} by Mode"
    y_title = y_title or value_column.replace("_", " ").title()

    nearest = alt.selection_point(
        nearest=True, on="pointerover", fields=["year"], empty=False
    )
    base = alt.Chart(trend_df)
    line = base.mark_line(strokeWidth=2.5, interpolate="monotone").encode(
        x=alt.X("year:O", title="Year", axis=alt.Axis(**ALT_AXIS_CONFIG)),
        y=alt.Y(
            f"{value_column}:Q",
            title=y_title,
            axis=alt.Axis(format=",.0f", **{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG}),
        ),
        color=alt.Color(
            "mode_group:N",
            title="Mode",
            scale=alt.Scale(
                range=list(BRAND_COLORS.values())[: trend_df["mode_group"].nunique()]
            ),
            legend=alt.Legend(orient="right", symbolType="circle", **ALT_LEGEND_CONFIG),
        ),
    )
    selectors = (
        base.mark_point().encode(x="year:O", opacity=alt.value(0)).add_params(nearest)
    )
    points = line.mark_point(
        size=80, filled=True, stroke="white", strokeWidth=1.5
    ).encode(
        opacity=alt.when(nearest).then(alt.value(1)).otherwise(alt.value(0)),
        tooltip=[
            alt.Tooltip("year:O", title="Year"),
            alt.Tooltip("mode_group:N", title="Mode"),
            alt.Tooltip(f"{value_column}:Q", title=y_title, format=",.0f"),
        ],
    )
    rules = (
        base.mark_rule(color=NEUTRAL_COLORS["border"], strokeDash=[4, 2])
        .encode(x="year:O")
        .transform_filter(nearest)
    )
    return alt.layer(line, selectors, points, rules).properties(
        width=width,
        height=height,
        title=alt.TitleParams(
            text=title,
            font=CHART_FONT,
            fontSize=16,
            fontWeight=600,
            color=NEUTRAL_COLORS["axis_title"],
            anchor="start",
            offset=12,
        ),
    )


# Percent Stacked Bar chart
def percent_stacked_bar(
    df,
    group_column,
    category_columns,
    year_column="year",
    year_range=None,
    chart_title=None,
    chart_subtitle=None,
    y_title="Percentage",
    colors=None,
    width=750,
    height=400,
):
    colors = colors or PASTEL_COLORS
    d = df.copy()
    if year_range is not None:
        d = d[d[year_column].between(*year_range)].copy()

    data = (
        d.groupby([year_column, group_column])[list(category_columns.values())]
        .sum()
        .reset_index()
    )
    data = data.melt(
        [year_column, group_column], var_name="category_column", value_name="amount"
    )
    data["category"] = data["category_column"].map(
        {v: k for k, v in category_columns.items()}
    )
    data["percentage"] = (
        data["amount"]
        / data.groupby([year_column, group_column])["amount"].transform("sum")
        * 100
    )

    bars = (
        alt.Chart(data)
        .mark_bar(stroke=None)
        .encode(
            x=alt.X(f"{year_column}:O", title="Year", axis=alt.Axis(**ALT_AXIS_CONFIG)),
            xOffset=alt.XOffset(
                f"{group_column}:N", title=group_column.replace("_", " ").title()
            ),
            y=alt.Y(
                "percentage:Q",
                title=y_title,
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(**ALT_AXIS_CONFIG, format=".0f"),
            ),
            color=alt.Color(
                "category:N",
                title="Expenditure Type",
                scale=alt.Scale(domain=list(category_columns.keys()), range=colors),
                legend=alt.Legend(orient="right", **ALT_LEGEND_CONFIG),
            ),
            tooltip=[
                alt.Tooltip(f"{year_column}:O", title="Year"),
                alt.Tooltip(f"{group_column}:N", title="Mode Group"),
                alt.Tooltip("category:N", title="Expenditure Type"),
                alt.Tooltip("percentage:Q", title="Share", format=".1f"),
                alt.Tooltip("amount:Q", title="Expenditure", format=",.0f"),
            ],
        )
    )

    title = (
        alt.TitleParams(text=chart_title, subtitle=chart_subtitle, font=CHART_FONT)
        if chart_subtitle
        else alt.TitleParams(text=chart_title, font=CHART_FONT)
    )

    return bars.properties(width=width, height=height, title=title).configure_view(
        strokeWidth=0
    )


# Breakdown chart with year selector
def breakdown_chart(
    df,
    component_columns,
    group_column,
    year_column="year",
    normalize=True,
    title=None,
    width=500,
    height=350,
):
    plot_df = (
        df.groupby([year_column, group_column])[component_columns]
        .sum(min_count=1)
        .reset_index()
        .melt(
            id_vars=[year_column, group_column],
            var_name="component",
            value_name="amount",
        )
    )
    plot_df["amount"] /= 1_000_000
    plot_df["component"] = (
        plot_df["component"]
        .str.replace("_real", "", regex=False)
        .str.replace("_", " ", regex=False)
        .str.title()
    )
    y_enc = alt.Y(
        "amount:Q",
        stack="normalize" if normalize else True,
        axis=alt.Axis(format=".0%" if normalize else ",.1f", **ALT_AXIS_CONFIG),
        title="Share of Total" if normalize else "Amount ($M)",
    )
    years = sorted(df[year_column].dropna().unique().tolist())
    year_sel = alt.param(
        name="year_sel",
        value=int(years[-1]),
        bind=alt.binding_select(options=[int(y) for y in years], name="Year "),
    )
    return (
        alt.Chart(plot_df)
        .transform_filter(f"datum[{repr(year_column)}] == year_sel")
        .mark_bar(cornerRadius=2)
        .encode(
            x=alt.X(
                f"{group_column}:N",
                title="Mode",
                axis=alt.Axis(labelAngle=0, **ALT_AXIS_CONFIG),
            ),
            y=y_enc,
            color=alt.Color(
                "component:N",
                title="Component",
                scale=alt.Scale(range=PASTEL_COLORS),
                legend=alt.Legend(
                    orient="bottom", direction="horizontal", **ALT_LEGEND_CONFIG
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title="Mode"),
                alt.Tooltip("component:N", title="Component"),
                alt.Tooltip("amount:Q", title="Amount ($M)", format=",.1f"),
            ],
        )
        .add_params(year_sel)
        .properties(
            width=width,
            height=height,
            title=alt.TitleParams(
                text=alt.ExprRef(
                    expr=f"'{title or 'Composition by Mode'} | ' + year_sel"
                ),
                font=CHART_FONT,
                fontSize=16,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                anchor="start",
            ),
        )
    )


# Scorecard Chart
def plot_scorecard(
    df,
    metrics,
    group_column,
    titles=None,
    x_labels=None,
    main_title=None,
    subtitles=None,
    colors=None,
    formats=None,
    width=280,
    height=260,
):
    titles = titles or metrics
    x_labels = x_labels or metrics
    subtitles = subtitles or [""] * len(metrics)
    colors = colors or list(BRAND_COLORS.values())[: len(metrics)]
    formats = formats or [".2f"] * len(metrics)

    order = df[group_column].drop_duplicates().tolist()
    charts = []

    for metric, title, xlabel, subtitle, color, fmt in zip(
        metrics, titles, x_labels, subtitles, colors, formats
    ):
        plot_df = df[[group_column, metric]].dropna().copy()

        bars = (
            alt.Chart(plot_df)
            .mark_bar(
                cornerRadiusEnd=6,
                height=28,
                color=color,
            )
            .encode(
                x=alt.X(
                    f"{metric}:Q",
                    title=xlabel,
                    axis=alt.Axis(
                        format=fmt,
                        domain=False,
                        **{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG},
                    ),
                ),
                y=alt.Y(
                    f"{group_column}:N",
                    sort=order,
                    title=None,
                    axis=alt.Axis(
                        ticks=False,
                        domain=False,
                        labelPadding=6,
                        labelFont=AXIS_FONT,
                        labelFontSize=13,
                        labelColor=NEUTRAL_COLORS["axis_label"],
                        labelFontWeight=500,
                    ),
                ),
                tooltip=[
                    alt.Tooltip(f"{group_column}:N", title=group_column),
                    alt.Tooltip(f"{metric}:Q", title=title, format=fmt),
                ],
            )
        )

        labels = (
            alt.Chart(plot_df)
            .mark_text(
                align="left",
                baseline="middle",
                font=CHART_FONT,
                fontSize=13,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                dx=8,
            )
            .encode(
                x=alt.X(f"{metric}:Q"),
                y=alt.Y(f"{group_column}:N", sort=order),
                text=alt.Text(f"{metric}:Q", format=fmt),
            )
        )

        charts.append(
            (bars + labels).properties(
                width=width,
                height=height,
                title=alt.TitleParams(
                    text=title,
                    subtitle=subtitle,
                    anchor="start",
                    font=CHART_FONT,
                    fontSize=16,
                    fontWeight=600,
                    color=NEUTRAL_COLORS["axis_title"],
                    subtitleFont=CHART_FONT,
                    subtitleFontSize=12,
                    subtitleColor=NEUTRAL_COLORS["axis_label"],
                    offset=12,
                ),
            )
        )

    chart = alt.hconcat(*charts, spacing=35)
    if main_title:
        chart = chart.properties(
            title=alt.TitleParams(
                text=main_title,
                anchor="start",
                font=CHART_FONT,
                fontSize=22,
                fontWeight=700,
                color=NEUTRAL_COLORS["axis_title"],
                offset=20,
            ),
        )
    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(labelFont=AXIS_FONT, titleFont=AXIS_FONT)
        .configure_title(font=CHART_FONT)
    )


# Efficiency and Effectiveness Heatmap
def efficiency_matrix(
    df,
    metrics,
    group_column,
    year_column=None,
    year=None,
    titles=None,
    normalize="zscore",
    chart_title=None,
    color_scheme="redblue",
    reverse_scale=False,
    width=500,
    height=300,
):
    """
    Creates a heatmap comparing efficiency and effectiveness metrics across modes.
    Metrics are normalized independently by year using z-scores or percentage of maximum.
    Missing values are preserved. reverse_scale makes lower values more favorable.
    Includes an interactive year selector and dynamic chart title.
    """
    df_plot = df.copy()
    titles = titles or metrics
    reverse_flags = (
        [reverse_scale] * len(metrics)
        if isinstance(reverse_scale, bool)
        else list(reverse_scale)
    )
    years = sorted(df_plot[year_column].dropna().unique().tolist())

    year_sel = alt.param(
        name="year_sel",
        value=year if year is not None else years[-1],
        bind=alt.binding_select(options=years, name="Year "),
    )
    # Aggregate by mode and year
    group_cols = [year_column, group_column] if year_column else [group_column]
    agg = df_plot.groupby(group_cols, as_index=False)[metrics].mean()

    for col in metrics:
        agg[col] = pd.to_numeric(agg[col], errors="coerce")

    # Reshape to long format
    plot_df = agg.melt(
        id_vars=group_cols,
        value_vars=metrics,
        var_name="metric",
        value_name="raw_value",
    )

    # Normalize each metric independently within each year
    norm_groups = [year_column, "metric"] if year_column else ["metric"]
    if normalize == "zscore":

        def zscore(x):
            valid = x.dropna().astype(float)
            std = valid.std()
            if len(valid) < 2 or pd.isna(std) or std == 0:
                return pd.Series(np.nan, index=x.index)
            return (x.astype(float) - valid.mean()) / std

        plot_df["norm_value"] = plot_df.groupby(norm_groups)["raw_value"].transform(
            zscore
        )
        legend_title = "Standard deviations"

    elif normalize == "percent_of_max":
        plot_df["norm_value"] = plot_df.groupby(norm_groups)["raw_value"].transform(
            lambda x: x / x.max() * 100
        )
        legend_title = "% of maximum"

    else:
        raise ValueError("normalize must be 'zscore' or 'percent_of_max'.")

    # Reverse selected metrics so lower values score better
    reverse_map = dict(zip(metrics, reverse_flags))
    plot_df["norm_value"] *= (
        plot_df["metric"].map(reverse_map).map({True: -1, False: 1})
    )

    # Display labels
    plot_df["metric_label"] = plot_df["metric"].map(dict(zip(metrics, titles)))

    # Heatmap
    chart = alt.Chart(plot_df)

    if year_sel is not None:
        chart = chart.transform_filter(
            f"datum[{repr(year_column)}] == year_sel"
        ).add_params(year_sel)
    diverging_colors = DIVERGING_COLORS["redblue"]

    return (
        chart.mark_rect(stroke="white", strokeWidth=2)
        .encode(
            x=alt.X(
                "metric_label:N",
                title=None,
                sort=titles,
                axis=alt.Axis(
                    labelAngle=0, ticks=False, domain=False, **ALT_AXIS_CONFIG
                ),
            ),
            y=alt.Y(
                f"{group_column}:N",
                title=None,
                sort=None,
                axis=alt.Axis(ticks=False, domain=False, **ALT_AXIS_CONFIG),
            ),
            color=alt.Color(
                "norm_value:Q",
                title=legend_title,
                scale=alt.Scale(
                    range=diverging_colors,
                    domainMid=0 if normalize == "zscore" else None,
                ),
                legend=alt.Legend(
                    orient="right",
                    direction="vertical",
                    **ALT_LEGEND_CONFIG,
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title="Mode"),
                alt.Tooltip("metric_label:N", title="Metric"),
                alt.Tooltip("raw_value:Q", title="Original Value", format=",.2f"),
                alt.Tooltip(
                    "norm_value:Q",
                    title="Standardized Score"
                    if normalize == "zscore"
                    else "% of maximum",
                    format=".2f",
                ),
            ],
        )
        .properties(
            width=width,
            height=height,
            title=alt.TitleParams(
                text=alt.ExprRef(expr=f"'{chart_title} | ' + year_sel")
                if chart_title and year_sel is not None
                else chart_title,
                anchor="start",
                font=CHART_FONT,
                fontSize=18,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                offset=15,
            )
            if chart_title
            else None,
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont=AXIS_FONT, titleFont=AXIS_FONT)
        .configure_title(font=CHART_FONT)
    )


# Simple Box Plot


def simple_box_plot(
    df,
    value_column,
    group_column,
    year_column=None,
    year=None,
    filters=None,
    value_format=",.0f",
    sort_by="median",
    show_n=True,
    log_scale=False,
    show_outliers=True,
    x_title=None,
    chart_title=None,
    colors=None,
    width=700,
    height=350,
):
    """
    Creates a horizontal box plot comparing distributions across groups.
    Box = middle 50%, line = median, whiskers = typical range, dots = outliers.
    Includes an interactive year selector, dynamic title, sample sizes, and sorting.
    """
    d = df.copy()
    # Static filters
    if filters:
        for col, vals in filters.items():
            d = d[d[col].isin(vals)] if isinstance(vals, list) else d[d[col] == vals]

    # Keep required columns and remove missing values
    columns = [group_column, value_column] + ([year_column] if year_column else [])
    d = d[columns].dropna()

    if log_scale:
        d = d[d[value_column] > 0]

    # Interactive year selector
    year_sel = None
    if year_column:
        years = sorted(d[year_column].unique().tolist())
        if not years:
            raise ValueError("No available years after filtering.")

        default_year = year if year is not None else years[-1]
        if default_year not in years:
            raise ValueError(f"Selected year {default_year} is not available.")

        year_sel = alt.param(
            name="year_sel",
            value=default_year,
            bind=alt.binding_select(options=years, name="Year "),
        )

    # Colors
    colors = colors if colors is not None else PASTEL_COLORS

    # Base chart and interactive year filter
    chart = alt.Chart(d)
    if year_sel is not None:
        chart = chart.transform_filter(
            f"datum[{repr(year_column)}] == year_sel"
        ).add_params(year_sel)

    # Dynamic sample sizes
    if show_n:
        chart = chart.transform_joinaggregate(
            group_n=f"count({value_column})",
            groupby=[group_column],
        ).transform_calculate(
            group_label=f"datum[{repr(group_column)}] + ' (n=' + datum.group_n + ')'"
        )
    else:
        chart = chart.transform_calculate(group_label=f"datum[{repr(group_column)}]")

    # Dynamic sorting
    if sort_by in ("median", "mean"):
        chart = chart.transform_joinaggregate(
            group_stat=f"{sort_by}({value_column})",
            groupby=[group_column],
        )
        y_sort = alt.EncodingSortField(field="group_stat", op="max", order="descending")
    else:
        y_sort = "ascending"

    # Box plot
    return (
        chart.mark_boxplot(
            extent=1.5 if show_outliers else "min-max",
            size=28,
            opacity=0.75,
            median=dict(color=NEUTRAL_COLORS["axis_title"], size=28),
            rule=dict(color=NEUTRAL_COLORS["axis_label"], opacity=0.8),
            outliers=dict(size=25, color=NEUTRAL_COLORS["axis_label"])
            if show_outliers
            else False,
        )
        .encode(
            x=alt.X(
                f"{value_column}:Q",
                title=x_title or value_column.replace("_", " ").title(),
                scale=alt.Scale(type="log") if log_scale else alt.Scale(zero=True),
                axis=alt.Axis(
                    format=value_format, **{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG}
                ),
            ),
            y=alt.Y(
                "group_label:N",
                sort=y_sort,
                title=None,
                axis=alt.Axis(ticks=False, domain=False, **ALT_AXIS_CONFIG),
            ),
            color=alt.Color(
                f"{group_column}:N",
                legend=None,
                scale=alt.Scale(range=colors),
            ),
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title="Group"),
                alt.Tooltip(
                    f"{value_column}:Q",
                    title=x_title or value_column,
                    format=value_format,
                ),
            ],
        )
        .properties(
            width=width,
            height=height,
            title=alt.TitleParams(
                text=alt.ExprRef(expr=f"'{chart_title} | ' + year_sel")
                if chart_title and year_sel is not None
                else chart_title,
                anchor="start",
                font=CHART_FONT,
                fontSize=18,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                offset=15,
            )
            if chart_title
            else None,
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont=AXIS_FONT, titleFont=AXIS_FONT)
        .configure_title(font=CHART_FONT)
    )


# Ridge Plot


def ridge_plot(
    df,
    value_column,
    category_column,
    year_column=None,
    year=None,
    filters=None,
    value_min=None,
    value_max=None,
    step=30,
    overlap=1.5,
    chart_title=None,
    x_title=None,
    category_title=None,
    colors=None,
):
    """
    Creates a ridge plot showing distributions across categories.
    Includes an interactive year selector and dynamic chart title.
    """
    d = df.copy()

    # Static filters
    if filters:
        for col, vals in filters.items():
            d = d[d[col].isin(vals)] if isinstance(vals, list) else d[d[col] == vals]
    # Filter values
    d = d[d[value_column].notna() & d[category_column].notna()]
    if value_min is not None:
        d = d[d[value_column] >= value_min]
    if value_max is not None:
        d = d[d[value_column] <= value_max]

    # Interactive year selector
    year_sel = None
    if year_column:
        years = sorted(d[year_column].dropna().unique().tolist())
        if not years:
            raise ValueError("No valid years found.")
        selected_year = year if year is not None else years[-1]
        if selected_year not in years:
            raise ValueError(f"Year {selected_year!r} not found in data.")

        year_sel = alt.param(
            name="year_sel",
            value=selected_year,
            bind=alt.binding_select(options=years, name="Year "),
        )

    # Colors
    colors = colors if colors is not None else PASTEL_COLORS
    categories = sorted(d[category_column].unique().tolist(), key=str)

    # Base chart and year filter
    chart = alt.Chart(d, width=800, height=step)
    if year_sel is not None:
        chart = chart.transform_filter(
            f"datum[{repr(year_column)}] == year_sel"
        ).add_params(year_sel)

    # Ridge plot
    return (
        chart.transform_density(
            value_column,
            groupby=[category_column],
            as_=[value_column, "density"],
        )
        .mark_area(
            interpolate="monotone",
            fillOpacity=1,
            stroke="white",
            strokeWidth=0.8,
        )
        .encode(
            x=alt.X(
                f"{value_column}:Q",
                title=x_title or value_column.replace("_", " ").title(),
                axis=alt.Axis(**{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG}),
            ),
            y=alt.Y(
                "density:Q",
                axis=None,
                scale=alt.Scale(range=[step, -step * overlap]),
            ),
            color=alt.Color(
                f"{category_column}:N",
                title=category_title or category_column.replace("_", " ").title(),
                scale=alt.Scale(domain=categories, range=colors),
                legend=alt.Legend(
                    orient="right", direction="vertical", **ALT_LEGEND_CONFIG
                ),
            ),
            tooltip=[
                alt.Tooltip(
                    f"{category_column}:N", title=category_title or category_column
                ),
                alt.Tooltip(
                    f"{value_column}:Q", title=x_title or value_column, format=".3f"
                ),
                alt.Tooltip("density:Q", title="Density", format=".3f"),
            ],
        )
        .facet(
            row=alt.Row(
                f"{category_column}:N",
                title=None,
                sort=categories,
                header=alt.Header(
                    labelAngle=0,
                    labelAlign="left",
                    labelFont=AXIS_FONT,
                    labelColor=NEUTRAL_COLORS["axis_label"],
                    labelFontSize=13,
                ),
            )
        )
        .properties(
            bounds="flush",
            title=alt.TitleParams(
                text=alt.ExprRef(expr=f"'{chart_title} | ' + year_sel")
                if chart_title and year_sel is not None
                else chart_title,
                anchor="start",
                font=CHART_FONT,
                fontSize=18,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                offset=15,
            )
            if chart_title
            else None,
        )
        .configure_facet(spacing=0)
        .configure_view(strokeWidth=0)
        .configure_axis(**ALT_AXIS_CONFIG)
        .configure_header(
            labelFont=AXIS_FONT,
            labelColor=NEUTRAL_COLORS["axis_label"],
            labelFontSize=13,
            labelFontWeight=500,
        )
        .configure_legend(**ALT_LEGEND_CONFIG)
        .configure_title(font=CHART_FONT)
    )


# Indexed Scissors Chart
def indexed_scissors(
    df,
    group_column,
    time_column,
    variable_columns,
    base_year,
    variable_labels=None,
    colors=None,
    chart_title=None,
    chart_subtitle=None,
):
    """
    Creates an indexed line chart comparing variables to a base year.
    Aggregates across agencies before calculating indices.
    Final grain: one row per mode group × year.
    """

    labels = variable_labels or {
        c: c.replace("_", " ").title() for c in variable_columns
    }
    colors = (
        colors
        if colors is not None
        else list(BRAND_COLORS.values())[: len(variable_columns)]
    )

    # Aggregate across agencies by mode group and year
    d = df[[group_column, time_column] + variable_columns].copy()
    d = d.groupby([group_column, time_column], as_index=False)[variable_columns].sum(
        min_count=1
    )

    # Extract base-year values separately for each group
    base = d[d[time_column] == base_year].copy()
    base = base.rename(columns={c: f"{c}_base" for c in variable_columns})
    d = d.merge(
        base[[group_column] + [f"{c}_base" for c in variable_columns]],
        on=group_column,
        how="left",
        validate="many_to_one",
    )

    # Calculate indices
    for c in variable_columns:
        baseline = d[f"{c}_base"]
        d[f"{c}_index"] = d[c] / baseline.where(baseline > 0) * 100

    # Reshape for visualization
    long = d.melt(
        id_vars=[group_column, time_column],
        value_vars=[f"{c}_index" for c in variable_columns],
        var_name="metric",
        value_name="index",
    )
    long["metric"] = long["metric"].map(
        {f"{c}_index": labels[c] for c in variable_columns}
    )

    # Indexed lines
    chart = (
        alt.Chart(long)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X(
                f"{time_column}:O",
                title=time_column.replace("_", " ").title(),
                axis=alt.Axis(**ALT_AXIS_CONFIG),
            ),
            y=alt.Y(
                "index:Q",
                title=f"Index ({base_year} = 100)",
                axis=alt.Axis(format=",.0f", **{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG}),
            ),
            color=alt.Color(
                "metric:N",
                title=None,
                scale=alt.Scale(domain=list(labels.values()), range=colors),
                legend=alt.Legend(
                    orient="right", direction="vertical", **ALT_LEGEND_CONFIG
                ),
            ),
            detail="metric:N",
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title="Mode"),
                alt.Tooltip(f"{time_column}:O", title="Year"),
                alt.Tooltip("metric:N", title="Metric"),
                alt.Tooltip("index:Q", title="Index", format=".1f"),
            ],
        )
        .properties(width=250, height=180)
    )

    return (
        chart.facet(f"{group_column}:N", columns=3, title=None)
        .properties(
            title=alt.TitleParams(
                text=chart_title,
                subtitle=chart_subtitle,
                anchor="start",
                font=CHART_FONT,
                fontSize=18,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                offset=15,
                subtitleFont=CHART_FONT,
                subtitleFontSize=12,
                subtitleColor=NEUTRAL_COLORS["axis_label"],
            )
            if chart_title
            else None,
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont=AXIS_FONT, titleFont=AXIS_FONT)
        .configure_header(
            labelFont=AXIS_FONT,
            labelColor=NEUTRAL_COLORS["axis_label"],
            labelFontSize=13,
            labelFontWeight=500,
        )
        .configure_legend(**ALT_LEGEND_CONFIG)
        .configure_title(font=CHART_FONT)
    )


# Grouped Scatter Plot
def grouped_scatter(
    df,
    x_variable,
    y_variable,
    group_column=None,
    size_column=None,
    label_column=None,
    year_column=None,
    tooltip_columns=None,
    x_title=None,
    y_title=None,
    chart_title=None,
):
    """Creates a generic scatter plot with optional grouping, sizing, labels, and year."""

    cols = [x_variable, y_variable] + [
        c for c in [group_column, size_column, label_column, year_column] if c
    ]
    d = df[cols].dropna().copy()
    d = d[(d[x_variable] > 0) & (d[y_variable] > 0)]
    tooltip_columns = tooltip_columns or cols

    enc = {
        "x": alt.X(
            f"{x_variable}:Q",
            title=x_title or x_variable.replace("_", " ").title(),
            axis=alt.Axis(**{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG}),
        ),
        "y": alt.Y(
            f"{y_variable}:Q",
            title=y_title or y_variable.replace("_", " ").title(),
            axis=alt.Axis(**{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG}),
        ),
        "tooltip": tooltip_columns,
    }

    if group_column:
        categories = sorted(d[group_column].dropna().unique().tolist(), key=str)
        enc["color"] = alt.Color(
            f"{group_column}:N",
            title=group_column.replace("_", " ").title(),
            scale=alt.Scale(domain=categories, range=CALITP_CATEGORY_BRIGHT_COLORS),
            legend=alt.Legend(orient="right", **ALT_LEGEND_CONFIG),
        )

    if size_column:
        enc["size"] = alt.Size(
            f"{size_column}:Q",
            title=size_column.replace("_", " ").title(),
            scale=alt.Scale(range=[30, 800]),
        )
    return (
        alt.Chart(d)
        .mark_circle(opacity=0.85, stroke="white", strokeWidth=0.7)
        .encode(**enc)
        .properties(
            width=600,
            height=450,
            title=alt.TitleParams(
                text=chart_title,
                font=CHART_FONT,
                fontSize=18,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                anchor="start",
            ),
        )
    )
