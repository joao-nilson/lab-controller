# controller.py
import yaml
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from pbs_manager import PBSManager
from prometheus_manager import PrometheusManager
from ups_manager import UpsManager

class LabController:
    def __init__(self, config_path: str = "config.yaml"):
        # Load configuration
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('lab-controller.log'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
        
        # Initialize managers
        self.ups = UpsManager()
        self.pbs = PBSManager(self.config['pbs']['bin_path'])
        self.prom = PrometheusManager(
            self.config['prometheus']['url'],
            self.config['prometheus']['timeout']
        )
        
        # State tracking
        self.running = True
        self.emergency_mode = False
        self.last_actions = {}
        
        self.logger.info("Lab Controller initialized")
    
    def run(self):
        self.logger.info("Starting controller main loop")
        
        while self.running:
            try:
                cycle_start = time.time()
                
                # 1. Gather current state
                ups_status = self.ups.get_ups_status()
                running_jobs = self.pbs.get_running_jobs()
                node_status = self.pbs.get_nodes_status()
                
                # 2. Check for emergency conditions
                emergency = self._check_emergency(ups_status)
                
                if emergency:
                    self._handle_emergency(running_jobs, node_status)
                else:
                    # 3. Check for warnings
                    warnings = self._check_warnings(ups_status, running_jobs, node_status)
                    
                    # 4. Handle warnings if any
                    if warnings:
                        self._handle_warnings(warnings, running_jobs)
                
                # 5. Log status
                self._log_status(running_jobs, ups_status)
                
                # 6. Sleep until next cycle
                self._sleep_until_next_cycle(cycle_start)
                
            except KeyboardInterrupt:
                self.logger.info("Shutdown requested by user")
                break
            except Exception as e:
                self.logger.error(f"Unexpected error: {e}", exc_info=True)
                time.sleep(60)  # Wait a minute before retrying
    
    def _check_emergency(self, ups_status: Dict) -> str:
        
        # Check if Prometheus is down
        if not self.prom.check_prometheus_up():
            return "prometheus_down"
        
        # Check UPS battery
        battery = ups_status.get('battery_voltage')
        if battery and battery < self.config['thresholds']['battery_critical']:
            return "battery_critical"
        
        # Check utility power
        utility_power = ups_status.get('utility_power')
        if utility_power is not None and utility_power == 0:
            return "power_loss"
        
        return ""
    
    def _check_warnings(self, ups_status: Dict, jobs: List, nodes: Dict) -> List[str]:
        warnings = []
        
        # Check UPS temperature
        temp = ups_status.get('temperature')
        if temp and temp > self.config['thresholds']['temperature_critical']:
            warnings.append("ups_overheat_critical")
        elif temp and temp > self.config['thresholds']['temperature_warning']:
            warnings.append("ups_overheat_warning")
        
        # Check UPS load
        load = ups_status.get('load_percentage')
        if load and load > self.config['thresholds']['load_high']:
            warnings.append("high_load")
        
        # Check battery level
        battery = ups_status.get('battery_voltage')
        if battery and battery < self.config['thresholds']['battery_low']:
            warnings.append("battery_low")
        
        return warnings
    
    def _handle_emergency(self, jobs: List, nodes: Dict):
        if self.emergency_mode:
            return  # Already in emergency mode
        
        self.logger.critical("EMERGENCY: Initiating emergency shutdown")
        self.emergency_mode = True
        
        # 1. Disable all queues
        queues = set(job['queue'] for job in jobs)
        for queue in queues:
            if self.pbs.disable_queue(queue):
                self.logger.info(f"Disabled queue {queue}")
        
        # 2. Delete all running jobs (with prejudice)
        for job in jobs:
            if self.pbs.delete_job(job['id'], force=True):
                self.logger.info(f"Deleted job {job['id']}")
            time.sleep(0.5)  # Small delay between operations
        
        # 3. Set all nodes offline
        for node in nodes:
            if self.pbs.set_node_offline(node):
                self.logger.info(f"Set node {node} offline")
        
        self.logger.critical("EMERGENCY: Shutdown sequence complete")
    
    def _handle_warnings(self, warnings: List[str], jobs: List):
        # Sort jobs by submit time (oldest first for protection)
        jobs.sort(key=lambda x: x['submit_time'])
        
        for warning in warnings:
            if warning == "high_load" or warning == "battery_low":
                # Reduce load by suspending newest jobs
                max_suspend = self.config['actions']['max_jobs_to_suspend']
                jobs_to_suspend = jobs[-max_suspend:] if jobs else []
                
                for job in jobs_to_suspend:
                    # Skip jobs running longer than protection period
                    job_age = time.time() - job['submit_time']
                    protection_minutes = self.config['actions']['fcfs_protection_minutes']
                    
                    if job_age > protection_minutes * 60:
                        if self.pbs.suspend_job(job['id']):
                            self.logger.info(f"Suspended job {job['id']} to reduce load")
                            time.sleep(0.5)
            
            elif "overheat" in warning:
                #TODO: implement more specific temperature logic
                self.logger.warning(f"Heat warning: {warning}")
    
    def _log_status(self, jobs: List, ups_status: Dict):
        status_msg = f"Jobs: {len(jobs)} running"
        
        if ups_status.get('utility_power') == 0:
            battery = ups_status.get('battery_voltage', 'unknown')
            status_msg += f" | UPS: On Battery ({battery}V)"
        else:
            status_msg += " | UPS: Grid Power OK"
        
        if self.emergency_mode:
            status_msg += " | EMERGENCY MODE"
        
        self.logger.info(status_msg)
    
    def _sleep_until_next_cycle(self, cycle_start: float):
        interval = self.config['intervals']['emergency_check'] if self.emergency_mode \
                  else self.config['intervals']['assessment_interval']
        
        elapsed = time.time() - cycle_start
        sleep_time = max(1, interval - elapsed)
        
        if sleep_time > 0:
            time.sleep(sleep_time)
    
    def shutdown(self):
        self.running = False
        self.logger.info("Controller shutting down")

if __name__ == "__main__":
    import sys
    
    # Load config from command line or default
    config_file = sys.argv[1] if len(sys.argv) > 1 else "config.yaml"
    
    try:
        controller = LabController(config_file)
        controller.run()
    except FileNotFoundError:
        print(f"Error: Config file '{config_file}' not found")
        print("Creating default config...")
        
        # Create default config
        default_config = {
            'thresholds': {
                'temperature_critical': 85,
                'temperature_warning': 75,
                'battery_low': 20,
                'battery_critical': 10,
                'load_high': 80
            },
            'intervals': {
                'assessment_interval': 60,
                'emergency_check': 10
            },
            'pbs': {
                'bin_path': '/opt/pbs/bin',
                'server': ''
            },
            'prometheus': {
                'url': 'http://localhost:9090',
                'timeout': 5
            },
            'actions': {
                'max_jobs_to_suspend': 3,
                'fcfs_protection_minutes': 60
            }
        }
        
        with open('config.yaml', 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False)
        
        print("Default config.yaml created. Please adjust and restart.")
    except Exception as e:
        print(f"Fatal error: {e}")
