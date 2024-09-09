import streamlit as st

st.set_page_config(
	layout= 'centered',
)

from models.functions import funAtualizaCampeonatos, funAtualizaEquipes, funAtualizaEstatisticas, funAtualizaJogos, funAtualizaPaises
from models.configs import CSS
from datetime import datetime

st.markdown( CSS, unsafe_allow_html=True )

coluna01, coluna02 = st.columns( [ 14, 1], vertical_alignment='center' )

coluna01.header( ':blue[:material/system_update_alt:] Atualizar Informações :blue[:material/system_update_alt:]' )

with coluna02.popover(label=':material/settings:'):
    st.text('Funções')
    st.page_link('paginas/jogosdia.py', label=':violet[:material/today:] Jogos do dia', use_container_width=True)

coluna01, coluna02 = st.columns( 2, vertical_alignment='top' )

with coluna01:
    with st.form( 'Funções' ):
        varAtualizaPaises = st.checkbox( label=':rainbow[:material/tour:] Países' )
        varAtualizaCampeonatos = st.checkbox( label=':rainbow[:material/trophy:] Campeonatos' )
        varAtualizaEquipes = st.checkbox( label=':rainbow[:material/sports_soccer:] Equipes' )
        varAtualizaJogos = st.checkbox( label=':rainbow[:material/sports_soccer:] Jogos' )
        varAtualizaEstatisticas = st.checkbox( label=':rainbow[:material/analytics:] Estatísticas' )
        st.markdown( '<hr style="margin: 1rem 0rem"></hr>', unsafe_allow_html=True )
        varAtualizar = st.form_submit_button(':blue[:material/update:] Atualizar', use_container_width=True)


with coluna02:

    if varAtualizar:

        st.session_state['requestInicio'] = datetime.now()

        with st.status( 'TESTE', expanded=True ):
            if varAtualizaPaises:
                st.write( ':rainbow[:material/manufacturing:] Atualizando PAÍSES...' )
                varOK = funAtualizaPaises()
                if varOK:
                    st.write( ':green[:material/task_alt:] PAÍSES atualizados com sucesso!!' )
                else:
                    st.write( ':red[:material/error:] ERRO na atualização dos PAÍSES!!' )
            
            if varAtualizaCampeonatos:
                st.divider()
                st.write( ':rainbow[:material/manufacturing:] Atualizando CAMPEONATOS...' )
                varOK = funAtualizaCampeonatos()
                if varOK:
                    st.write( ':green[:material/task_alt:] CAMPEONATOS atualizados com sucesso!!' )
                else:
                    st.write( ':red[:material/error:] ERRO na atualização dos CAMPEONATOS!!' )
            
            if varAtualizaEquipes:
                st.divider()
                st.write( ':rainbow[:material/manufacturing:] Atualizando EQUIPES...' )
                varOK = funAtualizaEquipes()
                if varOK:
                    st.write( ':green[:material/task_alt:] EQUIPES atualizadas com sucesso!!' )
                else:
                    st.write( ':red[:material/error:] ERRO na atualização das EQUIPES!!' )
            
            if varAtualizaJogos:
                st.divider()
                st.write( ':rainbow[:material/manufacturing:] Atualizando JOGOS...' )
                varOK = funAtualizaJogos()
                if varOK:
                    st.write( ':green[:material/task_alt:] JOGOS atualizados com sucesso!!' )
                else:
                    st.write( ':red[:material/error:] ERRO na atualização dos JOGOS!!' )
            
            if varAtualizaEstatisticas:
                st.divider()
                st.write( ':rainbow[:material/manufacturing:] Atualizando ESTATÍSTICAS...' )
                varOK = funAtualizaEstatisticas()
                if varOK:
                    st.write( ':green[:material/task_alt:] ESTATÍSTICAS atualizadas com sucesso!!' )
                else:
                    st.write( ':red[:material/error:] ERRO na atualização das ESTATÍSTICAS!!' )
