from obspy import UTCDateTime
from obspy.clients.fdsn import Client
import pandas as pd

client = Client("INGV")

def fetch_waveform(station: str, starttime: UTCDateTime, duration: int = 180, network = "IV", location = "*", channel = "HHZ"):
    try:
        st = client.get_waveforms(network, station, location, channel, starttime, starttime + duration)
        tr = st[0]
        df = pd.DataFrame({
            "times": pd.to_datetime(tr.times("timestamp"), unit="s"),
            "velocity": tr.data
        })
        return df
    
    except Exception as e:
        print(f"Error fetching waveform: {e}")
        return None