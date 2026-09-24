# Chart functions
import altair as alt
import matplotlib.pyplot as plt
import pandas as pd
from pypalettes import load_palette
from pywaffle import Waffle

alt.data_transformers.enable("vegafusion")


def prep_for_mode_trend(df, value_column):
    trend_df = (
        df.groupby(["year", "mode_group"])[value_column]
        .sum()
        .reset_index()
    )
    trend_df[value_column] = (
        trend_df[value_column]
        .round(0)
        .astype(int)
    )
    return trend_df


def mode_trend_chart(df, value_column, title=None, y_title=None):
    nearest = alt.selection_point(nearest=True, on="pointerover", fields=["year"], empty=False)
    base = alt.Chart(df)
    title = title or f"{value_column.replace('_', ' ').title()} by Mode"
    y_title = y_title or value_column.replace("_", " ").title()

    line = base.mark_line(strokeWidth=2.5, interpolate="monotone").encode(
        x=alt.X("year:O", title="Year", axis=alt.Axis(labelAngle=0, labelColor="#374151")),
        y=alt.Y(f"{value_column}:Q", title=y_title, axis=alt.Axis(
            format=",.0f", grid=True, gridColor="#E5E7EB", gridOpacity=.7,
            labelColor="#6B7280", titleColor="#374151")),
        color=alt.Color("mode_group:N", title="Mode",
            scale=alt.Scale(range=["#3B82F6", "#10B981", "#F59E0B", "#6366F1"]),
            legend=alt.Legend(orient="right", symbolType="circle"))
    )

    selectors = base.mark_point().encode(x="year:O", opacity=alt.value(0)).add_params(nearest)
    points = line.mark_point(size=80, filled=True, stroke="white", strokeWidth=1.5).encode(
        opacity=alt.when(nearest).then(alt.value(1)).otherwise(alt.value(0)),
        tooltip=[alt.Tooltip("year:O", title="Year"),
                 alt.Tooltip("mode_group:N", title="Mode"),
                 alt.Tooltip(f"{value_column}:Q", title=y_title, format=",.0f")])
    rules = base.mark_rule(color="#D1D5DB", strokeDash=[4, 2]).encode(
        x="year:O").transform_filter(nearest)


    return alt.layer(line, selectors, points, rules).properties(
    width=400, height=300,
    title=alt.TitleParams(text=title, fontSize=16, fontWeight=600,
                          color="#111827", anchor="start", offset=12))





def scatter_plot_regression(df, x_variable, y_variable, tooltip_columns=None, chart_title=None):
    """Creates a filtered scatter plot with a regression trend line."""
    d = df[(df[x_variable] > 0) & (df[y_variable] > 0)].copy()
    tooltip_columns = tooltip_columns or [x_variable, y_variable]

    scatter = alt.Chart(d).mark_circle(
        size=70, opacity=.55, color="#3B82F6", stroke="white", strokeWidth=1
    ).encode(
        x=alt.X(f"{x_variable}:Q", title=x_variable, axis=alt.Axis(
            labelColor="#6B7280", titleColor="#374151", grid=True, gridColor="#E5E7EB", gridOpacity=.7)),
        y=alt.Y(f"{y_variable}:Q", title=y_variable, axis=alt.Axis(
            labelColor="#6B7280", titleColor="#374151", grid=True, gridColor="#E5E7EB", gridOpacity=.7)),
        tooltip=tooltip_columns
    )

    trend = alt.Chart(d).transform_regression(x_variable, y_variable).mark_line(
        color="#111827", size=2.5
    ).encode(x=f"{x_variable}:Q", y=f"{y_variable}:Q")

    return (scatter + trend).properties(
        width=500, height=350,
        title=alt.TitleParams(text=chart_title, fontSize=16, fontWeight=600,
                              color="#111827", anchor="start", offset=12)
    ).configure_view(strokeWidth=0).configure_axis(
        labelFont="Arial", titleFont="Arial"
    ).configure_title(font="Arial")



def waffle_by_year(
    df,
    value_column,
    category_column,
    year_column,
    years=None,
    palette="CrystalGems",
    shuffle=9,
    rows=50,
    columns=10
):
    """
    Creates waffle charts showing category values across selected years.

    Parameters:
        df: DataFrame containing the data.
        value_column: Numeric column used to determine waffle sizes (eg: upt)
        category_column: Column defining the categories shown in the waffle (eg: mode)
        year_column: Column defining the time periods shown as separate waffles
        years: Optional list of years to include.
        palette: Color palette used for the categories.
        shuffle: Controls the ordering of colors in the palette.
        rows: Number of rows of squares in each waffle.
        columns: Number of columns of squares in each waffle.
    """
    df_plot = df.copy()

    if years is not None:
        df_plot = df_plot[df_plot[year_column].isin(years)]

    df_plot = (
        df_plot
        .groupby([year_column, category_column], as_index=False)[value_column]
        .sum()
    )

    all_years = df_plot[year_column].unique()
    all_categories = df_plot[category_column].unique()

    idx = pd.MultiIndex.from_product(
        [all_years, all_categories],
        names=[year_column, category_column]
    )

    df_plot = (
        df_plot
        .set_index([year_column, category_column])
        .reindex(idx, fill_value=0)
        .reset_index()
        .sort_values([year_column, category_column])
    )

    n_colors = len(all_categories)

    colors = load_palette(
        palette,
        keep_first_n=n_colors,
        shuffle=shuffle
    ) + ["white"]

    max_year_value = (
        df_plot[
            df_plot[year_column] == all_years.max()
        ][value_column].sum()
    )

    ncols = len(all_years)

    fig, axs = plt.subplots(
        ncols=ncols,
        figsize=(14, 8)
    )

    if ncols == 1:
        axs = [axs]

    for year, ax in zip(sorted(all_years), axs):
        values = list(
            df_plot[
                df_plot[year_column] == year
            ][value_column].values
        )

        values = sorted(values, reverse=True)

        values.append(
            max_year_value - sum(values)
        )

        Waffle.make_waffle(
            ax=ax,
            rows=rows,
            columns=columns,
            values=values,
            vertical=True,
            colors=colors
        )

        ax.yaxis.set_visible(True)
        ax.set_yticks(ax.get_yticks())

        ax.text(
            x=0.1,
            y=-0.04,
            s=str(int(year)),
            fontsize=14,
            ha="center"
        )

    from matplotlib.patches import Patch

    plt.legend(
        handles=[
            Patch(
                color=colors[i],
                label=category
            )
            for i, category in enumerate(all_categories)
        ],
        bbox_to_anchor=(1.05, 1),
        loc="upper left"
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
    height=400
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
        chart_title: Optional title for the chart.
        change_label: Label for the color legend.
        width: Width of each chart panel.
        height: Height of each chart panel.
    """
    df_plot = df.copy()

    if selected_groups is not None:
        df_plot = df_plot[
            df_plot[group_column].isin(selected_groups)
        ]

    chart = (
        alt.Chart(
            df_plot,
            title=chart_title
        )
        .mark_trail()
        .encode(
            x=alt.X(year_column + ":O")
                .title(None),
            y=alt.Y(category_column + ":N")
                .title(None),
            size=alt.Size(value_column + ":Q")
                .scale(range=[5, 20])
                .title(value_column),
            color=alt.Color("delta:Q")
                .scale(
                    domainMid=0,
                    range=["maroon", "lightgray", "blue"]
                )
                .title(change_label),
            tooltip=[
                alt.Tooltip(year_column + ":O", title="Year"),
                alt.Tooltip(value_column + ":Q", title=value_column)
            ],
            column=alt.Column(group_column + ":N")
                .title(group_column)
        )
        .transform_pivot(
            pivot=year_column,
            value=value_column,
            groupby=[
                category_column,
                group_column
            ]
        )
        .transform_calculate(
            delta=f"datum['{end_year}'] - datum['{start_year}']"
        )
        .transform_fold(
            [str(start_year), str(end_year)],
            as_=["year", value_column]
        )
        .properties(
            width=width,
            height=height
        )
        .configure_legend(
            orient="bottom",
            direction="horizontal"
        )
        .configure_view(
            stroke=None
        )
    )

    return chart


def percent_stacked_bar(
    df, group_column, category_columns, year_column=None, year=None,
    rank_column=None, top_n=10, chart_title=None, chart_subtitle=None,
    y_title="Percentage", colors=None, width=500, height=300
):
    df_plot = df.copy()

    if year_column is not None and year is not None:
        df_plot = df_plot[df_plot[year_column] == year]

    if rank_column is not None:
        top_groups = (
            df_plot.groupby(group_column)[rank_column].sum()
            .nlargest(top_n).index.tolist()
        )
        df_plot = df_plot[df_plot[group_column].isin(top_groups)]
    else:
        top_groups = df_plot[group_column].drop_duplicates().tolist()

    data = (
        df_plot.groupby(group_column)[list(category_columns.values())].sum()
        .reset_index()
        .melt(id_vars=group_column, var_name="category_column", value_name="amount")
    )

    data["category"] = data["category_column"].map(
        {v: k for k, v in category_columns.items()}
    )
    data["percentage"] = (
        data["amount"] / data.groupby(group_column)["amount"].transform("sum") * 100
    )

    title = (
        alt.TitleParams(text=chart_title, subtitle=chart_subtitle)
        if chart_subtitle else chart_title
    )

    return (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                f"{group_column}:N", title=group_column, sort=top_groups,
                axis=alt.Axis(labelAngle=-25)
            ),
            y=alt.Y(
                "sum(percentage):Q", title=y_title,
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(format=".0f")
            ),
            color=alt.Color(
                "category:N", title="Category",
                scale=alt.Scale(range=colors) if colors else alt.Scale()
            ),
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title=group_column),
                alt.Tooltip("category:N", title="Category"),
                alt.Tooltip("percentage:Q", title="Share", format=".1f"),
                alt.Tooltip("amount:Q", title="Amount", format=",.0f")
            ]
        )
        .properties(title=title, width=width, height=height)
    )


def ridge_plot(
    df, value_column, category_column, year_column=None, year=None,
    filters=None, value_min=None, value_max=None, step=30, overlap=1.5,
    chart_title=None, chart_subtitle=None, x_title=None, category_title=None
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
    if year_column and year is not None: d = d[d[year_column] == year]
    if filters:
        for col, vals in filters.items():
            d = d[d[col].isin(vals)] if isinstance(vals, list) else d[d[col] == vals]
    d = d[d[value_column].notna()]
    if value_min is not None: d = d[d[value_column] >= value_min]
    if value_max is not None: d = d[d[value_column] <= value_max]

    return (
        alt.Chart(d, width=800, height=step)
        .transform_density(value_column, groupby=[category_column], as_=[value_column, "density"])
        .mark_area(interpolate="monotone", fillOpacity=0.8, stroke="white", strokeWidth=0.5)
        .encode(
            x=alt.X(f"{value_column}:Q", title=x_title or value_column),
            y=alt.Y("density:Q", axis=None, scale=alt.Scale(range=[step, -step * overlap])),
            color=alt.Color(f"{category_column}:N", title=category_title or category_column),
            tooltip=[
                alt.Tooltip(f"{category_column}:N", title=category_title or category_column),
                alt.Tooltip(f"{value_column}:Q", title=x_title or value_column, format=".3f"),
                alt.Tooltip("density:Q", title="Density", format=".3f")
            ]
        )
        .facet(row=alt.Row(f"{category_column}:N", title=None,
                           header=alt.Header(labelAngle=0, labelAlign="left")))
        .properties(title=alt.TitleParams(text=chart_title, subtitle=chart_subtitle), bounds="flush")
        .configure_facet(spacing=0)
        .configure_view(stroke=None)
    )



def breakdown_chart(df, year, component_columns, group_column, year_column, normalize=True, title=None):
    """
    Creates a stacked bar chart showing the composition of a total
    broken into components, by group. Amounts are displayed in millions.
    """
    plot_df = (df[df[year_column] == year].groupby(group_column)[component_columns].sum().reset_index()
               .melt(id_vars=group_column, var_name="component", value_name="amount"))
    plot_df["amount"] /= 1_000_000
    plot_df["component"] = plot_df["component"].str.replace("_", " ", regex=False).str.title()

    y_enc = alt.Y("amount:Q", stack="normalize" if normalize else True,
                  axis=alt.Axis(format=".0%") if normalize else alt.Axis(format=",.1f"),
                  title="Share of Total" if normalize else "Amount ($M)")

    return alt.Chart(plot_df).mark_bar(cornerRadius=2).encode(
        x=alt.X(f"{group_column}:N", title="Mode", axis=alt.Axis(labelAngle=0)),
        y=y_enc,
        color=alt.Color("component:N", title="Component",
            scale=alt.Scale(scheme="pastel2"),
            legend=alt.Legend(orient="bottom", direction="horizontal")),
        tooltip=[
            alt.Tooltip(f"{group_column}:N", title="Mode"),
            alt.Tooltip("component:N", title="Component"),
            alt.Tooltip("amount:Q", title="Amount ($M)", format=",.1f")
        ]
    ).properties(
        width=500, height=350,
        title=alt.TitleParams(
            text=title or f"Composition by Mode, {year}",
            fontSize=16, fontWeight=600, color="#111827", anchor="start"
        )
    )



def plot_scorecard(df, metrics, group_column, titles=None, x_labels=None,
                   main_title=None, subtitles=None, colors=None, formats=None,
                   width=280, height=260):
    """
    Creates three side-by-side horizontal bar charts comparing
    three metrics across groups.
    """
    titles = titles or metrics; x_labels = x_labels or metrics
    subtitles = subtitles or [""] * len(metrics)
    colors = colors or ["#3B82F6", "#10B981", "#F59E0B"]
    formats = formats or [".2f"] * len(metrics); charts = []
    order = df[group_column].drop_duplicates().tolist()

    for metric, title, xlabel, subtitle, color, fmt in zip(metrics, titles, x_labels, subtitles, colors, formats):
        d = df[[group_column, metric]].dropna().copy()
        d["is_max"] = d[metric] == d[metric].max()

        bars = alt.Chart(d).mark_bar(cornerRadiusEnd=6, height=28).encode(
            x=alt.X(f"{metric}:Q", title=xlabel, axis=alt.Axis(
                grid=True, gridColor="#E5E7EB", gridOpacity=.7, domain=False,
                tickColor="#D1D5DB", labelColor="#6B7280", titleColor="#374151",
                titleFontSize=12, labelFontSize=11, format=fmt)),
            y=alt.Y(f"{group_column}:N", sort=order, title=None, axis=alt.Axis(
                labelColor="#374151", labelFontSize=12, labelFontWeight=500,
                ticks=False, domain=False)),
            color=alt.condition(alt.datum.is_max, alt.value(color), alt.value("#D9E2EC")),
            tooltip=[alt.Tooltip(f"{group_column}:N", title=group_column),
                     alt.Tooltip(f"{metric}:Q", title=title, format=fmt)])

        labels = alt.Chart(d).mark_text(
            align="left", baseline="middle", dx=7, fontSize=12,
            fontWeight="bold", color="#374151"
        ).encode(x=f"{metric}:Q", y=alt.Y(f"{group_column}:N", sort=order),
                 text=alt.Text(f"{metric}:Q", format=fmt))

        charts.append((bars + labels).properties(
            width=width, height=height,
            title=alt.TitleParams(text=title, subtitle=subtitle, anchor="start",
                fontSize=16, fontWeight=600, color="#111827",
                subtitleFontSize=11, subtitleColor="#6B7280", offset=12)))

    chart = alt.hconcat(*charts, spacing=35)
    if main_title:
        chart = chart.properties(title=alt.TitleParams(
            text=main_title, anchor="start", fontSize=22, fontWeight="bold",
            color="#111827", offset=20))

    return chart.configure_view(strokeWidth=0).configure_axis(
        labelFont="Arial", titleFont="Arial"
    ).configure_title(font="Arial")

    
def grouped_scatter(df, x_variable, y_variable, group_column=None, size_column=None,
                    label_column=None, tooltip_columns=None, x_title=None, y_title=None,
                    chart_title=None):
    """Creates a generic scatter plot with optional grouping, sizing, and labels."""
    cols = [x_variable, y_variable] + [c for c in [group_column, size_column, label_column] if c]
    d = df[cols].dropna().copy()
    d = d[(d[x_variable] > 0) & (d[y_variable] > 0)]
    tooltip_columns = tooltip_columns or cols

    enc = {
        "x": alt.X(f"{x_variable}:Q", title=x_title or x_variable.replace("_", " ").title(),
                   axis=alt.Axis(labelColor="#6B7280", titleColor="#374151", grid=True, gridColor="#E5E7EB", gridOpacity=.7)),
        "y": alt.Y(f"{y_variable}:Q", title=y_title or y_variable.replace("_", " ").title(),
                   axis=alt.Axis(labelColor="#6B7280", titleColor="#374151", grid=True, gridColor="#E5E7EB", gridOpacity=.7)),
        "tooltip": tooltip_columns
    }
    if group_column: enc["color"] = alt.Color(f"{group_column}:N", title=group_column.replace("_", " ").title())
    if size_column: enc["size"] = alt.Size(f"{size_column}:Q", title=size_column.replace("_", " ").title(), scale=alt.Scale(range=[30, 800]))

    return alt.Chart(d).mark_circle(
        opacity=.8, stroke="white", strokeWidth=.7
    ).encode(**enc).properties(
        width=600, height=450,
        title=alt.TitleParams(
            text=chart_title, fontSize=16, fontWeight=600,
            color="#111827", anchor="start"
        )
    )

def efficiency_matrix(
    df, metrics, group_column, year_column=None, year=None,
    titles=None, normalize="zscore", chart_title=None,
    color_scheme="redblue", reverse_scale=False, width=500, height=300
):
    """
    Heatmap matrix (mode × metric) with independently normalized metrics.

    reverse_scale can be:
        - bool: same direction for all metrics
        - list of bools: one flag per metric, e.g. [False, True, True]
    """
    df_plot = df.copy()
    if year_column is not None and year is not None:
        df_plot = df_plot[df_plot[year_column] == year]

    titles = titles or metrics
    if len(titles) != len(metrics):
        raise ValueError("titles must have the same length as metrics.")

    if isinstance(reverse_scale, bool):
        reverse_flags = [reverse_scale] * len(metrics)
    else:
        reverse_flags = list(reverse_scale)
        if len(reverse_flags) != len(metrics):
            raise ValueError("reverse_scale must have one value per metric.")

    agg = df_plot.groupby(group_column, as_index=False)[metrics].mean()
    long = agg.melt(
        id_vars=group_column, value_vars=metrics,
        var_name="metric", value_name="raw_value"
    )

    if normalize == "zscore":
        long["norm_value"] = long.groupby("metric")["raw_value"].transform(
            lambda x: (x - x.mean()) / x.std()
        )
        legend_title = ["Std. deviations", "from mode average"]
        subtitle = "Each column standardized separately (z-score) — compare within a column, not across columns"
    elif normalize == "percent_of_max":
        long["norm_value"] = long.groupby("metric")["raw_value"].transform(
            lambda x: x / x.max() * 100
        )
        legend_title = ["% of highest", "value in column"]
        subtitle = "Each column scaled to % of that column's max — compare within a column, not across columns"
    else:
        raise ValueError("normalize must be 'zscore' or 'percent_of_max'.")

    reverse_map = dict(zip(metrics, reverse_flags))
    long["norm_value"] *= long["metric"].map(reverse_map).map({True: -1, False: 1})

    long["metric_label"] = long["metric"].map(dict(zip(metrics, titles)))

    return (
        alt.Chart(long)
        .mark_rect(stroke="white", strokeWidth=2)
        .encode(
            x=alt.X("metric_label:N", title=None, sort=titles,
                    axis=alt.Axis(labelAngle=0)),
            y=alt.Y(f"{group_column}:N", title=None),
            color=alt.Color(
                "norm_value:Q", title=legend_title,
                scale=alt.Scale(scheme=color_scheme, domainMid=0)
            ),
            tooltip=[
                alt.Tooltip(f"{group_column}:N", title="Mode"),
                alt.Tooltip("metric_label:N", title="Metric"),
                alt.Tooltip("raw_value:Q", title="Value", format=",.2f")
            ]
        )
        .properties(
            width=width, height=height,
            title=alt.TitleParams(
                text=chart_title, subtitle=subtitle,
                fontSize=16, fontWeight=600, color="#111827", anchor="start",
                subtitleFontSize=11, subtitleColor="#6B7280"
            )
        )
        .configure_view(strokeWidth=0)
        .configure_axis(labelFont="Arial", titleFont="Arial")
        .configure_title(font="Arial")
    )

def indexed_scissors(df, group_column, time_column, variable_columns, base_year,
                     variable_labels=None, colors=None, chart_title=None, chart_subtitle=None):
    """Creates an indexed line chart comparing variables to a base year."""
    labels = variable_labels or {c: c.replace("_", " ").title() for c in variable_columns}
    d = df[[group_column, time_column] + variable_columns].dropna()
    d = d.groupby([group_column, time_column], as_index=False)[variable_columns].sum()

    base = d[d[time_column] == base_year].rename(columns={c: f"{c}_base" for c in variable_columns})
    d = d.merge(base[[group_column] + [f"{c}_base" for c in variable_columns]], on=group_column)
    for c in variable_columns:
        d[f"{c}_index"] = d[c] / d[f"{c}_base"] * 100

    long = d.melt([group_column, time_column], [f"{c}_index" for c in variable_columns],
                  var_name="metric", value_name="index")
    long["metric"] = long["metric"].map({f"{c}_index": labels[c] for c in variable_columns})

    return (
        alt.Chart(long).mark_line(point=True, strokeWidth=2.5).encode(
        x=alt.X(f"{time_column}:O", title=time_column.replace("_", " ").title()),
        y=alt.Y("index:Q", title=f"Index ({base_year} = 100)"),
        color=alt.Color("metric:N", title=None,
                        scale=alt.Scale(domain=list(labels.values()), range=colors) if colors else None),
        detail="metric:N",
        tooltip=[group_column, time_column, "metric", alt.Tooltip("index:Q", format=".1f")]
    ).properties(width=250, height=180)
     .facet(f"{group_column}:N", columns=3, title=None)
     .properties(title=alt.TitleParams(text=chart_title, subtitle=chart_subtitle,
                                       fontSize=18, fontWeight=600, anchor="start"))
     .configure_view(strokeWidth=0)
    )

