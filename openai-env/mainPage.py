import streamlit as st


def main():
    # Glavni setup
    st.title("AI Learning Assistant Platform")
    st.set_page_config(page_title="Research Assistants - Learn fast with us!", page_icon=":robot:")

    # Dvije kolone dugmadi
    col1, col2 = st.columns(2)

    with col1:
        if st.button("News Summarizer"):
            st.session_state.page = "news_summarizer"
            st.rerun()

    with col2:
        if st.button("Study Buddy"):
            st.session_state.page = "study_buddy"
            st.rerun()

    # Logika za redirekciju na osnovu parametra iz URL-a
    if "page" in st.session_state:
        if st.session_state.page == "news_summarizer":
            st.write("Redirecting to News Summarizer...")
            st.query_params(page="news_summarizer")
        elif st.session_state.page == "study_buddy":
            st.write("Redirecting to Study Buddy...")
            st.query_params(page="study_buddy")

    # Podesavanje parametara na osnovu kliknutih dugmadi
    query_params = st.query_params.get_all(key="page")
    st.write(query_params)
    if "page" in query_params:
        if query_params["page"][0] == "news_summarizer":
            st.query_params()
            st.session_state.page = "news_summarizer"
            st.rerun()
        elif query_params["page"][0] == "study_buddy":
            st.query_params()
            st.session_state.page = "study_buddy"
            st.rerun()


if __name__ == "__main__":
    main()
