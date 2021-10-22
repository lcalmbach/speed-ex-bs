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
            ,messung_id
            ,address
            ,ort
            ,start_date
            ,end_date
            ,zone
            ,richtung_strasse
            ,richtung
            ,fahrzeuge
            ,uebertretungsquote
            ,"v50"
            ,"v85"
            ,latitude
            ,longitude
            ,EXTRACT(year from start_date) AS jahr
        from 
            station
        where 
            latitude is not null
            and fahrzeuge > 0;
            """,
    "all_locations": """
        select
            messung_id
            ,address
            ,ort
            ,start_date
            ,end_date
            ,zone
            ,sum(fahrzeuge) as fahrzeuge
            ,avg(uebertretungsquote) as avg_uebertretungsquote
            ,avg(v50) as avg_v50
            ,avg(v85) as avg_v85
            ,latitude
            ,longitude
            ,EXTRACT(year from start_date) AS jahr
        from 
            station
        where 
            latitude is not null
            and fahrzeuge > 0
        group by 
            messung_id
            ,address
            ,ort
            ,start_date
            ,end_date
            ,zone
            ,latitude
            ,longitude
            ,EXTRACT(year from start_date)
            """,
    "all_violations":"""select 
            t2.messung_id
            ,t2.start_date
            ,t2.end_date
            ,t2.latitude
            ,t2.longitude
            ,t1.date_time
            ,t1.velocity_kmph
            ,t2.address
            ,t2.ort 
            ,t2.zone 
            ,t2.richtung
            ,t2.richtung_strasse
            ,t2.v50
            ,t2.v85
            ,t2.fahrzeuge
            ,t2.uebertretungsquote
        from 
            velocity t1 
            inner join station t2 on t2.id = t1.station_id
        """,
    "velocity_by_station": "select * from v_velocity_by_station",

    "station_velocities": """select 
        messung_id
        , station_id
        , date_trunc('hour',date_time) as date_time
        , TO_CHAR(date_time, 'HH24')::INT as hour
        , count(*) as count
        , max(velocity_kmph) as max_velocity
        , max(exceedance_kmph) as max_exceedance 
    from 
        velocity where messung_id = {}
    group by 
        messung_id
        , station_id
        , date_trunc('hour',date_time)
        , TO_CHAR(date_time, 'HH24')::INT""",
    
    "station_velocities_by_hour":"""select 
        messung_id
        , station_id
        , TO_CHAR(date_time, 'HH24')::INT as hour
        , count(*) as count
        , max(velocity_kmph) as max_velocity
        , max(exceedance_kmph) as max_exceedance 
    from 
        velocity where station_id = {}
    group by 
            messung_id
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
            ,t2.address
            ,count(*) as count
            ,avg(velocity_kmph) as avg_velocity
            ,avg(exceedance_kmph) as  avg_exceedance
        from 
            velocity t1
            inner join station t2 on t2.id = t1.station_id
        group by 
            station_id 
            ,t2.address
            ,EXTRACT(DOW FROM date_time)
        """,
    
    "station_exceedances_hour": """
        SELECT 
            station_id 
            ,EXTRACT(HOUR FROM date_time) as hour
            ,t2.address
            ,count(*) as count
            ,avg(velocity_kmph) as avg_velocity
            ,avg(exceedance_kmph) as  avg_exceedance
        from 
            velocity t1
            inner join station t2 on t2.id = t1.station_id
        group by 
            station_id 
            ,t2.address
            ,EXTRACT(HOUR FROM date_time)
        """
}


