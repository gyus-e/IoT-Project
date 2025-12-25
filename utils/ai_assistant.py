import streamlit as st
from google import genai
import os
from dotenv import load_dotenv

load_dotenv()

# Configure API
api_key = os.getenv("GOOGLE_API_KEY")

def render_ai_sidebar(context_text=""):
    with st.sidebar:
        st.markdown("---")
        st.header("🤖 AI Analyst")
        
        client = None
        
        if not api_key:
            st.warning("API Key mancante in .env")
            user_key = st.text_input("Inserisci Google API Key:", type="password")
            if user_key:
                os.environ["GOOGLE_API_KEY"] = user_key
                try:
                    client = genai.Client(api_key=user_key)
                except Exception as e:
                    st.error(f"Errore Init Client: {e}")
        else:
            try:
                client = genai.Client(api_key=api_key)
                st.success("AI Connected")
            except Exception as e:
                st.error(f"Errore Connessione AI: {e}")
        
        # Chat History
        if "messages" not in st.session_state:
            st.session_state.messages = []

        # Display chat messages
        with st.expander("Chat History", expanded=False):
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

        # Chat Input
        if prompt := st.chat_input("Chiedi al Sismologo AI..."):
            if not client:
                st.error("Inserisci prima una API Key valida.")
            else:
                # Add user message
                st.session_state.messages.append({"role": "user", "content": prompt})
                
                # Prepare context
                full_prompt = f"""
                Sei un esperto sismologo e data scientist.
                L'utente sta guardando una dashboard di analisi sismica.
                
                CONTESTO PAGINA ATTUALE:
                {context_text}
                
                DOMANDA UTENTE:
                {prompt}
                
                Rispondi in modo conciso, scientifico ma semplice. Usa l'italiano.
                """
                
                try:
                    # Using gemini-flash-latest (Stable 1.5) for best free tier availability
                    response = client.models.generate_content(
                        model="gemini-flash-latest", 
                        contents=full_prompt
                    )
                    ai_reply = response.text
                    
                    st.session_state.messages.append({"role": "assistant", "content": ai_reply})
                    st.rerun()
                except Exception as e:
                    st.error(f"Errore Generazione: {e}")
