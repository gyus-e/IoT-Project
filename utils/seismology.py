import numpy as np
import pandas as pd

def calculate_gutenberg_richter(df: pd.DataFrame, magnitude_col: str = 'magnitude', mc: float = None):
    """
    Calcola i parametri a e b della legge di Gutenberg-Richter usando il metodo MLE (Aki, 1965).
    
    Args:
        df: DataFrame contenente i dati sismici.
        magnitude_col: Nome della colonna magnitudo.
        mc: Magnitudo di completezza. Se None, viene stimata come la moda della distribuzione (arrotondata a 0.1).
        
    Returns:
        Un dizionario contenente:
        - 'a_value': valore a calcolato
        - 'b_value': valore b calcolato
        - 'mc': Magnitudo di completezza utilizzata
        - 'n_total': Numero di eventi >= Mc utilizzati per il calcolo
        - 'valid': Booleano, True se il calcolo è riuscito (abbastanza dati)
    """
    if df.empty or magnitude_col not in df.columns:
        return {'a_value': np.nan, 'b_value': np.nan, 'mc': np.nan, 'n_total': 0, 'valid': False}

    mags = df[magnitude_col].dropna()
    
    # Arrotondiamo a 1 decimale per coerenza con la pratica sismologica standard
    mags_rounded = mags.round(1)

    # 1. Stima Mc se non fornito
    if mc is None:
        if not mags_rounded.empty:
            # La moda è una stima semplice ma efficace per Mc in prima approssimazione
            # Se ci sono più mode, prendiamo la minima (approccio conservativo per non perdere dati, 
            # anche se in realtà si dovrebbe prendere la massima per essere sicuri della completezza.)
            mc = mags_rounded.mode().min()
        else:
            mc = 0.0
            
    # 2. Filtra dataset per M >= Mc
    # Usiamo i dati originali (non arrotondati) per il filtro e la media, per maggiore precisione,
    # ma il taglio avviene rispetto a Mc (che è arrotondato)
    df_above_mc = df[df[magnitude_col] >= mc]
    mags_above = df_above_mc[magnitude_col]
    n_total = len(mags_above)

    # 3. Controllo numero minimo di eventi
    if n_total < 10:
        return {
            'a_value': np.nan, 
            'b_value': np.nan, 
            'mc': mc, 
            'n_total': n_total,
            'valid': False
        }

    # 4. Calcolo MLE (Aki, 1965)
    mean_mag = mags_above.mean()
    
    # Evitiamo divisione per zero
    if np.isclose(mean_mag, mc):
        # Caso degenere: tutti gli eventi hanno esattamente magnitudo Mc
        b_value = np.nan 
        valid = False
    else:
        b_value = 0.4343 / (mean_mag - mc)
        valid = True

    # 5. Calcolo a-value
    # log10(N) = a - b * Mc  =>  a = log10(N) + b * Mc
    if valid:
        a_value = np.log10(n_total) + (b_value * mc)
    else:
        a_value = np.nan

    return {
        'a_value': a_value,
        'b_value': b_value,
        'mc': mc,
        'n_total': n_total,
        'valid': valid
    }
