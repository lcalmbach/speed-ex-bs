qry = {
    "min_max_timestamp": """select min(start_date) as min_timestamp, max(end_date) as max_timestamp from station;
        """,
    "year_violations": """select substr(timestamp,1,4) as jahr, count(*) as anz from violation where timestamp is not null group by substr(timestamp,1,4);
        """,
    "year_stations": """select substr(messbeginn,1,4) as jahr, count(*) as anz from station where messbeginn is not null group by substr(messbeginn,1,4);
        """,
    "all_stations": """
        select
            id as station_id
            ,site_id
            ,concat(street, ' ', house_number, ', ', location) as location
            ,direction_street
            ,start_date
            ,end_date
            ,zone
            ,direction
            ,vehicles
            ,exceedance_rate
            ,"v50"
            ,"v85"
            ,latitude
            ,longitude
            ,EXTRACT(year from start_date) AS jahr
        from 
            station
        where 
            latitude is not null
            and vehicles > 0;
            """,

    "all_locations": """
        select
            site_id
            ,concat(street, ' ', house_number, ', ', location) as location
            ,start_date
            ,end_date
            ,zone
            ,sum(vehicles) as vehicles
            ,avg(exceedance_rate) as avg_exceedance_rate
            ,avg(v50) as avg_v50
            ,avg(v85) as avg_v85
            ,latitude
            ,longitude
            ,EXTRACT(year from start_date) AS jahr
        from 
            station
        where 
            latitude is not null
            and vehicles > 0
        group by 
            site_id
            ,concat(street, ' ', house_number, ', ', location)
            ,start_date
            ,end_date
            ,zone
            ,latitude
            ,longitude
            ,EXTRACT(year from start_date)
            """,

    "all_violations":"""select 
            t1.station_id
            ,t2.start_date
            ,t2.end_date
            ,t2.latitude
            ,t2.longitude
            ,t1.date_time
            ,t1.velocity_kmph
            ,t2.address
            ,t2.location 
            ,t2.zone 
            ,t2.direction
            ,t2.direction_street
            ,t2.v50
            ,t2.v85
            ,t2.vehicles
            ,t2.exceedance_rate
        from 
            velocity t1 
            inner join station t2 on t2.id = t1.station_id
        """,
    "velocity_by_station": "select * from v_velocity_by_station",

    "station_velocities": """select 
        site_id
        , station_id
        , date_trunc('hour',date_time) as date_time
        , TO_CHAR(date_time, 'HH24')::INT as hour
        , EXTRACT(dow  FROM date_time) as dow
        , count(*) as count
        , max(velocity_kmph) as max_velocity
        , max(exceedance_kmph) as max_exceedance 
    from 
        velocity where site_id = {}
    group by 
        site_id
        , station_id
        , date_trunc('hour',date_time)
        , TO_CHAR(date_time, 'HH24')::INT
        , EXTRACT(dow  FROM date_time)""",

    "station_velocities_by_hour":"""select 
        site_id
        , station_id
        , TO_CHAR(date_time, 'HH24')::INT as hour
        , count(*) as count
        , max(velocity_kmph) as max_velocitystation_velocities
        , max(exceedance_kmph) as max_exceedance 
    from 
        velocity where station_id = {}
    group by 
            site_id
        , station_id
        , TO_CHAR(date_time, 'HH24')::INT""",
    "exceedance_count": "select count(*) as count from velocity where exceedance_kmph > 0;",
    "station_percentiles": """SELECT 
        station_id 
        ,percentile_cont(0.50) WITHIN GROUP (ORDER BY velocity_kmph) as "P50"
        ,percentile_cont(0.75) WITHIN GROUP (ORDER BY velocity_kmph) as "P75"
        ,percentile_cont(0.85) WITHIN GROUP (ORDER BY velocity_kmph) as "P90"
        ,percentile_cont(0.95) WITHIN GROUP (ORDER BY velocity_kmph) as "P95"
    FROM velocity
    group by station_id;""",

    "station_exceedances": """
        SELECT 
            station_id 
            ,t2.address
            ,velocity_kmph
            ,exceedance_kmph
        from velocity t1
        inner join station t2 on t2.id = t1.station_id""",

    "station_exceedances_weekday": """
        SELECT 
            station_id 
            ,EXTRACT(DOW FROM date_time) as dow
            ,concat(t2.street, ' ', t2.house_number, ', ', t2.location,' > ',t2.direction_street) as location
            ,count(*) as count
            ,avg(velocity_kmph) as avg_velocity
            ,avg(exceedance_kmph) as  avg_exceedance
        from 
            velocity t1
            inner join station t2 on t2.id = t1.station_id
        group by 
            station_id 
            ,concat(t2.street, ' ', t2.house_number, ', ', t2.location,' > ',t2.direction_street)
            ,EXTRACT(DOW FROM date_time)
        """,
    
    "station_exceedances_hour": """
        SELECT 
            station_id 
            ,EXTRACT(HOUR FROM date_time) as hour
            --,EXTRACT(DOW FROM date_time) as dow
            ,concat(t2.street, ' ', t2.house_number, ', ', t2.location,' > ',t2.direction_street) as location
            ,count(*) as count
            ,avg(velocity_kmph) as avg_velocity
            ,avg(exceedance_kmph) as  avg_exceedance
        from 
            velocity t1
            inner join station t2 on t2.id = t1.station_id
        group by 
            station_id 
            ,concat(t2.street, ' ', t2.house_number, ', ', t2.location,' > ',t2.direction_street)
            ,EXTRACT(HOUR FROM date_time)
            --, EXTRACT(DOW FROM date_time)
        """,
    
    "exceedance_count_ranked_by_weekday": """select 
	    dow,
        sum(case when rank_number = 1 then 1 else 0 end) as first,
        sum(case when rank_number = 7 then 1 else 0 end) as last
        from public.v_rank_weekdays
        {}
        group by dow""",
    "exceedance_count_ranked_by_hour": """select 
	    hour,
        sum(case when rank_number = 1 then 1 else 0 end) as first,
        sum(case when rank_number = 23 then 1 else 0 end) as last
        from public.v_rank_hour
        {}
        group by hour"""
}


