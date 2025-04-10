import streamlit as st
import gspread
import pandas as pd
import os
import json
from google.oauth2.service_account import Credentials

# Configurazione della pagina
st.set_page_config(page_title="Workout Tracker", layout="wide", initial_sidebar_state="expanded")

# Definizione dello scope per l'API
SCOPES = [
    'https://www.googleapis.com/auth/spreadsheets',
    'https://www.googleapis.com/auth/drive'
]

# Colori per i livelli di intensità
INTENSITY_COLORS = {
    "FAIL": "#FF4B4B",  # Rosso
    "RIR 0": "#FF8C4B",  # Arancione
    "RIR 0-1": "#FFD700",  # Oro
    "RIR 1-2": "#4CAF50",  # Verde
    "RIR 2-3": "#2196F3",  # Blu
}

# Opzioni di intensità
INTENSITY_OPTIONS = ["", "FAIL", "RIR 0", "RIR 0-1", "RIR 1-2", "RIR 2-3"]

# Dati utente
USER_DATA = {
    "antonio": {
        "password": "123456",
        "credentials_file": "test1",
        "name": "Antonio"
    },
    "stefano": {
        "password": "123456",
        "credentials_file": "test2",
        "name": "Stefano"
    }
}

# URL del Google Sheets
SHEETS_URL = "https://docs.google.com/spreadsheets/d/1ocESHDXfRD3u8VZjXkBXwj9G4PpeA93hCUtfTns509M/edit?gid=307799828#gid=307799828"

# CSS personalizzato
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 2rem;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.1);
    }
    
    .day-header {
        font-size: 1.8rem;
        background-color: #1E88E5;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        margin-bottom: 1.5rem;
    }
    
    .exercise-card {
        background-color: #f8f9fa;
        border-radius: 8px;
        padding: 1rem;
        box-shadow: 0 2px 5px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }
    
    .serie-card {
        border-radius: 5px;
        padding: 0.75rem;
        margin-bottom: 0.5rem;
    }
    
    .detail-text {
        font-size: 0.9rem;
        color: #555;
    }
    
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        background-color: #1E88E5;
        color: white;
    }
    
    .stButton>button:hover {
        background-color: #0D47A1;
    }
    
    /* Stili per i selettori di intensità */
    .intensity-fail {
        background-color: #FF4B4B !important;
        color: white !important;
    }
    .intensity-rir0 {
        background-color: #FF8C4B !important;
        color: white !important;
    }
    .intensity-rir0-1 {
        background-color: #FFD700 !important;
        color: black !important;
    }
    .intensity-rir1-2 {
        background-color: #4CAF50 !important;
        color: white !important;
    }
    .intensity-rir2-3 {
        background-color: #2196F3 !important;
        color: white !important;
    }
    
    /* Stili per il form di login */
    .login-container {
        max-width: 500px;
        margin: 0 auto;
        padding: 2rem;
        background-color: #f8f9fa;
        border-radius: 10px;
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }
    
    .login-header {
        font-size: 1.5rem;
        color: #1E88E5;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .login-button {
        margin-top: 1rem;
    }
    
    .welcome-text {
        font-size: 1.2rem;
        color: #333;
        text-align: center;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Funzione per autorizzare e ottenere il client
def get_google_client(credentials_file):
     # Ottieni i dati delle credenziali direttamente da st.secrets
    creds_data = st.secrets[credentials_file]
    
    # Crea un oggetto Credentials direttamente dai dati del secrets.toml
    creds = Credentials.from_service_account_info(creds_data, scopes=SCOPES)
    return gspread.authorize(creds)

# Funzione per estrarre i giorni e gli esercizi dal foglio
def extract_workout_data(worksheet):
    """Estrae i giorni e gli esercizi dal foglio con la struttura specificata."""
    values = worksheet.get_all_values()
    
    workout_data = {}
    current_day = None
    
    for i, row in enumerate(values):
        # Verifica se la riga inizia con "DAY"
        if len(row) > 0 and row[0].startswith("DAY "):
            current_day = row[0]
            workout_data[current_day] = []
            # Salta la riga dell'intestazione
            continue
        
        # Salta le righe di intestazione
        if len(row) > 0 and row[0] == "GRUPPO MUSCOLARE":
            continue
        
        # Se abbiamo un giorno corrente e la riga contiene dati validi di esercizio
        if current_day and len(row) >= 7 and row[0] and row[1]:
            exercise = {
                "gruppo": row[0],
                "nome": row[1],
                "tecnica": row[2],
                "note": row[3],
                "rest": row[4],
                "serie": row[5],
                "reps": row[6],
                "serie_dati": []
            }
            
            # Estrai i dati delle serie (C, R, INTENSITY)
            # Le serie iniziano dalla colonna 8 (indice 7)
            for serie_idx in range(4):  # Assumiamo fino a 4 serie
                base_idx = 8 + (serie_idx * 4)  # Ogni serie ha 4 colonne (INCREASE, C, R, INTENSITY)
                
                if base_idx < len(row):
                    serie_data = {
                        "increase": row[base_idx-1] if base_idx-1 < len(row) else "",
                        "carico": row[base_idx] if base_idx < len(row) else "",
                        "ripetizioni": row[base_idx+1] if base_idx+1 < len(row) else "",
                        "intensity": row[base_idx+2] if base_idx+2 < len(row) else ""
                    }
                    exercise["serie_dati"].append(serie_data)
            
            workout_data[current_day].append(exercise)
    
    return workout_data

# Funzione per aggiornare i dati C, R e Intensity nel foglio
def update_cr_values(worksheet, day, exercise_name, serie_index, carico, ripetizioni, intensity):
    """Aggiorna i valori di carico (C), ripetizioni (R) e intensità per un esercizio in una serie specifica"""
    values = worksheet.get_all_values()
    
    # Trova il giorno e l'esercizio
    day_row = -1
    exercise_row = -1
    
    for i, row in enumerate(values):
        if len(row) > 0 and row[0] == day:
            day_row = i
        
        # Se abbiamo trovato il giorno e questa riga contiene l'esercizio cercato
        if day_row != -1 and i > day_row and len(row) > 1 and row[1] == exercise_name:
            exercise_row = i
            break
    
    if exercise_row != -1:
        # Calcola le colonne per C, R e INTENSITY nella serie specificata
        c_col = 9 + (serie_index * 4)  # C è la 9ª colonna per la prima serie
        r_col = 10 + (serie_index * 4)  # R è la 10ª colonna per la prima serie
        i_col = 11 + (serie_index * 4)  # INTENSITY è la 11ª colonna per la prima serie
        
        # Aggiorna i valori nel foglio
        if carico:
            worksheet.update_cell(exercise_row + 1, c_col, carico)
        if ripetizioni:
            worksheet.update_cell(exercise_row + 1, r_col, ripetizioni)
        if intensity:
            worksheet.update_cell(exercise_row + 1, i_col, intensity)
        
        return True
    
    return False

# Inizializzazione delle variabili di sessione
if 'logged_in' not in st.session_state:
    st.session_state['logged_in'] = False

if 'user_email' not in st.session_state:
    st.session_state['user_email'] = ""

if 'credentials_file' not in st.session_state:
    st.session_state['credentials_file'] = ""

if 'user_name' not in st.session_state:
    st.session_state['user_name'] = ""

# Header principale
st.markdown("<h1 class='main-header'>Workout Tracker Pro</h1>", unsafe_allow_html=True)

# Pagina di login se l'utente non è loggato
if not st.session_state['logged_in']:
    st.markdown("<div class='login-container'>", unsafe_allow_html=True)
    st.markdown("<h2 class='login-header'>Accedi al tuo account</h2>", unsafe_allow_html=True)
    
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")
    
    login_pressed = st.button("Login", key="login_button")
    
    if login_pressed:
        if email in USER_DATA and USER_DATA[email]["password"] == password:
            st.session_state['logged_in'] = True
            st.session_state['user_email'] = email
            st.session_state['credentials_file'] = USER_DATA[email]["credentials_file"]
            st.session_state['user_name'] = USER_DATA[email]["name"]
            st.success("Login effettuato con successo!")
            st.rerun()
        else:
            st.error("Email o password non validi. Riprova.")
    
    st.markdown("</div>", unsafe_allow_html=True)

# Se l'utente è loggato, mostra l'applicazione
else:
    # Barra laterale con informazioni utente
    st.sidebar.title(f"🏋️ Benvenuto, {st.session_state['user_name']}!")
    st.sidebar.markdown("---")
    
    if st.sidebar.button("Logout"):
        st.session_state['logged_in'] = False
        st.session_state['user_email'] = ""
        st.session_state['credentials_file'] = ""
        st.session_state['user_name'] = ""
        st.rerun()
    
    # Tentativo di caricamento del foglio Google Sheets
    try:
        # Verifica che il file delle credenziali esista
        credentials_file = st.session_state['credentials_file']
        
        # Autorizzazione
        client = get_google_client(credentials_file)
        
        # Apertura del foglio
        spreadsheet = client.open_by_url(SHEETS_URL)
        
        # Lista dei fogli
        worksheet_list = spreadsheet.worksheets()
        worksheet_names = [ws.title for ws in worksheet_list]
        worksheet_names = worksheet_names[1:9]  # Escludi il primo foglio
        
        # Selezione del foglio
        st.sidebar.markdown("## 📊 Seleziona il foglio")
        selected_worksheet_name = st.sidebar.selectbox(
            "Settimana/Programma",
            worksheet_names,
            help="Scegli il foglio di lavoro che vuoi visualizzare/modificare"
        )
        worksheet = spreadsheet.worksheet(selected_worksheet_name)
        
        # Estrai i dati dal foglio
        workout_key = f'workout_data_{selected_worksheet_name}'
        if workout_key in st.session_state:
            workout_data = st.session_state[workout_key]
        else:
            with st.spinner("Caricamento dati in corso..."):
                workout_data = extract_workout_data(worksheet)
                st.session_state[workout_key] = workout_data
        
        # Visualizza i giorni
        if workout_data:
            days = list(workout_data.keys())
            
            # Selettore di giorno migliorato
            st.markdown("## 📅 Seleziona il Giorno")
            selected_day = st.selectbox(
                "Giorno di allenamento",
                days,
                help="Scegli il giorno di allenamento da visualizzare"
            )
            
            if selected_day:
                # Header del giorno selezionato
                st.markdown(f"<h2 class='day-header'>{selected_day}</h2>", unsafe_allow_html=True)
                day_exercises = workout_data[selected_day]
                
                # Visualizza gli esercizi del giorno selezionato
                for exercise in day_exercises:
                    with st.expander(f"💪 {exercise['nome']} ({exercise['gruppo']})"):
                        # Mostra i dettagli dell'esercizio
                        col1, col2, col3, col4 = st.columns(4)
                        with col1:
                            st.markdown(f"**Tecnica:** <span class='detail-text'>{exercise['tecnica']}</span>", unsafe_allow_html=True)
                        with col2:
                            st.markdown(f"**Note:** <span class='detail-text'>{exercise['note']}</span>", unsafe_allow_html=True)
                        with col3:
                            st.markdown(f"**Rest:** <span class='detail-text'>{exercise['rest']}</span>", unsafe_allow_html=True)
                        with col4:
                            st.markdown(f"**Serie x Reps:** <span class='detail-text'>{exercise['serie']} x {exercise['reps']}</span>", unsafe_allow_html=True)
                        
                        st.markdown("<hr>", unsafe_allow_html=True)
                        
                        # Visualizzazione più compatta delle serie
                        num_series = len(exercise['serie_dati'])
                        
                        # Determina il numero di colonne in base al numero di serie
                        num_cols = min(num_series, 4)  # Massimo 4 colonne
                        serie_cols = st.columns(num_cols)
                        
                        for i, serie_data in enumerate(exercise['serie_dati']):
                            col_idx = i % num_cols
                            with serie_cols[col_idx]:
                                st.markdown(f"<div class='serie-card'>", unsafe_allow_html=True)
                                st.subheader(f"Serie {i+1}")
                                
                                if serie_data['increase']:
                                    st.markdown(f"**Increase:** {serie_data['increase']}")
                                
                                # Input per il carico
                                carico = st.text_input(
                                    "Carico (kg)",
                                    value=serie_data['carico'],
                                    key=f"{selected_day}_{exercise['nome']}_serie{i+1}_carico"
                                )
                                
                                # Input per le ripetizioni
                                ripetizioni = st.text_input(
                                    "Ripetizioni",
                                    value=serie_data['ripetizioni'],
                                    key=f"{selected_day}_{exercise['nome']}_serie{i+1}_reps"
                                )
                                
                                # Menu a tendina per l'intensità
                                current_intensity = serie_data['intensity'] if serie_data['intensity'] in INTENSITY_OPTIONS else ""
                                intensity = st.selectbox(
                                    "Intensità",
                                    INTENSITY_OPTIONS,
                                    index=INTENSITY_OPTIONS.index(current_intensity) if current_intensity else 0,
                                    key=f"{selected_day}_{exercise['nome']}_serie{i+1}_intensity"
                                )
                                
                                # Mostra indicatore colorato per l'intensità selezionata
                                if intensity:
                                    color = INTENSITY_COLORS.get(intensity, "#FFFFFF")
                                    st.markdown(
                                        f"""
                                        <div style="background-color: {color}; 
                                                    color: {'black' if intensity == 'RIR 0-1' else 'white'}; 
                                                    padding: 5px; 
                                                    border-radius: 5px; 
                                                    text-align: center; 
                                                    margin-bottom: 10px;">
                                            {intensity}
                                        </div>
                                        """, 
                                        unsafe_allow_html=True
                                    )
                                
                                # Pulsante per salvare
                                if st.button("Salva", key=f"save_{selected_day}_{exercise['nome']}_serie{i+1}"):
                                    with st.spinner("Aggiornamento in corso..."):
                                        if update_cr_values(worksheet, selected_day, exercise['nome'], i, carico, ripetizioni, intensity):
                                            st.success("Dati aggiornati con successo!")
                                            
                                            # Aggiorna anche i dati in sessione
                                            serie_data['carico'] = carico
                                            serie_data['ripetizioni'] = ripetizioni
                                            serie_data['intensity'] = intensity
                                            st.session_state[workout_key] = workout_data
                                        else:
                                            st.error("Errore nell'aggiornamento dei dati.")
                                
                                st.markdown("</div>", unsafe_allow_html=True)
            else:
                st.warning("Non sono stati trovati dati nel formato atteso nel foglio selezionato.")
                
    except Exception as e:
        st.error(f"❌ Si è verificato un errore: {e}")
        st.error(f"Dettagli: {str(e)}")

# Istruzioni per l'uso nella barra laterale
if st.session_state['logged_in']:
    with st.sidebar.expander("📚 Istruzioni"):
        st.markdown("""
        ## Come utilizzare l'app
        
        1. **Seleziona il foglio**:
           - Scegli la settimana/programma dalla barra laterale
        
        2. **Navigazione**:
           - Seleziona il giorno di allenamento
           - Espandi gli esercizi per visualizzare i dettagli
        
        3. **Modifica dei dati**:
           - Per ogni serie puoi modificare:
             - Il carico (C)
             - Le ripetizioni effettive (R)
             - L'intensità (FAIL, RIR 0, RIR 0-1, ecc.)
           - Clicca sul pulsante "Salva" per aggiornare il foglio
        
        4. **Intensità**:
           - **FAIL** = Non sei riuscito a completare le ripetizioni
           - **RIR 0** = Nessuna ripetizione rimasta (a cedimento)
           - **RIR 0-1** = 0-1 ripetizioni rimanenti
           - **RIR 1-2** = 1-2 ripetizioni rimanenti
           - **RIR 2-3** = 2-3 ripetizioni rimanenti
        """)

    # Footer
    st.sidebar.markdown("---")
    st.sidebar.markdown("© 2025 Workout Tracker Pro")