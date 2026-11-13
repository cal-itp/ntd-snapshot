import textwrap

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
    "labelFontSize": 12,
    "titleFontSize": 15,
    "labelColor": NEUTRAL_COLORS["axis_label"],
    "titleColor": NEUTRAL_COLORS["axis_title"],
    "labelFontWeight": 500,
    "titleFontWeight": 500,
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


# RTPA profile dashboard
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
    service_map = {
        "DO": "DIRECTLY OPERATED",
        "PT": "PURCHASED",
        "TX": "PURCHASED",
        "TN": "PURCHASED",
    }

    service = data[data["year"] == latest_year].copy()
    service["service_type"] = (
        service["type_of_service"].astype(str).str.strip().str.upper().map(service_map)
    )

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
    colors = [
        BRAND_COLORS["navy"],
        BRAND_COLORS["teal"],
        BRAND_COLORS["yellow"],
        BRAND_COLORS["blue"],
    ]

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
            .mark_text(font=CHART_FONT, baseline="middle", **kw)
            .encode(x=alt.value(x), y=alt.value(y), text=alt.value(text))
        )

    static = [
        rect(0, W, 0, HDR, BRAND_COLORS["navy"]),
        rect(0, W, 0, 3, BRAND_COLORS["teal"]),
        rect(0, W, HDR, H, NEUTRAL_COLORS["background"]),
        label(
            "REGIONAL PROFILE / RTPA",
            26,
            16,
            align="left",
            color=PASTEL_COLORS[7],
            fontSize=11,
            fontWeight="bold",
        ),
        label(
            rtpa_name,
            24,
            40,
            align="left",
            color=NEUTRAL_COLORS["surface"],
            fontSize=22,
            fontWeight="bold",
        ),
        label(
            county_line,
            24,
            66,
            align="left",
            color=NEUTRAL_COLORS["surface"],
            fontSize=12,
            limit=W - 48,
        ),
        label(
            district_line,
            24,
            84,
            align="left",
            color=NEUTRAL_COLORS["surface"],
            fontSize=12,
            limit=W - 48,
        ),
        label(
            f"{total_agencies} agencies · Reporting years {first_year}–{latest_year}",
            W - 24,
            40,
            align="right",
            color=NEUTRAL_COLORS["surface"],
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
                color=BRAND_COLORS["teal"],
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
                    font=CHART_FONT,
                    align="left",
                    baseline="top",
                    lineBreak="\n",
                    color=BRAND_COLORS["navy"],
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
                    font=CHART_FONT,
                    align="left",
                    baseline="top",
                    lineBreak="\n",
                    color=NEUTRAL_COLORS["subtle_text"],
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
                    range=[BRAND_COLORS["teal"], BRAND_COLORS["yellow"]],
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
        f"AGENCY OPERATING STRUCTURE (% OF VRH) — {latest_year}",
        0,
        12,
        align="left",
        color=BRAND_COLORS["navy"],
        fontSize=13,
        fontWeight="bold",
    ).properties(width=450, height=25)

    percentages = (
        alt.Chart(bar_data)
        .transform_filter(alt.datum.ntd_id == agency_param)
        .transform_calculate(label="format(datum.percentage, '.1f') + '%'")
        .mark_text(font=CHART_FONT, fontSize=12, fontWeight="bold")
        .encode(
            x=alt.X("type:N", axis=None),
            text="label:N",
            color=alt.Color(
                "type:N",
                scale=alt.Scale(
                    domain=["DIRECTLY OPERATED", "PURCHASED"],
                    range=[BRAND_COLORS["teal"], BRAND_COLORS["yellow"]],
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
        .mark_text(font=CHART_FONT, fontSize=10, color=NEUTRAL_COLORS["subtle_text"])
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


def rtpa_ntd_value_profile(datasets, rtpa, width=400, height=300, chart_titles=None):
    """RTPA dashboard with shared agency dropdown and dynamic agency subtitles."""
    group_cols = ["source_agency", "ntd_id", "year"]
    aggregated, agencies = {}, set()
    chart_titles = chart_titles or {}

    for value_col, (df, chart_title) in datasets.items():
        d = df[df["rtpa_name"] == rtpa].copy()
        aggregated[value_col] = (
            d.groupby(group_cols, as_index=False)[value_col].sum(),
            chart_titles.get(value_col, chart_title),
        )
        agencies.update(d["source_agency"].dropna().unique())

    agencies = sorted(agencies)
    agency_sel = alt.param(
        name="agency",
        value=None,
        bind=alt.binding_select(
            options=[None] + agencies,
            labels=["All agencies"] + agencies,
            name="Agency: ",
        ),
    )

    charts = []
    for i, (value_col, (agg, chart_title)) in enumerate(aggregated.items()):
        agg = agg.rename(columns={value_col: "value"})
        chart_width = width * 2 if i == 0 else width

        title = (
            alt.Chart({"values": [{}]})
            .mark_text(
                align="left",
                baseline="middle",
                font=CHART_FONT,
                fontSize=16,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
            )
            .encode(x=alt.value(0), y=alt.value(12), text=alt.value(chart_title))
            .properties(width=chart_width, height=25)
        )

        subtitle = (
            alt.Chart({"values": [{}]})
            .transform_calculate(t="agency ? agency : 'All agencies'")
            .mark_text(
                align="left",
                baseline="middle",
                font=CHART_FONT,
                fontSize=12,
                color=NEUTRAL_COLORS["subtle_text"],
            )
            .encode(x=alt.value(0), y=alt.value(10), text="t:N")
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
                    axis=alt.Axis(
                        **{**ALT_AXIS_CONFIG, **ALT_GRID_CONFIG, "format": "~s"}
                    ),
                    scale=alt.Scale(zero=False),
                ),
                color=alt.Color(
                    "source_agency:N",
                    scale=alt.Scale(
                        domain=agencies, range=CALITP_CATEGORY_BRIGHT_COLORS
                    ),
                    legend=None,
                ),
                tooltip=[
                    "source_agency:N",
                    "year:O",
                    alt.Tooltip("value:Q", format=","),
                ],
            )
            .transform_filter("!agency || datum.source_agency == agency")
            .properties(width=chart_width, height=height)
        )
        charts.append(alt.vconcat(title, subtitle, chart, spacing=2))

    rows = [charts[0]]
    rows.extend(
        alt.hconcat(*charts[i : i + 2], spacing=20) for i in range(1, len(charts), 2)
    )

    dashboard = (
        alt.vconcat(*rows, spacing=25)
        .add_params(agency_sel)
        .resolve_scale(y="independent")
        .configure_view(strokeWidth=0, fill=NEUTRAL_COLORS["background"])
        .configure_axis(**ALT_AXIS_CONFIG)
        .configure_legend(**ALT_LEGEND_CONFIG)
        .configure_title(font=CHART_FONT)
    )
    return dashboard, agency_sel


# RTPA Breakdown Chart
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

    d = df.loc[df[rtpa_column] == rtpa].copy()
    agencies = sorted(d[agency_column].dropna().unique().tolist())
    years = sorted(d[year_column].dropna().unique().tolist())

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
                f"{group_column}:N",
                title="Mode",
                axis=alt.Axis(labelAngle=0),
            ),
            y=alt.Y(
                "amount:Q",
                stack="normalize" if normalize else "zero",
                title="Share of Total" if normalize else "Amount ($M)",
                axis=alt.Axis(
                    **{
                        **ALT_AXIS_CONFIG,
                        **ALT_GRID_CONFIG,
                        "format": ".0%" if normalize else ",.1f",
                    }
                ),
            ),
            color=alt.Color(
                "component:N",
                title="Component",
                scale=alt.Scale(
                    domain=plot_df["component"].unique().tolist(),
                    range=PASTEL_COLORS,
                ),
                legend=alt.Legend(orient="right", direction="vertical"),
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
                font=CHART_FONT,
                fontSize=16,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                anchor="start",
            ),
        )
    )

    return chart, agency_sel, year_sel


# RTPA funding composition
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
    d = df.loc[df[rtpa_column] == rtpa].copy()

    agencies = sorted(d[agency_column].dropna().unique().tolist())
    years = sorted(d[year_column].dropna().unique().tolist())

    plot_df = d.groupby([year_column, agency_column], as_index=False, dropna=False)[
        component_columns
    ].sum()
    plot_df = plot_df.melt(
        id_vars=[year_column, agency_column],
        var_name="component",
        value_name="amount",
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
        bind=alt.binding_select(options=agencies, name="Agency: "),
        value=[{agency_column: agencies[0]}],
    )
    year_sel = alt.selection_point(
        name="Year",
        fields=[year_column],
        bind=alt.binding_select(options=years, name="Year: "),
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
                title="Share of Total" if normalize else "Amount ($M)",
                axis=alt.Axis(
                    **{
                        **ALT_AXIS_CONFIG,
                        **ALT_GRID_CONFIG,
                        "format": ".0%" if normalize else ",.1f",
                    }
                ),
            ),
            color=alt.Color(
                "component:N",
                title="Funding Source",
                scale=alt.Scale(
                    domain=plot_df["component"].unique().tolist(),
                    range=PASTEL_COLORS,
                ),
                legend=alt.Legend(orient="right", direction="vertical"),
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
                font=CHART_FONT,
                fontSize=16,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                anchor="start",
            ),
        )
    )
    return chart, agency_sel, year_sel


# Grouped Ranking Chart
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

    colors = [
        BRAND_COLORS["teal"],
        BRAND_COLORS["blue"],
        BRAND_COLORS["yellow"],
        NEUTRAL_COLORS["grey"],
    ]

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
            axis=alt.Axis(
                labelLimit=180, ticks=False, domain=False, labelFont=AXIS_FONT
            ),
        )

        bars = base.mark_bar(cornerRadiusEnd=3, height=15).encode(
            x=alt.X(
                metric + ":Q",
                title=None,
                axis=alt.Axis(
                    grid=True,
                    gridColor=ALT_GRID_CONFIG["gridColor"],
                    gridOpacity=ALT_GRID_CONFIG["gridOpacity"],
                    tickCount=4,
                    format="$,.0f",
                ),
            ),
            y=y,
            color=alt.value(color),
            tooltip=[
                "source_agency:N",
                alt.Tooltip(metric + ":Q", format="$.2f"),
                "rank:Q",
            ],
        )

        labels = base.mark_text(**ALT_TEXT_CONFIG).encode(
            x=metric + ":Q", y=y, text="value_label:N"
        )

        return alt.layer(bars, labels).properties(
            width=panel_w,
            height=alt.Step(bar_step),
            title=alt.Title(
                str(group),
                font=CHART_FONT,
                fontSize=14,
                fontWeight="bold",
                color=NEUTRAL_COLORS["axis_title"],
                anchor="start",
            ),
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
                    font=CHART_FONT,
                    fontSize=17,
                    fontWeight="bold",
                    color=NEUTRAL_COLORS["axis_title"],
                )
            )
        )

    return (
        alt.vconcat(*rows, spacing=15)
        .add_params(year_p, mode_p)
        .configure_view(stroke=None)
        .configure_axis(**ALT_AXIS_CONFIG)
        .configure_title(color=NEUTRAL_COLORS["axis_title"], font=CHART_FONT)
        .configure_concat(spacing=15)
    )


# Agency Opex Dashboard
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
    peer_colors = alt.Scale(
        domain=["Rural", "Urban"], range=[BRAND_COLORS["teal"], BRAND_COLORS["yellow"]]
    )
    charts, cards = [], []
    card_w = (width - 40) / 3

    # KPI CARDS
    for m, title, fmt in metrics:
        selected = (
            alt.Chart(d)
            .transform_filter(
                f"datum[{repr(year_col)}] == yr && datum[{repr(mode_col)}] == mode && datum[{repr(agency_col)}] == agency && isValid(datum.{m})"
            )
            .transform_aggregate(value=f"mean({m})")
        )

        card_bg = (
            alt.Chart({"values": [{}]})
            .mark_rect(
                color=NEUTRAL_COLORS["surface"],
                stroke=NEUTRAL_COLORS["border"],
                strokeWidth=1,
                cornerRadius=8,
            )
            .encode(
                x=alt.value(0), x2=alt.value(card_w), y=alt.value(0), y2=alt.value(76)
            )
        )

        card_label = (
            alt.Chart({"values": [{}]})
            .mark_text(
                align="left",
                baseline="middle",
                font=CHART_FONT,
                fontSize=12,
                fontWeight=500,
                color=NEUTRAL_COLORS["axis_label"],
            )
            .encode(x=alt.value(14), y=alt.value(20), text=alt.value(title))
        )

        card_value = selected.mark_text(
            align="left",
            baseline="middle",
            font=CHART_FONT,
            fontSize=25,
            fontWeight="bold",
            color=CALITP_CATEGORY_BRIGHT_COLORS[5],
        ).encode(x=alt.value(14), y=alt.value(51), text=alt.Text("value:Q", format=fmt))

        cards.append(
            alt.layer(card_bg, card_label, card_value).properties(
                width=card_w, height=76
            )
        )

    # PEER COMPARISON CHARTS
    for m, title, fmt in metrics:
        base = alt.Chart(d).transform_filter(
            f"datum[{repr(year_col)}] == yr && datum[{repr(mode_col)}] == mode && isValid(datum.{m})"
        )

        axis_y = alt.Y(
            type_col + ":N",
            title=None,
            sort=["Rural", "Urban"],
            scale=alt.Scale(paddingInner=0.4, paddingOuter=0.3),
            axis=alt.Axis(
                labelPadding=12,
                labelLimit=150,
                ticks=False,
                domain=False,
                labelColor=NEUTRAL_COLORS["axis_title"],
            ),
        )

        median = (
            base.transform_aggregate(median_value=f"median({m})", groupby=[type_col])
            .mark_tick(thickness=5, size=32)
            .encode(
                x=alt.X(
                    "median_value:Q",
                    title=title,
                    axis=alt.Axis(
                        format=fmt, **ALT_GRID_CONFIG, tickCount=5, titlePadding=10
                    ),
                ),
                y=axis_y,
                color=alt.Color(type_col + ":N", scale=peer_colors, legend=None),
                tooltip=[
                    alt.Tooltip("median_value:Q", title="Peer group median", format=fmt)
                ],
            )
        )

        points = (
            base.transform_filter(f"datum[{repr(agency_col)}] != agency")
            .mark_circle(stroke="white", strokeWidth=1.2, opacity=1, size=110)
            .encode(
                x=alt.X(
                    m + ":Q",
                    title=title,
                    axis=alt.Axis(
                        format=fmt, **ALT_GRID_CONFIG, tickCount=5, titlePadding=10
                    ),
                ),
                y=axis_y,
                color=alt.Color(
                    type_col + ":N",
                    scale=peer_colors,
                    legend=alt.Legend(orient="right", direction="vertical"),
                ),
                tooltip=[
                    alt.Tooltip(agency_col + ":N", title="Agency"),
                    alt.Tooltip(type_col + ":N", title="Classification"),
                    alt.Tooltip(m + ":Q", title=title, format=fmt),
                ],
            )
        )

        selected_point = (
            base.transform_filter(f"datum[{repr(agency_col)}] == agency")
            .mark_point(
                shape="diamond",
                filled=True,
                color=CALITP_CATEGORY_BRIGHT_COLORS[5],
                size=260,
                stroke="white",
                strokeWidth=1.2,
            )
            .encode(
                x=alt.X(
                    m + ":Q",
                    title=title,
                    axis=alt.Axis(
                        format=fmt, **ALT_GRID_CONFIG, tickCount=5, titlePadding=10
                    ),
                ),
                y=axis_y,
                tooltip=[
                    alt.Tooltip(agency_col + ":N", title="Agency"),
                    alt.Tooltip(type_col + ":N", title="Classification"),
                    alt.Tooltip(m + ":Q", title=title, format=fmt),
                ],
            )
        )

        charts.append(
            alt.layer(median, points, selected_point).properties(
                width=width, height=125
            )
        )

    # DASHBOARD HEADER
    header_title = (
        alt.Chart({"values": [{}]})
        .transform_calculate(
            t=f"{repr(dashboard_title + ' | ')} + toString(yr) + ' | ' + mode"
        )
        .mark_text(
            align="left",
            baseline="middle",
            font=CHART_FONT,
            fontSize=20,
            fontWeight="bold",
            color=BRAND_COLORS["navy"],
        )
        .encode(x=alt.value(0), y=alt.value(15), text="t:N")
        .properties(width=width, height=35)
    )

    header_subtitle = (
        alt.Chart({"values": [{}]})
        .transform_calculate(t="agency")
        .mark_text(
            align="left",
            baseline="middle",
            font=CHART_FONT,
            fontSize=15,
            fontWeight="bold",
            color=BRAND_COLORS["navy"],
        )
        .encode(x=alt.value(0), y=alt.value(12), text="t:N")
        .properties(width=width, height=30)
    )

    header = alt.vconcat(header_title, header_subtitle, spacing=0)

    return (
        alt.vconcat(header, alt.hconcat(*cards, spacing=15), *charts, spacing=16)
        .add_params(yp, ap, mp)
        .configure_view(stroke=None, fill=NEUTRAL_COLORS["background"])
        .configure_axis(**ALT_AXIS_CONFIG)
        .configure_legend(
            **{**ALT_LEGEND_CONFIG, "orient": "right", "direction": "vertical"}
        )
        .configure_title(font=CHART_FONT, anchor="start")
        .configure_concat(spacing=16)
    )


# Apex Service Growth
def agency_opex_service_growth(
    dataframes,
    rtpa,
    metrics,
    agency_col="source_agency",
    rtpa_col="rtpa_name",
    mode_col="mode_full_name",
    year_col="year",
    width=750,
    height=320,
):
    growth_frames = []
    for col, (source, label) in metrics.items():
        d = dataframes[source]
        d = d.loc[d[rtpa_col] == rtpa].copy()

        annual = (
            d.groupby([agency_col, mode_col, year_col], as_index=False)[col]
            .sum()
            .sort_values([agency_col, mode_col, year_col])
        )

        annual["growth"] = (
            annual.groupby([agency_col, mode_col])[col].pct_change() * 100
        )

        annual["metric"] = label
        growth_frames.append(
            annual[[agency_col, mode_col, year_col, "metric", "growth"]]
        )

    growth = pd.concat(growth_frames, ignore_index=True)
    growth = growth.dropna(subset=["growth"])

    agencies = sorted(growth[agency_col].unique().tolist())
    modes = sorted(growth[mode_col].unique().tolist())
    years = sorted(growth[year_col].unique().tolist())

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

    metric_order = [label for source, label in metrics.values()]
    filter_expr = (
        f"datum[{repr(agency_col)}] == agency_sel && "
        f"datum[{repr(mode_col)}] == mode_sel && "
        f"datum[{repr(year_col)}] == year_sel"
    )
    base = alt.Chart(growth).transform_filter(filter_expr)

    chart = (
        base.mark_bar(cornerRadiusEnd=3, size=28, color=BRAND_COLORS["teal"])
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
                axis=alt.Axis(format=".0f", **ALT_GRID_CONFIG),
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
            **{**ALT_TEXT_CONFIG, "fontWeight": "bold", "color": BRAND_COLORS["navy"]},
            dy=alt.expr("datum.growth >= 0 ? -10 : 10"),
        )
        .encode(
            x=alt.X("metric:N", sort=metric_order),
            y=alt.Y("growth:Q"),
            text=alt.Text("label:N"),
        )
    )

    title = (
        alt.Chart({"values": [{}]})
        .mark_text(
            align="left",
            font=CHART_FONT,
            fontSize=19,
            fontWeight="bold",
            color=BRAND_COLORS["navy"],
        )
        .encode(
            x=alt.value(0),
            y=alt.value(16),
            text=alt.value("Agency Operating & Service Performance Growth"),
        )
        .properties(width=width, height=28)
    )

    subtitle = (
        alt.Chart({"values": [{}]})
        .transform_calculate(
            t="agency_sel + ' | ' + mode_sel + ' | ' + toString(year_sel - 1) + '–' + toString(year_sel)"
        )
        .mark_text(
            align="left",
            font=CHART_FONT,
            fontSize=13,
            fontWeight=500,
            color=NEUTRAL_COLORS["axis_label"],
        )
        .encode(x=alt.value(0), y=alt.value(12), text="t:N")
        .properties(width=width, height=24)
    )

    return (
        alt.vconcat(title, subtitle, alt.layer(chart, labels), spacing=5)
        .add_params(agency_p, mode_p, year_p)
        .configure_view(stroke=None)
        .configure_axis(
            **{
                **ALT_AXIS_CONFIG,
                "labelPadding": 12,
                "labelLimit": 250,
                "labelColor": NEUTRAL_COLORS["axis_title"],
                "labelFontSize": 12,
                "labelFontWeight": 500,
            }
        )
        .configure_title(font=CHART_FONT, anchor="start")
    )


# Farebox Recovery Chart
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

    d[year_column] = pd.to_numeric(d[year_column], errors="coerce")
    d[recovery_column] = pd.to_numeric(d[recovery_column], errors="coerce")
    d[fare_column] = pd.to_numeric(d[fare_column], errors="coerce")
    d[subsidy_column] = pd.to_numeric(d[subsidy_column], errors="coerce")
    d = d.dropna(subset=[year_column, recovery_column, fare_column, subsidy_column])

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
        f"datum[{repr(year_column)}] == year_sel && "
        f"(mode_sel == 'All Modes' || datum[{repr(mode_column)}] == mode_sel)"
    )

    points = (
        alt.Chart(d)
        .transform_filter(filter_expr)
        .mark_circle(
            size=160, opacity=0.9, stroke=NEUTRAL_COLORS["surface"], strokeWidth=1.2
        )
        .encode(
            x=alt.X(
                f"{fare_column}:Q",
                title="Fare Revenue per Trip ($)",
                axis=alt.Axis(format="$,.2f", **ALT_GRID_CONFIG, labelPadding=10),
            ),
            y=alt.Y(
                f"{subsidy_column}:Q",
                title="Net Subsidy per Trip ($)",
                axis=alt.Axis(format="$,.2f", **ALT_GRID_CONFIG, labelPadding=10),
            ),
            color=alt.Color(
                f"{recovery_column}:Q",
                title="Farebox Recovery",
                scale=alt.Scale(
                    range=DIVERGING_COLORS["bluegreen"], domain=[0, 0.5, 1], clamp=True
                ),
                legend=alt.Legend(
                    orient="right",
                    direction="vertical",
                    gradientLength=150,
                    gradientThickness=16,
                ),
            ),
            tooltip=[
                alt.Tooltip(f"{agency_column}:N", title="Agency"),
                alt.Tooltip(f"{id_column}:N", title="NTD ID"),
                alt.Tooltip("reporting_module:N", title="Reporting Module"),
                alt.Tooltip(f"{mode_column}:N", title="Mode"),
                alt.Tooltip(f"{year_column}:Q", title="Year", format=".0f"),
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
            align="left",
            font=CHART_FONT,
            fontSize=19,
            fontWeight="bold",
            color=BRAND_COLORS["navy"],
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
            t=f"{repr(rtpa_name + ' | ')} + mode_sel + ' | ' + toString(year_sel) + "
            "' | Each point represents one agency-mode combination'"
        )
        .mark_text(
            align="left",
            font=CHART_FONT,
            fontSize=13,
            fontWeight=500,
            color=NEUTRAL_COLORS["axis_label"],
        )
        .encode(x=alt.value(0), y=alt.value(12), text="t:N")
        .properties(width=width, height=24)
    )

    return (
        alt.vconcat(title, subtitle, points, spacing=3)
        .add_params(year_p, mode_p)
        .configure_view(stroke=None, fill=NEUTRAL_COLORS["surface"])
        .configure_axis(**ALT_AXIS_CONFIG)
        .configure_legend(
            **ALT_LEGEND_CONFIG,
            orient="right",
            direction="vertical",
            padding=8,
            offset=12,
        )
    )


# RTPA vs State Funding Share Chart
def rtpa_vs_state_funding_share(
    expense_sources,
    df,
    components,
    rtpa,
    rtpa_column,
    id_column,
    year_column,
    agency_column,
    ncols=2,
    min_n_fit=10,
    panel_width=380,
    panel_height=280,
    title=None,
):
    """
    Grid of scatters, one panel per funding source.
    Grey = statewide agencies; colored = selected RTPA.
    Fit line and statistics are statewide.
    """

    keys = [id_column, year_column]
    comp_cols = [c for cols in components.values() for c in cols]
    extra = [agency_column, rtpa_column]

    # STATEWIDE DATA
    labels = df.groupby(keys, as_index=False)[extra].first()
    funds = df.groupby(keys, as_index=False)[comp_cols].sum()
    df = labels.merge(funds, on=keys, how="left")
    df["in_rtpa"] = df[rtpa_column] == rtpa

    # EXPENSES
    exp_cols = []
    for i, (d, cols) in enumerate(expense_sources):
        agg = d.groupby(keys, as_index=False)[cols].sum()
        agg = agg.rename(columns={c: f"exp{i}__{c}" for c in cols})
        df = df.merge(agg, on=keys, how="left")
        exp_cols += [f"exp{i}__{c}" for c in cols]
    df[exp_cols] = df[exp_cols].fillna(0)
    df["total_expenses"] = df[exp_cols].sum(axis=1) / 1_000_000

    # FUNDING SHARES
    for name, cols in components.items():
        df[f"amt_{name}"] = df[cols].sum(axis=1) / 1_000_000
    df["total_funding"] = df[[f"amt_{n}" for n in components]].sum(axis=1)
    df = df[(df["total_expenses"] > 0) & (df["total_funding"] > 0)].copy()

    id_vars = [
        id_column,
        year_column,
        agency_column,
        rtpa_column,
        "in_rtpa",
        "total_expenses",
        "total_funding",
    ]

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

    # STATEWIDE FIT
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
                    "label": f"Statewide: slope = {slope:+.2f}   R² = {r2:.2f}   n = {len(g)} ({n_rtpa} in RTPA)",
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

    # YEAR SELECTION
    year_sel = alt.selection_point(
        name="Year",
        fields=[year_column],
        bind=alt.binding_select(options=years, name="Year: "),
        value=[{year_column: years[-1]}],
    )

    x_scale = alt.Scale(type="log", domain=[lo * 0.8, hi * 1.25])
    y_scale = alt.Scale(domain=[0, 1])
    color = alt.value(PASTEL_COLORS[15])

    tooltip = [
        alt.Tooltip(f"{year_column}:O", title="Year"),
        alt.Tooltip(f"{agency_column}:N", title="Agency"),
        alt.Tooltip(f"{rtpa_column}:N", title="RTPA"),
        alt.Tooltip("funding_type:N", title="Funding Source"),
        alt.Tooltip("share:Q", title="Share of Funding", format=".1%"),
        alt.Tooltip("amount:Q", title="Source Amount ($M)", format=",.1f"),
        alt.Tooltip("total_funding:Q", title="Total Funding ($M)", format=",.1f"),
        alt.Tooltip("total_expenses:Q", title="Total Expenses ($M)", format=",.1f"),
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
                    title="Total Expenses ($M, log)" if is_bottom else None,
                    axis=alt.Axis(format=",.0f", **ALT_GRID_CONFIG),
                ),
                y=alt.Y(
                    "share:Q",
                    scale=y_scale,
                    title="Share of Total Funding" if is_left else None,
                    axis=alt.Axis(format=".0%", **ALT_GRID_CONFIG),
                ),
            )

        # STATEWIDE AGENCIES
        others = (
            enc(
                alt.Chart(long).mark_circle(
                    opacity=0.4, size=45, color=NEUTRAL_COLORS["light_grey"], clip=True
                )
            )
            .encode(tooltip=tooltip)
            .transform_filter("!datum.in_rtpa")
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )
        if i == 0:
            others = others.add_params(year_sel)

        # SELECTED RTPA
        mine = (
            enc(
                alt.Chart(long).mark_circle(
                    opacity=0.95,
                    size=110,
                    clip=True,
                    stroke=NEUTRAL_COLORS["surface"],
                    strokeWidth=1,
                )
            )
            .encode(color=color, tooltip=tooltip)
            .transform_filter("datum.in_rtpa")
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )

        fit_line = (
            alt.Chart(fit_df)
            .mark_line(color=BRAND_COLORS["navy"], strokeWidth=2)
            .encode(x=alt.X("x:Q", scale=x_scale), y=alt.Y("y:Q", scale=y_scale))
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )

        fit_text = (
            alt.Chart(label_df)
            .mark_text(
                align="left",
                baseline="top",
                font=CHART_FONT,
                fontSize=11,
                color=NEUTRAL_COLORS["axis_label"],
            )
            .encode(x=alt.value(8), y=alt.value(6), text="label:N")
            .transform_filter(is_type)
            .transform_filter(year_sel)
        )

        return alt.layer(others, fit_line, mine, fit_text).properties(
            width=panel_width,
            height=panel_height,
            title=alt.TitleParams(
                text=name,
                font=CHART_FONT,
                fontSize=14,
                fontWeight=600,
                color=NEUTRAL_COLORS["axis_title"],
                anchor="start",
            ),
        )

    panels = [make_panel(i, n) for i, n in enumerate(types)]
    rows = [alt.hconcat(*panels[r * ncols : (r + 1) * ncols]) for r in range(n_rows)]

    chart = alt.vconcat(*rows).properties(
        title=alt.TitleParams(
            text=title or f"Funding Source Share vs. Agency Size: {rtpa} vs. Statewide",
            subtitle="Grey = statewide agencies; colored = selected RTPA; line = statewide fit",
            font=CHART_FONT,
            fontSize=18,
            fontWeight="bold",
            color=BRAND_COLORS["navy"],
            anchor="start",
        )
    )

    return (
        chart.configure_view(stroke=None, fill=NEUTRAL_COLORS["surface"])
        .configure_axis(**ALT_AXIS_CONFIG)
        .configure_legend(**ALT_LEGEND_CONFIG)
    ), year_sel
