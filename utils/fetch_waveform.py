from obspy import UTCDateTime
from obspy.clients.fdsn import Client
from obspy.geodetics import locations2degrees
import pandas as pd

client = Client("INGV")

def get_nearby_stations(latitude: float, longitude: float, starttime: UTCDateTime, max_radius: float = 1.0, max_stations: int = 5):
    """
    Finds the nearest seismic stations to a given coordinate within a max radius (in degrees).
    Returns a list of station codes sorted by distance (ascending).
    """
    try:
        # INGV service might require a time window for station availability
        t0 = UTCDateTime(starttime)
        inventory = client.get_stations(network="IV", level="station",
                                        latitude=latitude, longitude=longitude,
                                        maxradius=max_radius,
                                        starttime=t0, endtime=t0 + 100) # Check availability around event time
        
        if not inventory or len(inventory) == 0:
            return []

        station_list = []

        for network in inventory:
            for station in network:
                dist = locations2degrees(latitude, longitude, station.latitude, station.longitude)
                station_list.append((station.code, dist))
        
        # Sort by distance
        station_list.sort(key=lambda x: x[1])
        
        # Return top N stations codes
        return [s[0] for s in station_list[:max_stations]]

    except Exception as e:
        print(f"Error finding stations: {e}")
        return []

def fetch_waveform(station: str, starttime: UTCDateTime, duration: int = 120, network = "IV", location = "*", channel = "HHZ"):
    try:
        # Added padding to starttime to ensure we catch the event
        t0 = UTCDateTime(starttime)
        st = client.get_waveforms(network, station, location, channel, t0, t0 + duration)
        if not st:
            return None
            
        tr = st[0]
        df = pd.DataFrame({
            "times": pd.to_datetime(tr.times("timestamp"), unit="s"),
            "velocity": tr.data
        })
        return df
    
    except Exception as e:
        print(f"Error fetching waveform: {e}")
        return None
