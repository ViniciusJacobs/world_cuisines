import streamlit as st
from PIL import Image



st.set_page_config(page_title="Home",
                  page_icon="", layout = 'wide')


#image_path = 'C:/Users/vini_/Documents/World_Cuisines/logo.png'
image = Image.open('logo.png')
st.sidebar.image(image, width =280)

st.sidebar.markdown('# Gastronote Explorer')
st.sidebar.markdown('## Descubra Sabores, Compartilhe Experiências! 🌍✨')
st.sidebar.markdown("""---""")

st.write('# Gastronote Explorer Dash ')

st.markdown(
    """
É com entusiasmo que apresentamos o Gastronote Explorer Dash, uma ferramenta sob medida para impulsionar nossa visão estratégica no dinâmico cenário do mercado global de restaurantes. Nos comprometemos a fornecer insights e análises fundamentadas para orientar escolhas inteligentes, culminando no sucesso contínuo de nossa empresa.
   """    
)

st.markdown(
    """
    ### Maximize seu Poder de Decisão:
    - Visão **Macro**: 
        - Ganhe uma perspectiva global com análises de geolocalização, proporcionando insights valiosos para aprimorar nossa presença em mercados-chave.
    - Visão **País**:
        - Quantidade de restaurantes por países;
        - Países com maior quantidade de avaliações **Excelente** (acima 4,75);
        - Média de avaliações e preço médio para melhor compreensão do mercado local.

    - Visão **Culinária**:
        - Os melhores restaurantes por tipo de culinária;
        - As top 10 culinárias com base em avaliações positivas;
        - Mitigue riscos ou avalie opoertunidades ao entender as piores culinárias conforme feedback dos clientes. 


    ### Dúvidas/Sugestões:
          suporte@gastronote.com
   """    
)
