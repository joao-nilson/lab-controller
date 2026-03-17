#ups_manager.py
import logging
from typing import List, Dict, Optional
import sqlite3

#select last line of table: SELECT * FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status );
#changing * makes possible to select the row of the line and display only that

class UpsManager:
    def __init__(self):
        self.conn = sqlite3.connect("/var/log/ups/ups-log.db")
        self.cur = self.conn.cursor()

    def get_ups_status(self) -> Dict[str, Optional[float]]:
        #get last line of db with sql query
        self.cur.execute("SELECT * FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        last_line = self.cur.fetchone() 
        if last_line is None:
            return None
        print(last_line)
        return last_line

    def get_log_timestamp(self):
        self.cur.execute("SELECT timestamp FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        val = self.cur.fetchone()
        if val is None:
            return None
        timestamp = val[0]
        print("TIMESTAMP: ", timestamp)
        return timestamp

    def get_load(self):
        self.cur.execute("SELECT load FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        val = self.cur.fetchone()
        if val is None:
            return None
        load = val[0]
        print("LOAD: ", load)
        return load

    def get_Vbatt(self):
        self.cur.execute("SELECT vbattery FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        val = self.cur.fetchone()
        if val is None:
            return None
        vbattery = val[0]
        print("BATTERY VOLTAGE: ", vbattery)
        return vbattery

    def get_temperature(self):
        self.cur.execute("SELECT temperature FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        val = self.cur.fetchone()
        if val is None:
            return None
        temp = val[0]
        print("TEMPERATURE: ", temp)
        return temp

    def get_flags(self):
        self.cur.execute("SELECT flags FROM status WHERE ROWID IN ( SELECT max( ROWID ) FROM status )")
        val = self.cur.fetchone()
        if val is None:
            return None
        flags = val[0]
        print("STATUS FLAGS: ", flags)
        return flags

    def close(self):
        self.conn.close()

i = UpsManager()
i.get_ups_status()
i.get_log_timestamp()
i.get_load()
i.get_Vbatt()
i.get_temperature()
i.get_flags()
i.close()
