import os
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
import pandas as pd
import numpy as np

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

client = Client("INGV")

def fetch_catalog():
    print("Fetching Earthquake Catalog (2000-2024) in chunks...")
    all_data = []
    
    # Split request into 2-year chunks to avoid 20k limit
    chunks = [
        ("2000-01-01", "2001-12-31"),
        ("2002-01-01", "2003-12-31"),
        ("2004-01-01", "2005-12-31"),
        ("2006-01-01", "2007-12-31"),
        ("2008-01-01", "2009-12-31"),
        ("2010-01-01", "2011-12-31"),
        ("2012-01-01", "2013-12-31"),
        ("2014-01-01", "2015-12-31"),
        ("2016-01-01", "2017-12-31"),
        ("2018-01-01", "2019-12-31"),
        ("2020-01-01", "2021-12-31"),
        ("2022-01-01", "2023-12-31"),
        ("2024-01-01", "2025-12-31"),
    ]

    for start_str, end_str in chunks:
        print(f"  Requesting {start_str} to {end_str}...")

        try:
            starttime = UTCDateTime(start_str)
            endtime = UTCDateTime(end_str)
            
            catalog = client.get_events(
                starttime=starttime, 
                endtime=endtime, 
                minmagnitude=2.5, 
                minlatitude=27.0, 
                maxlatitude=48.0, 
                minlongitude=-7.0, 
                maxlongitude=37.5,
            )
            
            print(f"  -> Found {len(catalog)} events.")
            
            for event in catalog:

                try:
                    origin = event.origins[0]
                    mag = event.magnitudes[0].mag

                    event_data = {
                        "time": origin.time.datetime,
                        "latitude": origin.latitude,
                        "longitude": origin.longitude,
                        "depth": origin.depth / 1000.0 if origin.depth else 0, # km
                        "magnitude": mag,
                        "magnitude_type": event.magnitudes[0].magnitude_type if event.magnitudes else None,
                        "azimuthal_gap": origin.quality.azimuthal_gap if origin.quality and origin.quality.azimuthal_gap else None,
                        "used_phase_count": origin.quality.used_phase_count if origin.quality and origin.quality.used_phase_count else None,
                        "standard_error": origin.quality.standard_error if origin.quality and origin.quality.standard_error else None,
                        "horizontal_uncertainty": origin.origin_uncertainty.horizontal_uncertainty if origin.origin_uncertainty else None,
                        "depth_uncertainty": origin.depth_errors.uncertainty if origin.depth_errors and origin.depth_errors.uncertainty else None,
                    }

                    all_data.append(event_data)

                except IndexError:
                    continue

        except Exception as e:
            print(f"  Error fetching chunk {start_str}: {e}")


    if all_data:
        df = pd.DataFrame(all_data)
        # Sort by time
        df = df.sort_values("time")
        output_path = os.path.join(DATA_DIR, "catalog.csv")
        df.to_csv(output_path, index=False)
        print(f"Total Catalog saved to {output_path} ({len(df)} events)")
    else:
        print("No data fetched.")


def fetch_waveform_earthquake():
    print("Fetching Earthquake Waveform (Amatrice 2016)...")
    # Evento Amatrice 2016-08-24 01:36:32 UTC M6.0
    # Stazione IV.AMT (Amatrice) o vicina. Proviamo stazioni in zona.
    # Usiamo una stazione banda larga es. IV.GIGS o simile se AMT satura.
    # Proviamo IV.NRCA (Norcia) che è molto vicina.
    
    t0 = UTCDateTime("2016-08-24T01:36:00")
    duration = 180 # 3 minuti
    
    try:
        # Network IV, Stazione NRCA, Canale HHZ (Verticale High Broad Band)
        st = client.get_waveforms("IV", "NRCA", "*", "HHZ", t0, t0 + duration)
        tr = st[0]
        
        # Convert to simple CSV for the "Simulated IoT Sensor"
        df = pd.DataFrame({
            "times": tr.times(),
            "velocity": tr.data
        })
        
        # Normalize for visualization
        # df["velocity"] = df["velocity"] / df["velocity"].abs().max()
        
        output_path = os.path.join(DATA_DIR, "waveform_quake.csv")
        df.to_csv(output_path, index=False)
        print(f"Earthquake waveform saved to {output_path}")
        
    except Exception as e:
        print(f"Error fetching earthquake waveform: {e}")

def fetch_waveform_napoli():
    print("Fetching 'Napoli Scudetto' Waveform (2023-05-04)...")
    # Napoli Udinese 1-1, fischio finale 22:37 locale = 20:37 UTC
    # Stazione IV.OVO (Osservatorio Vesuviano) o IV.PAOL (Paolisi)
    # Lo stadio è a Fuorigrotta. Stazioni vicine: OVOOs (Vesuvio).
    # Proviamo IV.OVO
    
    t0 = UTCDateTime("2023-05-04T20:35:00") # UTC (22:35 locale)
    duration = 600 # 10 minuti di festa
    
    try:
        # Scarichiamo dati HHZ
        st = client.get_waveforms("IV", "OVO", "*", "HHZ", t0, t0 + duration)
        tr = st[0]
        
        df = pd.DataFrame({
            "times": tr.times(),
            "velocity": tr.data
        })
        
        output_path = os.path.join(DATA_DIR, "waveform_napoli.csv")
        df.to_csv(output_path, index=False)
        print(f"Napoli waveform saved to {output_path}")
        
    except Exception as e:
        print(f"Error fetching Napoli waveform (trying backup station IV.CAMI): {e}")
        try:
             # Backup: Casamicciola o altra stazione campana se OVO fallisce
            st = client.get_waveforms("IV", "CAMI", "*", "HHZ", t0, t0 + duration)
            tr = st[0]
            df = pd.DataFrame({"times": tr.times(), "velocity": tr.data})
            df.to_csv(os.path.join(DATA_DIR, "waveform_napoli.csv"), index=False)
            print("Napoli waveform saved from backup station.")
        except Exception as e2:
            print(f"Failed backup fetch: {e2}")


if __name__ == "__main__":
    fetch_catalog()
    fetch_waveform_earthquake()
    fetch_waveform_napoli()
