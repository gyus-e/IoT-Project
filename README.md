# Dashboard sismica

Progetto di visualizzazione dati, analisi statistica e monitoraggio di eventi sismici nel Mediterraneo, basato sui dati forniti dall'[Istituto Nazionale di Geofisica e Vulcanologia (INGV)](https://terremoti.ingv.it/
).

---

## Contesto accademico

Progetto sviluppato per il corso di **Operating Systems for Mobile, Cloud and IoT** (A.A. 2025/2026).  
**Università degli Studi di Napoli Federico II** - Corso di Laurea Magistrale in Informatica.

**Gruppo G28:**
* [Giuseppe AMATO](https://github.com/gyus-e/)
* [Giuseppe DI MARTINO](https://github.com/giuseppedima/)

**Docente:** Prof. [Silvio BARRA](https://www.docenti.unina.it/silvio.barra)

---

## Funzionalità principali

### 1. Dashboard interattiva
* Visualizzazione geospaziale degli eventi sismici su mappa interattiva.
* Filtri avanzati nella sidebar: range temporale, profondità, magnitudo, latitudine/longitudine.
* Interazione con i singoli eventi: selezione su mappa per visualizzare i dettagli e recuperare le forme d'onda (waveform) dalla stazione più vicina.
* Analisi spettrale (FFT) del segnale sismico selezionato.

### 2. Analisi statistica
* Calcolo della Legge di Gutenberg-Richter (parametri *a* e *b*) tramite metodo MLE (Maximum Likelihood Estimation).
* Interpretazione automatica del *b-value* (stress sismico vs sciame).
* Istogrammi temporali e analisi dei tempi di attesa tra eventi.
* Pattern spazio-temporali.

### 3. Segnali sismici e real-time
* Monitoraggio in tempo reale delle stazioni (OVO, CSFT, IOCA, SORR).
* Rilevamento anomalie/allerte.
* Confronto segnali: analisi comparativa tra un evento naturale (Terremoto Campi Flegrei) e un evento antropico (Festa Scudetto Napoli 2023).

### 4. Allerte e anomalie
* Calcolo del tempo di ritorno probabilistico.
* Identificazione di eventi "rari" basata sulla storia sismica dell'area selezionata.

### 5. AI assistant
* Chatbot integrato basato su Google Gemini.
* Context-Aware: l'IA riceve dinamicamente i dati visualizzati (statistiche, evento selezionato, grafici) per fornire risposte precise e scientifiche.

---

## Stack tecnologico

* **Language:** Python
* **UI framework:** [Streamlit](https://streamlit.io/)
* **Sismologia:** [ObsPy](https://github.com/obspy/obspy) (Client FDSN, gestione waveform)
* **Data science:** Pandas, NumPy
* **Visualizzazione:** Plotly Express / Graph Objects
* **AI/LLM:** Google GenAI SDK (Gemini Flash Lite)

---

## Installazione e configurazione

### 1. Clona la repository
```bash
git clone https://github.com/gyus-e/IoT-Project.git
cd IoT-Project

```

### 2. Crea un ambiente virtuale (Opzionale ma consigliato)

```bash
python -m venv venv
# Su Windows
venv\Scripts\activate
# Su Mac/Linux
source venv/bin/activate

```

### 3. Installa le dipendenze

```bash
pip install -r requirements.txt

```

### 4. Configura le chiavi API

Il progetto richiede una API Key di Google (Gemini) per l'assistente virtuale.

1. Rinomina il file `.env.example` in `.env`.
2. Inserisci la tua chiave nel file `.env`:

```text
GOOGLE_API_KEY="la_tua_chiave_api_qui"

```

### 5. Scarica i dati (Importante!)

Prima di avviare l'applicazione, è necessario scaricare il catalogo sismico e le waveform di confronto. Esegui lo script dedicato:

```bash
python scripts/fetch_data.py

```

*Questo script scaricherà i dati necessari e li salverà nella cartella `data/`.*

---

## Utilizzo

Avvia l'applicazione Streamlit:

```bash
streamlit run Home.py

```

L'applicazione sarà accessibile nel browser all'indirizzo `http://localhost:8501`.

---

## Licenza e crediti

I dati sismici sono proprietà dell'[Istituto Nazionale di Geofisica e Vulcanologia (INGV)](https://terremoti.ingv.it/) e sono utilizzati tramite i servizi web FDSN conformemente alla policy di utilizzo dati INGV.

Progetto a scopo didattico.
