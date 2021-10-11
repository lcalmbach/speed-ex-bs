qry = {
    "min_max_timestamp": """select min(timestamp) as min_timestamp, max(timestamp) as max_timestamp from violation order by timestamp desc;
        """,
    "year_violations": """select substr(timestamp,1,4) as jahr, count(*) as anz from violation where timestamp is not null group by substr(timestamp,1,4);
        """,
    "year_stations": """select substr(messbeginn,1,4) as jahr, count(*) as anz from station where messbeginn is not null group by substr(messbeginn,1,4);
        """,
    "all_stations": """select
            "latitude"
            ,"longitude"
            ,"messung_id" 
            ,"messbeginn" 
            ,"messende" 
            ,coalesce("strasse",'') strasse
            ,coalesce("hausnummer",'') hausnummer
            ,"ort" 
            ,"zone"
            ,"richtung" 
            ,"richtung_strasse" 
            ,coalesce("fahrzeuge",-999) "fahrzeuge"
            ,coalesce("v50",-999) "v50"
            ,coalesce("v85",-999) "v85"
            ,coalesce("uebertretungsquote",-999) "uebertretungsquote"
        from 
            station
        where 
            latitude is not null
            and messung_id < 10;
        """,
    "all_violations":"""select 
            t2.messung_id
            ,t2.messbeginn
            ,t2.messende
            ,t2.latitude
            ,t2.longitude
            ,t1.timestamp
            ,t1.geschwindigkeit
            ,coalesce(t2.strasse,'') strasse
            ,coalesce(t2.hausnummer,'') hausnummer
            ,t2.ort 
            ,t2.zone 
            ,t2.richtung
            ,t2.richtung_strasse
            ,t2.v50
            ,t2.v85
            ,t2.fahrzeuge
            ,t2.uebertretungsquote
        from 
            violation t1 
            inner join station t2 on t2.messung_id = t1.messung_id and t2.richtung = t1.richtung
        where
            t2.messung_id < 10
        """
}


