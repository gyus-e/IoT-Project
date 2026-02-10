import sys
import os

# Add the parent directory to sys.path to allow importing utils
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.fetch_waveform import fetch_waveform
from obspy import UTCDateTime

if __name__ == "__main__":

    # Max event Campi Flegrei: 2025-03-13 00:25:02.349000 M4.6 at 40.818833, 14.1575
    df_max_event = fetch_waveform(
        station="OVO", 
        starttime=UTCDateTime("2025-03-13T00:25:02.349000"),
        duration=300
    )

    if df_max_event is not None:
        df_max_event.to_csv("data/waveform_max_event_flegrei.csv", index=False)
        print(f"Successfully downloaded waveform for Max Event.")
    else:
        print("Failed to download waveform for Max Event.")

    
    # Napoli scudetto
    df_scudetto = fetch_waveform(
        station="OVO", 
        starttime=UTCDateTime("2023-05-04T20:37:00"), # (Approximate time of goal/final whistle celebration)
        duration=300
    )

    if df_scudetto is not None:
        df_scudetto.to_csv("data/waveform_napoli_scudetto.csv", index=False)
        print(f"Successfully downloaded waveform for Napoli Scudetto.")
    else:
        print("Failed to download waveform for Napoli Scudetto.")