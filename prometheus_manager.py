# prometheus_manager.py
import requests
import logging
from typing import Dict, Optional

class PrometheusManager:
    def __init__(self, url: str = "http://localhost:9090", timeout: int = 5):
        self.base_url = url.rstrip('/')
        self.timeout = timeout
        self.logger = logging.getLogger(__name__)
    
    def query(self, query: str) -> Optional[float]:
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/query",
                params={"query": query},
                timeout=self.timeout
            )
            response.raise_for_status()
            data = response.json()

            if data.get("status") == "success":# and data["data"]["result"]:
                results = data.get("data", {}).get("result", [])

                if len(results) > 0:
                    # results[0]["value"] é uma lista [timestamp, "valor"]
                    value = results[0].get(

    "value")
                    if value and len(value) > 1:
                        return float(value[1])
                else:
                    self.logger.warning(f"Query returned no results: {query}")


                #return float(data["data"]["result"][0]["value"][1])
            
        except Exception as e:
            self.logger.error(f"Prometheus query failed for '{query}': {e}")
        
        return None
    
    def get_node_temperature(self, node: str) -> Optional[float]:
        prom_query = f'node_hwmon_temp_celsius{{instance=~"{node}.*"}}'
        print("node temperature prometheus: ", prom_query)
        return self.query(prom_query)
    
    def check_prometheus_up(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/-/healthy", timeout=2)
            return response.status_code == 200
        except:
            return False

i = PrometheusManager()
temp = i.get_node_temperature("200.17.71.25:9100")
print(f"Temperatura retornada: {temp}")
