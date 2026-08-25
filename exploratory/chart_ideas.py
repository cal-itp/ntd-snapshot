# Chart functions
import altair as alt
from pywaffle import Waffle

from process_ntd import (
    load_service_and_opex,
    subset_california,
    add_mode_group,
)

alt.data_transformers.enable("vegafusion")

def prep_for_mode_trend(df):
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

def mode_trend_chart(df, value_column):
    nearest = alt.selection_point(
        nearest = True,
        on= "pointerover",
        fields=["year"],
        empty=False,
    )

    line = alt.Chart(df).mark_line().encode(
        x="year:O",
        y = alt.Y(f"{value_column}:Q"),
        color= "mode_group:N",
    )
    
    selectors = (
        alt.Chart(df)
        .mark_point()
        .encode(
            x= "year:O",
            opacity = alt.value(0))
        .add_params(nearest)
    )

    # Highlight points
    points = line.mark_point().encode(
        opacity=alt.when(nearest).then(alt.value(1)).otherwise(alt.value(0)),
        tooltip=[
            "year",
            "mode_group",
            alt.Tooltip("unlinked_passenger_trips:Q", format=",")
        ]
    )
    
    # Vertical hover line
    rules = alt.Chart(ca_bus_rail_upt).mark_rule(color="gray").encode(
        x="year:O"
    ).transform_filter(
        nearest
    )
    
    # Combine
    trend_chart = (
        alt.layer(line, selectors, points, rules)
        .properties(width=700, height=400)
    )


    return trend_chart
    


def scatter_plot_regression(
    df,
    x_variable,
    y_variable,
    tooltip_columns=None,
    chart_title=None
):
    """Creates a filtered scatter plot with a regression trend line.."""

    df_filtered = df[
        (df[x_variable] > 0) & (df[y_variable] > 0)
    ]

    if tooltip_columns is None:
        tooltip_columns = [x_variable, y_variable]

    scatter = alt.Chart(df_filtered).mark_circle(
        opacity=0.5
    ).encode(
        x=alt.X(x_variable + ':Q', title=x_variable),
        y=alt.Y(y_variable + ':Q', title=y_variable),
        tooltip=tooltip_columns
    )

    trend = alt.Chart(df_filtered).transform_regression(
        x_variable,
        y_variable
    ).mark_line(
        color='darkblue',
        size=3
    ).encode(
        x=x_variable + ':Q',
        y=y_variable + ':Q'
    )

    compare_chart = (scatter + trend).properties(
        width=600,
        height=400,
        title=chart_title
    )

    return compare_chart


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
    df,
    group_column,
    category_columns,
    year_column=None,
    year=None,
    rank_column=None,
    top_n=10,
    chart_title=None,
    chart_subtitle=None,
    y_title="Percentage",
    colors=None,
    width=750,
    height=450
):
    """
    Creates a 100% stacked bar chart showing the composition of a value
    across groups.

    Parameters:
        df: DataFrame containing the data.
        group_column: What gets a bar (e.g., "source_agency").
        category_columns: What makes up each bar, provided as a dictionary
            mapping category names to value columns.
        rank_column: What determines the top groups (e.g., "unlinked_passenger_trips").
        year_column: Time variable used to filter the data (e.g., "year").
        year: Specific year to include.
        top_n: Number of top groups to display.
        chart_title: Optional chart title.
        chart_subtitle: Optional chart subtitle.
        y_title: Label for the y-axis.
        colors: Optional list of colors for the categories.
        width: Chart width.
        height: Chart height.
    """

    df_plot = df.copy()

    if year_column is not None and year is not None:
        df_plot = df_plot[df_plot[year_column] == year]

    if rank_column is not None:
        top_groups = (
            df_plot
            .groupby(group_column)[rank_column]
            .sum()
            .nlargest(top_n)
            .index
            .tolist()
        )

        df_plot = df_plot[
            df_plot[group_column].isin(top_groups)
        ]

    else:
        top_groups = (
            df_plot[group_column]
            .drop_duplicates()
            .tolist()
        )

    data = (
        df_plot
        .groupby(group_column)[list(category_columns.values())]
        .sum()
        .reset_index()
    )

    data = (
        data[
            [group_column] + list(category_columns.values())
        ]
        .melt(
            id_vars=group_column,
            var_name="category_column",
            value_name="amount"
        )
    )

    reverse_mapping = {
        v: k for k, v in category_columns.items()
    }

    data["category"] = data["category_column"].map(
        reverse_mapping
    )

    data["total"] = (
        data
        .groupby(group_column)["amount"]
        .transform("sum")
    )

    data["percentage"] = (
        data["amount"] / data["total"] * 100
    )

    chart = (
        alt.Chart(data)
        .mark_bar()
        .encode(
            x=alt.X(
                group_column + ":N",
                title=group_column,
                sort=top_groups,
                axis=alt.Axis(labelAngle=-25)
            ),

            y=alt.Y(
                "sum(percentage):Q",
                title=y_title,
                scale=alt.Scale(domain=[0, 100]),
                axis=alt.Axis(format=".0f")
            ),

            color=alt.Color(
                "category:N",
                title="Category",
                scale=(
                    alt.Scale(range=colors)
                    if colors is not None
                    else alt.Scale()
                )
            ),

            tooltip=[
                alt.Tooltip(
                    group_column + ":N",
                    title=group_column
                ),
                alt.Tooltip(
                    "category:N",
                    title="Category"
                ),
                alt.Tooltip(
                    "percentage:Q",
                    title="Share",
                    format=".1f"
                ),
                alt.Tooltip(
                    "amount:Q",
                    title="Amount",
                    format=",.0f"
                )
            ]
        )
        .properties(
            title=alt.TitleParams(
                text=chart_title,
                subtitle=chart_subtitle
            ),
            width=width,
            height=height
        )
    )

    return chart


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
    category_title=None
):
    """
    Creates a ridge plot showing the distribution of a numeric variable
    across categories.

    Parameters:
        df: DataFrame containing the data.
        value_column: Numeric column whose distribution is shown (e.g., "farebox_recovery_ratio").
        category_column: Column defining the groups shown as separate ridges (e.g., "mode_full_name").
        year_column: Time variable used to filter the data (e.g., "year").
        year: Specific year to include.
        filters: Optional dictionary of column-value pairs used to filter data.
        value_min: Optional minimum value to include.
        value_max: Optional maximum value to include.
        step: Height of each ridge.
        overlap: Amount of overlap between ridges.
        chart_title: Optional chart title.
        chart_subtitle: Optional chart subtitle.
        x_title: Optional x-axis title.
        category_title: Optional category legend title.
    """

    df_plot = df.copy()

    # Filter year
    if year_column is not None and year is not None:
        df_plot = df_plot[df_plot[year_column] == year]

    # Apply additional filters
    if filters is not None:
        for column, values in filters.items():
            if isinstance(values, list):
                df_plot = df_plot[df_plot[column].isin(values)]
            else:
                df_plot = df_plot[df_plot[column] != values]

    # Filter invalid values
    df_plot = df_plot[
        df_plot[value_column].notna()
    ]

    if value_min is not None:
        df_plot = df_plot[df_plot[value_column] >= value_min]

    if value_max is not None:
        df_plot = df_plot[df_plot[value_column] <= value_max]

    chart = (
        alt.Chart(df_plot, width=800, height=step)
        .transform_density(
            value_column,
            groupby=[category_column],
            as_=[value_column, "density"]
        )
        .mark_area(
            interpolate="monotone",
            fillOpacity=0.8,
            stroke="white",
            strokeWidth=0.5
        )
        .encode(
            x=alt.X(
                value_column + ":Q",
                title=x_title or value_column
            ),

            y=alt.Y(
                "density:Q",
                axis=None,
                scale=alt.Scale(
                    range=[step, -step * overlap]
                )
            ),

            color=alt.Color(
                category_column + ":N",
                title=category_title or category_column
            ),

            tooltip=[
                alt.Tooltip(
                    category_column + ":N",
                    title=category_title or category_column
                ),
                alt.Tooltip(
                    value_column + ":Q",
                    title=x_title or value_column,
                    format=".3f"
                ),
                alt.Tooltip(
                    "density:Q",
                    title="Density",
                    format=".3f"
                )
            ]
        )
        .facet(
            row=alt.Row(
                category_column + ":N",
                title=None,
                header=alt.Header(
                    labelAngle=0,
                    labelAlign="left"
                )
            )
        )
        .properties(
            title=alt.TitleParams(
                text=chart_title,
                subtitle=chart_subtitle
            ),
            bounds="flush"
        )
        .configure_facet(spacing=0)
        .configure_view(stroke=None)
    )

    return chart


    
                
        
    


       
        

    
            
        
        
        