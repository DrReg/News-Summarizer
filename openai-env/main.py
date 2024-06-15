import openai
from dotenv import find_dotenv, load_dotenv
import requests
import json
import streamlit as st
from newsAssistant import ChatAssistant


# Pravim metodu koja poziva NewsAPI i vraca sta mu API kaze, ima i custom URL kojem mu prosljedjujem temu i API kljuc

# Ova metoda ima zadatak da salje zahtjev NewsAPI-ju i da samo vrati informacije iz clanaka u obliku teksta

def get_news(topic=None, category=None, phrase=None, date_filter=None):
    base_url = "https://newsapi.org/v2/top-headlines"
    params = {
        "apiKey": news_api_key,
        "country": "us",
    }
    if topic:
        params["q"] = topic
    if category:
        params["category"] = category
    if phrase:
        params["qInTitle"] = phrase
    if date_filter:
        try:
            if date_filter == "this_month":
                params["from"] = (datetime.now() - timedelta(days=datetime.now().day)).strftime("%Y-%m-%d")
                params["to"] = datetime.now().strftime("%Y-%m-%d")

            elif date_filter == "this_year":
                params["from"] = datetime(datetime.now().year, 1, 1).strftime("%Y-%m-%d")
                params["to"] = datetime.now().strftime("%Y-%m-%d")

            elif date_filter == "ever":
                pass  # Nema potrebe da ovdje posebna logika bude napravljena

            elif date_filter == "custom":
                start_date = st.date_input("Start Date")
                end_date = st.date_input("End Date")
                params["from"] = start_date.strftime("%Y-%m-%d")
                params["to"] = end_date.strftime("%Y-%m-%d")
                
        except Exception as e:
            st.error(f"Error pri procesu filtera: {str(e)}")
            return []
    
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()  # Postavi status error za los odgovor
        articles = response.json().get("articles", [])

    except requests.exceptions.RequestException as e:
        st.error(f"Error pri vracanju novih clankova: {str(e)}")
        return []
    
    news_list = []

    for article in articles:
        news_item = {
            "title": article["title"],
            "description": article["description"],
            "url": article["url"]
        }
        news_list.append(news_item)
    
    return news_list

def main():
    # news = get_news("Psychology")
    # print(news)

    chat = ChatAssistant()

    # Streamlit frontend

    st.title("News Summary")

    categories = ["business", "entertainment", "general", "health", "science", "sports", "technology"]

    with st.form(key="user_input_form"):
        instructions = st.text_input("Unesi tematiku:")

        # Opcioni filteri
        
        with st.expander("Filteri (opciono)"):
            categories = ["", "business", "entertainment", "general", "health", "science", "sports", "technology"]
            selected_category = st.selectbox("Select a news category", categories)

            date_filters = ["", "this_month", "this_year", "ever", "custom"]
            selected_date_filter = st.selectbox("Odaberi vremenski filter", date_filters)

            if selected_date_filter == "custom":
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
                                        "description": "Kategorija novosti, npr. 'business' "
                                    },

                                    "phrase": {
                                        "type": "string",
                                        "description": "Tačna fraza za pretragu u naslovu"
                                    },

                                    "date_filter": {
                                        "type": "string",
                                        "description": "Filter za datum: this_month, this_year, ever, custom"
                                    }
                                    
                                },
                                "required": ["topic"],
                            },
                        },
                    }
                ]
            )

            if selected_category:
                tools[0]["function"]["parameters"]["properties"]["category"] = selected_category
            if exact_phrase:
                tools[0]["function"]["parameters"]["properties"]["phrase"] = exact_phrase
            if selected_date_filter:
                tools[0]["function"]["parameters"]["properties"]["date_filter"] = selected_date_filter

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
