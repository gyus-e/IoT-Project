import os
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
import pandas as pd

# Configuration
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'data')
os.makedirs(DATA_DIR, exist_ok=True)

client = Client("INGV")
chunks = [
    (UTCDateTime("2000-01-01"), UTCDateTime("2001-12-31")),
    (UTCDateTime("2002-01-01"), UTCDateTime("2003-12-31")),
    (UTCDateTime("2004-01-01"), UTCDateTime("2005-12-31")),
    (UTCDateTime("2006-01-01"), UTCDateTime("2007-12-31")),
    (UTCDateTime("2008-01-01"), UTCDateTime("2009-12-31")),
    (UTCDateTime("2010-01-01"), UTCDateTime("2011-12-31")),
    (UTCDateTime("2012-01-01"), UTCDateTime("2013-12-31")),
    (UTCDateTime("2014-01-01"), UTCDateTime("2015-12-31")),
    (UTCDateTime("2016-01-01"), UTCDateTime("2017-12-31")),
    (UTCDateTime("2018-01-01"), UTCDateTime("2019-12-31")),
    (UTCDateTime("2020-01-01"), UTCDateTime("2021-12-31")),
    (UTCDateTime("2022-01-01"), UTCDateTime("2023-12-31")),
    (UTCDateTime("2024-01-01"), UTCDateTime("2025-12-31")),
]

def fetch_catalog():
    print("Fetching Earthquake Catalog (2000-2025) in chunks...")
    all_data = []

    for starttime, endtime in chunks:
        print(f"\t Requesting {starttime} to {endtime}...")

        try:
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
            print(f"  Error fetching chunk {starttime} to {endtime}: {e}")


    if all_data:
        df = pd.DataFrame(all_data)
        # Sort by time
        df = df.sort_values("time")
        output_path = os.path.join(DATA_DIR, "catalog.csv")
        df.to_csv(output_path, index=False)
        print(f"Total Catalog saved to {output_path} ({len(df)} events)")
    else:
        print("No data fetched.")


if __name__ == "__main__":
    fetch_catalog()
