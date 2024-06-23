import os
from dotenv import load_dotenv
import openai
import requests
import json

import time
import logging
from datetime import datetime
import streamlit as st


load_dotenv()

client = openai.OpenAI()

model = "gpt-4-turbo"  # "gpt-3.5-turbo-16k"

# == Korak 0. Zakačićemo fajl u OpenAI embeddings ===
# filepath = "./cryptocurrency.pdf"
# file_object = client.files.create(file=open(filepath, "rb"), purpose="assistants")


# == Korak 2. - Kreiramo asistenta
assistant = client.beta.assistants.create(
    name="Study Buddy",
    instructions="""Ti si asistent koji zna mnogo o tumačenju istraživačkih radova. 
    Tvoja uloga je da rezimiraš radove, razjasniš terminologiju unutar konteksta i izdvojiš ključne brojke i podatke. 
    Unakrsno obrađuj informacije za dodatne uvide i sveobuhvatan odgovor na srodna pitanja. 
    Analiziraš radove, uočavajući prednosti i mane tražene teme. 
    Efikasno odgovaraš na upite, uključujući povratne informacije da bi poboljšao svoju preciznost. 
    Bezbijedno rukuješ sa podacima i ažuriraš svoju bazu znanja najnovijim istraživanjima. 
    Pridržavaš se etičkih standarda, poštuješ intelektualnu svojinu i pružaš korisnicima uputstva o svim ograničenjima. 
    Održavaš povratnu spregu za kontinuirano poboljšanje i korisničku podršku. 
    Tvoj krajnji cilj je da olakšaš razumijevanje složenog naučnog materijala, čineći ga dostupnijim i razumljivijim.""",
    model=model,
    tools=[{"type": "file_search"}],
)


# == Korak 2.1 Prema najnovijoj verziji OpenAI API asistent od sad prima za file retrieval vector store objekat pa se on mora pripremiti

# Kreiram vector store u kome ce se referencirati fajlovi
vector_store = client.beta.vector_stores.create(name="Study literature")
 
# Smijestam fajlove u varijable
file_paths = ["cryptocurrency.pdf", "VW Caddy - 4-cylinder diesel engine (2.0 l engine, 2-valve, TDI).pdf"]
file_streams = [open(path, "rb") for path in file_paths]
 
# Koristim vector store batch update helper da ih asociram sa svojim fajlovima
file_batch = client.beta.vector_stores.file_batches.upload_and_poll(
  vector_store_id=vector_store.id, files=file_streams
)
 
# Prvi put kada napravim store zelim da vidim da li je sve u redu
print(file_batch.status)
print(file_batch.file_counts)


# Cinimo vector store dostupnim asistentu
assistant = client.beta.assistants.update(
  assistant_id=assistant.id,
  tool_resources={"file_search": {"vector_store_ids": [vector_store.id]}},
)

# === Štampam ID asistenta kako bi ga zakucao u program poslije ===
assis_id = assistant.id
print(assis_id)

# == Zakucan ID kada prvi put pokrenemo i kreiramo asistenta, nema potrebe da imamo više istih asistenata
# thread_id = ""
# assis_id = ""

# == Korak 4. Kreiramo thread
message = "Šta je mining?"

thread = client.beta.threads.create()
thread_id = thread.id
print(thread_id)

message = client.beta.threads.messages.create(
    thread_id=thread_id, role="user", content=message
)

# == Pokreni asistenta
run = client.beta.threads.runs.create(
    thread_id=thread_id,
    assistant_id=assis_id,
    instructions="Molim te obraćaj se korisniku po imenu Roberto Cavalli.",
)


def wait_for_run_completion(client, thread_id, run_id, sleep_interval=5):
    """
    Čeka da se run proces završi i štampa argumente.
    :param client: Objekat OpenAI client-a.
    :param thread_id: ID thread-a.
    :param run_id: ID run objekta.
    :param sleep_interval: Vrijeme čekanja u sekundama.
    """
    while True:
        try:
            run = client.beta.threads.runs.retrieve(thread_id=thread_id, run_id=run_id)
            if run.completed_at:
                elapsed_time = run.completed_at - run.created_at
                formatted_elapsed_time = time.strftime(
                    "%H:%M:%S", time.gmtime(elapsed_time)
                )
                print(f"Run completed in {formatted_elapsed_time}")
                logging.info(f"Run completed in {formatted_elapsed_time}")
                # Get messages here once Run is completed!
                messages = client.beta.threads.messages.list(thread_id=thread_id)
                last_message = messages.data[0]
                response = last_message.content[0].text.value
                print(f"Odgovor asistenta: {response}")
                break
        except Exception as e:
            logging.error(f"Desio se error dok se izvršavao run: {e}")
            break
        logging.info("Čekam run da se završi...")
        time.sleep(sleep_interval)


# == Pokreće sve
wait_for_run_completion(client=client, thread_id=thread_id, run_id=run.id)

# === Provjera run koraka - Debug logovi prilikom programiranja ===
run_steps = client.beta.threads.runs.steps.list(thread_id=thread_id, run_id=run.id)
print(f"Run Steps --> {run_steps.data[0]}")