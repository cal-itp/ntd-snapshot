# Chart functions
import textwrap

import altair as alt
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from pypalettes import load_palette
from pywaffle import Waffle

# import ipywidgets as widgets

alt.data_transformers.enable("vegafusion")
NAVY, TEAL, YELLOW, BLUE = "#162933", "#00b2a9", "#ffb81c", "#5493b6"
GREY, BORDER = "#4b4f54", "#d9d9d6"
FONT = "Century Gothic, Helvetica, Arial, sans-serif"


def composition_by_year(df, cols, chart_title=None, colors=None, width=650, height=140):
    colors = colors or [
        "#AEC6CF",
        "#FFDAB9",
        "#BFD8B8",
        "#D8BFD8",
        "#FFE5A5",
        "#C5CAE9",
        "#F4B6C2",
        "#B2DFDB",
    ]
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
                x=alt.X("year:O", title="Year"),
                y=alt.Y(
                    "pct:Q", title="Share of agencies", scale=alt.Scale(domain=[0, 100])
                ),
                color=alt.Color(f"{col}:N", scale=scale, legend=None),
                tooltip=[
                    "year:O",
                    alt.Tooltip(f"{col}:N", title=title),
                    "n:Q",
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
            .mark_text(align="left", dx=8, fontSize=11)
            .encode(y=alt.Y("y:O", axis=None), text="category:N")
        ).properties(width=150, height=max(40, len(cats) * 22))

        charts.append(alt.hconcat(bars, legend, spacing=8))

    chart = alt.vconcat(*charts, spacing=20).configure_view(strokeWidth=0)
    return chart.properties(title=chart_title) if chart_title else chart


def prep_for_mode_trend(df, value_column):
    trend_df = df.groupby(["year", "mode_group"])[value_column].sum().reset_index()
    trend_df[value_column] = trend_df[value_column].round(0).astype(int)
    return trend_df


def mode_trend_chart(df, value_column, title=None, y_title=None):
    nearest = alt.selection_point(
        nearest=True, on="pointerover", fields=["year"], empty=False
    )
    base = alt.Chart(df)
    title = title or f"{value_column.replace('_', ' ').title()} by Mode"
    y_title = y_title or value_column.replace("_", " ").title()

    line = base.mark_line(strokeWidth=2.5, interpolate="monotone").encode(
        x=alt.X(
            "year:O", title="Year", axis=alt.Axis(labelAngle=0, labelColor="#374151")
        ),
        y=alt.Y(
            f"{value_column}:Q",
            title=y_title,
            axis=alt.Axis(
                format=",.0f",
                grid=True,
                gridColor="#E5E7EB",
                gridOpacity=0.7,
                labelColor="#6B7280",
                titleColor="#374151",
            ),
        ),
        color=alt.Color(
            "mode_group:N",
            title="Mode",
            scale=alt.Scale(range=["#3B82F6", "#10B981", "#F59E0B", "#6366F1"]),
            legend=alt.Legend(orient="right", symbolType="circle"),
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
        base.mark_rule(color="#D1D5DB", strokeDash=[4, 2])
        .encode(x="year:O")
        .transform_filter(nearest)
    )

    return alt.layer(line, selectors, points, rules).properties(
        width=400,
        height=300,
        title=alt.TitleParams(
            text=title,
            fontSize=16,
            fontWeight=600,
            color="#111827",
            anchor="start",
            offset=12,
        ),
    )


def scatter_plot_regression(
    df, x_variable, y_variable, tooltip_columns=None, chart_title=None
):
    """Creates a filtered scatter plot with a regression trend line."""
    d = df[(df[x_variable] > 0) & (df[y_variable] > 0)].copy()
    tooltip_columns = tooltip_columns or [x_variable, y_variable]

    scatter = (
        alt.Chart(d)
        .mark_circle(
            size=70, opacity=0.55, color="#3B82F6", stroke="white", strokeWidth=1
        )
        .encode(
            x=alt.X(
                f"{x_variable}:Q",
                title=x_variable,
                axis=alt.Axis(
                    labelColor="#6B7280",
                    titleColor="#374151",
                    grid=True,
                    gridColor="#E5E7EB",
                    gridOpacity=0.7,
                ),
            ),
            y=alt.Y(
                f"{y_variable}:Q",
                title=y_variable,
                axis=alt.Axis(
                    labelColor="#6B7280",
                    titleColor="#374151",
                    grid=True,
                    gridColor="#E5E7EB",
                    gridOpacity=0.7,
                ),
            ),
            tooltip=tooltip_columns,
        )
    )

    trend = (
        alt.Chart(d)
        .transform_regression(x_variable, y_variable)
        .mark_line(color="#111827", size=2.5)
        .encode(x=f"{x_variable}:Q", y=f"{y_variable}:Q")
    )

    return (
        (scatter + trend)
        .properties(
            width=500,
            height=350,
            title=alt.TitleParams(
                text=chart_title,
                fontSize=16,
                fontWeight=600,
                color="#111827",
                anchor="start",
                offset=12,
            ),
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont="Arial", titleFont="Arial")
        .configure_title(font="Arial")
    )


def waffle_by_year(
    df,
    value_column,
    category_column,
    year_column,
    years=None,
    palette="CrystalGems",
    shuffle=9,
    rows=50,
    columns=10,
):
    """Creates waffle charts showing category values across selected years."""
    d = df.copy()
    if years is not None:
        d = d[d[year_column].isin(years)]

    d = d.groupby([year_column, category_column], as_index=False)[value_column].sum()

    all_years = d[year_column].unique()
    all_categories = d[category_column].unique()

    idx = pd.MultiIndex.from_product(
        [all_years, all_categories], names=[year_column, category_column]
    )
    d = (
        d.set_index([year_column, category_column])
        .reindex(idx, fill_value=0)
        .reset_index()
        .sort_values([year_column, category_column])
    )

    colors = load_palette(
        palette, keep_first_n=len(all_categories), shuffle=shuffle
    ) + ["white"]

    max_value = d.loc[d[year_column] == all_years.max(), value_column].sum()
    fig, axs = plt.subplots(ncols=len(all_years), figsize=(14, 8))
    axs = [axs] if len(all_years) == 1 else axs

    for year, ax in zip(sorted(all_years), axs):
        values = sorted(
            d.loc[d[year_column] == year, value_column].tolist(), reverse=True
        )
        values.append(max_value - sum(values))

        Waffle.make_waffle(
            ax=ax,
            rows=rows,
            columns=columns,
            values=values,
            vertical=True,
            colors=colors,
        )
        ax.yaxis.set_visible(True)
        ax.text(0.1, -0.04, str(int(year)), fontsize=14, ha="center")

    from matplotlib.patches import Patch

    plt.legend(
        handles=[
            Patch(color=colors[i], label=cat) for i, cat in enumerate(all_categories)
        ],
        bbox_to_anchor=(1.05, 1),
        loc="upper left",
    )
    plt.tight_layout()
    return fig


def before_after_trail(
    df,
    value_column,
    category_column,
    group_column,
    year_column="year",
    start_year=2021,
    end_year=2024,
    selected_groups=None,
    chart_title=None,
    change_label="Change (%)",
    width=200,
    height=400,
):
    """
    Creates a before-and-after trail chart comparing a value across two years.

    Parameters:
        df: DataFrame containing the data.
        value_column: Numeric column being compared (e.g., "vehicle_revenue_hours").
        category_column: Column defining the categories (e.g., "mode").
        group_column: Column defining separate chart panels (e.g., "primary_uza_name").
        year_column: Column containing the years being compared (e.g., "year").
        start_year: Earlier year in the comparison.
        end_year: Later year in the comparison.
        selected_groups: Optional list of groups to include.
        chart_title: Optional chart title.
        change_label: Label for the color legend.
        width: Width of each chart panel.
        height: Height of each chart panel.
    """
    d = df.copy()
    if selected_groups is not None:
        d = d[d[group_column].isin(selected_groups)]

    return (
        alt.Chart(d, title=chart_title)
        .mark_trail()
        .encode(
            x=alt.X(f"{year_column}:O").title(None),
            y=alt.Y(f"{category_column}:N").title(None),
            size=alt.Size(f"{value_column}:Q").scale(range=[5, 20]).title(value_column),
            color=alt.Color("delta:Q")
            .scale(domainMid=0, range=["maroon", "lightgray", "blue"])
            .title(change_label),
            tooltip=[
                alt.Tooltip(f"{year_column}:O", title="Year"),
                alt.Tooltip(f"{value_column}:Q", title=value_column),
            ],
            column=alt.Column(f"{group_column}:N").title(group_column),
        )
        .transform_pivot(
            pivot=year_column,
            value=value_column,
            groupby=[category_column, group_column],
        )
        .transform_calculate(delta=f"datum['{end_year}'] - datum['{start_year}']")
        .transform_fold([str(start_year), str(end_year)], as_=["year", value_column])
        .properties(width=width, height=height)
        .configure_legend(orient="bottom", direction="horizontal")
        .configure_view(stroke=None)
    )


def percent_stacked_bar(
    df,
    group_column,
    category_columns,
    year_column="year",
    year_range=(2019, 2024),
    chart_title=None,
    chart_subtitle=None,
    y_title="Percentage",
    colors=None,
    width=700,
    height=400,
):
    d = df[df[year_column].between(*year_range)].copy()

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
            x=alt.X(f"{year_column}:O", title="Year"),
            xOffset=alt.XOffset(f"{group_column}:N", title="Mode Group"),
            y=alt.Y("percentage:Q", title=y_title, scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(
                "category:N",
                title="Expenditure Type",
                scale=alt.Scale(range=colors) if colors else alt.Scale(),
            ),
            tooltip=[
                alt.Tooltip(f"{year_column}:O", title="Year"),
                alt.Tooltip(f"{group_column}:N", title="Mode Group"),
                alt.Tooltip("category:N", title="Type"),
                alt.Tooltip("percentage:Q", title="Share", format=".1f"),
                alt.Tooltip("amount:Q", title="Amount", format=",.0f"),
            ],
        )
    )

    labels = data.groupby([year_column, group_column], as_index=False)[
        "percentage"
    ].sum()
    text = (
        alt.Chart(labels)
        .mark_text(dy=-8, fontSize=11, fontWeight=500, color="#374151")
        .encode(
            x=alt.X(f"{year_column}:O"),
            xOffset=alt.XOffset(f"{group_column}:N"),
            y=alt.Y("percentage:Q"),
            text=alt.Text(f"{group_column}:N"),
        )
    )

    title = (
        alt.TitleParams(text=chart_title, subtitle=chart_subtitle)
        if chart_subtitle
        else chart_title
    )

    return (bars + text).properties(width=width, height=height, title=title)


# def percent_stacked_bar(
#     df,
#     group_column,
#     category_columns,
#     year_column=None,
#     year=None,
#     rank_column=None,
#     top_n=10,
#     chart_title=None,
#     chart_subtitle=None,
#     y_title="Percentage",
#     colors=None,
#     width=500,
#     height=300,
# ):
#     df_plot = df.copy()

#     if year_column is not None and year is not None:
#         df_plot = df_plot[df_plot[year_column] == year]

#     if rank_column is not None:
#         top_groups = (
#             df_plot.groupby(group_column)[rank_column]
#             .sum()
#             .nlargest(top_n)
#             .index.tolist()
#         )
#         df_plot = df_plot[df_plot[group_column].isin(top_groups)]
#     else:
#         top_groups = df_plot[group_column].drop_duplicates().tolist()

#     data = (
#         df_plot.groupby(group_column)[list(category_columns.values())]
#         .sum()
#         .reset_index()
#         .melt(id_vars=group_column, var_name="category_column", value_name="amount")
#     )

#     data["category"] = data["category_column"].map(
#         {v: k for k, v in category_columns.items()}
#     )
#     data["percentage"] = (
#         data["amount"] / data.groupby(group_column)["amount"].transform("sum") * 100
#     )

#     title = (
#         alt.TitleParams(text=chart_title, subtitle=chart_subtitle)
#         if chart_subtitle
#         else chart_title
#     )

#     return (
#         alt.Chart(data)
#         .mark_bar()
#         .encode(
#             x=alt.X(
#                 f"{group_column}:N",
#                 title=group_column,
#                 sort=top_groups,
#                 axis=alt.Axis(labelAngle=-25),
#             ),
#             y=alt.Y(
#                 "sum(percentage):Q",
#                 title=y_title,
#                 scale=alt.Scale(domain=[0, 100]),
#                 axis=alt.Axis(format=".0f"),
#             ),
#             color=alt.Color(
#                 "category:N",
#                 title="Category",
#                 scale=alt.Scale(range=colors) if colors else alt.Scale(),
#             ),
#             tooltip=[
#                 alt.Tooltip(f"{group_column}:N", title=group_column),
#                 alt.Tooltip("category:N", title="Category"),
#                 alt.Tooltip("percentage:Q", title="Share", format=".1f"),
#                 alt.Tooltip("amount:Q", title="Amount", format=",.0f"),
#             ],
#         )
#         .properties(title=title, width=width, height=height)
#     )


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
    chart_subtitle=None,
    x_title=None,
    category_title=None,
):
    """
    Creates a ridge plot showing the distribution of a numeric variable
    across categories.

    Parameters:
        df: DataFrame containing the data.
        value_column: Numeric variable whose distribution is shown.
        category_column: Column defining the groups shown as ridges.
        year_column: Time variable used to filter the data.
        year: Specific year to include.
        filters: Optional dictionary of column-value pairs for filtering.
        value_min: Optional minimum value to include.
        value_max: Optional maximum value to include.
        step: Height of each ridge.
        overlap: Amount of overlap between ridges.
        chart_title: Optional chart title.
        chart_subtitle: Optional chart subtitle.
        x_title: Optional x-axis title.
        category_title: Optional category label title.
    """
    d = df.copy()
    if year_column and year is not None:
        d = d[d[year_column] == year]

    if filters:
        for col, vals in filters.items():
            d = d[d[col].isin(vals)] if isinstance(vals, list) else d[d[col] == vals]
    d = d[d[value_column].notna()]
    if value_min is not None:
        d = d[d[value_column] >= value_min]
    if value_max is not None:
        d = d[d[value_column] <= value_max]

    return (
        alt.Chart(d, width=800, height=step)
        .transform_density(
            value_column, groupby=[category_column], as_=[value_column, "density"]
        )
        .mark_area(
            interpolate="monotone", fillOpacity=0.8, stroke="white", strokeWidth=0.5
        )
        .encode(
            x=alt.X(f"{value_column}:Q", title=x_title or value_column),
            y=alt.Y(
                "density:Q", axis=None, scale=alt.Scale(range=[step, -step * overlap])
            ),
            color=alt.Color(
                f"{category_column}:N", title=category_title or category_column
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
                header=alt.Header(labelAngle=0, labelAlign="left"),
            )
        )
        .properties(
            title=alt.TitleParams(text=chart_title, subtitle=chart_subtitle),
            bounds="flush",
        )
        .configure_facet(spacing=0)
        .configure_view(stroke=None)
    )


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
    chart_subtitle=None,
    colors=None,
    width=700,
    height=350,
):
    """
    Simple horizontal box plot: one box per group, sorted by median.
    Box = middle 50%, line = median, whiskers = typical range, dots = unusual values.
    """
    d = df.copy()
    if year_column and year is not None:
        d = d[d[year_column] == year]
    if filters:
        for col, vals in filters.items():
            d = d[d[col].isin(vals)] if isinstance(vals, list) else d[d[col] == vals]

    d = d[[group_column, value_column]].dropna()
    if log_scale:
        d = d[d[value_column] > 0]

    if show_n:
        n = d.groupby(group_column)[value_column].size()
        d["group_label"] = d[group_column].map(lambda g: f"{g} (n={n[g]})")
    else:
        d["group_label"] = d[group_column]

    order = (
        d.groupby("group_label")[value_column]
        .agg(sort_by)
        .sort_values(ascending=False)
        .index.tolist()
        if sort_by in ("median", "mean")
        else d["group_label"].drop_duplicates().tolist()
    )

    return (
        alt.Chart(d)
        .mark_boxplot(
            extent=1.5 if show_outliers else "min-max",
            size=28,
            opacity=0.65,
            median=dict(color="#111827", size=28),
            rule=dict(color="#6B7280", opacity=0.8),
            outliers=dict(size=25, color="#6B7280") if show_outliers else False,
        )
        .encode(
            x=alt.X(
                f"{value_column}:Q",
                title=x_title or value_column.replace("_", " ").title(),
                scale=alt.Scale(type="log") if log_scale else alt.Scale(zero=True),
                axis=alt.Axis(
                    format=value_format,
                    grid=True,
                    gridColor="#E5E7EB",
                    labelColor="#6B7280",
                    titleColor="#374151",
                ),
            ),
            y=alt.Y(
                "group_label:N",
                sort=order,
                title=None,
                axis=alt.Axis(
                    labelFontSize=12, labelFontWeight=500, ticks=False, domain=False
                ),
            ),
            color=alt.Color(
                "group_label:N",
                legend=None,
                sort=order,
                scale=alt.Scale(range=colors) if colors else alt.Scale(),
            ),
        )
        .properties(
            width=width,
            height=height,
            title=alt.TitleParams(
                text=chart_title,
                subtitle=chart_subtitle,
                anchor="start",
                fontSize=16,
                fontWeight=600,
                color="#111827",
                subtitleFontSize=11,
                subtitleColor="#6B7280",
            ),
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont="Arial", titleFont="Arial")
        .configure_title(font="Arial")
    )


def breakdown_chart(
    df, year, component_columns, group_column, year_column, normalize=True, title=None
):
    """
    Creates a stacked bar chart showing expenditure composition
    by mode group for a selected year.

    Aggregates expenditure components across all agencies and
    service types. Amounts are displayed in millions.

    When normalized, each bar represents the percentage
    contribution of each expenditure component.

    """
    plot_df = (
        df[df[year_column] == year]
        .groupby(group_column)[component_columns]
        .sum(min_count=1)
        .reset_index()
        .melt(id_vars=group_column, var_name="component", value_name="amount")
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
        axis=alt.Axis(format=".0%") if normalize else alt.Axis(format=",.1f"),
        title="Share of Total" if normalize else "Amount ($M)",
    )

    return (
        alt.Chart(plot_df)
        .mark_bar(cornerRadius=2)
        .encode(
            x=alt.X(f"{group_column}:N", title="Mode", axis=alt.Axis(labelAngle=0)),
            y=y_enc,
            color=alt.Color(
                "component:N",
                title="Component",
                scale=alt.Scale(scheme="pastel2"),
                legend=alt.Legend(orient="bottom", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title="Mode"),
                alt.Tooltip("component:N", title="Component"),
                alt.Tooltip("amount:Q", title="Amount ($M)", format=",.1f"),
            ],
        )
        .properties(
            width=500,
            height=350,
            title=alt.TitleParams(
                text=title or f"Composition by Mode, {year}",
                fontSize=16,
                fontWeight=600,
                color="#111827",
                anchor="start",
            ),
        )
    )


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
    """
    Creates three side-by-side horizontal bar charts comparing
    three metrics across groups.
    """
    titles = titles or metrics
    x_labels = x_labels or metrics
    subtitles = subtitles or [""] * len(metrics)
    colors = colors or ["#3B82F6", "#10B981", "#F59E0B"]
    formats = formats or [".2f"] * len(metrics)
    charts = []
    order = df[group_column].drop_duplicates().tolist()

    for metric, title, xlabel, subtitle, color, fmt in zip(
        metrics, titles, x_labels, subtitles, colors, formats
    ):
        d = df[[group_column, metric]].dropna().copy()
        d["is_max"] = d[metric] == d[metric].max()

        bars = (
            alt.Chart(d)
            .mark_bar(cornerRadiusEnd=6, height=28)
            .encode(
                x=alt.X(
                    f"{metric}:Q",
                    title=xlabel,
                    axis=alt.Axis(
                        grid=True,
                        gridColor="#E5E7EB",
                        gridOpacity=0.7,
                        domain=False,
                        tickColor="#D1D5DB",
                        labelColor="#6B7280",
                        titleColor="#374151",
                        titleFontSize=12,
                        labelFontSize=11,
                        format=fmt,
                    ),
                ),
                y=alt.Y(
                    f"{group_column}:N",
                    sort=order,
                    title=None,
                    axis=alt.Axis(
                        labelColor="#374151",
                        labelFontSize=12,
                        labelFontWeight=500,
                        ticks=False,
                        domain=False,
                    ),
                ),
                color=alt.condition(
                    alt.datum.is_max, alt.value(color), alt.value("#D9E2EC")
                ),
                tooltip=[
                    alt.Tooltip(f"{group_column}:N", title=group_column),
                    alt.Tooltip(f"{metric}:Q", title=title, format=fmt),
                ],
            )
        )

        labels = (
            alt.Chart(d)
            .mark_text(
                align="left",
                baseline="middle",
                dx=7,
                fontSize=12,
                fontWeight="bold",
                color="#374151",
            )
            .encode(
                x=f"{metric}:Q",
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
                    fontSize=16,
                    fontWeight=600,
                    color="#111827",
                    subtitleFontSize=11,
                    subtitleColor="#6B7280",
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
                fontSize=22,
                fontWeight="bold",
                color="#111827",
                offset=20,
            )
        )

    return (
        chart.configure_view(strokeWidth=0)
        .configure_axis(labelFont="Arial", titleFont="Arial")
        .configure_title(font="Arial")
    )


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
            axis=alt.Axis(
                labelColor="#6B7280",
                titleColor="#374151",
                grid=True,
                gridColor="#E5E7EB",
                gridOpacity=0.7,
            ),
        ),
        "y": alt.Y(
            f"{y_variable}:Q",
            title=y_title or y_variable.replace("_", " ").title(),
            axis=alt.Axis(
                labelColor="#6B7280",
                titleColor="#374151",
                grid=True,
                gridColor="#E5E7EB",
                gridOpacity=0.7,
            ),
        ),
        "tooltip": tooltip_columns,
    }
    if group_column:
        enc["color"] = alt.Color(
            f"{group_column}:N", title=group_column.replace("_", " ").title()
        )
    if size_column:
        enc["size"] = alt.Size(
            f"{size_column}:Q",
            title=size_column.replace("_", " ").title(),
            scale=alt.Scale(range=[30, 800]),
        )

    return (
        alt.Chart(d)
        .mark_circle(opacity=0.8, stroke="white", strokeWidth=0.7)
        .encode(**enc)
        .properties(
            width=600,
            height=450,
            title=alt.TitleParams(
                text=chart_title,
                fontSize=16,
                fontWeight=600,
                color="#111827",
                anchor="start",
            ),
        )
    )


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
    Creates a heatmap comparing efficiency metrics across modes.

    Each metric is normalized independently using z-scores or
    percentage of maximum values.

    Missing values are preserved and excluded from normalization.

    reverse_scale reverses the interpretation of selected metrics,
    so lower costs receive a more favorable score.

    Final visualization grain:
        one row per mode × metric.
    """
    df_plot = df.copy()

    if year_column is not None and year is not None:
        df_plot = df_plot[df_plot[year_column] == year]

    titles = titles or metrics

    if isinstance(reverse_scale, bool):
        reverse_flags = [reverse_scale] * len(metrics)
    else:
        reverse_flags = list(reverse_scale)

    if len(titles) != len(metrics) or len(reverse_flags) != len(metrics):
        raise ValueError("Titles and reverse_scale must match metrics.")

    # Aggregate by mode
    agg = df_plot.groupby(group_column, as_index=False)[metrics].mean()

    # Ensure numeric metric values
    for col in metrics:
        agg[col] = pd.to_numeric(agg[col], errors="coerce")

    # Reshape to long format
    long = agg.melt(
        id_vars=group_column,
        value_vars=metrics,
        var_name="metric",
        value_name="raw_value",
    )

    # Normalize each metric independently
    if normalize == "zscore":

        def zscore(x):
            valid = x.dropna().astype(float)
            std = valid.std()

            if len(valid) < 2 or pd.isna(std) or std == 0:
                return pd.Series(np.nan, index=x.index)

            return (x.astype(float) - valid.mean()) / std

        long["norm_value"] = long.groupby("metric")["raw_value"].transform(zscore)

        legend_title = "Standard deviations"

    elif normalize == "percent_of_max":
        long["norm_value"] = long.groupby("metric")["raw_value"].transform(
            lambda x: x / x.max() * 100
        )

        legend_title = "% of maximum"

    else:
        raise ValueError("normalize must be 'zscore' or 'percent_of_max'.")

    # Reverse selected metrics so lower costs score better
    reverse_map = dict(zip(metrics, reverse_flags))

    long["norm_value"] *= long["metric"].map(reverse_map).map({True: -1, False: 1})

    # Display labels
    long["metric_label"] = long["metric"].map(dict(zip(metrics, titles)))

    # Heatmap
    return (
        alt.Chart(long)
        .mark_rect(stroke="white", strokeWidth=2)
        .encode(
            x=alt.X(
                "metric_label:N",
                title=None,
                sort=titles,
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(
                f"{group_column}:N",
                title=None,
                sort=None,
            ),
            color=alt.Color(
                "norm_value:Q",
                title=legend_title,
                scale=alt.Scale(
                    scheme=color_scheme,
                    domainMid=0,
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title="Mode"),
                alt.Tooltip("metric_label:N", title="Metric"),
                alt.Tooltip(
                    "raw_value:Q",
                    title="Original Value",
                    format=",.2f",
                ),
                alt.Tooltip(
                    "norm_value:Q",
                    title="Standardized Score",
                    format=".2f",
                ),
            ],
        )
        .properties(
            width=width,
            height=height,
            title=chart_title,
        )
    )


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
    Creates an indexed line chart comparing variables
    to a base year.

    Aggregates across agencies before calculating indices.

    Final grain:
        one row per mode group × year.
    """

    labels = variable_labels or {
        c: c.replace("_", " ").title() for c in variable_columns
    }

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

    return (
        alt.Chart(long)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X(
                f"{time_column}:O",
                title=time_column.replace("_", " ").title(),
            ),
            y=alt.Y(
                "index:Q",
                title=f"Index ({base_year} = 100)",
            ),
            color=alt.Color(
                "metric:N",
                title=None,
                scale=alt.Scale(
                    domain=list(labels.values()),
                    range=colors,
                )
                if colors
                else None,
            ),
            detail="metric:N",
            tooltip=[
                group_column,
                time_column,
                "metric",
                alt.Tooltip("index:Q", format=".1f"),
            ],
        )
        .properties(width=250, height=180)
        .facet(
            f"{group_column}:N",
            columns=3,
            title=None,
        )
        .properties(
            title=alt.TitleParams(
                text=chart_title,
                subtitle=chart_subtitle,
                fontSize=18,
                fontWeight=600,
                anchor="start",
            )
        )
        .configure_view(strokeWidth=0)
    )


def comparison_bar_chart(
    df,
    calc1,
    calc2,
    title1,
    title2,
    x_title1,
    x_title2,
    tooltip1,
    tooltip2,
    color1="mode",
    color2="mode_full_name",
):
    return (
        alt.hconcat(
            alt.Chart(df)
            .transform_calculate(metric=calc1)
            .mark_bar()
            .encode(
                x=alt.X("metric:Q", title=x_title1),
                y=alt.Y("mode_full_name:N", sort="-x", title=None),
                color=alt.Color(f"{color1}:N", legend=None),
                tooltip=[
                    "mode_full_name:N",
                    alt.Tooltip("metric:Q", title=tooltip1, format=".1f"),
                ],
            )
            .properties(width=400, height=300, title=title1),
            alt.Chart(df)
            .transform_calculate(metric=calc2)
            .mark_bar()
            .encode(
                x=alt.X("metric:Q", title=x_title2),
                y=alt.Y("mode_full_name:N", sort="-x", title=None),
                color=alt.Color(f"{color2}:N", legend=None),
                tooltip=[
                    "mode_full_name:N",
                    alt.Tooltip("metric:Q", title=tooltip2, format=".1f"),
                ],
            )
            .properties(width=400, height=300, title=title2),
        )
        .resolve_scale(y="independent")
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont="Arial", titleFont="Arial")
        .configure_title(font="Arial")
    )


### AGENCY REPORT CHARTS ###


def _val(x):
    return str(x) if pd.notna(x) else "N/A"


def _wrap(text, px, font_size, bold=False):
    """Wrap text to roughly fit a pixel width (approximate char width)."""
    char_w = font_size * (0.62 if bold else 0.56)
    chars = max(8, int(px / char_w))
    return "\n".join(
        textwrap.wrap(str(text), width=chars, break_long_words=True)
    ) or str(text)


def _list_values(s):
    """Unique, cleaned, sorted values (numeric-aware, e.g. district 3.0 -> '3')."""
    out = set()
    for v in s.dropna():
        v = str(v).strip()
        if not v:
            continue
        try:
            f = float(v)
            v = str(int(f)) if f.is_integer() else v
        except ValueError:
            pass
        out.add(v)
    return sorted(
        out, key=lambda v: (0, int(v), v) if v.isdigit() else (1, 0, v.lower())
    )


def _joined(df, col, singular, plural):
    vals = _list_values(df[col]) if col in df.columns else []
    if not vals:
        return f"{singular}: N/A"
    return f"{singular if len(vals) == 1 else plural}: {', '.join(vals)}"


def history(g, col, label):
    h = g.dropna(subset=[col]).sort_values("year").copy()
    if h.empty:
        return f"{label} history unavailable"
    h[col] = h[col].astype(str).str.strip()
    h = h.drop_duplicates("year", keep="last")
    first, last = h.iloc[0], h.iloc[-1]
    start, end = int(first["year"]), int(last["year"])
    values = h[col].str.lower().unique()
    if len(values) == 1:
        return f"Always {last[col].lower()} ({start}–{end})"
    if col == "agency_status":
        s = h[col].str.lower()
        active_years = h.loc[s == "active", "year"]
        if last[col].lower() == "inactive" and not active_years.empty:
            return f"Sporadically active; currently inactive. Last active: {int(active_years.max())}"
        if last[col].lower() == "active" and (s == "inactive").any():
            return "Sporadically inactive; currently active"
    return f"{label} changed: {first[col]} ({start}) to {last[col]} ({end})"


def rtpa_profile_chart(df_opex, rtpa_name, width=1200):
    data = df_opex[df_opex["rtpa_name"].astype(str) == str(rtpa_name)].copy()
    if data.empty:
        raise ValueError(f"No RTPA found: {rtpa_name}")
    data["year"] = pd.to_numeric(data["year"], errors="coerce")
    data = data.dropna(subset=["year"])
    if data.empty:
        raise ValueError(f"No valid reporting years for {rtpa_name}")

    first_year, latest_year = int(data["year"].min()), int(data["year"].max())
    total_agencies = data["ntd_id"].nunique(dropna=False)
    rows = []

    for ntd_id, d in data.groupby(data["ntd_id"].astype(str)):
        d = d.sort_values("year")
        r = d.iloc[-1]
        has_pop = pd.notna(r.get("uza_population"))
        pop = f"{int(r['uza_population']):,}" if has_pop else "N/A"
        pop_year = f"Population {int(r['year'])}" if has_pop else "Population year N/A"
        rows.append(
            {
                "ntd_id": str(ntd_id),
                "label": f"{_val(r.get('source_agency'))} ({ntd_id})",
                "main_0": _val(r.get("source_agency")),
                "detail_0": f"NTD {ntd_id} · {_val(r.get('source_city'))}, {_val(r.get('source_state'))}",
                "main_1": _val(r.get("agency_status")),
                "detail_1": history(d, "agency_status", "Agency status"),
                "main_2": _val(r.get("reporter_type")),
                "detail_2": history(d, "reporter_type", "Reporter type"),
                "main_3": _val(r.get("primary_uza_name")),
                "detail_3": f"{pop_year}: {pop}",
            }
        )

    agencies = pd.DataFrame(rows).sort_values("label").reset_index(drop=True)

    # --- RTPA-level info (union across all reporting years) ---
    county_line = _joined(data, "county_name", "County", "Counties")
    district_line = _joined(
        data, "caltrans_district", "Caltrans District", "Caltrans Districts"
    )

    HDR = 100
    off = HDR - 72
    W = width
    one = pd.DataFrame({"_": [0]})

    xs, widths = [0.025, 0.37, 0.55, 0.74], [0.32, 0.18, 0.19, 0.235]
    headings = ["AGENCY", "AGENCY STATUS", "REPORTER TYPE", "URBANIZED AREA"]
    colors = [NAVY, TEAL, YELLOW, BLUE]

    TOP = 120 + off  # where the main text starts
    LINE_MAIN, LINE_DETAIL = 20, 15  # line heights in px

    for j, w in enumerate(widths):
        px = (w - 0.025) * W
        agencies[f"main_{j}_w"] = agencies[f"main_{j}"].map(
            lambda t: _wrap(t, px, 16, bold=True)
        )
        agencies[f"detail_{j}_w"] = agencies[f"detail_{j}"].map(
            lambda t: _wrap(t, px, 12)
        )
        # detail starts just below however many lines the main text takes
        agencies[f"detail_y_{j}"] = (
            TOP + (agencies[f"main_{j}_w"].str.count("\n") + 1) * LINE_MAIN + 16
        )
        agencies[f"bottom_{j}"] = (
            agencies[f"detail_y_{j}"]
            + (agencies[f"detail_{j}_w"].str.count("\n") + 1) * LINE_DETAIL
        )

    # panel height grows to fit the longest agency
    H = int(
        max(250 + off, agencies[[f"bottom_{j}" for j in range(4)]].max().max() + 20)
    )

    def rect(x0, x1, y0, y1, color):
        return (
            alt.Chart(one)
            .mark_rect(color=color)
            .encode(
                x=alt.value(x0), x2=alt.value(x1), y=alt.value(y0), y2=alt.value(y1)
            )
        )

    def label(text, x, y, **kw):
        return (
            alt.Chart(one)
            .mark_text(font=FONT, baseline="middle", **kw)
            .encode(x=alt.value(x), y=alt.value(y), text=alt.value(text))
        )

    static = [
        rect(0, W, 0, HDR, NAVY),
        rect(0, W, 0, 3, TEAL),
        rect(0, W, HDR, H, "#fafbfb"),
        label(
            "REGIONAL PROFILE / RTPA",
            26,
            16,
            align="left",
            color="#b1e4e3",
            fontSize=11,
            fontWeight="bold",
        ),
        label(
            rtpa_name,
            24,
            40,
            align="left",
            color="white",
            fontSize=22,
            fontWeight="bold",
        ),
        label(
            county_line, 24, 66, align="left", color="white", fontSize=12, limit=W - 48
        ),
        label(
            district_line,
            24,
            84,
            align="left",
            color="white",
            fontSize=12,
            limit=W - 48,
        ),
        label(
            f"{total_agencies} {'agency' if total_agencies == 1 else 'agencies'} · Reporting years {first_year}–{latest_year}",
            W - 24,
            40,
            align="right",
            color="white",
            fontSize=12,
        ),
    ]

    for x, w, h, c in zip(xs, widths, headings, colors):
        static.append(
            label(
                h,
                x * W,
                91 + off,
                align="left",
                color=TEAL,
                fontSize=12,
                fontWeight="bold",
            )
        )
        static.append(rect(x * W, min((x + w) * W, W - 12), 105 + off, 108 + off, c))

    agency_param = alt.param(
        name="agency_sel",
        value=str(agencies["ntd_id"].iloc[0]),
        bind=alt.binding_select(
            options=[str(x) for x in agencies["ntd_id"]],
            labels=list(agencies["label"]),
            name="Agency: ",
        ),
    )

    dynamic = []
    for j, (x, w) in enumerate(zip(xs, widths)):
        dynamic.append(
            alt.Chart(agencies)
            .mark_text(
                font=FONT,
                align="left",
                baseline="top",
                lineBreak="\n",
                color=NAVY,
                fontSize=16,
                fontWeight="bold",
            )
            .encode(
                x=alt.value(x * W),
                y=alt.value(TOP),
                text=f"main_{j}_w",
                tooltip=f"main_{j}",
            )
            .transform_filter(alt.datum.ntd_id == agency_param)
        )
        dynamic.append(
            alt.Chart(agencies)
            .mark_text(
                font=FONT,
                align="left",
                baseline="top",
                lineBreak="\n",
                color=GREY,
                fontSize=12,
            )
            .encode(
                x=alt.value(x * W),
                y=alt.Y(f"detail_y_{j}:Q", scale=None),
                text=f"detail_{j}_w",
                tooltip=f"detail_{j}",
            )
            .transform_filter(alt.datum.ntd_id == agency_param)
        )

    chart = (
        alt.layer(*static, *dynamic)
        .properties(width=W, height=H)
        .add_params(agency_param)
        .configure_view(stroke=None)
    )

    return chart, agency_param


def rtpa_ntd_value_profile(datasets, rtpa, width=400, height=300):
    """RTPA dashboard with a shared agency dropdown and responsive chart layout."""
    group_cols = ["source_agency", "ntd_id", "year"]
    aggregated, agencies = {}, set()

    for value_col, df in datasets.items():
        d = df[df["rtpa_name"] == rtpa].copy()
        if d.empty:
            raise ValueError(f"No rows found for rtpa_name={rtpa!r} in {value_col}")
        missing = [c for c in group_cols + [value_col] if c not in d.columns]
        if missing:
            raise ValueError(f"Missing columns in {value_col}: {missing}")
        aggregated[value_col] = d.groupby(group_cols, as_index=False)[value_col].sum()
        agencies.update(d["source_agency"].dropna().unique())

    if not aggregated:
        raise ValueError("No datasets provided.")

    agencies = sorted(agencies)
    agency_sel = alt.selection_point(
        name="Agency",
        fields=["source_agency"],
        bind=alt.binding_select(
            options=[None] + agencies,
            labels=["All agencies"] + agencies,
            name="FOCUS AGENCY  ▼  ",
        ),
    )

    charts = []
    for i, (value_col, agg) in enumerate(aggregated.items()):
        agg = agg.rename(columns={value_col: "value"})
        chart = (
            alt.Chart(agg)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y(
                    "value:Q",
                    title=value_col.replace("_", " ").title(),
                    axis=alt.Axis(format="~s"),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(
                    "source_agency:N",
                    scale=alt.Scale(domain=agencies, scheme="tableau20"),
                    legend=None,
                ),
                tooltip=[
                    "source_agency:N",
                    "year:O",
                    alt.Tooltip("value:Q", format=","),
                ],
            )
            .transform_filter(agency_sel)
            .properties(
                width=width * 2 if i == 0 else width,
                height=height,
                title=value_col.replace("_", " ").title(),
            )
        )
        charts.append(chart)

    rows = [charts[0]]
    rows.extend(
        alt.hconcat(*charts[i : i + 2], spacing=20) for i in range(1, len(charts), 2)
    )

    dashboard = (
        alt.vconcat(*rows, spacing=25)
        .add_params(agency_sel)
        .resolve_scale(y="independent")
        .properties(title="1.1 Ridership, OPEX, CAPEX, VRH and VRM Trend")
        .configure_view(strokeWidth=0, fill="white")
        .configure_axis(labelFont="Arial", titleFont="Arial")
        .configure_title(font="Arial")
    )
    return dashboard, agency_sel
