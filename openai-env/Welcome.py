import streamlit as st
from PIL import Image



def main():
    # Glavni setup
    st.set_page_config(page_title="AI Researcher - Online Platform", page_icon=":🧑‍🔬:")

    st.title("Kompjuter uči uz tebe!")
    st.sidebar.success("Izaberite bilo koju stranicu iznad.")

    st.write("Dobro došli na platformu AI Istraživača!")
    st.write(""" Na ovoj stranici možeš da koristiš **vještačku inteligenciju** da naučiš nove teme i
             usavršiš postojeće znanje sve uz pomoć *naših asistenata* - specijalizovanih vještačkih inteligencija osmišljeni kao pomoć studentima,
             profesorima i svim radoznalim osobama.""")
    
    image = Image.open("studybuddy.png")
    st.image(image, caption="Vaš lični digitalni profesor.", use_column_width=True)

    st.header("News Summarizer")

    st.write("Ovaj asistent ima ulogu pružanja sažetaka na temu koju korisnik izabere.")
    st.write("Trenutno podržava funckije:")
    st.write("""
             - *Sažete pretrage članaka novosti*
             - *Filtriranje na osnovu datuma, ključne riječi i kategorije*
             - *Vraćanje URL adresa ako korisnik želi da pročita izvorni članak*
             
             """)
    
    st.header("Study Buddy")

    st.write("Pametni asistent koji na osnovu datoteke koje korisnik zakači ima mogućnost konverzacije.")
    st.write("Trenutno podržava funckije:")
    st.write("""
             - *Odgovora na pitanja*
             - *Pisanje sažetaka*
             - *Izdvajanje citata*
             - *Osmišljavanje pitanja*
             
             """)
    
    st.warning("Možete doprinijeti projektu na našem GitHub nalogu: https://github.com/DrReg/News-Summarizer")


 


if __name__ == "__main__":
    main()
