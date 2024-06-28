import openai
from dotenv import load_dotenv
import os
import time 
import json
import requests
import datetime

# openai.api_key = os.environ.get("OPENAI_API_KEY") je default
# Ovdje postavljam konfiguracije za instanciranje OpenAI assistent-a

load_dotenv()
news_api_key = os.environ.get("NEWS_API_KEY")
client = openai.OpenAI()
model = "gpt-3.5-turbo-16k"

class ChatAssistant:
    # thread_id = "thread_Tewm453iffuVWoqKvvaAz45d"
    # assistant_id = "asst_Q42qFA2YPAfmQUAwtRM1ah5o"

    thread_id = "thread_0AiD85unNVq5hB2S4cG2BSst"
    assistant_id = "asst_r9RondbWTKb0OOf96wvsEmZh"

    # Glavni konstruktor za asistenta

    def __init__(self, model: str = model):
        self.client = client
        self.model = model
        self.assistant = None
        self.thread = None
        self.run = None
        self.summary = None

        # Provjerava da li postoji vec neki assistent da je podesen (u slucaju da imam vise assistent-ova)

        if ChatAssistant.assistant_id:
            self.assistant = self.client.beta.assistants.retrieve(
                assistant_id = ChatAssistant.assistant_id
            )
        
        if ChatAssistant.thread_id:
            self.thread = self.client.beta.threads.retrieve(
                thread_id = ChatAssistant.thread_id
            )



    # Pravim metodu koja poziva NewsAPI i vraca sta mu API kaze, ima i custom URL kojem mu prosljedjujem temu i API kljuc

    # Ova metoda ima zadatak da salje zahtjev NewsAPI-ju i da samo vrati informacije iz clanaka u obliku teksta

    def get_news(self, topic, category, phrase, start_date, end_date):

        #Bazicni URL u slucaju da se samo vrsi pretraga po temi (default case)

        url = (
            f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=5"
        )

        #U slucaju da filtera koje je korisnik izabrao, dodaju se na bazicni URL

        if category:
            url += f"&category={category}"
        if phrase:
            url += f"&qInTitle={phrase}"
        if start_date:
            url += f"&from={start_date}"
        if end_date:
            url += f"&to={end_date}"

        try:
            response = requests.get(url)
            if response.status_code == 200:
                news = json.dumps(response.json(), indent=4)
                news_json = json.loads(news)

                data = news_json

                # Prolazim kroz JSON fajl odgovora i kupim podatke u varijable da bi ih kasnije obradio
                
                status = data["status"]
                total_results = data["totalResults"]
                articles = data.get("articles", [])

                final_news = []

                # articles je lista pa moram proci kroz sve elemente

                for article in articles:
                    news_item = {
                        "title": article.get("title", ""),
                        "description": article.get("description", ""),
                        "content": article.get("content", ""),
                        "source": article.get("source", {}).get("name", ""),
                        "author": article.get("author", ""),
                        "url": article.get("url", "")
                    }

                    final_news.append(news_item)


                return final_news
            else: 
                return []
            
        except requests.exceptions.RequestException as e:
            print("Error pri NewsAPI key zahtjevu :( ", e)
            
        # Metoda za kreiranje assistenta

    def create_assistant(self, name, instructions, tools):
        if not self.assistant:
            assistant_obj = self.client.beta.assistants.create(
                name = name,
                instructions = instructions,
                tools = tools,
                model = self.model
            )
            ChatAssistant.assistant_id = assistant_obj.id
            self.assistant = assistant_obj
            print(f"Assistant ID :::: {self.assistant.id}")

    # Metoda za kreiranje thread-a

    def create_thread(self):
        if not self.thread:
            thread_obj = self.client.beta.threads.create()
            ChatAssistant.thread_id = thread_obj.id
            self.thread = thread_obj
            print(f"Thread ID :::: {self.thread.id}")

    # Metoda koja dodaje poruku na thread

    def add_msg_to_thread(self, role, content):
        if self.thread:
            self.client.beta.threads.messages.create(
                thread_id = self.thread.id,
                role = role,
                content = content
            )

    # Metoda koja pokrece assistent-a

    def run_assistant(self, instructions):
        if self.thread and self.assistant:
            self.run = self.client.beta.threads.runs.create(
                assistant_id = self.assistant.id,
                thread_id = self.thread.id,
                instructions = instructions
            )
            print(f"Run ID :::: {self.run.id}")
    
    # Metoda koja uzima posljednje informacije iz niza poruka

    def process_message(self):
        if self.thread:
            messages = self.client.beta.threads.messages.list(thread_id = self.thread.id)
            summary = []

            last_message = messages.data[0]
            role = last_message.role
            response = last_message.content[0].text.value
            summary.append(response)

            self.summary = "\n".join(summary)
            print(f"Summary--->{role.capitalize()}: ==> {response}")

    # Helper funkcija koja uzima argumente neke custom funkcije i prosljedjuje je assistentu, provjerava i da li postoje te funkcije jer fora je da se ovdje proslijedi bilo kakva custom fukcija 

    def call_required_actions(self, required_actions):
        if not self.run:
            return
        tools_outputs = []

        for action in required_actions["tool_calls"]:
            func_name = action["function"]["name"]
            arguments = json.loads(action["function"]["arguments"])

            if func_name == "get_news":
                output = self.get_news(
                    topic=arguments.get("topic"), 
                    category=arguments.get("category"), 
                    phrase=arguments.get("phrase"), 
                    start_date=arguments.get("start_date"),
                    end_date=arguments.get("end_date")
                )

                print(f"Output funkcije :::: {output}")
                
                final_str = ""
                for item in output:
                    final_str += "".join(item["title"] + " - " + item["description"] + " - " + item["content"] + " - " + item["url"] +" \n ")
                
                tools_outputs.append({"tool_call_id": action["id"], "output": final_str})

            else:
                raise ValueError(f"Nepoznata funckija: {func_name}")
            
        print("Prosljedjujem output u Assistent-a...")
        self.client.beta.threads.runs.submit_tool_outputs(
            thread_id=self.thread.id,
            run_id=self.run.id,
            tool_outputs=tools_outputs
        )

    #za streamlit

    def get_summary(self):
        return self.summary

    # Pomocna metoda koja ceka i izvrsava run faze

    def wait_for_completed(self):
        if self.thread and self.run:
            while True:
                time.sleep(5)
                run_status = self.client.beta.threads.runs.retrieve(
                    thread_id = self.thread.id,
                    run_id = self.run.id
                )
                print(f"Run status :::: {run_status.model_dump_json(indent=4)}")

                if run_status.status == "completed":
                    self.process_message()
                    break
                elif run_status.status == "requires_action":
                    print("Pozivam funkcije...")
                    self.call_required_actions(
                        required_actions = run_status.required_action.submit_tool_outputs.model_dump()
                    )
    
    # Metoda koja zapisuje sve korake za debug svrhe

    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id,
            run_id=self.run.id
        )
        print(f"Run-steps :::: {run_steps}")
        return run_steps.data
    

    # ==== STREAMLIT FRONTEND

@staticmethod
def main():
    # news = get_news("Psychology")
    # print(news)
    import streamlit as st
    chat = ChatAssistant()

    # Streamlit frontend
    st.set_page_config(page_title="News Summarizer - Get details quick", page_icon=":📝:")
    st.title("News Summary")

    categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

    with st.form(key="user_input_form"):
        topic = st.text_input("Unesi tematiku:")

        # Opcioni filteri
        
        with st.expander("Filteri (opciono)"):
            categories = ["", "business", "entertainment", "general", "health", "science", "sports", "technology"]
            selected_category = st.selectbox("Select a news category", categories)

            date_filters = ["", "this_month", "this_year", "ever", "custom"]
            selected_date_filter = st.selectbox("Odaberi vremenski filter", date_filters)

            today = datetime.date.today()

            # Izracunaj pocetak trenutnog mjeseca

            start_of_this_month = today.replace(day=1)

            # Izracunaj pocetak trenutne godine

            start_of_this_year = today.replace(month=1, day=1)
        
            if selected_date_filter == "this_month":
                start_date = start_of_this_month
                end_date = today
            elif selected_date_filter == "this_year":
                start_date = start_of_this_year
                end_date = today
            elif selected_date_filter == "custom":
                st.write("Custom date range")
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
            else:
                start_date = None
                end_date = None


            exact_phrase = st.text_input("Sadrži frazu: (opciono)")

        submit_btn = st.form_submit_button(label="Pokreni Assistent-a")

        if submit_btn:
            chat.create_assistant(
                name="News Summarizer",
                instructions="Tvoj zadatak je da budes personalni asistent za korisnike koji zna da napravi kratak sazetak teksta iz spiska clankova",
                tools=[
                    {
                        "type":"function",
                        "function":{
                            "name": "get_news",
                            "description": "Uzima listu clankova na zadatu temu koje mu proslijedi NewsAPI",
                            "parameters": {
                                "type": "object",
                                "properties": {
                                    "topic": {
                                        "type": "string",
                                        "description": "Tema clanka novosti, npr. 'deep learning' "
                                    },

                                    "category": {
                                        "type": "string",
                                        "description": "Kategorija novosti, npr. 'zdravlje, zabava, sport"
                                    },

                                    "phrase": {
                                        "type": "string",
                                        "description": "Tačna fraza za pretragu u naslovu"
                                    },

                                    "start_date": {
                                        "type": "string",
                                        "description": "Pocetni datum od kojeg se prostire datumski filter"
                                    },

                                    "end_date": {
                                        "type": "string",
                                        "description": "Zavrsni datum do kojeg se prostire datumski filter"
                                    }
                                },
                                "required": ["topic"],
                            },
                        },
                    }
                ]
            )

            chat.create_thread()

            # Dodajem poruku i pokrecem asistenta
            chat.add_msg_to_thread(
                role="user",
                content=f"napravi sazetak novosti na ovu temu = {topic}, ovu kategoriju = {selected_category}, ovu frazu = {exact_phrase}, ovaj pocetni datum pretrage = {start_date}, ovaj krajnji datum pretrage = {end_date} i poslije svakog sazetka prikazi Citaj jos link koji vodi na adresu clanka"
            )
            chat.run_assistant(instructions="Napravi sazetak istinitih novosti koje su se desile i poslije svakog sazetka prikazi Citaj jos link koji vodi na adresu clanka")

            # Ceka da se zavrsi proces

            chat.wait_for_completed()

            summary = chat.get_summary()

            st.write(summary)

            st.text("Debug log:")
            st.code(chat.run_steps(), line_numbers=True)


if __name__ == "__main__":
    main()