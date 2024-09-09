import datetime
import streamlit as st

st.set_page_config(
	layout= 'wide',
)

from models.functions import funJogosDia
from models.configs import CSS, varEngine
from models.models import tbCampeonatos
import pandas as pd

st.markdown( CSS, unsafe_allow_html=True )

if ['filtroPaís'] not in st.session_state:
    st.warning('Estou aqui')
    st.session_state['filtroPaís'] = None
if ['filtroCampeonato'] not in st.session_state:
    st.session_state['filtroCampeonato'] = None
if ['filtroData'] not in st.session_state:
    st.session_state['filtroData'] = None

st.subheader(f':green[:material/sports_soccer:] Jogos do Dia :green[:material/today:]', anchor=False)

dfCampeonatos = pd.read_sql_table( tbCampeonatos.name, varEngine )

st.info( st.session_state['filtroPaís'] )

if st.session_state['filtroPaís']:
    dfCampeonatos = dfCampeonatos[ dfCampeonatos['País'].isin( st.session_state['filtroPaís'] ) ]

st.dataframe( dfCampeonatos )

colFiltros, colfuncoes = st.columns( [ 9, 1 ] )

with colFiltros.popover(label=':material/filter: Filtros', use_container_width=True):

    colFiltroPais, colFiltroCampeonatos, colFiltroData = st.columns( [ 1, 1, 1 ] )

    with colFiltroPais:
        varPaises = st.multiselect(
                        label=':blue[:material/flag:] Pais',
                        options=dfCampeonatos['País'].sort_values().unique(),
                        placeholder='Selecione um ou mais Países'
                    )
        st.session_state['filtroPaís'] = varPaises
        st.info(st.session_state['filtroPaís'])

    with colFiltroCampeonatos:
        varCampeonatos =    st.multiselect(
                                label=':blue[:material/trophy:] Campeonato',
                                options=dfCampeonatos['Nome'].sort_values().unique(),
                                placeholder='Selecione um ou mais Campeonatos'
                            )
        st.session_state['filtroCampeonato'] = varCampeonatos

    with colFiltroData:
        varData = st.date_input(
                label= ':blue[:material/today:] Data',
                value= [datetime.date.today(), datetime.date.today()],
                format='DD/MM/YYYY',
                # label_visibility='hidden',
        )
        st.session_state['filtroData'] = varData



with colfuncoes.popover(label=':material/settings:', use_container_width=True):
    st.text('Funções')
    st.page_link('paginas/functions.py', label=':violet[:material/manufacturing:] Manutenção', use_container_width=True,)

st.divider()

funJogosDia( varData )