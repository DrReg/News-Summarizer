import openai
from dotenv import find_dotenv, load_dotenv
import os
import time 
import json

# openai.api_key = os.environ.get("OPENAI_API_KEY") je default
# Ovdje postavljam konfiguracije za instanciranje OpenAI assistent-a

load_dotenv()
news_api_key = os.environ.get("NEWS_API_KEY")
client = openai.OpenAI()
model = "gpt-3.5-turbo-16k"

class ChatAssistant:
    # thread_id = "thread_Tewm453iffuVWoqKvvaAz45d"
    # assistant_id = "asst_Q42qFA2YPAfmQUAwtRM1ah5o"

    thread_id = ""
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
                output = get_news(topic=arguments.get("topic"), 
                                  category=arguments.get("category"), 
                                  phrase=arguments.get("phrase"), 
                                  date_filter=arguments.get("date_filter"))
                print(f"Output funkcije :::: {output}")
                final_str = ""
                for item in output:
                    final_str += "".join(item["title"] + " - " + item["description"] + "\n")
                
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
    
    # Metoda koja izvrsava sve korake

    def run_steps(self):
        run_steps = self.client.beta.threads.runs.steps.list(
            thread_id=self.thread.id,
            run_id=self.run.id
        )
        print(f"Run-steps :::: {run_steps}")
        return run_steps.data