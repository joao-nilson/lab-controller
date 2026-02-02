#ups_manager.py
import logging
from typing import List, Dict, Optional
import sqlite3

#select last line of table: SELECT * FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status );
#changing * makes possible to select the row of the line and display only that

class UpsManager:
    def __init__(self):
        conn = sqlite3.connect("/var/log/ups/ups-log.db")
        cur = conn.cursor()

    def get_ups_status(self) -> Dict[str, Optional[float]]:
        #get last line of db with sql query
        last_line = cur.execute("SELECT * FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        last_line.fetchone() is None
        print(last_line)
        return last_line

    def get_log_timestamp(self):
        timestamp = cur.execute("SELECT timestamp FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        timestamp.fetchone() is None
        print("TIMESTAMP: ", timestamp)
        return timestamp

    def get_load(self):
        load = cur.execute("SELECT load FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        load.fetchone() is None
        print("LOAD: ", load)
        return load

    def get_Vbatt(self):
        vbattery = cur.execute("SELECT vbattery FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        vbattery.fetchone() is None
        print("BATTERY VOLTAGE: " vbattery)
        return vbattery

    def get_temperature(self):
        temp = cur.execute("SELECT temperature FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        temp.fetchone() is None
        print("TEMPERATURE: ", temp)
        return temp

    def get_flags(self):
        flags = cur.execute("SELECT flags FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        flags.fetchone() is None
        print("STATUS FLAGS: ", flags)
        return flags

    conn.close()
