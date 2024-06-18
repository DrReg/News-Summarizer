import openai
from dotenv import find_dotenv, load_dotenv
import requests
import json
import streamlit as st
from newsAssistant import ChatAssistant


def main():
    # news = get_news("Psychology")
    # print(news)

    chat = ChatAssistant()

    # Streamlit frontend

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
            chat.run_assistant(instructions="Napravi sazetak novosti i poslije svakog sazetka prikazi Citaj jos link koji vodi na adresu clanka")

            # Ceka da se zavrsi proces

            chat.wait_for_completed()

            summary = chat.get_summary()

            st.write(summary)

            st.text("Debug log:")
            st.code(chat.run_steps(), line_numbers=True)


if __name__ == "__main__":
    main()
