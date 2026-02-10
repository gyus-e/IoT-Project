from typing import Generator, Tuple, Optional
from obspy import UTCDateTime
from obspy.clients.fdsn import Client
import pandas as pd
import datetime

# INGV Client
client = Client("INGV", force_redirect=True)

def fetch_earthquake_data(
    starttime: datetime.date, 
    endtime: datetime.date
) -> Generator[Tuple[float, Optional[pd.DataFrame]], None, None]:
    """
    Fetches earthquake data from INGV in chunks.
    Yields (progress_percentage, chunk_dataframe).
    
    Hashcoded filters:
    - Min Magnitude: 2.5
    - Area: Mediterranean (Lat 27-48, Lon -7-37.5)
    """
    
    # Hardcoded limits
    MIN_MAGNITUDE = 2.5
    MIN_LAT = 27.0
    MAX_LAT = 48.0
    MIN_LON = -7.0
    MAX_LON = 37.5
    
    # Convert to UTCDateTime
    start_utc = UTCDateTime(starttime)
    end_utc = UTCDateTime(endtime)
    
    total_duration = end_utc - start_utc
    current_start = start_utc
    
    # Chunking logic: Go from current_start to end of that year (or end_utc)
    
    while current_start < end_utc:
        # Calculate end of current year
        end_of_year = UTCDateTime(f"{current_start.year}-12-31T23:59:59.999999")
        
        # Chunk strategy: 1 year (Calendar Year)
        # From Start -> Dec 31 of same year
        current_end = min(end_of_year, end_utc)

        # Calculate progress
        if total_duration > 0:
            progress = (current_end - start_utc) / total_duration
        else:
            progress = 1.0
        
        try:
            # Fetch events
            catalog = client.get_events(
                starttime=current_start, 
                endtime=current_end, 
                minmagnitude=MIN_MAGNITUDE, 
                minlatitude=MIN_LAT, 
                maxlatitude=MAX_LAT, 
                minlongitude=MIN_LON, 
                maxlongitude=MAX_LON,
            )
            
            # Process Catalog to List of Dicts
            all_data = []
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
            
            if all_data:
                df_chunk = pd.DataFrame(all_data)
                yield progress, df_chunk
            else:
                yield progress, pd.DataFrame() # Empty DF if no events
                
        except Exception as e:
            print(f"Error fetching chunk {current_start} - {current_end}: {e}")
            yield progress, None # Indicate error or empty
            
        # Move to next chunk (add small epsilon to avoid overlap or just use next second)
        current_start = current_end + 0.000001
