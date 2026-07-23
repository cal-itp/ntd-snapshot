# NTD Monthly Ridership by RTPA

Provide CalSTA with NTD Monthly Ridership by each regional transportation planning authority (RTPA)

Per the [SB125 Final Guidelines](https://calsta.ca.gov/-/media/calsta-media/documents/sb125-final-guidelines-a11y.pdf)
>Caltrans will provide all RTPAs with a summary report each month that meets the requirements of this statutory provision, drawn from the data reported to the National Transit Database. The data will be drawn from the NTD at: [Complete Monthly Ridership (with adjustments and estimates) | FTA (dot.gov)](https://www.transit.dot.gov/ntd/data-product/monthly-module-adjusted-data-release). RTPAs are required to post a link to this report and data in a manner easily accessed by the public, so that ridership trends within their region can be easily reviewed.

This report shows annual NTD ridership trends for transit agencies.
Transit agencies are organized regionally by the Regional Transportation Planning Authority to which they belong.
Ridership trends are visualized by agency, mode, type of service, and reporter type within each RTPA's report.

## Definitions
- **Monthly NTD Reporter**: Full Reporters that submit Monthly Ridership (MR) and monthly Safety and Security reports to NTD.
- **FTA**: Federal Transit Administration.
- **Mode**: A system for carrying transit passengers described by specific right-of-way (ROW), technology and operational features. Examples: Bus, Cable Car, Light Rail. etc
- **NTD**: National Transit Database. A reporting system that collects public transportation financial and operating information.
- **RTPA**: Regional Transportation Planning Authority.
- **TOS**: Type of Service. Describes how public transportation services are provided by the transit agency: directly operated (DO) or purchased transportation (PT) services.
- **UZA**: Urbanized Areas. An urbanized area is an incorporated area with a population of 50,000 or more that is designated as such by the U.S. Department of Commerce, Bureau of the Census.


## Methodology
NTD monthly service data is filtered to California Reporters. Each California Reporter is assigned to the RTPA it is served by.

Ridership metrics (unlinked passenger trips, change in unlinked passenger trips) are calculated by agency, by mode, by type of service, and by reporter type.

The processed data and aggregated data used in the report are available for download in our public data repository.


## Frequently Asked Questions
**Q: Which Monthly NTD Reporters are in this report? Why are some Reporters missing from an RTPA?**

Per the [NTD Complete Monthly Ridership Report](https://www.transit.dot.gov/ntd/data-product/monthly-module-adjusted-data-release) webpage:
>File Summary: Contains monthly-updated service information reported by urban Full Reporters.

Transit operators/agencies that are **Urban full reporters, that submit monthly ridership data to NTD from 2018 to present**, are included in this report.

Operators/agencies that do not appear in the report may be due to:
- Were previously Urban full reporters, but are currently not
- Non-monthly reporters (small system/rural/reduced reporters)
- Has not reported data (empty or NULL values) since 2018
- Has reported "0" data since 2018

Examples:
- **Reporter A** is an urban full reporter from 2019-2022, then became a reduced reporter for 2023. Reporter A's ridership data will be displayed for 2019-2022 only.
- **Reporter B** is an urban full reporter from 2000-2017, then became a reduced reporter for 2018. Reporter B will not display ridership data.
- **Reporter C** was a reduced reporter form 2015-2020, then became an urban full reporter and began submitting monthly ridership data to NTD for 2021. Reporter C's ridership data will be displayed for 2021-present.


**Q: Where can I download my RTPA's data?**

Data from this report can be downloaded from the Cal-ITP public data repository, see `Download the Data!` below. A Google Account is required to access the repository. Once logged in, navigate to `ntd_monthly_ridership/`, click the year you want to download, then click `download`.

The zipped dataset contains all the RTPAs as individual Excel workbooks. The time-series data is cumulative; the most recent file contains all the years prior.


**Q: How can my RTPA/Agency meet the requirements of the SB125 Guidelines regarding how "to make publicly available a summary of ridership data"**

Per the [SB125 Final Guidelines](https://calsta.ca.gov/-/media/calsta-media/documents/sb125-final-guidelines-a11y.pdf):
>RTPAs are required to post a link to this report and data in a manner easily accessed by the public, so that ridership trends within their region can be easily reviewed.

Hyperlinking this report on your RTPA's/Agency's webpage is a common method to meeting this requirement.

## Datasets / Data Sources

- NTD monthly service data as [Excel](https://www.transit.dot.gov/ntd/data-product/monthly-module-adjusted-data-release) or [dashboard API](https://data.transportation.gov/Public-Transit/Complete-Monthly-Ridership-with-Adjustments-and-Es/8bui-9xvu/about_data)
  - Data in our [warehouse](https://dbt-docs.dds.dot.ca.gov/#!/model/model.calitp_warehouse.fct_complete_monthly_ridership_with_adjustments_and_estimates)
- [California RTPA list](https://gis.data.ca.gov/datasets/CAEnergy::regional-transportation-planning-agencies/explore?appid=cf412a17daaa47bca93c6d6b7e77aff0&edit=true)
- **[Download the Data!](https://console.cloud.google.com/storage/browser/calitp-publish-data-analysis)**


## Who We Are
This website was created by the [California Department of Transportation](https://dot.ca.gov/)'s Division of Data and Digital Services. We are a group of data analysts and scientists who analyze transportation data, such as General Transit Feed Specification (GTFS) data, or data from funding programs such as the Active Transportation Program. Our goal is to transform messy and indecipherable original datasets into usable, customer-friendly products to better the transportation landscape. For more of our work, visit our [portfolio](https://analysis.dds.dot.ca.gov).

<img src="https://raw.githubusercontent.com/cal-itp/data-analyses/refs/heads/main/calitp-portfolio/src/calitp_portfolio/templates/assets/CT%2BDDS-Logo_FC-Black_Horizontal_Digital.png" alt="Alt text" width="274" height="72">

<br>Caltrans®, the California Department of Transportation® and the Caltrans logo are registered service marks of the California Department of Transportation and may not be copied, distributed, displayed, reproduced or transmitted in any form without prior written permission from the California Department of Transportation.
