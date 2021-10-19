qry = {
    "min_max_timestamp": """select min(start_date) as min_timestamp, max(end_date) as max_timestamp from station;
        """,
    "year_violations": """select substr(timestamp,1,4) as jahr, count(*) as anz from violation where timestamp is not null group by substr(timestamp,1,4);
        """,
    "year_stations": """select substr(messbeginn,1,4) as jahr, count(*) as anz from station where messbeginn is not null group by substr(messbeginn,1,4);
        """,
    "all_stations": """
        select
            messung_id
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
}


