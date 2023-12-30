import numpy  as np
import pandas as pd
#import inflection
#import datetime as dt
#import math
import plotly.express as px
#import seaborn as sns
#from matplotlib import pyplot as plt
#from IPython.core.display import HTML
import folium
from haversine import haversine, Unit
from folium.plugins import MarkerCluster
from geopy.geocoders import Nominatim
import plotly.graph_objects as go
from PIL import Image
import streamlit as st
from streamlit_folium import st_folium


pd.set_option('display.max_columns', None)


df_raw = pd.read_csv('data/zomato.csv')

df = df_raw.copy()


##===========================================================================================
## Funções
##===========================================================================================

#Mapenando paises
COUNTRIES = {
    1: "India",
    14: "Australia",
    30: "Brazil",
    37: "Canada",
    94: "Indonesia",
    148: "New Zealand",
    162: "Philippines",
    166: "Qatar",
    184: "Singapore",
    189: "South Africa",
    191: "Sri Lanka",
    208: "Turkey",
    214: "United Arab Emirates",
    215: "England",
    216: "United States of America",
}

def country_name(country_id):
    return COUNTRIES.get(country_id, "Unknown")

# Mapeando preços
def categorize_price(price_range):
    if price_range == 1:
        return "cheap"
    elif price_range == 2:
        return "normal"
    elif price_range == 3:
        return "expensive"
    else:
        return "gourmet"
    
#Mapeando Cores
COLORS = {
"3F7E00": "darkgreen",
"5BA829": "green",
"9ACD32": "lightgreen",
"CDD614": "orange",
"FFBA00": "red",
"CBCBC8": "darkred",
"FF7800": "darkred",
}

def colors_name(rating_color):
    return COLORS.get(rating_color, "Unknown")


#Tabela de freq absoluta e relativa

def tabela_de_frequencia(df, coluna_texto):
    tabela_frequencia = df[coluna_texto].value_counts().reset_index()
    tabela_frequencia.columns = [coluna_texto, 'count']
    tabela_frequencia = tabela_frequencia.sort_values(by='count', ascending=False)
    
    # Calcular a frequência relativa em porcentagem
    total_registros = len(df)
    tabela_frequencia['percent'] = (tabela_frequencia['count'] / total_registros) * 100
    
    return tabela_frequencia

def formatar_numero_milhoes(numero):
    milhoes = numero / 1000000
    return f'{milhoes:.1f}MM'

def clean_df(df):
    #Ajuste nomes das variáveis
    df = df.rename(columns=lambda x: x.strip().lower())  # Remove espaços e torna minúsculas
    df = df.rename(columns=lambda x: x.replace(' ', '_'))  # Substitui espaços por underscores
    df = df.rename(columns=lambda x: x.strip('!'))  # Remove caracteres especiais

    #Removendo os NAs
    df = df.dropna(subset=['cuisines'])

    # Aplicar a função country_name à coluna 'country_code' para criar a coluna 'countries'
    df['countries'] = df['country_code'].apply(country_name)

    # Aplicar a função à coluna 'price_range' para criar a nova coluna 'price_category'
    df['price_category'] = df['price_range'].apply(categorize_price)

    # Aplicar a função color_name à coluna 'rating_color' para criar a coluna 'color_name'
    df['color_name'] = df['rating_color'].apply(colors_name)

    # Usar somente um tipo de cozinha inicialmente no projeto
    df["cuisines"] = df.loc[:, "cuisines"].apply(lambda x: x.split(",")[0])

    # Remover colunas inutilizadas
    df = df.drop('country_code', axis=1)
    df = df.drop('rating_color', axis=1)

    # Remover coluna com apenas um valor, ou seja sem valor para análise
        # Verificando as colunas com apenas um valor distinto
        #valores_distintos = df.nunique()
        #colunas_com_apenas_um_valor = valores_distintos[valores_distintos == 1].index

        #print("Colunas com apenas um valor em todas as linhas:")
        #print(colunas_com_apenas_um_valor)
    df = df.drop('switch_to_order_menu', axis=1)

    # Remover Duplicadas
    df = df.drop_duplicates()
    return df




def map_world(df):
    # Selecione as colunas relevantes
    columns = ['countries', 'city', 'cuisines', 'aggregate_rating', 'latitude', 'longitude', 'restaurant_id', 'restaurant_name', 'average_cost_for_two', 'currency']

    columns_grouped = ['countries', 'city', 'aggregate_rating', 'cuisines', 'latitude', 'longitude', 'restaurant_id', 'restaurant_name', 'average_cost_for_two', 'currency']

    data_plot = df1.loc[:, columns].groupby(columns_grouped).median().reset_index()

    # Crie o mapa
    map_ = folium.Map(zoom_start=10)

    # Inicialize o cluster de países mesmo que esteja comentado
    country_cluster = None

    # Adicione os marcadores de países ao cluster
    for country, country_data in df1.groupby('countries'):
        country_latitude, country_longitude = country_data.iloc[0]['latitude'], country_data.iloc[0]['longitude']
        num_restaurants = len(country_data)

        if country_cluster is None:
            country_cluster = MarkerCluster().add_to(map_)

        folium.CircleMarker(
            location=[country_latitude, country_longitude],
            radius=8,
            fill=True,
            fill_opacity=0.7,
            color='green',
            tooltip=f"{country} - {num_restaurants} restaurants"
        ).add_to(country_cluster)

    # Crie um cluster de marcadores para os restaurantes
    marker_cluster = MarkerCluster().add_to(map_)

    # Adicione os marcadores de restaurantes ao cluster
    for index, location_info in data_plot.iterrows():
        folium.Marker(
            location=[location_info['latitude'], location_info['longitude']],
            popup=folium.Popup(
                f"{location_info['restaurant_name']}\n"
                f"Rating: {location_info['aggregate_rating']}\n"
                f"Average Cost for Two: {location_info['average_cost_for_two']} {location_info['currency']}\n"
                f"Cuisines: {location_info['cuisines']}",
                parse_html=True
            ),
            icon=None  # Define o ícone como None para não exibir pop-up
        ).add_to(marker_cluster)

    # Adicione um controle de camadas para que o usuário possa alternar entre países e restaurantes
    folium.LayerControl(collapsed=False).add_to(map_)

    st_folium( map_, width=620)
    
    
    
def maior_qnt_restaurant(df1):
    # Seu código para processar os dados
    apo = df1 \
        .filter(['countries', 'restaurant_id']) \
        .groupby('countries') \
        .agg({'restaurant_id': 'nunique'}) \
        .reset_index() \
        .sort_values('restaurant_id', ascending=False) \
        .head(7)

    # Criar o gráfico de barras com o Plotly Express
    fig = px.bar(apo, x='countries', y='restaurant_id', 
                 title='Países com maior quantidade de restaurantes',
                 labels={'restaurant_id': 'Quantidade'},
                 color='countries',  # Você pode ajustar isso para a paleta desejada
                 color_discrete_sequence=px.colors.sequential.Viridis)  # Paleta para daltonianos

    # Ajustar layout
    fig.update_layout(xaxis_title=None, showlegend=False)  # Não mostrar título no eixo x e remover a legenda

    # Exibir o gráfico
    return fig



def paises_mais_restaurantes_bem_aval(df1):
    # Filtrar os dados
    filtro_avaliacoes = df1.loc[df1['aggregate_rating'] >= 4.75, ['countries', 'aggregate_rating']]

    # Contar o número de avaliações por país
    contagem_avaliacoes = filtro_avaliacoes['countries'].value_counts().reset_index()
    contagem_avaliacoes.columns = ['countries', 'count']

    # Selecionar os 5 países com a maior contagem
    top_paises = contagem_avaliacoes.head(3)

    # Criar o gráfico de pizza com o Plotly Express
    fig = px.pie(top_paises, values='count', names='countries',
                 title='Países maior qnt de restaurantes bem avaliados',
                 labels={'count': 'Quantidade'},
                 color='countries',  # Você pode ajustar isso para a paleta desejada
                 color_discrete_sequence=px.colors.sequential.Viridis  # Paleta para daltonianos
                 )

    # Ajustar layout
    fig.update_layout(showlegend=False)  # Não mostrar a legenda

    # Exibir o gráfico
    return fig





##===========================================================================================
## Limpeza dos dados
##===========================================================================================

df1 = clean_df(df)


##===========================================================================================
## Barra Lateral 
##===========================================================================================

#image_path = 'C:/Users/vini_/Documents/World_Cuisines/logo.png'
image = Image.open('logo.png')
st.sidebar.image(image, width =280)

st.sidebar.markdown('# Gastronote Explorer')
st.sidebar.markdown('## Descubra Sabores, Compartilhe Experiências! 🌍✨')
st.sidebar.markdown("""---""")

paises = ['Philippines', 'Brazil', 'Australia', 'United States of America',
       'Canada', 'Singapore', 'United Arab Emirates', 'India',
       'Indonesia', 'New Zealand', 'England', 'Qatar', 'South Africa',
       'Sri Lanka', 'Turkey']

paises_filtro = st.sidebar.multiselect('Seleção Países', paises , default = ['India','United States of America', 'South Africa', 'England' , 'Australia', 'Brazil' ])
st.sidebar.markdown("""---""")


# filtros de paises

linhas_selecionadas = df1['countries'].isin(  paises_filtro )
df1 = df1.loc[linhas_selecionadas,:]



##===========================================================================================
## Layout no Streamlit
##===========================================================================================



st.markdown('# Gastronote Explorer')

# Define as larguras desejadas para cada coluna


with st.container():
        st.title('Countries')
        col1,col2,col3 = st.columns(3)
        with col1:
            país_com_mais_restaurante = df1['countries'].value_counts().idxmax()
            col1.metric('Mais Restaurantes', país_com_mais_restaurante)
            
        with col2:
            país_restaurantes_mais_caros = df1.query('price_range == 4').filter(['countries']).value_counts().idxmax()[0]
            col2.metric('Restaurantes mais caros', país_restaurantes_mais_caros)     
            
            
            
            df_expanded = df1 \
                .assign(cuisines=df1['cuisines'] \
                        .str.split(', ')) \
                .explode('cuisines')

            # Calcular o número de cozinhas distintas por país
            variedade_por_pais = df_expanded.groupby('countries')['cuisines'].nunique()
            variedade_por_pais.idxmax()
        
        
        with col3:
            paíse_com_maior_variedade = variedade_por_pais.idxmax()
            col3.metric('Mais variedade culin', paíse_com_maior_variedade)  
            
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        fig = maior_qnt_restaurant(df1)
        st.plotly_chart(fig, use_container_width = True)
      
    with col2:
        fig = paises_mais_restaurantes_bem_aval(df1)
        st.plotly_chart(fig, use_container_width = True)
        
        
with st.container():
    st.markdown("""---""") 
 
    st.markdown('#### Visão_Geral')
                # Calcula a média das avaliações e o preço médio para cada país no DataFrame existente
    df_agrupado = df1.groupby('countries').agg({
            'aggregate_rating': 'mean',
            'average_cost_for_two': 'mean'
        }).reset_index()

        # Realiza o join com o DataFrame original para obter a coluna 'currency'
    df_final = pd.merge(df_agrupado, df1[['countries', 'currency']], on='countries', how='left').drop_duplicates().sort_values('aggregate_rating', ascending = False)

        # Exibe o DataFrame final
    df_final.columns = ['Países', 'Média_Avaliações', 'Média_Preço_Casal', 'Moeda']
    df_final = df_final.reset_index(drop=True)
    st.dataframe(df_final)