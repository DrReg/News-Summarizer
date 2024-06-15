import openai
from dotenv import find_dotenv, load_dotenv
import requests
import json
import streamlit as st
from newsAssistant import ChatAssistant


# Pravim metodu koja poziva NewsAPI i vraca sta mu API kaze, ima i custom URL kojem mu prosljedjujem temu i API kljuc

# Ova metoda ima zadatak da salje zahtjev NewsAPI-ju i da samo vrati informacije iz clanaka u obliku teksta
def get_news(topic):
    url = (
        f"https://newsapi.org/v2/everything?q={topic}&apiKey={news_api_key}&pageSize=5"
    )

    try:
        response = requests.get(url)
        if response.status_code == 200:
            news = json.dumps(response.json(), indent=4)
            news_json = json.loads(news)

            data = news_json

            # Prolazim kroz JSON fajl odgovora i kupim podatke u varijable da bi ih kasnije obradio
            
            status = data["status"]
            total_results = data["totalResults"]
            articles = data["articles"]

            final_news = []

            # articles je lista pa moram proci kroz sve elemente

            for article in articles:
                source_name = article["source"]["name"]
                author = article["author"]
                title = article["title"]
                description = article["description"]
                url = article["url"]
                content = article["content"]

                # Sve ove varijable smijestam u jednu jer je lakse i smanjujem redudantne argumente kasnije

                title_description = f"""
                    Title: {title},
                    Author: {author}
                    Source: {source_name}
                    Description: {description}
                    URL: {url}
                    Content: {content}
                """

                final_news.append(title_description)

            return final_news
        else: 
            return []
        
    except requests.exceptions.RequestException as e:
        print("Error pri NewsAPI key zahtjevu :( ", e)

def main():
    # news = get_news("Psychology")
    # print(news)

    chat = ChatAssistant()

    # Streamlit frontend

    st.title("News Summary")

    with st.form(key="user_input_form"):
        instructions = st.text_input("Unesi tematiku:")
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
                content=f"napravi sazetak novosti na ovu temu: {instructions}"
            )
            chat.run_assistant(instructions="Napravi sazetak novosti")

            # Ceka da se zavrsi proces

            chat.wait_for_completed()

            summary = chat.get_summary()

            st.write(summary)

            st.text("Debug log:")
            st.code(chat.run_steps(), line_numbers=True)


if __name__ == "__main__":
    main()
