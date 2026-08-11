df['opex_per_vehicle'] = df['operating_expenses_total']/df['vehicles_operated_in_maxiumum_service']
df['cost_per_route_mile'] = df['operating_expenses_total'] / df['direction_route_miles']

df['net_subsidy_per_passenger_trip'] = (df['operating_expenses_total']- df['fare_revenue'])/df['unlinked_passenger_trips']
df['net_subsidy_per_passenger_mile'] = (df['operating_expenses_total']- df['fare_revenue'])/df['passenger_miles_traveled']


# System speed — proxy for congestion, route design, mode mix (useful across bus vs rail comparisons)
df['avg_speed_mph'] = df['vehicle_revenue_miles'] / df['vehicle_revenue_hours']


# Revenue productivity — fare dollars generated per hour of service
df['fare_revenue_per_vrh'] = df['fare_revenue'] / df['vehicle_revenue_hours']


# Average trip length
df['avg_trip_length_miles'] = df['passenger_miles_traveled'] / df['unlinked_passenger_trips']

# Load factor — average passengers carried per mile of service (capacity utilization)
df['load_factor'] = df['passenger_miles_traveled'] / df['vehicle_revenue_miles']


df['service_area_density'] = df['uza_population'] / df['uza_area_sq_miles']

# Service supply per resident 
df['vrh_per_capita'] = df['vehicle_revenue_hours'] / df['uza_population']
df['upt_per_capita'] = df['unlinked_passenger_trips'] / df['uza_population']

# Route coverage relative to service area
df['route_miles_per_sqmi'] = df['direction_route_miles'] / df['uza_area_sq_miles']