import streamlit as st
from google import genai
import streamlit.components.v1 as components
import os
from dotenv import load_dotenv

load_dotenv()

# Configure API
api_key = os.getenv("GOOGLE_API_KEY")

def get_ai_response(prompt, context_text):
    """Call Google Gemini API"""
    if not api_key:
        return "⚠️ API Key mancante. Configurala nel file .env."
    
    try:
        client = genai.Client(api_key=api_key)
        full_prompt = f"""
        Sei un esperto sismologo e data scientist.
        L'utente sta guardando una dashboard di analisi sismica.
        
        CONTESTO PAGINA ATTUALE:
        {context_text}
        
        DOMANDA UTENTE:
        {prompt}
        
        Rispondi in modo conciso, scientifico ma semplice. Usa l'italiano.
        """
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=full_prompt
        )
        return response.text
    except Exception as e:
        return f"Errore: {str(e)}"

@st.fragment
def render_chat_content(context_text):
    """
    Isolated fragment for chat logic to prevent full app reruns.
    """
    # Initialize processing state
    if "chat_processing" not in st.session_state:
        st.session_state.chat_processing = False

    # Helper Callback for Input
    def handle_input():
        if st.session_state.popover_chat_input:
            # Add User Message
            st.session_state.messages.append({"role": "user", "content": st.session_state.popover_chat_input})
            # Set processing flag - This triggers the UI update on the NEXT run
            st.session_state.chat_processing = True

    # Chat History
    chat_container = st.container(height=350)
    with chat_container:
        if not st.session_state.messages:
            st.info("👋 Ciao! Sono l'assistente sismologo. Chiedimi qualcosa sui dati.")
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
    
    # Input Area - Use on_submit callback!
    st.chat_input(
        "Chiedi...", 
        key="popover_chat_input", 
        on_submit=handle_input
    )
    
    # Handle AI Response (Processing Phase)
    if st.session_state.chat_processing:
        # Retrieve last user message
        last_user_msg = st.session_state.messages[-1]["content"]
        
        # Display spinner inside the chat container
        with chat_container:
            # Ensure we import time if not already available in this scope
            import time
            
            # 1. Scroll to BOTTOM to show "Sto pensando..." (Inject JS *outside* the message bubble to avoid empty space)
            ts_start = int(time.time() * 1000)
            js_scroll_bottom = f"""
            <script>
                setTimeout(function() {{
                    var messages = window.parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                    if (messages.length > 0) {{
                        var lastMessage = messages[messages.length - 1];
                        lastMessage.scrollIntoView({{block: 'end', behavior: 'smooth'}});
                    }}
                }}, 100);
            </script>
            <div style="display:none;">{ts_start}_start</div>
            """
            components.html(js_scroll_bottom, height=0, width=0)

            with st.chat_message("assistant"):
                with st.spinner("Sto pensando..."):
                    ai_reply = get_ai_response(last_user_msg, context_text)
                st.markdown(ai_reply) # Render immediately!
        
        # Scroll to the top of the new message
        # We target the last stChatMessage element and scroll it to the TOP (block='start')
        # We add a longer delay (1sec) and a retry mechanism to fight against Streamlit's auto-scroll
        import time
        unique_id = int(time.time() * 1000)
        js_scroll = f"""
        <script>
            function scrollToTop() {{
                try {{
                    var messages = window.parent.document.querySelectorAll('[data-testid="stChatMessage"]');
                    if (messages.length > 0) {{
                        var lastMessage = messages[messages.length - 1];
                        lastMessage.scrollIntoView({{block: 'start', behavior: 'smooth'}});
                    }}
                }} catch(e) {{
                    console.log("Scroll error:", e);
                }}
            }}

            // Attempt 1: 1000ms
            setTimeout(scrollToTop, 1000);
            
            // Attempt 2: 1500ms (just in case)
            setTimeout(scrollToTop, 1500);
        </script>
        <div style="display:none;">{unique_id}</div>
        """
        components.html(js_scroll, height=0, width=0)
        
        # Add AI Message to history for next run
        st.session_state.messages.append({"role": "assistant", "content": ai_reply})
        
        # Reset processing flag
        st.session_state.chat_processing = False

def render_ai_assistant(context_text=""):
    """
    Renders a floating action button using st.popover with custom CSS.
    """
    # Initialize State
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # --- CSS Styles ---
    # Enforce floating bubble look for the popover button
    st.markdown("""
    <style>
        /* Target the container of the popover to position it fixed */
        div[data-testid="stPopover"] {
            position: fixed !important;
            bottom: 30px !important;
            right: 30px !important;
            width: 60px !important;
            height: 60px !important;
            z-index: 999990 !important;
            display: block !important;
            background-color: transparent !important;
        }
        
        /* Style the popover button itself to be the round FAB */
        div[data-testid="stPopover"] > button {
            width: 60px !important;
            height: 60px !important;
            border-radius: 50% !important;
            background-color: #ff4b4b !important;
            color: white !important;
            border: none !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            font-size: 24px !important;
            padding: 0 !important;
            display: flex !important;
            align-items: center !important;
            justify-content: center !important;
            margin: 0 !important;
        }

        /* Hover effect */
        div[data-testid="stPopover"] > button:hover {
            transform: scale(1.1);
            background-color: #ff3333 !important;
            box-shadow: 0 6px 16px rgba(0,0,0,0.4) !important;
        }
        
        /* Remove default secondary color border if any */
        div[data-testid="stPopover"] > button:active, 
        div[data-testid="stPopover"] > button:focus {
            background-color: #ff4b4b !important;
            border: none !important;
            outline: none !important;
            box-shadow: 0 4px 12px rgba(0,0,0,0.3) !important;
            color: white !important;
        }

        /* Enforce fixed size for the popover content (the chat window) */
        div[data-testid="stPopoverBody"] {
            width: 400px !important;
            max-width: 90vw !important;
            height: 500px !important;
            max-height: 80vh !important;
            border: 1px solid #4a4a4a;
            border-radius: 10px;
        }
        
    </style>
    """, unsafe_allow_html=True)

    # Use st.popover for the floating window effect
    with st.popover("💬", use_container_width=False):
        st.markdown("### 🤖 Assistant")
        # Render the chat content inside a fragment to isolate reruns
        render_chat_content(context_text)
