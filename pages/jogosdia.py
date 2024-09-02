import streamlit as st

st.set_page_config(
	layout= 'wide',
)

from models.functions import funJogosDia
from models.configs import CSS

st.markdown( CSS, unsafe_allow_html=True )

coluna01, coluna02 = st.columns( [ 14, 1], vertical_alignment='center' )

coluna01.header(':green[:material/sports_soccer:] Jogos do Dia :green[:material/today:]')

with coluna02.popover(label=':material/settings:'):
    st.text('Funções')
    st.page_link('pages/functions.py', label=':violet[:material/manufacturing:] Manutenção', use_container_width=True)

st.divider()

st.dataframe(
   funJogosDia(),
   column_config={
        'Data': st.column_config.DatetimeColumn(format="DD/MM/YYYY - HH:mm ",),
        'Bandeira': st.column_config.ImageColumn(),
        'Logo': st.column_config.ImageColumn(),
        'Logo Casa': st.column_config.ImageColumn(),
        'Logo Fora': st.column_config.ImageColumn(),
        'Status': st.column_config.Column( help='TESTE' )
	},
	use_container_width=True,
    hide_index=True
)

# st.dataframe(
# 	funJogosDia(),
# 	column_config={
# 		'date': st.column_config.Column('Data'),
# 		'league_id': st.column_config.Column('ID Campeonato'),
# 		'league_season': st.column_config.Column('Temporada'),
# 		'date': st.column_config.Column('Data'),
# 		'date': st.column_config.Column('Data'),
# 		'date': st.column_config.Column('Data'),		
# 	}
# )