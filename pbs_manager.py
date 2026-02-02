# pbs_manager.py
import subprocess
import json
import logging
from typing import List, Dict, Optional

class PBSManager:
    def __init__(self, bin_path: str = "/opt/pbs/bin"):
        self.bin_path = bin_path
        self.logger = logging.getLogger(__name__)
    
    def _run_command(self, command: str, args: List[str]) -> Dict:
        cmd = [f"{self.bin_path}/{command}"] + args + ["-F", "json"]
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                return json.loads(result.stdout)
            else:
                self.logger.error(f"PBS command failed: {result.stderr}")
                return {}
                
        except Exception as e:
            self.logger.error(f"PBS command error: {e}")
            return {}
    
    def get_running_jobs(self) -> List[Dict]:
        data = self._run_command("qstat", ["-f"])
        jobs = []
        
        for job_id, job_info in data.get("Jobs", {}).items():
            if job_info.get("job_state") == "R":  # Running jobs only
                jobs.append({
                    "id": job_id,
                    "name": job_info.get("Job_Name", ""),
                    "user": job_info.get("Job_Owner", "").split("@")[0],
                    "queue": job_info.get("queue", ""),
                    "nodes": self._parse_nodes(job_info.get("exec_host", "")),
                    "cpu_percent": float(job_info.get("resources_used", {}).get("cpupercent", 0)),
                    "submit_time": int(job_info.get("mtime", 0))
                })
        
        # Sort by submit time (FCFS)
        jobs.sort(key=lambda x: x["submit_time"])
        return jobs
    
    def _parse_nodes(self, exec_host: str) -> List[str]:
        if not exec_host:
            return []
        
        nodes = set()
        for host in exec_host.split("+"):
            node = host.split("/")[0]
            if node:
                nodes.add(node)
        
        return list(nodes)
    
    def get_nodes_status(self) -> Dict[str, str]:
        data = self._run_command("pbsnodes", ["-a"])
        nodes = {}
        
        for node_name, node_info in data.items():
            nodes[node_name] = node_info.get("state", "unknown")
        
        return nodes
    
    def suspend_job(self, job_id: str) -> bool:
        #implement suspend job logic
        return False
    
    def delete_job(self, job_id: str, force: bool = False) -> bool:
        #implement delete job logic
        return False

    def disable_queue(self, queue_name: str) -> bool:
        #implement disable queue logic
        return False
    
    def set_node_offline(self, node_name: str) -> bool:
        """Set a PBS node to offline"""
        #implement logic
        return False
