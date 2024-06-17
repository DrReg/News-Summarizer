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
