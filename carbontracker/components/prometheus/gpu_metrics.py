import requests
import re
from carbontracker.components.handler import Handler

class PrometheusGPU(Handler):
    def __init__(self, pids=None, devices_by_pid=None):
        Handler.__init__( self, pids, devices_by_pid )
        self.url = "http://localhost:9835/metrics"
        self.devices_list = []
    
    def init(self):
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

        uuid_pattern = re.compile( "([a-f0-9-]{36})" )
        metrics = self._get_metrics()
        instant_watts = [x[0] for x in metrics if x[0].startswith( "nvidia_smi_power_draw_instant_watts" ) ]
        uuids = [uuid_pattern.findall(x)[0] for x in instant_watts ]
        return uuids

    def available(self):
        #return requests.get( self.url ).status_code == 200
        return True

    def power_usage(self, devices=None):
        if devices == None:
            devices = self.devices_list

        uuid_pattern = re.compile( "([a-f0-9-]{36})" )
        metrics = self._get_metrics()
        instant_watts = [
                float(x[1])
                for x in metrics
                if x[0].startswith( "nvidia_smi_power_draw_instant_watts" )
                and uuid_pattern.findall(x[0])[0] in devices
            ]
        return instant_watts