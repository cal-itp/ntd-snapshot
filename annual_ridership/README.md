# NTD Annual Ridership by RTPA


Provide CalSTA with NTD Annual Ridership by each regional transportation planning authority (RTPA)

Per the [SB125 Final Guidelines](https://calsta.ca.gov/-/media/calsta-media/documents/sb125-final-guidelines-a11y.pdf)
>Caltrans will provide all RTPAs with a summary report each month that meets the requirements of this statutory provision... For RTPAs with transit operators who do not report monthly data to the NTD, Caltrans will include the most recent annual ridership numbers provided to the NTD.


This report shows annual NTD ridership trends for transit agencies.
Transit agencies are organized regionally by the Regional Transportation Planning Authority to which they belong.
Ridership trends are visualized by agency, mode, type of service, and reporter type within each RTPA's report.

## Definitions
- **Annual NTD Reporter**: Transit agencies that are required  to report yearly to the NTD, includes rural, urban and reduced reporters.
- **FTA**: Federal Transit Administration.
- **Mode**: A system for carrying transit passengers described by specific right-of-way (ROW), technology and operational features. Examples: Bus, Cable Car, Light Rail. etc
- **NTD**: National Transit Database. A reporting system that collects public transportation financial and operating information.
- **RTPA**: Regional Transportation Planning Authority.
- **Service**: (Type of Service). Describes how public transportation services are provided by the transit agency: directly operated (DO) or purchased transportation (PT) services.
- **UZA**: Urbanized Areas. An urbanized area is an incorporated area with a population of 50,000 or more that is designated as such by the U.S. Department of Commerce, Bureau of the Census.


## Methodology
NTD annual service data is filtered to California Reporters. Each California Reporter is assigned to the RTPA it is served by.

Ridership metrics (unlinked passenger trips, change in unlinked passenger trips) are calculated by agency, by mode, by type of service, and by reporter type.

The processed data and aggregated data used in the report are available for download in our public data repository.


## Frequently Asked Questions
**Q: Which Annual NTD Reporters are in this report? Why are some Reporters missing from an RTPA?**

Transit operators/agencies that submit annual reports to NTD are included in this report. Reporters that were previously active reporters, but are currently not, may appear. This may result in Reporters showing zero or partial ridership data in the report.

If a Reporter, type of service, mode, or any combination of, is not a annual reporter or has not reported data since 2018, they will not appear in the report.

Examples:
- **Reporter A** is an annual reporter from 2019-2022, then became inactive and did not report for 2023. Reporter A's ridership data will be displayed for 2019-2022 only.
- **Reporter B** is an annual from 2000-2017, then became inactive and did not report for 2018. Reporter B will be named in the report, but will not display ridership data.
- **Reporter C** was an inactive reporter form 2015-2020, then became an active full reporter for 2021. Reporter C's ridership data will be displayed for 2021-present.


**Q: Where can I download my RTPA's data?**

Data from this report can be downloaded from the Cal-ITP public data repository, see `Download the Data!` below. A Google Account is required to access the repository. Once logged in, navigate to `ntd_annual_ridership/`, click the year you want to download, then click `download`.

The zipped dataset contains all the RTPAs as individual Excel workbooks. The time-series data is cumulative; the most recent file contains all the years prior.


**Q: How can my RTPA/Agency meet the requirements of the SB125 Guidelines regarding how "to make publicly available a summary of ridership data"**

Per the [SB125 Final Guidelines](https://calsta.ca.gov/-/media/calsta-media/documents/sb125-final-guidelines-a11y.pdf):
>RTPAs are required to post a link to this report and data in a manner easily accessed by the public, so that ridership trends within their region can be easily reviewed.

Hyperlinking this report on your RTPA's/Agency's webpage is a common method to meeting this requirement.

## Datasets / Data Sources
- NTD annual service data as [Excel](https://www.transit.dot.gov/ntd/data-product/ts22-service-data-and-operating-expenses-time-series-system-0) or [dashboard API](https://data.transportation.gov/Public-Transit/2024-NTD-Annual-Data-Service-Data-and-Operating-Ex/ectq-t3k3/about_data)
  - Data in our [warehouse](https://dbt-docs.dds.dot.ca.gov/#!/model/model.calitp_warehouse.fct_service_data_and_operating_expenses_time_series_by_mode)
- [California RTPA list](https://gis.data.ca.gov/datasets/CAEnergy::regional-transportation-planning-agencies/explore?appid=cf412a17daaa47bca93c6d6b7e77aff0&edit=true)
- **[Download the Data!](https://console.cloud.google.com/storage/browser/calitp-publish-data-analysis)**


## Who We Are
This website was created by the [California Department of Transportation](https://dot.ca.gov/)'s Division of Data and Digital Services. We are a group of data analysts and scientists who analyze transportation data, such as General Transit Feed Specification (GTFS) data, or data from funding programs such as the Active Transportation Program. Our goal is to transform messy and indecipherable original datasets into usable, customer-friendly products to better the transportation landscape. For more of our work, visit our [portfolio](https://analysis.dds.dot.ca.gov).

<img src="https://raw.githubusercontent.com/cal-itp/data-analyses/refs/heads/main/calitp-portfolio/src/calitp_portfolio/templates/assets/CT%2BDDS-Logo_FC-Black_Horizontal_Digital.png" alt="Alt text" width="274" height="72">

<br>Caltrans®, the California Department of Transportation® and the Caltrans logo are registered service marks of the California Department of Transportation and may not be copied, distributed, displayed, reproduced or transmitted in any form without prior written permission from the California Department of Transportation.
