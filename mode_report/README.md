# Transit Mode Report Summary
Mode report provides a mode-level overview of transit spending, service delivery and cost-effectiveness using NTD data. Rather than comparing individual agencies, the analysis summarizes patterns across transit modes and broader mode groups. Related modes are grouped to facilitate interpretation for some analysis - for example **Bus** includes modes such as `Bus`, `BRT`, `Commuter Bus` and `Trolley Bus`, while **Rail** includes modes such as `Commuter Rail`, `Heavy Rail`, `Light Rail` and `StreetCar`. The remaining modes are grouped into `Others`. The analysis considers expenditure trends, spending composition, service intensity, operating costs, farebox recovery, fare revenue, and fleet utilization to describe differences in how transit services are funded and delivered.


## 1. Trend and Composition
### 1.1 Ridership, OPEX, CAPEX, VRH and VRM Trend
This chart shows trends in `transit ridership`, `operating expenditures`, `capital expenditures`, and `service levels` across transit modes over time. It provides a high-level view of how passenger demand, transit spending, and service delivery have changed over time.

*How to read the chart*

- **X-axis:** Shows `Years`.
- **Y-axis:** Represents the value of the selected measure: `Unlinked Passenger Trips`, `Operating Expenditures`, `Capital Expenditures`, `Vehicle Revenue Hours`, or `Vehicle Revenue Miles`.
- **Trend:** Changes over time show whether ridership, spending, or service levels are increasing or declining.
- **Comparison:** The relative movement of the measures highlights periods when ridership, spending, and service delivery have diverged or moved together.


<div style="border-top: 1px solid #999; margin: 2em 0;"></div>


### 1.2 CAPEX and OPEX Share by Mode Group

This chart shows how `operating expenditures` and `capital expenditures` are distributed across transit mode groups from `2019` to `2024`. Each bar represents the total expenditure for a mode group in a given year, with the stacked segments showing the share attributable to OPEX and CAPEX.

*How to read the chart*

- **X-axis:** Shows `year`, with bars grouped by `mode group`.
- **Y-axis:** Shows each expenditure type as a `share of total expenditure (%)`, ranging from 0% to 100%.
- **Composition:** The relative size of each colored segment shows the share of CAPEX or OPEX within the mode group's total expenditure for that year.
- **Trend:** Changes in the composition over time show whether a mode group's spending has shifted toward operating or capital expenditures.
- **Comparison:** Differences in the OPEX and CAPEX shares across mode groups highlight differences in how transit spending is allocated.

<div style="border-top: 1px solid #999; margin: 2em 0;"></div>

### 1.3 Expenses Breakdown by Mode for Latest NTD Year

These two stacked bar charts show the composition of `operating` and `capital expenditures` across transit mode groups in `2024`. The charts show how each mode group allocates its total expenditures across different spending components. Because the bars are normalized, the focus is on the relative share of each component rather than the absolute amount spent.

*How to read the chart*

- **X-axis:** Shows `mode group`.
- **Y-axis:** Shows each expenditure component as a `share of total expenditures (%)`, with each bar totaling 100%.
- **OPEX:** Components include `Vehicle Operations`, `Vehicle Maintenance`, `Non-Vehicle Maintenance`, and `General Administration`.
- **CAPEX:** Components include `Rolling Stock`, `Facilities`, and `Other Expenditures`.
- **Composition:** The relative size of each segment shows the share of total OPEX or CAPEX allocated to that component within a mode group.
- **Comparison:** Differences in segment sizes across mode groups highlight how spending composition varies across transit modes.


<div style="border-top: 4px solid #ddd; margin: 2em 0;"></div>

## 2. Efficiency/ Performance
Efficiency and performance evaluate how transit modes use their operating and capital resources. The analysis looks at `spending concentration`, `spending per capita`, and `year-to-year spending volatility`, while also comparing `operating costs per vehicle revenue hour`, `vehicle revenue mile`, and `passenger trip`. Together, these measures show how much agencies spend, how consistently they spend, and how efficiently spending is translated into transit service and passenger trips.

### 2.1 Mode Performance (Herfindahl-Hirschman Index, Spending Per Capita and Volatility)

The OPEX and CAPEX scorecards compare transit mode groups across three measures: `expense concentration`, `spending per capita`, and `spending volatility`. Together, they show how spending is distributed, the level of spending relative to population, and how much spending changed from the previous year.

*How to read the chart*

- **Measures:** Each scorecard shows `Expense Concentration`, `Spending per Capita`, and `Spending Volatility`.
- **Expense Concentration:** Measured using the `Herfindahl-Hirschman Index (HHI)`. Higher values indicate that spending is concentrated in fewer expenditure components, while lower values indicate a more evenly distributed spending composition.
- **Spending per Capita:** Shows operating or capital expenditure relative to the population of the service area.
- **Spending Volatility:** Shows the `average absolute year-over-year change` in spending. The 2024 scorecards compare spending in `2024` with `2023`; higher values indicate larger changes in spending.
- **Bars:** Each bar represents a transit mode group. The highlighted bar represents the mode group with the highest value for that metric.
- **Comparison:** Values should be compared within each metric because the three measures use different units and scales.


<div style="border-top: 1px solid #999; margin: 2em 0;"></div>

### 2.2 Cost-Efficiency by Mode

This heatmap compares `operating cost efficiency` across transit modes in 2024 using `operating expenditure per Vehicle Revenue Hour (VRH)`, `Vehicle Revenue Mile (VRM)`, and `Unlinked Passenger Trip (UPT)`. Each metric is standardized separately using a `z-score` and reverse-scaled so that lower relative costs indicate greater cost efficiency.

*How to read the chart*

- **Rows:** Each row represents a `transit mode`.
- **Columns:** Each column represents a cost-efficiency measure: `OPEX per VRH`, `OPEX per VRM`, or `OPEX per Trip`.
- **Color:** `Blue` indicates relatively lower cost and greater cost efficiency, while `red` indicates relatively higher cost. Values near the midpoint represent costs closer to the mode average.
- **Standardization:** Each column is standardized separately using a `z-score`, so the colors show how each mode compares with other modes for that metric.
- **Interpretation:** Because each column is standardized independently, colors should be compared `within each column`, not across columns.
- **Cost per VRH:** Operating expenditure associated with each hour of revenue service.
- **Cost per VRM:** Operating expenditure associated with each revenue-generating vehicle mile.
- **Cost per Trip:** Operating expenditure associated with each unlinked passenger trip.


<div style="border-top: 1px solid #999; margin: 2em 0;"></div>


### 2.3 Cost per VRH: Variation Within Each Mode

This box plot shows the distribution of `operating expense per Vehicle Revenue Hour (VRH)` across California agencies within each transit mode in `2024`. Unlike the mode-level averages shown in the previous chart, this view shows how much costs vary between individual agencies operating the same mode. Modes are ordered by their `median cost`, and the number of agencies included in each mode is shown as `(n=...)`.

*How to read the chart*

- **X-axis:** Shows `operating expense per Vehicle Revenue Hour (VRH)`. Values farther to the right indicate higher operating costs per hour of revenue service.
- **Y-axis:** Shows `transit mode`. Modes are ordered from higher to lower median cost.
- **Box:** Represents the middle `50%` of agencies in a mode, from the `25th percentile` to the `75th percentile`. A wider box indicates greater variation in costs among the agencies in that mode.
- **Median:** The dark line inside the box represents the `median` cost. Half of the agencies have costs below this value and half have costs above it. The median is used to represent the typical agency because it is less affected by unusually high or low costs than an average.
- **Whiskers:** Extend beyond the box to the lowest and highest observations that fall within `1.5 × IQR` of the lower and upper quartiles. They represent the typical range of agency costs within the mode.
- **Dots:** Represent `outliers` beyond the whiskers. These agencies have unusually high or low costs compared with other agencies in the same mode.
- **Overall spread:** The position of the box shows the typical cost level for a mode, while the width of the box and length of the whiskers show how much costs vary across agencies.


<div style="border-top: 4px solid #ddd; margin: 2em 0;"></div>

## 3. Cost-effectiveness
Cost-effectiveness examines how effectively transit modes generate fare revenue relative to their operating costs. It uses `farebox recovery`, `fare revenue per passenger trip`, and `net subsidy per trip` to show how much of the cost is supported by fares and how much subsidy is required. The indexed comparison of operating costs and fare revenue from `2019` onward also shows whether expenses and fare revenue have grown at similar or different rates over time.

### 3.1 Farebox Recovery Ratio by Mode

This ridge plot shows the distribution of `Farebox Recovery Ratio` across transit modes in California in `2024`. Farebox Recovery Ratio represents the share of operating expenses covered by fare revenue. The chart shows both the typical level of farebox recovery and the variation across agencies within each mode.

*How to read the chart*

- **X-axis:** Shows `Farebox Recovery Ratio`. Higher values indicate a greater share of operating expenses covered by fare revenue.
- **Ridges:** Each ridge represents the distribution of farebox recovery ratios across agencies within a transit mode.
- **Peak:** Indicates where observations are most concentrated within a mode.
- **Spread:** A wider ridge indicates greater variation in farebox recovery ratios across agencies, while a narrower ridge indicates more similar values.
- **Density:** The height of a ridge represents the relative concentration of observations at a given recovery ratio. Because density is normalized within each mode, ridge height should not be used to compare the number of agencies across modes.


<div style="border-top: 1px solid #999; margin: 2em 0;"></div>

### 3.2 Cost Effectiveness Matrix

This heatmap compares the `cost-effectiveness` of different transit modes in 2024 using `Farebox Recovery`, `Fare Revenue per Trip`, and `Net Subsidy per Trip`. Each metric is standardized separately using a `z-score`, with the scale oriented so that higher fare-related values and lower subsidy requirements indicate greater cost-effectiveness.

*How to read the chart*

- **Rows:** Each row represents a `transit mode`.
- **Columns:** Each column represents a cost-effectiveness measure: `Farebox Recovery`, `Fare Revenue per Trip`, or `Net Subsidy per Trip`.
- **Color:** `Blue` indicates relatively greater cost-effectiveness, while `red` indicates relatively lower cost-effectiveness. Values near the midpoint represent results closer to the mode average.
- **Standardization:** Each column is standardized separately using a `z-score`, so colors show how each mode compares with other modes for that metric.
- **Direction:** For `Farebox Recovery` and `Fare Revenue per Trip`, higher values are more favorable. For `Net Subsidy per Trip`, the scale is reversed because lower subsidy requirements are more favorable.
- **Interpretation:** Because each column is standardized independently, colors should be compared `within each column`, not across columns.


<div style="border-top: 1px solid #999; margin: 2em 0;"></div>

### 3.3 Operating Costs vs. Fare Revenue, Indexed to 2019

This chart compares how `operating expenses` and `fare revenue` have changed relative to their `2019` levels across transit mode groups. Both measures are indexed to `2019 = 100`, which puts them on a common scale and makes their growth rates directly comparable even though their actual dollar amounts are very different. Each panel represents a transit mode group, with separate lines for operating expenses and fare revenue.

Using a common base year makes it easier to see whether fare revenue has kept pace with changes in operating expenses. For example, if operating expenses rise to `150` while fare revenue rises to `120`, operating expenses have grown by `50%` since 2019 while fare revenue has grown by `20%`.

*How to read the chart*

- **X-axis:** Shows `year`, starting from the 2019 base year.
- **Y-axis:** Shows the indexed value, where `2019 = 100`. A value of `120` means the measure is `20% higher` than in 2019, while a value of `80` means it is `20% lower`.
- **Lines:** `Blue` represents `Operating Expenses`; `orange` represents `Fare Revenue`.
- **Index:** Each year's value is divided by that mode group's value in `2019` and multiplied by 100. This sets both measures to the same starting point, allowing their relative growth to be compared.
- **Gap between lines:** A widening gap indicates that operating expenses and fare revenue are growing at different rates. If the operating expense line is above the fare revenue line, expenses have grown faster relative to 2019.
- **Convergence:** Lines moving closer together indicate that the relative growth rates of operating expenses and fare revenue are becoming more similar.
- **Important:** The indexed values show `relative change since 2019`, not actual dollar amounts. Two mode groups can have the same index while having very different levels of spending or fare revenue.


<div style="border-top: 4px solid #ddd; margin: 2em 0;"></div>


## 4. Service Effectiveness
`Service effectiveness` focuses on how efficiently transit resources are converted into passenger service and how intensively the fleet is used. By comparing operating costs with passenger trips per vehicle mile and hour, the analysis shows the relationship between service costs and passenger utilization. Fleet utilization and operating speed provide additional insight into how intensively vehicles are used and how quickly service is delivered.

### 4.1 Operating Efficiency: Cost vs. Service Utilization and Service Intensity

These scatter plots examine the relationship between `operating cost` and `passenger utilization` across transit mode groups. The VRM-based chart relates costs and passenger trips to the amount of service provided in miles, while the VRH-based chart uses hours of service. Both axes are shown on a `log10` scale to make differences across agencies easier to visualize when values vary substantially.

*How to read the chart*

- **X-axis:** Shows `operating expense per Vehicle Revenue Mile (VRM)` in the VRM-based chart and `operating expense per Vehicle Revenue Hour (VRH)` in the VRH-based chart. Values increase from left to right.
- **Y-axis:** Shows `passenger trips per VRM` in the VRM-based chart and `passenger trips per VRH` in the VRH-based chart. Values increase from bottom to top.
- **Colors:** Each color represents a `mode group`.
- **Point size:** Represents total `Unlinked Passenger Trips (UPT)`. Larger points indicate more passenger trips.
- **Log scale:** Both axes use `log10` scaling. A fixed distance on an axis represents a multiplicative change rather than a fixed numerical change.
- **Position:** Points toward the `upper-right` have both higher operating costs per unit of service and higher passenger utilization per unit of service, while points toward the `lower-left` have lower values for both.
- **VRM-based chart:** Evaluates cost and passenger utilization relative to the amount of service provided in `miles`.
- **VRH-based chart:** Evaluates cost and passenger utilization relative to the amount of service provided in `hours`.


<div style="border-top: 1px solid #999; margin: 2em 0;"></div>


### 4.2 Fleet & Service Delivery

This chart compares `fleet utilization` and `operating speed` across transit modes. Fleet utilization shows how many hours each vehicle is used for revenue service, while operating speed shows how quickly vehicles travel while providing that service.

*How to read the chart*

- **Y-axis:** Shows `transit mode`, with modes ordered by the value of the measure shown in each chart.
- **X-axis:** `Fleet Utilization` shows `Vehicle Revenue Hours (VRH) per vehicle`. Higher Fleet Utilization values indicate more intensive use of the fleet. `Operating Speed` shows `average operating speed (mph)`, calculated as `Vehicle Revenue Miles (VRM) ÷ Vehicle Revenue Hours (VRH)`. Higher Operating Speed values indicate faster service.
- **Bars:** Each bar represents the value of the corresponding measure for a transit mode.
- **Comparison:** The two charts provide complementary views of service delivery: a mode can have high fleet utilization without having high operating speed, or vice versa.



<div style="border-top: 4px solid #ddd; margin: 2em 0;"></div>
