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
            if data["status"] == "success" and data["data"]["result"]:
                return float(data["data"]["result"][0]["value"][1])
            
        except Exception as e:
            self.logger.error(f"Prometheus query failed for '{query}': {e}")
        
        return None
    
    def get_ups_status(self) -> Dict[str, Optional[float]]:
        #implement nobreal status logic
        return False
    
    def get_node_temperature(self, node: str) -> Optional[float]:
        query = f'node_hwmon_temp_celsius{{instance=~"{node}.*"}}'
        return self.query(query)
    
    def check_prometheus_up(self) -> bool:
        try:
            response = requests.get(f"{self.base_url}/-/healthy", timeout=2)
            return response.status_code == 200
        except:
            return False
