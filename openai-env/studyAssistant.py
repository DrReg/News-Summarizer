from dotenv import load_dotenv
import openai

import time
from datetime import datetime
import streamlit as st


load_dotenv()

client = openai.OpenAI()

model = "gpt-4-1106-preview"  # "gpt-3.5-turbo-16k"


# Ovi ID-jevi su trajno ukodirani jer prosto referenciraju ranije kreirani asistent

thread_id = "thread_inGWHWAOfo3yxnwNZCophiXL"
assis_id = "asst_KPhtBJnaLiJaYqGDqnoHn9oP"

# Inicijalizacija chat sesije

if "file_id_list" not in st.session_state:
    st.session_state.file_id_list = []

if "start_chat" not in st.session_state:
    st.session_state.start_chat = False

if "thread_id" not in st.session_state:
    st.session_state.thread_id = None


# Front end podešavanje

st.set_page_config(page_title="Study Buddy - Chat and Learn", page_icon=":books:")


# ==== Definicije funkcija =====
def upload_to_openai(filepath):
    with open(filepath, "rb") as file:
        response = client.files.create(file=file.read(), purpose="assistants")
    return response.id


# === Sidebar - gdje korisnici mogu zakačiti fajlove

file_uploaded = st.sidebar.file_uploader(
    "Zakači fajl da se pretvori u embeddings.", key="file_upload"
)

# Dugme za upload fajla, pravi file_id

if st.sidebar.button("Zakači fajl"):
    if file_uploaded:
        with open(f"{file_uploaded.name}", "wb") as f:
            f.write(file_uploaded.getbuffer())
        another_file_id = upload_to_openai(f"{file_uploaded.name}")
        st.session_state.file_id_list.append(another_file_id)
        st.sidebar.write(f"File ID:: {another_file_id}")

# Prikaz file_id-jeva

if st.session_state.file_id_list:
    st.sidebar.write("Uploaded File IDs:")
    for file_id in st.session_state.file_id_list:
        st.sidebar.write(file_id)
        # Asocira svaki fajl sa asistentom
        assistant_file = client.beta.assistants.files.create(
            assistant_id=assis_id, file_id=file_id
        )

# Dugme za inicijalizaciju chat sesije

if st.sidebar.button("Pokreni chat..."):
    if st.session_state.file_id_list:
        st.session_state.start_chat = True

        # Kreira nov thread za sesiju
        chat_thread = client.beta.threads.create()
        st.session_state.thread_id = chat_thread.id
        st.write("Thread ID:", chat_thread.id)
    else:
        st.sidebar.warning(
            "Nema pronađenih fajlova. Zakačite makar jedan fajl da biste počeli."
        )


# Funkcija za procesiranje poruke sa citatima

def process_message_with_citations(message):
    """Izvuci sadržaj i napomene iz poruke i formatiraj citate kao fusnote."""
    message_content = message.content[0].text
    annotations = (
        message_content.annotations if hasattr(message_content, "annotations") else []
    )
    citations = []

    # Prolazi kroz niz notacija i dodaje citate
    for index, annotation in enumerate(annotations):
        # Mijenja tekst sa fusnotom
        message_content.value = message_content.value.replace(
            annotation.text, f" [{index + 1}]"
        )

        # Getuje citate na osnovu fajla
        if file_citation := getattr(annotation, "file_citation", None):
            # Preuzima detalje o citiranom fajlu (ovde lažni odgovor pošto ne možemo da pozovemo OpenAI)
            cited_file = {
                "filename": "cryptocurrency.pdf"
            }  # Treba se zamijeniti pravim vracanjem fajla
            citations.append(
                f'[{index + 1}] {file_citation.quote} from {cited_file["filename"]}'
            )
        elif file_path := getattr(annotation, "file_path", None):
            # Placeholder za file download citiranje
            cited_file = {
                "filename": "cryptocurrency.pdf"
            }  # TODO: Trebao bi zamijeniti sa pravim vracanjem fajla
            citations.append(
                f'[{index + 1}] Klikni [ovdje](#) za download {cited_file["filename"]}'
            )  # Link za download bi trebao zamijeniti sa pravom putanjom do fajla

    # Dodaje fusnote na kraju odgovora

    full_response = message_content.value + "\n\n" + "\n".join(citations)
    return full_response


# Glavni interfejs

st.title("Study Buddy")
st.write("Learn fast by chatting with your documents")


# Provjera sesija

if st.session_state.start_chat:
    if "openai_model" not in st.session_state:
        st.session_state.openai_model = "gpt-4-1106-preview"
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Prikaz ranijih poruka

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # chat za korisnika

    if prompt := st.chat_input("What's new?"):
        # Dodaje korisnikovu poruku na ekran
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # dodaje korisnikovu poruku na thread
        client.beta.threads.messages.create(
            thread_id=st.session_state.thread_id, role="user", content=prompt
        )

        # Kreira run sa dodatnim instrukcijama

        run = client.beta.threads.runs.create(
            thread_id=st.session_state.thread_id,
            assistant_id=assis_id,
            instructions="""Molim te da odgovoriš na pitanja koristeći znanje dato u datotekama.
            Kada dodaješ dodatne informacije, pazi da ih istakneš podebljanim ili podvučenim tekstom.""",
        )

        # Prikaz spinnera da prikaze da asistent radi

        with st.spinner("Sačekajte... Osmišljam odgovor..."):
            while run.status != "completed":
                time.sleep(1)
                run = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state.thread_id, run_id=run.id
                )
            # Vrati poruke generisane od asistenta
            messages = client.beta.threads.messages.list(
                thread_id=st.session_state.thread_id
            )
            # Prikazi poruke asistenta
            assistant_messages_for_run = [
                message
                for message in messages
                if message.run_id == run.id and message.role == "assistant"
            ]

            for message in assistant_messages_for_run:
                full_response = process_message_with_citations(message=message)
                st.session_state.messages.append(
                    {"role": "assistant", "content": full_response}
                )
                with st.chat_message("assistant"):
                    st.markdown(full_response, unsafe_allow_html=True)

    else:
        # Opominje korisnika za chat
        st.write(
            "Molim Vas zakačite makar jedan fajl da biste mogli da pokrenete 'Pokreni Chat' dugme"
        )