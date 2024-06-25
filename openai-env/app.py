import streamlit as st

# Main entry point for the Streamlit app
query_params = st.query_params.get(key="page")

if "page" in query_params:
    if query_params["page"][0] == "news_summarizer":
        import newsSummarizer
        newsSummarizer.main()
    elif query_params["page"][0] == "study_buddy":
        import studyAssistant
        studyAssistant.main()
    else:
        import mainPage
        mainPage.main()
else:
    import mainPage
    mainPage.main()