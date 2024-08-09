import requests
import re
import time
from carbontracker.components.handler import Handler

MEASURE_DELAY = 1

class PrometheusCPU(Handler):
    def __init__(self, pids=None, devices_by_pid=None):
        Handler.__init__( self, pids, devices_by_pid )
        self.url = "http://localhost:9101/metrics"
        self.devices_list = []
    
    def init(self):
        """Initializes the handler."""
        self.devices_list = self.devices()

        print( "Configured: CPU/Prometheus" )

    def shutdown(self):
        pass

    def _get_metrics(self):
        response = requests.get( self.url )
        if response.status_code != 200:
            return None
        metrics = response.text.splitlines()
        return [ x.split(" ") for x in metrics if not x.startswith("#") ]

    def devices(self):
        """Returns a list of devices (str) associated with the component."""

        class_pattern = re.compile( "class=\"([a-z0-9:-]+)\"" )
        metrics = self._get_metrics()
        instant_watts = [x[0] for x in metrics if x[0].startswith( "hex_powercap_energy_total" ) ]
        classes = [class_pattern.findall(x)[0] for x in instant_watts ]
        return classes

    def available(self):
        #return requests.get( self.url ).status_code == 200
        return True

    def power_usage(self, devices=None):
        if devices == None:
            devices = self.devices_list
        
        before_power = self._measure_power( devices )
        time.sleep( MEASURE_DELAY )
        after_power = self._measure_power( devices )

        power_usages = [
            self._compute_power(before, after) for before, after in zip(before_power, after_power)
        ]
        return power_usages
    
    def _measure_power(self, devices):
        class_pattern = re.compile( "class=\"([a-z0-9:-]+)\"" )
        metrics = self._get_metrics()
        instant_watts = [
                int(x[1])
                for x in metrics
                if x[0].startswith( "hex_powercap_energy_total" )
                and class_pattern.findall(x[0])[0] in devices
            ]
        return instant_watts
    
    def _compute_power(self, before, after):
        """Compute avg. power usage from two samples in microjoules."""
        joules = (after - before) / 1000000
        watt = joules / MEASURE_DELAY
        return watt
