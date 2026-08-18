# Additional Transit Performance Metrics

In 2023, UCLA Institute of Transportation Studies published a white paper titled ["Options for the Future of State Funding for Transit Operations in California Informing the Future of the Transportation Development Act"](https://escholarship.org/uc/item/2zb6z5rm)

UCLA concluded that current transit performance metrics like "farebox recovery ratios" are:

>a cost-effectiveness metric currently applied as “one size fits all” in the TDA.
>
>As transit has two divergent and context-sensitive goals
>    1. Efficiency in transit-oriented markets and
>    2. Effectiveness in transit-dependent ones
>
> tailoring metrics to match these market opportunities would likely result in managerial actions that would eventually increase ridership.

The paper continues on to propose the use of other common metrics used in transportation management. Also explains how each metrics:

>[has] different implicit goals, which makes some metrics better for use in some areas than others.


| Metric type | Metric example | Implicit Goal(s) | Advantages | Limitations |
|---|---|---|---|---|
| Cost-efficiency | Operating cost per revenue hour | Reduce costs* | Useful in both financial and service planning | Favors high labor productivity in dense, congested areas; does not track use |
|  | Operating cost per revenue mile |  |  |  |
|  | Operating cost per vehicle trip |  |  |  |
| Service-effectiveness | Passengers per revenue-vehicle hour | Increase ridership; reduce poorly patronized service | Useful for service planning; emphasizes what matters to riders | Favors high ridership; does not track costs |
|  | Passengers per revenue-vehicle mile | Increase ridership; reduce low-ridership route miles/segments | Useful for service planning | Favors high ridership and fast vehicle speeds; does not track costs |
| Cost-effectiveness | Farebox recovery ratio | Reduce costs; increase fares; increase ridership | Commonly used; easy to calculate | Combines both cost-efficiency and service-effectiveness into a single measure; difficult to deconstruct and interpret |


This report intends to explores these metrics with data submitted to the NTD for all reporters in California.


## Definitions
**Regional Transportation Planning Authorities (RTPA)**: A county or multi-county entity charged to meet state transportation planning and programming requirements.

**Transportation Development Act (TDA)**: law [that] provides funding to be allocated to transit and non-transit related purposes that comply with regional transportation plans.

**Type of Service (TOS)**: Describes how public transportation services are provided by the transit agency: directly operated (DO) or purchased transportation (PT) services.

**UCLA Institute of Transportation Studies**: serves as the transportation research arm of the state with branches at UC Berkeley, UCLA, UC Davis, and UC Irvine.

**Unlined Passenger Trips (UPT)**: The number of passengers who board public transportation vehicles. Passengers are counted each time they board vehicles no matter how many vehicles they use to travel from their origin to their destination.

**Vehicle Revenue Hours (VRH)**: The hours that vehicles are scheduled to or actually travel while in revenue service.

**Vehicle Revenue Miles (VRM)**: The miles that vehicles are scheduled to or actually travel while in revenue service.

## Datasets / Data Sources
- NTD annual service data as [Excel](https://www.transit.dot.gov/ntd/data-product/ts22-service-data-and-operating-expenses-time-series-system-0) or [dashboard API](https://data.transportation.gov/Public-Transit/2024-NTD-Annual-Data-Service-Data-and-Operating-Ex/ectq-t3k3/about_data)
  - Data in our [warehouse](https://dbt-docs.dds.dot.ca.gov/#!/model/model.calitp_warehouse.fct_service_data_and_operating_expenses_time_series_by_mode)
- [California RTPA list](https://gis.data.ca.gov/datasets/CAEnergy::regional-transportation-planning-agencies/explore?appid=cf412a17daaa47bca93c6d6b7e77aff0&edit=true)
- **[Download the Data!](https://console.cloud.google.com/storage/browser/calitp-publish-data-analysis)**


## Who We Are
This website was created by the [California Department of Transportation](https://dot.ca.gov/)'s Division of Data and Digital Services. We are a group of data analysts and scientists who analyze transportation data, such as General Transit Feed Specification (GTFS) data, or data from funding programs such as the Active Transportation Program. Our goal is to transform messy and indecipherable original datasets into usable, customer-friendly products to better the transportation landscape. For more of our work, visit our [portfolio](https://analysis.dds.dot.ca.gov).

<img src="https://raw.githubusercontent.com/cal-itp/data-analyses/refs/heads/main/calitp-portfolio/src/calitp_portfolio/templates/assets/CT%2BDDS-Logo_FC-Black_Horizontal_Digital.png" alt="Alt text" width="274" height="72">

<br>Caltrans®, the California Department of Transportation® and the Caltrans logo are registered service marks of the California Department of Transportation and may not be copied, distributed, displayed, reproduced or transmitted in any form without prior written permission from the California Department of Transportation.
