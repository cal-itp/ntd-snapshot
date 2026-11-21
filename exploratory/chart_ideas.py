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

ALT_AXIS_CONFIG = {
    "labelFont": "Arial",
    "titleFont": "Arial",
    "labelFontSize": 13,
    "titleFontSize": 15,
    "labelColor": "#374151",
    "titleColor": "#111827",
    "labelFontWeight": 500,
    "titleFontWeight": 600,
    "domainColor": "#9CA3AF",
    "tickColor": "#9CA3AF",
}


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
    """Interactive ridge plot showing distributions across categories with year selection."""

    d = df.copy()

    if filters:
        for col, vals in filters.items():
            d = d[d[col].isin(vals)] if isinstance(vals, list) else d[d[col] == vals]

    d = d[d[value_column].notna()]
    if value_min is not None:
        d = d[d[value_column] >= value_min]
    if value_max is not None:
        d = d[d[value_column] <= value_max]

    year_sel = None
    if year_column:
        years = sorted(d[year_column].dropna().unique().tolist())
        if not years:
            raise ValueError("No valid years found.")
        selected_year = year if year is not None else years[-1]
        if selected_year not in years:
            raise ValueError(f"Year {selected_year!r} not found in data.")

        year_sel = alt.selection_point(
            name="Year",
            fields=[year_column],
            bind=alt.binding_select(options=years, name="Year "),
            value=[{year_column: selected_year}],
        )

    chart = alt.Chart(d, width=800, height=step)
    if year_sel is not None:
        chart = chart.transform_filter(year_sel)

    ridge = (
        chart.transform_density(
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
        .properties(bounds="flush")
    )

    if year_sel is not None:
        subtitle = (
            alt.Chart(d)
            .transform_filter(year_sel)
            .transform_aggregate(selected_year=f"max({year_column})")
            .transform_calculate(
                subtitle=f"'{chart_subtitle or ''} | ' + toString(datum.selected_year)"
            )
            .mark_text(align="left", baseline="middle", fontSize=12, color="#666")
            .encode(text="subtitle:N")
            .properties(width=800, height=20)
        )

        chart = alt.vconcat(subtitle, ridge, spacing=2).add_params(year_sel)
        chart = chart.properties(
            title=alt.TitleParams(text=chart_title, anchor="start")
        )
    else:
        chart = ridge.properties(
            title=alt.TitleParams(
                text=chart_title, subtitle=chart_subtitle, anchor="start"
            )
        )

    return chart.configure_facet(spacing=0).configure_view(stroke=None)


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

        bars = (
            alt.Chart(d)
            .mark_bar(cornerRadiusEnd=6, height=28, color=color)
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
    char_w = font_size * (0.62 if bold else 0.56)
    chars = max(8, int(px / char_w))
    return "\n".join(
        textwrap.wrap(str(text), width=chars, break_long_words=True)
    ) or str(text)


def _list_values(s):
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
    return f"{singular if len(vals) == 1 else plural}: {', '.join(vals) if vals else 'N/A'}"


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
        active = h.loc[s == "active", "year"]
        if last[col].lower() == "inactive" and not active.empty:
            return f"Sporadically active; currently inactive. Last active: {int(active.max())}"
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

    first_year, latest_year = int(data.year.min()), int(data.year.max())
    total_agencies = data["ntd_id"].nunique()
    rows = []

    for ntd_id, d in data.groupby(data["ntd_id"].astype(str)):
        d = d.sort_values("year")
        r = d.iloc[-1]
        pop = r.get("uza_population")
        has_pop = pd.notna(pop)

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
                "detail_3": f"Population {int(r['year'])}: {int(pop):,}"
                if has_pop
                else "Population N/A",
            }
        )

    agencies = pd.DataFrame(rows).sort_values("label").reset_index(drop=True)

    county_line = _joined(data, "county_name", "County", "Counties")
    district_line = _joined(
        data, "caltrans_district", "Caltrans District", "Caltrans Districts"
    )

    # Operating structure: latest year, weighted by vehicle revenue hours
    service_map = {"DO": "DIRECTLY OPERATED", "PT": "PURCHASED"}

    service = data[data["year"] == latest_year].copy()
    service["service_type"] = (
        service["type_of_service"].astype(str).str.strip().str.upper()
    )
    service["service_type"] = service["service_type"].map(service_map)

    operating = (
        service.dropna(subset=["service_type"])
        .groupby([service["ntd_id"].astype(str), "service_type"])[
            "vehicle_revenue_hours"
        ]
        .sum()
        .unstack(fill_value=0)
        .reindex(columns=["DIRECTLY OPERATED", "PURCHASED"], fill_value=0)
    )

    operating["total"] = operating.sum(axis=1)
    operating["direct_pct"] = (
        operating["DIRECTLY OPERATED"].div(operating["total"].replace(0, np.nan)) * 100
    )
    operating["purchased_pct"] = (
        operating["PURCHASED"].div(operating["total"].replace(0, np.nan)) * 100
    )

    agencies = agencies.merge(
        operating[["direct_pct", "purchased_pct"]],
        left_on="ntd_id",
        right_index=True,
        how="left",
    )

    # Layout
    HDR, off, W = 100, 28, width
    TOP = 120 + off
    LINE_MAIN, LINE_DETAIL = 20, 15
    one = pd.DataFrame({"_": [0]})

    xs, widths = [0.025, 0.37, 0.55, 0.74], [0.32, 0.18, 0.19, 0.235]
    headings = ["AGENCY", "AGENCY STATUS", "REPORTER TYPE", "URBANIZED AREA"]
    colors = [NAVY, TEAL, YELLOW, BLUE]

    for j, w in enumerate(widths):
        px = (w - 0.025) * W
        agencies[f"main_{j}_w"] = agencies[f"main_{j}"].map(
            lambda t: _wrap(t, px, 16, True)
        )
        agencies[f"detail_{j}_w"] = agencies[f"detail_{j}"].map(
            lambda t: _wrap(t, px, 12)
        )
        agencies[f"detail_y_{j}"] = (
            TOP + (agencies[f"main_{j}_w"].str.count("\n") + 1) * LINE_MAIN + 16
        )
        agencies[f"bottom_{j}"] = (
            agencies[f"detail_y_{j}"]
            + (agencies[f"detail_{j}_w"].str.count("\n") + 1) * LINE_DETAIL
        )

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
            f"{total_agencies} agencies · Reporting years {first_year}–{latest_year}",
            W - 24,
            40,
            align="right",
            color="white",
            fontSize=12,
        ),
    ]

    for x, w, heading, color in zip(xs, widths, headings, colors):
        static += [
            label(
                heading,
                x * W,
                91 + off,
                align="left",
                color=TEAL,
                fontSize=12,
                fontWeight="bold",
            ),
            rect(x * W, min((x + w) * W, W - 12), 105 + off, 108 + off, color),
        ]

    agency_param = alt.param(
        name="agency_sel",
        value=str(agencies["ntd_id"].iloc[0]),
        bind=alt.binding_select(
            options=agencies["ntd_id"].tolist(),
            labels=agencies["label"].tolist(),
            name="Agency: ",
        ),
    )

    dynamic = []
    for j, x in enumerate(xs):
        dynamic.extend(
            [
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
                .transform_filter(alt.datum.ntd_id == agency_param),
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
                .transform_filter(alt.datum.ntd_id == agency_param),
            ]
        )

    # Operating structure bar
    bar_data = agencies.melt(
        id_vars=["ntd_id"],
        value_vars=["direct_pct", "purchased_pct"],
        var_name="type",
        value_name="percentage",
    ).dropna(subset=["percentage"])

    bar_data["type"] = bar_data["type"].map(
        {"direct_pct": "DIRECTLY OPERATED", "purchased_pct": "PURCHASED"}
    )

    bar = (
        alt.Chart(bar_data)
        .transform_filter(alt.datum.ntd_id == agency_param)
        .mark_bar(size=24)
        .encode(
            x=alt.X(
                "percentage:Q",
                stack="zero",
                scale=alt.Scale(domain=[0, 100]),
                axis=None,
            ),
            color=alt.Color(
                "type:N",
                scale=alt.Scale(
                    domain=["DIRECTLY OPERATED", "PURCHASED"],
                    range=["#25855A", "#E5A000"],
                ),
                legend=None,
            ),
            order=alt.Order("type:N", sort="ascending"),
            tooltip=[
                alt.Tooltip("type:N", title="Operating structure"),
                alt.Tooltip("percentage:Q", title="Share of VRH", format=".1f"),
            ],
        )
        .properties(width=450, height=28)
    )

    title = label(
        "AGENCY OPERATING STRUCTURE",
        0,
        12,
        align="left",
        color=NAVY,
        fontSize=13,
        fontWeight="bold",
    ).properties(width=450, height=25)

    percentages = (
        alt.Chart(bar_data)
        .transform_filter(alt.datum.ntd_id == agency_param)
        .transform_calculate(label="format(datum.percentage, '.1f') + '%'")
        .mark_text(font=FONT, fontSize=12, fontWeight="bold")
        .encode(
            x=alt.X("type:N", axis=None),
            text="label:N",
            color=alt.Color(
                "type:N",
                scale=alt.Scale(
                    domain=["DIRECTLY OPERATED", "PURCHASED"], range=[TEAL, YELLOW]
                ),
                legend=None,
            ),
            tooltip=[
                "type:N",
                alt.Tooltip("percentage:Q", format=".1f", title="Share (%)"),
            ],
        )
        .properties(width=450, height=22)
    )

    structure_labels = (
        alt.Chart(pd.DataFrame({"type": ["DIRECTLY OPERATED", "PURCHASED"]}))
        .mark_text(font=FONT, fontSize=10, color=GREY)
        .encode(x=alt.X("type:N", axis=None), text="type:N")
        .properties(width=450, height=20)
    )

    operating_section = alt.vconcat(
        title, bar, percentages, structure_labels, spacing=4
    )

    chart = (
        alt.vconcat(
            alt.layer(*static, *dynamic).properties(width=W, height=H),
            operating_section,
            spacing=12,
        )
        .add_params(agency_param)
        .configure_view(stroke=None)
    )

    return chart, agency_param


def rtpa_breakdown_chart(
    df,
    rtpa,
    component_columns,
    group_column="mode_group",
    agency_column="source_agency",
    rtpa_column="rtpa_name",
    year_column="year",
    normalize=True,
    width=500,
    height=350,
    title=None,
):
    """Interactive stacked bar chart with RTPA, agency, and year selection."""
    required = [
        rtpa_column,
        year_column,
        agency_column,
        group_column,
        *component_columns,
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    d = df.loc[df[rtpa_column] == rtpa].copy()
    if d.empty:
        raise ValueError(f"No rows found for RTPA={rtpa!r}")

    agencies = sorted(d[agency_column].dropna().unique().tolist())
    years = sorted(d[year_column].dropna().unique().tolist())

    if not years:
        raise ValueError(f"No valid years found for RTPA={rtpa!r}")

    plot_df = d.groupby(
        [year_column, agency_column, group_column], as_index=False, dropna=False
    )[component_columns].sum()
    plot_df = plot_df.melt(
        id_vars=[year_column, agency_column, group_column],
        var_name="component",
        value_name="amount",
    )
    plot_df["amount"] /= 1_000_000
    plot_df["component"] = (
        plot_df["component"].str.replace("_", " ", regex=False).str.title()
    )

    agency_sel = alt.selection_point(
        name="Agency",
        fields=[agency_column],
        bind=alt.binding_select(
            options=agencies,
            name="Agency  ",
        ),
        value=[{agency_column: agencies[0]}],
    )
    year_sel = alt.selection_point(
        name="Year",
        fields=[year_column],
        bind=alt.binding_select(options=years, name="Year "),
        value=[{year_column: years[-1]}],
    )

    chart = (
        alt.Chart(plot_df)
        .mark_bar(cornerRadius=2)
        .encode(
            x=alt.X(f"{group_column}:N", title="Mode", axis=alt.Axis(labelAngle=0)),
            y=alt.Y(
                "amount:Q",
                stack="normalize" if normalize else "zero",
                axis=alt.Axis(format=".0%" if normalize else ",.1f"),
                title="Share of Total" if normalize else "Amount ($M)",
            ),
            color=alt.Color(
                "component:N",
                title="Component",
                scale=alt.Scale(scheme="pastel2"),
                legend=alt.Legend(orient="bottom", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip(f"{year_column}:O", title="Year"),
                alt.Tooltip(f"{agency_column}:N", title="Agency"),
                alt.Tooltip(f"{group_column}:N", title="Mode"),
                alt.Tooltip("component:N", title="Component"),
                alt.Tooltip("amount:Q", title="Amount ($M)", format=",.1f"),
            ],
        )
        .transform_filter(agency_sel)
        .transform_filter(year_sel)
        .add_params(agency_sel, year_sel)
        .properties(
            width=width,
            height=height,
            title=alt.TitleParams(
                text=title or "Expenditure Composition by Mode — Selected Agency",
                fontSize=16,
                fontWeight=600,
                color="#111827",
                anchor="start",
            ),
        )
    )
    return chart, agency_sel, year_sel


def rtpa_funding_composition(
    df,
    rtpa,
    components,
    agency_column="source_agency",
    rtpa_column="rtpa_name",
    year_column="year",
    normalize=True,
    width=500,
    height=350,
    title=None,
):
    """Interactive stacked funding composition chart with agency and year selection."""

    component_columns = [c for cols in components.values() for c in cols]
    required = [rtpa_column, year_column, agency_column, *component_columns]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    d = df.loc[df[rtpa_column] == rtpa].copy()
    if d.empty:
        raise ValueError(f"No rows found for RTPA={rtpa!r}")

    agencies = sorted(d[agency_column].dropna().unique().tolist())
    years = sorted(d[year_column].dropna().unique().tolist())
    if not agencies or not years:
        raise ValueError(f"No valid agencies or years found for RTPA={rtpa!r}")

    plot_df = d.groupby([year_column, agency_column], as_index=False, dropna=False)[
        component_columns
    ].sum()
    plot_df = plot_df.melt(
        id_vars=[year_column, agency_column], var_name="component", value_name="amount"
    )
    plot_df["amount"] /= 1_000_000

    component_lookup = {
        col: funding_type for funding_type, cols in components.items() for col in cols
    }
    plot_df["funding_type"] = plot_df["component"].map(component_lookup)
    plot_df["component"] = (
        plot_df["component"]
        .str.replace(r"^(operating_|capital_)", "", regex=True)
        .str.replace("_", " ", regex=False)
        .str.title()
    )

    agency_sel = alt.selection_point(
        name="Agency",
        fields=[agency_column],
        bind=alt.binding_select(options=agencies, name="Agency  "),
        value=[{agency_column: agencies[0]}],
    )
    year_sel = alt.selection_point(
        name="Year",
        fields=[year_column],
        bind=alt.binding_select(options=years, name="Year "),
        value=[{year_column: years[-1]}],
    )

    chart = (
        alt.Chart(plot_df)
        .mark_bar(cornerRadius=2)
        .encode(
            x=alt.X(
                "funding_type:N",
                title=None,
                sort=list(components.keys()),
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(
                "amount:Q",
                stack="normalize" if normalize else "zero",
                axis=alt.Axis(format=".0%" if normalize else ",.1f"),
                title="Share of Total" if normalize else "Amount ($M)",
            ),
            color=alt.Color(
                "component:N",
                title="Funding Source",
                scale=alt.Scale(scheme="pastel2"),
                legend=alt.Legend(orient="bottom", direction="horizontal"),
            ),
            tooltip=[
                alt.Tooltip(f"{year_column}:O", title="Year"),
                alt.Tooltip(f"{agency_column}:N", title="Agency"),
                alt.Tooltip("funding_type:N", title="Funding Type"),
                alt.Tooltip("component:N", title="Funding Source"),
                alt.Tooltip("amount:Q", title="Amount ($M)", format=",.1f"),
            ],
        )
        .transform_filter(agency_sel)
        .transform_filter(year_sel)
        .add_params(agency_sel, year_sel)
        .properties(
            width=width,
            height=height,
            title=alt.TitleParams(
                text=title or "Funding Composition by Selected Agency",
                fontSize=16,
                fontWeight=600,
                color="#111827",
                anchor="start",
            ),
        )
    )

    return chart, agency_sel, year_sel


def rtpa_ntd_value_profile(datasets, rtpa, width=400, height=300, chart_titles=None):
    """RTPA dashboard with shared agency dropdown and dynamic agency subtitles."""
    group_cols = ["source_agency", "ntd_id", "year"]
    aggregated, agencies = {}, set()
    chart_titles = chart_titles or {}

    for value_col, (df, chart_title) in datasets.items():
        d = df[df["rtpa_name"] == rtpa].copy()
        if d.empty:
            raise ValueError(f"No rows found for rtpa_name={rtpa!r} in {value_col}")
        missing = [c for c in group_cols + [value_col] if c not in d.columns]
        if missing:
            raise ValueError(f"Missing columns in {value_col}: {missing}")
        aggregated[value_col] = (
            d.groupby(group_cols, as_index=False)[value_col].sum(),
            chart_titles.get(value_col, chart_title),
        )
        agencies.update(d["source_agency"].dropna().unique())

    if not aggregated:
        raise ValueError("No datasets provided.")

    agencies = sorted(agencies)
    agency_sel = alt.param(
        name="agency",
        value=None,
        bind=alt.binding_select(
            options=[None] + agencies,
            labels=["All agencies"] + agencies,
            name="Agency  ",
        ),
    )

    charts = []
    for i, (value_col, (agg, chart_title)) in enumerate(aggregated.items()):
        agg = agg.rename(columns={value_col: "value"})
        chart_title = chart_titles.get(value_col, chart_title)
        chart_width = width * 2 if i == 0 else width

        subtitle = (
            alt.Chart({"values": [{}]})
            .transform_calculate(t="agency ? agency : 'All agencies'")
            .mark_text(align="left", fontSize=12, color="#7656A5")
            .encode(x=alt.value(0), y=alt.value(12), text="t:N")
            .properties(width=chart_width, height=20)
        )

        chart = (
            alt.Chart(agg)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("year:O", title="Year"),
                y=alt.Y(
                    "value:Q",
                    title=chart_title,
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
            .transform_filter("!agency || datum.source_agency == agency")
            .properties(width=chart_width, height=height, title=chart_title)
        )
        charts.append(alt.vconcat(subtitle, chart, spacing=0))

    rows = [charts[0]]
    rows.extend(
        alt.hconcat(*charts[i : i + 2], spacing=20) for i in range(1, len(charts), 2)
    )

    dashboard = (
        alt.vconcat(*rows, spacing=25)
        .add_params(agency_sel)
        .resolve_scale(y="independent")
        .configure_view(strokeWidth=0, fill="white")
        .configure_axis(labelFont="Arial", titleFont="Arial")
        .configure_title(font="Arial")
    )
    return dashboard, agency_sel


def create_grouped_ranking_chart(
    df,
    metrics,
    groups,
    group_col="peer_group",
    filter_col=None,
    filter_value=None,
    panel_w=380,
    bar_step=22,
):
    years = sorted(df["year"].unique())
    modes = sorted(df["mode_full_name"].dropna().unique())
    pool = (
        df[df[filter_col] == filter_value]
        if filter_col and filter_value is not None
        else df
    )
    default_mode = pool["mode_full_name"].value_counts().idxmax()

    year_p = alt.param(
        name="year_sel",
        value=int(years[-1]),
        bind=alt.binding_select(options=[int(y) for y in years], name="Year:"),
    )
    mode_p = alt.param(
        name="mode_sel",
        value=default_mode,
        bind=alt.binding_select(options=modes, name="Mode:"),
    )

    colors = [TEAL, BLUE, YELLOW, GREY]

    def panel(group, metric, color):
        filters = [
            f"datum[{repr(group_col)}] == {repr(group)}",
            "datum.year == year_sel",
            "datum.mode_full_name == mode_sel",
        ]
        if filter_col and filter_value is not None:
            filters.append(f"datum[{repr(filter_col)}] == {repr(filter_value)}")

        base = (
            alt.Chart(df)
            .transform_filter(" && ".join(filters))
            .transform_window(
                rank="rank()", sort=[alt.SortField(metric, order="descending")]
            )
            .transform_calculate(value_label=f"'$' + format(datum.{metric}, ',.2f')")
        )

        y = alt.Y(
            "source_agency:N",
            title=None,
            sort=alt.EncodingSortField(field="rank", order="ascending"),
            axis=alt.Axis(labelLimit=180, ticks=False, domain=False),
        )

        bars = base.mark_bar(cornerRadiusEnd=3, height=15).encode(
            x=alt.X(
                metric + ":Q",
                title=None,
                axis=alt.Axis(grid=True, gridColor=BORDER, tickCount=4, format="$,.0f"),
            ),
            y=y,
            color=alt.value(color),
            tooltip=[
                "source_agency:N",
                alt.Tooltip(metric + ":Q", format="$.2f"),
                "rank:Q",
            ],
        )

        labels = base.mark_text(align="left", dx=5, fontSize=11, color=NAVY).encode(
            x=metric + ":Q", y=y, text="value_label:N"
        )

        return alt.layer(bars, labels).properties(
            width=panel_w,
            height=alt.Step(bar_step),
            title=alt.Title(str(group), fontSize=14, fontWeight="bold", anchor="start"),
        )

    rows = []
    for metric, title in metrics.items():
        first = panel(groups[0], metric, colors[0])
        others = alt.vconcat(
            *[
                panel(g, metric, colors[i % len(colors)])
                for i, g in enumerate(groups[1:], start=1)
            ],
            spacing=5,
        )
        rows.append(
            alt.hconcat(first, others, spacing=20)
            .resolve_scale(x="shared", y="independent")
            .properties(
                title=alt.Title(
                    text=alt.ExprRef(
                        expr=f"{repr(title + ' | ')} + mode_sel + ' | ' + year_sel"
                    ),
                    fontSize=17,
                    fontWeight="bold",
                    color=NAVY,
                )
            )
        )

    return (
        alt.vconcat(*rows, spacing=15)
        .add_params(year_p, mode_p)
        .configure_view(stroke=None)
        .configure_axis(**ALT_AXIS_CONFIG)
        .configure_title(color=NAVY, font=FONT)
        .configure_concat(spacing=15)
    )


def plot_agency_opex_dashboard(
    df,
    rtpa,
    agency_col="source_agency",
    rtpa_col="rtpa_name",
    type_col="rural_urban",
    year_col="year",
    mode_col="mode_full_name",
    width=850,
    dashboard_title="Agency Opex Performance",
):
    d = df[df[rtpa_col] == rtpa].dropna(subset=[agency_col, type_col, mode_col]).copy()
    years = sorted(d[year_col].dropna().unique().tolist())
    agencies = sorted(d[agency_col].dropna().unique().tolist())
    modes = sorted(d[mode_col].dropna().unique().tolist())

    if not years or not agencies or not modes:
        raise ValueError(f"No valid data found for {rtpa}.")

    yp = alt.param(
        name="yr",
        value=int(years[-1]),
        bind=alt.binding_select(options=[int(y) for y in years], name="Year: "),
    )
    ap = alt.param(
        name="agency",
        value=agencies[0],
        bind=alt.binding_select(options=agencies, name="Agency: "),
    )
    mp = alt.param(
        name="mode",
        value=modes[0],
        bind=alt.binding_select(options=modes, name="Mode group: "),
    )

    metrics = [
        ("hhi", "Expense Concentration", ".2f"),
        ("per_capita", "Spending per Capita", "$,.0f"),
        ("volatility", "Spending Volatility", ".1%"),
    ]
    colors = alt.Scale(domain=["Rural", "Urban"], range=["#25855A", "#E5A000"])
    charts, cards = [], []

    for m, title, fmt in metrics:
        base = alt.Chart(d).transform_filter(
            f"datum[{repr(year_col)}] == yr && datum[{repr(mode_col)}] == mode && isValid(datum.{m})"
        )
        selected = base.transform_filter(f"datum[{repr(agency_col)}] == agency")

        cards.append(
            selected.transform_aggregate(value=f"mean({m})")
            .mark_text(fontSize=25, fontWeight="bold", color="#7656A5")
            .encode(text=alt.Text("value:Q", format=fmt))
            .properties(
                width=width / 3 - 15,
                height=40,
                title=alt.Title(title, anchor="start", fontSize=12, color="#667085"),
            )
        )

        axis_y = alt.Y(
            type_col + ":N",
            title=None,
            sort=["Rural", "Urban"],
            scale=alt.Scale(paddingInner=0.3, paddingOuter=0.3),
            axis=alt.Axis(labelPadding=12, labelLimit=150),
        )

        median = (
            base.transform_aggregate(median_value=f"median({m})", groupby=[type_col])
            .mark_tick(color="#555555", thickness=3, size=20)
            .encode(
                x=alt.X("median_value:Q", axis=alt.Axis(format=fmt, title=None)),
                y=axis_y,
            )
        )

        points = (
            base.transform_calculate(selected=f"datum[{repr(agency_col)}] == agency")
            .mark_circle(stroke="white", strokeWidth=1.5, opacity=0.95)
            .encode(
                x=alt.X(
                    m + ":Q", title=None, axis=alt.Axis(format=fmt, gridColor="#E9ECF2")
                ),
                y=axis_y,
                color=alt.condition(
                    "datum.selected",
                    alt.value("#7656A5"),
                    alt.Color(type_col + ":N", scale=colors, legend=None),
                ),
                size=alt.condition("datum.selected", alt.value(200), alt.value(85)),
                tooltip=[
                    alt.Tooltip(agency_col + ":N", title="Agency"),
                    alt.Tooltip(type_col + ":N", title="Classification"),
                    alt.Tooltip(m + ":Q", title=title, format=fmt),
                ],
            )
        )

        charts.append(
            alt.layer(median, points).properties(
                width=width,
                height=75,
                title=alt.Title(
                    title,
                    anchor="start",
                    fontSize=15,
                    fontWeight="bold",
                    color="#24324A",
                ),
            )
        )

    header_title = (
        alt.Chart({"values": [{}]})
        .transform_calculate(
            t=f"{repr(dashboard_title + ' | ')} + toString(yr) + ' | ' + mode"
        )
        .mark_text(
            align="left",
            baseline="middle",
            fontSize=16,
            fontWeight="bold",
            color="#24324A",
        )
        .encode(x=alt.value(0), y=alt.value(12), text="t:N")
        .properties(width=width, height=55)
    )

    header_subtitle = (
        alt.Chart({"values": [{}]})
        .transform_calculate(t="agency")
        .mark_text(align="left", baseline="middle", fontSize=13, color="#667085")
        .encode(x=alt.value(0), y=alt.value(38), text="t:N")
        .properties(width=width, height=55)
    )

    header = alt.layer(header_title, header_subtitle)

    return (
        alt.vconcat(header, alt.hconcat(*cards, spacing=20), *charts, spacing=18)
        .add_params(yp, ap, mp)
        .configure_view(stroke=None)
        .configure_axis(**{**ALT_AXIS_CONFIG, "labelPadding": 12, "labelLimit": 150})
        .configure_title(font=FONT, anchor="start")
        .configure_concat(spacing=15)
    )


def agency_opex_service_growth(
    df,
    rtpa,
    metrics,
    agency_col="source_agency",
    rtpa_col="rtpa_name",
    mode_col="mode_full_name",
    year_col="year",
    width=750,
    height=320,
):
    d = df[df[rtpa_col] == rtpa].copy()
    required = [agency_col, mode_col, year_col] + list(metrics)
    missing = [c for c in required if c not in d.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    d = d.dropna(subset=[agency_col, mode_col, year_col])
    annual = (
        d.groupby([agency_col, mode_col, year_col], as_index=False)[list(metrics)]
        .sum()
        .sort_values([agency_col, mode_col, year_col])
    )

    for col in metrics:
        annual[f"{col}_growth"] = (
            annual.groupby([agency_col, mode_col])[col].pct_change() * 100
        )

    growth = annual.melt(
        id_vars=[agency_col, mode_col, year_col],
        value_vars=[f"{col}_growth" for col in metrics],
        var_name="metric",
        value_name="growth",
    )
    growth["metric"] = (
        growth["metric"].str.replace("_growth", "", regex=False).map(metrics)
    )
    growth = growth.dropna(subset=["growth"])

    agencies = sorted(growth[agency_col].unique().tolist())
    modes = sorted(growth[mode_col].unique().tolist())
    years = sorted(growth[year_col].unique().tolist())

    if not agencies or not modes or not years:
        raise ValueError(f"No valid growth data found for {rtpa}.")

    agency_p = alt.param(
        name="agency_sel",
        value=agencies[0],
        bind=alt.binding_select(options=agencies, name="Agency: "),
    )
    mode_p = alt.param(
        name="mode_sel",
        value=modes[0],
        bind=alt.binding_select(options=modes, name="Mode: "),
    )
    year_p = alt.param(
        name="year_sel",
        value=int(years[-1]),
        bind=alt.binding_select(options=[int(y) for y in years], name="Year: "),
    )

    metric_order = list(metrics.values())
    filter_expr = (
        f"datum[{repr(agency_col)}] == agency_sel && "
        f"datum[{repr(mode_col)}] == mode_sel && "
        f"datum[{repr(year_col)}] == year_sel"
    )
    base = alt.Chart(growth).transform_filter(filter_expr)

    chart = (
        base.mark_bar(cornerRadiusEnd=3, size=28, color=TEAL)
        .encode(
            x=alt.X(
                "metric:N",
                title=None,
                sort=metric_order,
                scale=alt.Scale(paddingInner=0.3, paddingOuter=0.15),
                axis=alt.Axis(labelAngle=0, labelLimit=250, labelPadding=12),
            ),
            y=alt.Y(
                "growth:Q",
                title="Year-over-Year Change (%)",
                axis=alt.Axis(format=".0f", grid=True, gridColor=BORDER),
                scale=alt.Scale(zero=True),
            ),
            tooltip=[
                alt.Tooltip("metric:N", title="Measure"),
                alt.Tooltip("growth:Q", title="YoY Change", format="+.1f"),
            ],
        )
        .properties(width=width, height=height)
    )

    labels = (
        base.transform_calculate(label="format(datum.growth, '+.1f') + '%'")
        .mark_text(
            fontSize=11,
            fontWeight="bold",
            color=NAVY,
            dy=alt.expr("datum.growth >= 0 ? -10 : 10"),
        )
        .encode(
            x=alt.X("metric:N", sort=metric_order),
            y=alt.Y("growth:Q"),
            text=alt.Text("label:N"),
        )
    )

    subtitle = (
        alt.Chart({"values": [{}]})
        .transform_calculate(
            t="agency_sel + ' | ' + mode_sel + ' | ' + "
            "toString(year_sel - 1) + '–' + toString(year_sel)"
        )
        .mark_text(
            align="left", font=FONT, fontSize=14, fontWeight="bold", color="#24324A"
        )
        .encode(x=alt.value(0), y=alt.value(12), text="t:N")
        .properties(width=width, height=24)
    )

    return (
        alt.vconcat(subtitle, alt.layer(chart, labels), spacing=5)
        .add_params(agency_p, mode_p, year_p)
        .configure_view(stroke=None)
        .configure_axis(
            **{
                **ALT_AXIS_CONFIG,
                "labelPadding": 12,
                "labelLimit": 250,
                "labelColor": "#24324A",
                "labelFontSize": 12,
                "labelFontWeight": "bold",
            }
        )
        .configure_title(font=FONT, anchor="start")
    )


def create_farebox_subsidy_scatter(
    df,
    rtpa_name,
    year_column="year",
    agency_column="source_agency",
    id_column="ntd_id",
    mode_column="mode_full_name",
    filter_column="rtpa_name",
    recovery_column="farebox_recovery_ratio",
    fare_column="fare_revenue_per_trip",
    subsidy_column="net_subsidy_per_trip",
    width=850,
    height=500,
):
    """Interactive scatter plot of agency fare revenue, subsidy, and recovery."""

    import json

    required = [
        year_column,
        agency_column,
        id_column,
        mode_column,
        filter_column,
        recovery_column,
        fare_column,
        "reporting_module",
        subsidy_column,
    ]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"Missing columns: {missing}")

    d = df.loc[df[filter_column] == rtpa_name].copy()
    if d.empty:
        raise ValueError(f"No data found for RTPA={rtpa_name!r}")

    d = d.dropna(
        subset=[
            year_column,
            agency_column,
            mode_column,
            recovery_column,
            fare_column,
            subsidy_column,
        ]
    )
    years = sorted(d[year_column].unique().tolist())
    modes = sorted(d[mode_column].dropna().unique().tolist())

    if not years or not modes:
        raise ValueError(f"No valid data found for RTPA={rtpa_name!r}")

    year_p = alt.param(
        name="year_sel",
        value=years[-1],
        bind=alt.binding_select(options=years, name="Year: "),
    )
    mode_p = alt.param(
        name="mode_sel",
        value="All Modes",
        bind=alt.binding_select(options=["All Modes"] + modes, name="Mode: "),
    )

    filter_expr = (
        f"datum[{json.dumps(year_column)}] == year_sel && "
        f"(mode_sel == 'All Modes' || datum[{json.dumps(mode_column)}] == mode_sel)"
    )

    points = (
        alt.Chart(d)
        .transform_filter(filter_expr)
        .mark_point(
            filled=True, size=180, opacity=0.9, stroke="#000000", strokeWidth=0.5
        )
        .encode(
            x=alt.X(
                f"{fare_column}:Q",
                title="Fare Revenue per Trip ($)",
                axis=alt.Axis(format="$,.2f", grid=True, labelPadding=8),
            ),
            y=alt.Y(
                f"{subsidy_column}:Q",
                title="Net Subsidy per Trip ($)",
                axis=alt.Axis(format="$,.2f", grid=True, labelPadding=8),
            ),
            color=alt.Color(
                f"{recovery_column}:Q",
                title="Farebox Recovery",
                scale=alt.Scale(scheme="blues", domain=[0, 1], clamp=True),
                legend=alt.Legend(
                    orient="right",
                    direction="vertical",
                    gradientLength=150,
                    gradientThickness=16,
                    labelFontSize=12,
                    titleFontSize=13,
                    titleFontWeight="bold",
                ),
            ),
            shape=alt.Shape(
                f"{mode_column}:N",
                title="Mode",
                legend=alt.Legend(
                    orient="right",
                    direction="vertical",
                    labelFontSize=12,
                    titleFontSize=13,
                    titleFontWeight="bold",
                    symbolSize=130,
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{agency_column}:N", title="Agency"),
                alt.Tooltip(f"{id_column}:N", title="NTD ID"),
                alt.Tooltip("reporting_module:N", title="Reporting Module"),
                alt.Tooltip(f"{mode_column}:N", title="Mode"),
                alt.Tooltip(f"{year_column}:O", title="Year"),
                alt.Tooltip(
                    f"{recovery_column}:Q", title="Farebox Recovery", format=".1%"
                ),
                alt.Tooltip(
                    f"{fare_column}:Q", title="Fare Revenue / Trip", format="$,.2f"
                ),
                alt.Tooltip(
                    f"{subsidy_column}:Q", title="Net Subsidy / Trip", format="$,.2f"
                ),
            ],
        )
        .properties(width=width, height=height)
    )

    title = (
        alt.Chart({"values": [{}]})
        .mark_text(
            align="left", font=FONT, fontSize=19, fontWeight="bold", color="#000000"
        )
        .encode(
            x=alt.value(0),
            y=alt.value(16),
            text=alt.value("Fare Revenue & Subsidy per Passenger Trip"),
        )
        .properties(width=width, height=28)
    )

    subtitle = (
        alt.Chart({"values": [{}]})
        .transform_calculate(
            t=f"'{rtpa_name} | ' + mode_sel + ' | ' + toString(year_sel) + "
            "' | Each point represents one agency-mode combination'"
        )
        .mark_text(
            align="left", font=FONT, fontSize=14, fontWeight="bold", color="#000000"
        )
        .encode(x=alt.value(0), y=alt.value(12), text="t:N")
        .properties(width=width, height=24)
    )

    return (
        alt.vconcat(title, subtitle, points, spacing=3)
        .add_params(year_p, mode_p)
        .configure_view(stroke=None)
        .configure_axis(
            **{
                **ALT_AXIS_CONFIG,
                "labelPadding": 10,
                "labelLimit": 250,
                "labelColor": "#000000",
                "titleColor": "#000000",
                "labelFontSize": 13,
                "titleFontSize": 15,
                "labelFontWeight": "bold",
                "titleFontWeight": "bold",
            }
        )
        .configure_legend(
            labelFontSize=12,
            titleFontSize=13,
            labelColor="#000000",
            titleColor="#000000",
            padding=8,
            offset=12,
            orient="right",
        )
    )


def rtpa_funding_share_vs_size_grid(
    expense_sources,
    funding_df,
    components,
    rtpa,
    rtpa_column,
    id_column,
    year_column,
    agency_column,
    color_column=None,
    show_legend=False,
    scale=1_000_000,
    unit="$M",
    ncols=2,
    min_n_fit=3,
    panel_width=380,
    panel_height=280,
    title=None,
):
    """
    Grid of scatters for ONE RTPA: total expenses (x, log) vs. each funding source's
    share of total funding (y), one panel per source, with a single year dropdown.

    expense_sources : list of (df, [columns]) summed into total_expenses
    funding_df      : agency-level df with funding columns, agency name, RTPA
    components      : {"Federal": [cols], "State": [cols], ...} one panel per key
    ncols           : panels per row
    """
    keys = [id_column, year_column]

    # ---- validate ----
    def check(df, cols, name):
        missing = [c for c in [*keys, *cols] if c not in df.columns]
        if missing:
            raise ValueError(f"{name}: missing columns {missing}")

    comp_cols = [c for cols in components.values() for c in cols]
    extra = [agency_column, rtpa_column]
    if color_column and color_column not in extra:
        extra.append(color_column)
    check(funding_df, [*extra, *comp_cols], "funding_df")
    for i, (d, cols) in enumerate(expense_sources):
        check(d, cols, f"expense_sources[{i}]")

    # ---- filter to RTPA, one row per agency-year ----
    f = funding_df.loc[funding_df[rtpa_column] == rtpa]
    if f.empty:
        raise ValueError(f"No rows found for RTPA={rtpa!r}")

    labels = f.groupby(keys, as_index=False)[extra].first()
    funds = f.groupby(keys, as_index=False)[comp_cols].sum()
    df = labels.merge(funds, on=keys, how="left")

    # ---- expenses ----
    exp_cols = []
    for i, (d, cols) in enumerate(expense_sources):
        agg = d.groupby(keys, as_index=False)[cols].sum()
        agg = agg.rename(columns={c: f"exp{i}__{c}" for c in cols})
        df = df.merge(agg, on=keys, how="left")
        exp_cols += [f"exp{i}__{c}" for c in cols]
    df[exp_cols] = df[exp_cols].fillna(0)
    df["total_expenses"] = df[exp_cols].sum(axis=1) / scale

    # ---- funding totals and shares ----
    for name, cols in components.items():
        df[f"amt_{name}"] = df[cols].sum(axis=1) / scale
    df["total_funding"] = df[[f"amt_{n}" for n in components]].sum(axis=1)
    df = df[(df["total_expenses"] > 0) & (df["total_funding"] > 0)].copy()
    if df.empty:
        raise ValueError(
            f"No rows with positive expenses and funding for RTPA={rtpa!r}."
        )

    id_vars = [id_column, year_column, agency_column, "total_expenses", "total_funding"]
    if color_column and color_column not in id_vars:
        id_vars.append(color_column)

    long = []
    for name in components:
        t = df[id_vars].copy()
        t["funding_type"] = name
        t["amount"] = df[f"amt_{name}"]
        t["share"] = df[f"amt_{name}"] / df["total_funding"]
        long.append(t)
    long = pd.concat(long, ignore_index=True)

    years = sorted(long[year_column].unique().tolist())
    types = list(components.keys())
    lo, hi = long["total_expenses"].min(), long["total_expenses"].max()

    # ---- per year x source linear fit of share on log10(expenses) ----
    fit_rows, label_rows = [], []
    for (yr, ft), g in long.groupby([year_column, "funding_type"]):
        if len(g) >= min_n_fit and g["total_expenses"].nunique() > 1:
            lx = np.log10(g["total_expenses"])
            slope, intercept = np.polyfit(lx, g["share"], 1)
            r2 = (
                np.corrcoef(lx, g["share"])[0, 1] ** 2
                if g["share"].nunique() > 1
                else np.nan
            )
            for x in (g["total_expenses"].min(), g["total_expenses"].max()):
                fit_rows.append(
                    {
                        year_column: yr,
                        "funding_type": ft,
                        "x": x,
                        "y": intercept + slope * np.log10(x),
                    }
                )
            label_rows.append(
                {
                    year_column: yr,
                    "funding_type": ft,
                    "label": f"slope = {slope:+.2f}   R² = {r2:.2f}   n = {len(g)}",
                }
            )
        else:
            label_rows.append(
                {
                    year_column: yr,
                    "funding_type": ft,
                    "label": f"n = {len(g)} (too few for a fit)",
                }
            )
    fit_df = pd.DataFrame(fit_rows, columns=[year_column, "funding_type", "x", "y"])
    label_df = pd.DataFrame(label_rows)

    # ---- one shared year selection ----
    year_sel = alt.selection_point(
        name="Year",
        fields=[year_column],
        bind=alt.binding_select(options=years, name="Year "),
        value=[{year_column: years[-1]}],
    )

    x_scale = alt.Scale(type="log", domain=[lo * 0.8, hi * 1.25])
    y_scale = alt.Scale(domain=[0, 1])

    if color_column:
        color = alt.Color(
            f"{color_column}:N",
            title=color_column.replace("_", " ").title(),
            scale=alt.Scale(scheme="tableau20"),
            legend=alt.Legend(orient="bottom", direction="horizontal", columns=3)
            if show_legend
            else None,
        )
    else:
        color = alt.value("#4c78a8")

    tooltip = [
        alt.Tooltip(f"{year_column}:O", title="Year"),
        alt.Tooltip(f"{agency_column}:N", title="Agency"),
        alt.Tooltip("funding_type:N", title="Funding Source"),
        alt.Tooltip("share:Q", title="Share of Funding", format=".1%"),
        alt.Tooltip("amount:Q", title=f"Source Amount ({unit})", format=",.1f"),
        alt.Tooltip("total_funding:Q", title=f"Total Funding ({unit})", format=",.1f"),
        alt.Tooltip(
            "total_expenses:Q", title=f"Total Expenses ({unit})", format=",.1f"
        ),
    ]

    n_rows = -(-len(types) // ncols)

    def make_panel(i, name):
        is_bottom = (i // ncols) == n_rows - 1
        is_left = (i % ncols) == 0
        is_type = alt.datum.funding_type == name

        points = (
            alt.Chart(long)
            .mark_circle(opacity=0.8, size=80)
            .encode(
                x=alt.X(
                    "total_expenses:Q",
                    scale=x_scale,
                    title=f"Total Expenses ({unit}, log)" if is_bottom else None,
                    axis=alt.Axis(format=",.0f"),
                ),
                y=alt.Y(
                    "share:Q",
                    scale=y_scale,
                    title="Share of Total Funding" if is_left else None,
                    axis=alt.Axis(format=".0%"),
                ),
                color=color,
                tooltip=tooltip,
            )
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        if i == 0:
            points = points.add_params(year_sel)  # define the selection once

        fit_line = (
            alt.Chart(fit_df)
            .mark_line(color="#111827", strokeWidth=2)
            .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale))
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        fit_text = (
            alt.Chart(label_df)
            .mark_text(align="left", baseline="top", fontSize=11, color="#374151")
            .encode(x=alt.value(8), y=alt.value(6), text="label:N")
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        return alt.layer(fit_line, points, fit_text).properties(
            width=panel_width,
            height=panel_height,
            title=alt.TitleParams(
                text=name, fontSize=13, fontWeight=600, color="#111827", anchor="start"
            ),
        )

    panels = [make_panel(i, n) for i, n in enumerate(types)]
    rows = [alt.hconcat(*panels[r * ncols : (r + 1) * ncols]) for r in range(n_rows)]

    chart = alt.vconcat(*rows).properties(
        title=alt.TitleParams(
            text=title or f"Funding Source Share vs. Agency Size: {rtpa}",
            subtitle="Solid line = linear fit of share on log(expenses)",
            fontSize=16,
            fontWeight=600,
            color="#111827",
            anchor="start",
        )
    )
    return chart, year_sel


def rtpa_vs_state_funding_share(
    expense_sources,
    funding_df,
    components,
    rtpa,
    rtpa_column,
    id_column,
    year_column,
    agency_column,
    color_column=None,
    show_legend=False,
    scale=1_000_000,
    unit="$M",
    ncols=2,
    min_n_fit=10,
    panel_width=380,
    panel_height=280,
    title=None,
    highlight_color="#e45756",
    grey="#c4c8cf",
):
    """
    Grid of scatters, one panel per funding source: total expenses (x, log) vs. the
    source's share of total funding (y). ALL agencies statewide are drawn in grey,
    agencies in the selected RTPA are colored. The fit line and stats are statewide.
    One shared year dropdown.

    expense_sources : list of (df, [columns]) summed into total_expenses
    funding_df      : agency-level df (statewide) with funding columns, agency name, RTPA
    components      : {"Federal": [cols], "State": [cols], ...} one panel per key
    color_column    : colors the RTPA's dots (e.g. agency_column); None = one highlight color
    """
    keys = [id_column, year_column]

    # ---- validate ----
    def check(df, cols, name):
        missing = [c for c in [*keys, *cols] if c not in df.columns]
        if missing:
            raise ValueError(f"{name}: missing columns {missing}")

    comp_cols = [c for cols in components.values() for c in cols]
    extra = [agency_column, rtpa_column]
    if color_column and color_column not in extra:
        extra.append(color_column)
    check(funding_df, [*extra, *comp_cols], "funding_df")
    for i, (d, cols) in enumerate(expense_sources):
        check(d, cols, f"expense_sources[{i}]")

    if not (funding_df[rtpa_column] == rtpa).any():
        raise ValueError(f"No rows found for RTPA={rtpa!r}")

    # ---- statewide: one row per agency-year ----
    labels = funding_df.groupby(keys, as_index=False)[extra].first()
    funds = funding_df.groupby(keys, as_index=False)[comp_cols].sum()
    df = labels.merge(funds, on=keys, how="left")
    df["in_rtpa"] = df[rtpa_column] == rtpa

    # ---- expenses ----
    exp_cols = []
    for i, (d, cols) in enumerate(expense_sources):
        agg = d.groupby(keys, as_index=False)[cols].sum()
        agg = agg.rename(columns={c: f"exp{i}__{c}" for c in cols})
        df = df.merge(agg, on=keys, how="left")
        exp_cols += [f"exp{i}__{c}" for c in cols]
    df[exp_cols] = df[exp_cols].fillna(0)
    df["total_expenses"] = df[exp_cols].sum(axis=1) / scale

    # ---- funding totals and shares ----
    for name, cols in components.items():
        df[f"amt_{name}"] = df[cols].sum(axis=1) / scale
    df["total_funding"] = df[[f"amt_{n}" for n in components]].sum(axis=1)
    df = df[(df["total_expenses"] > 0) & (df["total_funding"] > 0)].copy()
    if df.empty:
        raise ValueError("No rows with positive expenses and funding.")

    id_vars = [
        id_column,
        year_column,
        agency_column,
        rtpa_column,
        "in_rtpa",
        "total_expenses",
        "total_funding",
    ]
    if color_column and color_column not in id_vars:
        id_vars.append(color_column)

    long = []
    for name in components:
        t = df[id_vars].copy()
        t["funding_type"] = name
        t["amount"] = df[f"amt_{name}"]
        t["share"] = df[f"amt_{name}"] / df["total_funding"]
        long.append(t)
    long = pd.concat(long, ignore_index=True)

    years = sorted(long[year_column].unique().tolist())
    types = list(components.keys())
    lo, hi = long["total_expenses"].min(), long["total_expenses"].max()

    # ---- statewide fit per year x source ----
    fit_rows, label_rows = [], []
    for (yr, ft), g in long.groupby([year_column, "funding_type"]):
        n_rtpa = int(g["in_rtpa"].sum())
        if (
            len(g) >= min_n_fit
            and g["total_expenses"].nunique() > 1
            and g["share"].nunique() > 1
        ):
            lx = np.log10(g["total_expenses"])
            slope, intercept = np.polyfit(lx, g["share"], 1)
            r2 = np.corrcoef(lx, g["share"])[0, 1] ** 2
            for x in (g["total_expenses"].min(), g["total_expenses"].max()):
                fit_rows.append(
                    {
                        year_column: yr,
                        "funding_type": ft,
                        "x": x,
                        "y": intercept + slope * np.log10(x),
                    }
                )
            label_rows.append(
                {
                    year_column: yr,
                    "funding_type": ft,
                    "label": f"Statewide: slope = {slope:+.2f}   R² = {r2:.2f}   "
                    f"n = {len(g)} ({n_rtpa} in RTPA)",
                }
            )
        else:
            label_rows.append(
                {
                    year_column: yr,
                    "funding_type": ft,
                    "label": f"n = {len(g)} (too few for a fit)",
                }
            )
    fit_df = pd.DataFrame(fit_rows, columns=[year_column, "funding_type", "x", "y"])
    label_df = pd.DataFrame(label_rows)

    # ---- one shared year selection ----
    year_sel = alt.selection_point(
        name="Year",
        fields=[year_column],
        bind=alt.binding_select(options=years, name="Year "),
        value=[{year_column: years[-1]}],
    )

    x_scale = alt.Scale(type="log", domain=[lo * 0.8, hi * 1.25])
    y_scale = alt.Scale(domain=[0, 1])

    if color_column:
        color = alt.Color(
            f"{color_column}:N",
            title=color_column.replace("_", " ").title(),
            scale=alt.Scale(scheme="tableau20"),
            legend=alt.Legend(orient="bottom", direction="horizontal", columns=3)
            if show_legend
            else None,
        )
    else:
        color = alt.value(highlight_color)

    tooltip = [
        alt.Tooltip(f"{year_column}:O", title="Year"),
        alt.Tooltip(f"{agency_column}:N", title="Agency"),
        alt.Tooltip(f"{rtpa_column}:N", title="RTPA"),
        alt.Tooltip("funding_type:N", title="Funding Source"),
        alt.Tooltip("share:Q", title="Share of Funding", format=".1%"),
        alt.Tooltip("amount:Q", title=f"Source Amount ({unit})", format=",.1f"),
        alt.Tooltip("total_funding:Q", title=f"Total Funding ({unit})", format=",.1f"),
        alt.Tooltip(
            "total_expenses:Q", title=f"Total Expenses ({unit})", format=",.1f"
        ),
    ]

    n_rows = -(-len(types) // ncols)

    def make_panel(i, name):
        is_bottom = (i // ncols) == n_rows - 1
        is_left = (i % ncols) == 0
        is_type = alt.datum.funding_type == name

        def enc(chart):
            return chart.encode(
                x=alt.X(
                    "total_expenses:Q",
                    scale=x_scale,
                    title=f"Total Expenses ({unit}, log)" if is_bottom else None,
                    axis=alt.Axis(format=",.0f"),
                ),
                y=alt.Y(
                    "share:Q",
                    scale=y_scale,
                    title="Share of Total Funding" if is_left else None,
                    axis=alt.Axis(format=".0%"),
                ),
            )

        # statewide agencies (grey, behind)
        others = (
            enc(
                alt.Chart(long).mark_circle(
                    opacity=0.45, size=45, color=grey, clip=True
                )
            )
            .encode(tooltip=tooltip)
            .transform_filter("!datum.in_rtpa")
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        if i == 0:
            others = others.add_params(year_sel)  # define the selection once

        # selected RTPA (colored, on top)
        mine = (
            enc(
                alt.Chart(long).mark_circle(
                    opacity=0.95, size=110, clip=True, stroke="white", strokeWidth=0.8
                )
            )
            .encode(color=color, tooltip=tooltip)
            .transform_filter("datum.in_rtpa")
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        fit_line = (
            alt.Chart(fit_df)
            .mark_line(color="#111827", strokeWidth=2)
            .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale))
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        fit_text = (
            alt.Chart(label_df)
            .mark_text(align="left", baseline="top", fontSize=11, color="#374151")
            .encode(x=alt.value(8), y=alt.value(6), text="label:N")
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        return alt.layer(others, fit_line, mine, fit_text).properties(
            width=panel_width,
            height=panel_height,
            title=alt.TitleParams(
                text=name, fontSize=13, fontWeight=600, color="#111827", anchor="start"
            ),
        )

    panels = [make_panel(i, n) for i, n in enumerate(types)]
    rows = [alt.hconcat(*panels[r * ncols : (r + 1) * ncols]) for r in range(n_rows)]

    chart = alt.vconcat(*rows).properties(
        title=alt.TitleParams(
            text=title or f"Funding Source Share vs. Agency Size: {rtpa} vs. Statewide",
            subtitle="Grey = all California agencies; colored = selected RTPA; "
            "solid line = statewide linear fit of share on log(expenses)",
            fontSize=16,
            fontWeight=600,
            color="#111827",
            anchor="start",
        )
    )
    return chart, year_sel
