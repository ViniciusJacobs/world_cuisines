import numpy  as np
import pandas as pd
import plotly.express as px
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
    
# Dicionário de mapeamento para traduzir os valores para inglês
    mapping_dict = {
    'Excellent': 'Excellent',
    'Very Good': 'Very Good',
    'Good': 'Good',
    'Excelente': 'Very Good',  # Exemplo de mapeamento adicional
    'Muito bom': 'Very Good',
    'Average': 'Average',
    'Not rated': 'Not rated',
    'Poor': 'Poor',
    'Vynikajúce': 'Excellent',  # Exemplo de mapeamento adicional
    'Muito Bom': 'Very Good',
    'Bardzo dobrze': 'Very Good',
    'Muy Bueno': 'Very Good',
    'Bueno': 'Good',
    'Baik': 'Good',
    'Biasa': 'Average',
    'Skvělá volba': 'Excellent',  # Exemplo de mapeamento adicional
    'Velmi dobré': 'Very Good',
    'Harika': 'Excellent',
    'Çok iyi': 'Very Good',
    'Eccellente': 'Excellent',
    'Veľmi dobré': 'Very Good',
    'Buono': 'Good',
    'Bom': 'Good',
    'Skvělé': 'Excellent',
    'Wybitnie': 'Excellent',
    'Sangat Baik': 'Very Good',
    'Terbaik': 'Excellent',
    'İyi': 'Good'
        }

    # Mapeando os valores usando o dicionário e criando a nova coluna
    df['rating_text_uni'] = df['rating_text'].map(mapping_dict)

    # Verificando se há valores NaN e atribuindo 'Outros'
    if df['rating_text_uni'].isnull().any():
        df['rating_text_uni'].fillna('Not Rated', inplace=True)
    
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
    

def culinarias_melhor_avaliadas(df1):
    # Seu código para processar os dados
    apo = df1.loc[df1['rating_text_uni'] == 'Excellent', ['cuisines', 'restaurant_id']] \
            .groupby(['cuisines']) \
            .agg({'restaurant_id': 'count'})\
            .reset_index()\
            .sort_values('restaurant_id', ascending = False)\
            .head(6)


    # Criar o gráfico de barras com o Plotly Express
    fig = px.bar(apo, x='cuisines', y='restaurant_id', 
                 title='Culinárias com melhores avaliaçoes',
                 labels={'restaurant_id': 'Quantidade'},
                 color='cuisines',  # Você pode ajustar isso para a paleta desejada
                 color_discrete_sequence=px.colors.sequential.Viridis)  # Paleta para daltonianos
    
    fig.update_layout(showlegend=False) 
    return fig



def paises_mais_restaurantes_bem_aval(df1):
    # Filtrar os dados
    filtro_avaliacoes = df1.loc[df1['price_range'] == 4, ['cuisine', 'aggregate_rating']]

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


def cuisines_mais_caras(df1):
    # Filtrar os dados
    filtro_cuisines_caras = df1.loc[df1['price_range'] == 4, ['cuisines']]

    # Contar o número de ocorrências de cada culinária
    contagem_cuisines = filtro_cuisines_caras['cuisines'].value_counts().reset_index()
    contagem_cuisines.columns = ['cuisines', 'count']

    # Selecionar as 5 culinárias com a maior contagem
    top_cuisines = contagem_cuisines.head(5)

    # Criar o gráfico de pizza com o Plotly Express
    fig = px.pie(top_cuisines, values='count', names='cuisines',
                 title='Culinárias com preço mais elevado',
                 labels={'count': 'Quantidade'},
                 color='cuisines',  # Você pode ajustar isso para a paleta desejada
                 color_discrete_sequence=px.colors.sequential.Viridis  # Paleta para daltonianos
                 )

    # Ajustar layout
    fig.update_layout(showlegend=False)  # Não mostrar a legenda

    # Exibir o gráfico
    return fig



def culinarias_avaliacoes_ruins_ou_medias(df1):
    # Filtrar os dados para avaliações "Ruins" ou "Média"
    filtro_avaliacoes_ruins_medias = df1.loc[(df1['rating_text_uni'] == 'Average') | (df1['rating_text_uni'] == 'Poor'),
                                             ['cuisines', 'restaurant_id']] \
                                        .groupby(['cuisines']) \
                                        .agg({'restaurant_id': 'count'}) \
                                        .reset_index() \
                                        .sort_values('restaurant_id', ascending=False) \
                                        .head(6)

    # Criar o gráfico de barras com o Plotly Express
    fig = px.bar(filtro_avaliacoes_ruins_medias, x='cuisines', y='restaurant_id',
                 title='Culinárias com avaliações Ruins ou Médias',
                 labels={'restaurant_id': 'Quantidade'},
                 color='cuisines',  # Você pode ajustar isso para a paleta desejada
                 color_discrete_sequence=px.colors.sequential.Viridis)  # Paleta para daltonianos

    fig.update_layout(showlegend=False, xaxis_title='')
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
        st.title('Cuisines')
        col1,col2 = st.columns(2)
        with col1:
            apo = df1.loc[df1['rating_text_uni'] == 'Excellent', ['cuisines', 'restaurant_id']] \
                .groupby(['cuisines']) \
                .agg({'restaurant_id': 'count'})\
                .reset_index()\
                .sort_values('restaurant_id', ascending = False)

               
            col1.metric('Culinária melhor avaliada',  apo.iloc[0,0])
            
        with col2:
            culinária_mais_cara = df1.loc[df1['price_range'] == 4,['cuisines', 'price_range']].groupby('cuisines').agg({'price_range':'count'}).reset_index().sort_values('price_range',ascending = False)
            col2.metric('Culinária com preços mais altos', culinária_mais_cara.iloc[0,0])     
            
            
            
            df_expanded = df1 \
                .assign(cuisines=df1['cuisines'] \
                        .str.split(', ')) \
                .explode('cuisines')

            # Calcular o número de cozinhas distintas por país
            variedade_por_pais = df_expanded.groupby('countries')['cuisines'].nunique()
            variedade_por_pais.idxmax()
        
        
            
with st.container():
    col1, col2 = st.columns(2)
    with col1:
        fig = culinarias_melhor_avaliadas(df1)
        st.plotly_chart(fig, use_container_width = True)
      
    with col2:
        fig = cuisines_mais_caras(df1)
        st.plotly_chart(fig, use_container_width = True)
        
        
with st.container():
    col1, col2 = st.columns(2)
    
    with col1:
       
    # Calcula a média das avaliações e o preço médio para cada país no DataFrame existente
        df_agrupado = df1.groupby('cuisines').agg({
            'aggregate_rating': 'mean',
            'average_cost_for_two': 'mean'
        }).reset_index()

        # Realiza o join com o DataFrame original para obter a coluna 'currency'
        df_final = pd.merge(df_agrupado, df1[['cuisines', 'currency']], on='cuisines', how='left').drop_duplicates().sort_values('aggregate_rating', ascending = False)

        # Exibe o DataFrame final
        df_final.columns = ['Culinária', 'Média_Avaliações', 'Média_Preço_Casal', 'Moeda']
        df_final = df_final.reset_index(drop=True)
        st.dataframe(df_final)
    
    with col2:
        fig = culinarias_avaliacoes_ruins_ou_medias(df1)
        st.plotly_chart(fig, use_container_width = True) 