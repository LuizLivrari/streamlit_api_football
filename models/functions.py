import requests
from models.configs import HEADERS, varEngine
from models.models import tbJogos, tbCampeonatos, tbEstatisticas, tbPaises, tbEquipes, tbStatus
from datetime import datetime
import json
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import Select
from sqlalchemy.orm import Session
import streamlit as st
import time

def funErros( parErros ):

	st.error( f'{parErros}' )

	if 'rateLimit' in parErros.keys():

		varTempoAguardar = 60 - ( datetime.now() - st.session_state['requestInicio'] ).seconds
		alerta = st.empty()
		for i in range( varTempoAguardar, 0, -1 ):
			alerta.info(f':red[:material/timer:] Aguardando limite de requisições. {i}s')
			time.sleep(1)
		alerta.info(':green[:material/resume:] Continuando atualização...')

		st.session_state['requestInicio'] = datetime.now()

		return True

	else:

		return False


def funRequest( parURL, parPArametros ):
	jsonRequest = requests.request("GET", parURL, params=parPArametros, headers=HEADERS )
	return jsonRequest.json()


def funAtualizaJogos():

	varURL = 'https://v3.football.api-sports.io/fixtures'

	with varEngine.begin() as engine:
		listaCampeonatos = engine.execute( Select( tbCampeonatos.c.ID, tbCampeonatos.c['Temporada Atual'] ) ).all()

	listaJogos = []

	for varCampeonato, varTemporada in listaCampeonatos:
	
		varParams = {
			'league': varCampeonato,
			'season': varTemporada
		}

		jsonJogos = funRequest( varURL, varParams )

		with open( 'JSONS/fixtures.json', 'w' ) as arquivoJSON:
			json.dump( jsonJogos, arquivoJSON, indent=4 )

		varErro = jsonJogos['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False
			jsonJogos = funRequest( varURL, varParams )
		
		for jogo in jsonJogos['response']:

			fixture = jogo['fixture']
			league = jogo['league']
			teams = jogo['teams']
			
			# Criar um dicionário para a jogo
			fixture_dict = {
				'ID': fixture['id'],
				'Data': datetime.fromtimestamp(fixture['timestamp']),#.strftime('%Y-%m-%d %H:%M:%S'),
				'ID Campeonato': league['id'],
				'Temporada': league['season'],
				'ID Equipe Casa': teams['home']['id'],
				'ID Equipe Fora': teams['away']['id'],
				'Status': fixture['status']['short'],
			}
			
			# Adicionar o dicionário à lista
			listaJogos.append(fixture_dict)

		if not listaJogos:
			return True

	with Session( varEngine ) as session:

		varInsert = insert( tbJogos )
		varInsertOrUpdate = varInsert\
			.on_conflict_do_update(
				constraint=tbJogos.primary_key,
				set_={
					'Data': varInsert.excluded.Data,
					'Status':varInsert.excluded.Status
				}
			)

		session.execute( varInsertOrUpdate, listaJogos )
		session.commit()

	return True


def funAtualizaEstatisticas():

	varURL = 'https://v3.football.api-sports.io/fixtures'

	varSQL = """
		select
			"ID"
		from
			partidas
		where
			"Status" = 'FT'
		and
			not exists( select * from partidas_estatisticas pe where pe."ID Jogo" = partidas."ID" )
		order by
			"Data"
	"""

	dfjogos = pd.read_sql_query( varSQL, varEngine )

	varQtdejogos = 20

	for chunkParitdas in range(0, len( dfjogos ), varQtdejogos):

		# print( 'Total:', len( dfjogos ), '  --  Chunk:', chunkParitdas, '  --  vStep:', varQtdejogos )

		varIDs = '-'.join( dfjogos[ chunkParitdas:chunkParitdas+varQtdejogos ][ 'ID' ].astype( str ) )

		# print( 'varIDs:', varIDs )

		varParams = {
			'ids': varIDs
		}

		jsonEstatisticas = funRequest( varURL, varParams )

		with open( 'JSONS/estatisticas.json', 'w' ) as arquivoJSON:
			json.dump( jsonEstatisticas, arquivoJSON, indent=4 )

		varErro = jsonEstatisticas['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False
			jsonEstatisticas = funRequest( varURL, varParams )

		# Lista para armazenar os resultados
		listaEstatisticas = []
		
		# Iterar sobre as jogos
		for estatistica in jsonEstatisticas['response']:

			if len( estatistica ) == 0:
				print( 'JSON ZERADO' )
				return True

			fixture = estatistica['fixture']
			teams = estatistica['teams']
			score = estatistica['score']
			estatisticas = estatistica['statistics']

			# Criar um dicionário para a jogo
			for estatistica in estatisticas:

				dicEstatistica = {item['type']: item['value'] for item in estatistica['statistics']}

				st.info( f'Partida { teams['home']['name'] } X { teams['away']['name'] } -- estatísticas: { len( dicEstatistica ) }.' )

				if len( dicEstatistica ) == 0:
					st.info( f'Partida { teams['home']['name'] } X { teams['away']['name'] } sem estatísticas.' )
					continue

				fixture_dict = {
					'ID Jogo': fixture['id'],
					'ID Equipe': estatistica['team']['id'],
					'Gols HT': score['halftime']['home'] if estatistica['team']['id'] == teams['home']['id'] else score['halftime']['away'],
					'Gols FT': score['fulltime']['home'] if estatistica['team']['id'] == teams['home']['id'] else score['fulltime']['away'],
					'Chutes no Gol': dicEstatistica['Shots on Goal'] if dicEstatistica['Shots on Goal'] else 0,
					'Chutes para Fora': dicEstatistica['Shots off Goal'] if dicEstatistica['Shots off Goal'] else 0,
					'Chutes Bloqueados': dicEstatistica['Blocked Shots'] if dicEstatistica['Blocked Shots'] else 0,
					'Chutes Dentro Area': dicEstatistica['Shots insidebox'] if dicEstatistica['Shots insidebox'] else 0,
					'Chutes Fora Area': dicEstatistica['Shots outsidebox'] if dicEstatistica['Shots outsidebox'] else 0,
					'Faltas': dicEstatistica['Fouls'] if dicEstatistica['Fouls'] else 0,
					'Escanteios': dicEstatistica['Corner Kicks'] if dicEstatistica['Corner Kicks'] else 0,
					'Impedimentos': dicEstatistica['Offsides'] if dicEstatistica['Offsides'] else 0,
					'Posse de Bola': dicEstatistica['Ball Possession'].replace( '%','' ) if dicEstatistica['Ball Possession'] else 0,
					'Cartoes Amarelos': dicEstatistica['Yellow Cards'] if dicEstatistica['Yellow Cards'] else 0,
					'Cartoes Vermelhos': dicEstatistica['Red Cards'] if dicEstatistica['Red Cards'] else 0,
					'Passes Total': dicEstatistica['Total passes'] if dicEstatistica['Total passes'] else 0,
					'Passes Certos': dicEstatistica['Passes accurate'] if dicEstatistica['Passes accurate'] else 0,
					'Passes %': dicEstatistica['Passes %'].replace( '%','' ) if dicEstatistica['Passes %'] else 0,
					'Gols Esperados': dicEstatistica['expected_goals'] if dicEstatistica['expected_goals'] else 0
				}
			
				# Adicionar o dicionário à lista
				listaEstatisticas.append(fixture_dict)

		if not listaEstatisticas:
			return True

		with Session( varEngine ) as session:

			session.execute( insert( tbEstatisticas ), listaEstatisticas )
			session.commit()

	return True


def funGetPredictions():

	varURL = 'https://v3.football.api-sports.io/predictions'

	varSQL = """
		select
			*
		from
			jogos
		where
			status = 'NS'
		and
			date::date = current_date
		order by
			date
	"""

	dfjogos = pd.read_sql_query( varSQL, varEngine )

	# print( dfjogos.to_dict(orient= 'records') )

	for jogo in dfjogos.to_dict(orient= 'records'):

		varParams = {
			'fixture': jogo['fixture_id']
		}

		jsonPrediction = funRequest( varURL, varParams )

		with open( 'JSONS/predictions.json', 'a' ) as arquivoJSON:
			json.dump( jsonPrediction, arquivoJSON, indent=4 )

		varErro = jsonPrediction['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False
			jsonPrediction = funRequest( varURL, varParams )

		print( 'jogo:', jogo )
		print( '		Predictions:', jsonPrediction )

	return True


def funJogosDia( varData ):

	# HTML e CSS para criar o divisor vertical
	st.markdown(
		"""
		<style>
		.vertical-divider {
			display: inline-block;
			border-left: 2px solid #ccc;
			height: 67px;
			margin: 0 10px;
		}
		.abc {
			display: flex;
  			justify-content: center;
  			align-items: center;
		}
		</style>
		""",
		unsafe_allow_html=True
	)

	dfPaises = pd.read_sql_table( tbPaises.name, varEngine )
	dfCampeonatos = pd.read_sql_table( tbCampeonatos.name, varEngine )
	dfjogos = pd.read_sql_table( tbJogos.name, varEngine )
	dfEquipes = pd.read_sql_table( tbEquipes.name, varEngine )
	dfStatus = pd.read_sql_table( tbStatus.name, varEngine )
	dfEstatisticas = pd.read_sql_table( tbEstatisticas.name, varEngine )

	dfEstatisticas.set_index(['ID Jogo', 'ID Equipe'], inplace=True)

	filtroDataInicial = ( dfjogos['Data'].dt.date >= varData[0] )
	filtroDataFinal = ( dfjogos['Data'].dt.date <= ( varData[1] if len( varData ) == 2 else varData[0] ) )

	dfjogosDia= dfjogos[ filtroDataInicial & filtroDataFinal ]

	dfFinal = \
		dfjogosDia\
			.merge(
				dfCampeonatos[ [ 'ID', 'Nome', 'Logo', 'País'] ]\
					.rename(
						columns={
							'ID': 'ID Campeonato',
							'Nome': 'Campeonato',
						}
					),
				on='ID Campeonato',
			)\
			.merge(
				dfPaises\
					.rename(
						columns= {
							'Nome': 'País'
						}
					),
				on='País',
		  	)\
			.merge(
				dfStatus\
					.rename(
						columns={
							'Sigla': 'Status'
						}
					),
				on='Status',
			)\
			.merge(
				dfEquipes[ [ 'ID', 'Nome', 'Sigla', 'Logo' ] ]\
					.rename(
						columns={
							'ID': 'ID Equipe Casa',
							'Nome': 'Equipe Casa',
							'Sigla': 'Sigla Casa',
							'Logo': 'Logo Casa',
						}
					),
				on='ID Equipe Casa',
				how='left'
			)\
			.merge(
				dfEquipes[ [ 'ID', 'Nome', 'Sigla', 'Logo' ] ]\
					.rename(
						columns={
							'ID': 'ID Equipe Fora',
							'Nome': 'Equipe Fora',
							'Sigla': 'Sigla Fora',
							'Logo': 'Logo Fora',
						}
					),
				on='ID Equipe Fora',
				how='left'
			)\
		
	# dfFinal.set_index( 'Data', drop=True, inplace=True )
	dfFinal['X'] = 'X'
	dfFinal = dfFinal[ [ 'ID', 'Data', 'País', 'Sigla', 'Bandeira', 'Campeonato', 'Logo', 'Status', 'Logo Casa', 'ID Equipe Casa', 'Equipe Casa', 'X', 'ID Equipe Fora', 'Equipe Fora', 'Logo Fora', ] ]
	dfFinal.sort_values( 'Data', ascending=True, inplace=True )

	for data in dfFinal['Data'].dt.date.unique():

		st.markdown( f'###### {data.strftime('%d/%m/%Y')}' )

		for jogo in dfFinal[dfFinal['Data'].dt.date == data ].to_dict(orient='records'):

			with st.form(key=str(jogo['ID'])):

				colData, colDivider01, colJogo, colDivider02, colDetalhes = st.columns([1, 0.5, 7, 0.5, 1], vertical_alignment='center')

				colData.markdown( f'<div class="abc"> { str( jogo['Data'].time() ) } </div>', unsafe_allow_html=True )
				colData.markdown( f'<div class="abc"> { jogo['Status'] } </div>', unsafe_allow_html=True )
					# Renderiza o divisor
				colDivider01.markdown('<div class="vertical-divider"></div>', unsafe_allow_html=True)


				with colJogo:
					colLogo, colEquipe, colPlacar = st.columns( [0.1, 0.85, 0.05], vertical_alignment='center' )

					with colLogo:
						st.image( jogo['Logo Casa'], width=30 )
						st.image( jogo['Logo Fora'], width=30 )

					with colEquipe:
						st.write( jogo['Equipe Casa'] )
						st.write( jogo['Equipe Fora'] )

					with colPlacar:
						st.write( str( dfEstatisticas.get( 'Gols FT', default='' ).get( ( jogo['ID'], jogo['ID Equipe Casa'] ), default='' ) ) )
						st.write( str( dfEstatisticas.get( 'Gols FT', default='' ).get( ( jogo['ID'], jogo['ID Equipe Fora'] ), default='' ) ) )

				colDivider02.markdown('<div class="vertical-divider"></div>', unsafe_allow_html=True)

				colDetalhes.form_submit_button(label=':material/expand_content:', help='Ver detalhes da partida.' )


def funAtualizaPaises():

	varURL = 'https://v3.football.api-sports.io/countries'

	jsonPaises = funRequest( varURL, None )

	with open( 'JSONS/paises.json', 'w' ) as arquivoJSON:
		json.dump( jsonPaises, arquivoJSON, indent=2 )

	varErro = jsonPaises['errors']

	if varErro:
		continua = funErros( varErro )
		if not continua:
			return False
		jsonPaises = funRequest( varURL, None )

	jsonPaises = jsonPaises['response']

	listaPaises = []

	for pais in jsonPaises:
		dictPaises = {
			'Nome': pais['name'],
			'Sigla': pais['code'],
			'Bandeira': pais['flag'],
		}

		listaPaises.append( dictPaises )


	with varEngine.begin() as engine:

		vStep = int( ( 65535 / len( listaPaises[0] ) ) ) 

		if vStep == 0:
			vStep = 1

		for chunk in range(0, len( listaPaises ), vStep):

			print( 'Chunk: ', chunk, '  --  vStep: ', vStep )

			varInsert = insert( tbPaises ).values( listaPaises[ chunk:chunk+vStep ] )
			varInsertOrUpdate = varInsert.on_conflict_do_update( constraint='paises_pkey', set_=dict( Sigla=varInsert.excluded.Sigla, Bandeira=varInsert.excluded.Bandeira  ) )

			engine.execute( varInsertOrUpdate )

	return True


def funAtualizaCampeonatos():

	varURL = 'https://v3.football.api-sports.io/leagues'

	tmpCampeonatos = [ 39, 40, 61, 62, 71, 72, 78, 79, 135, 136, 140, 141 ]

  	# Lista para armazenar os resultados
	listaCampeonatos = []
  
	for tmpCampeonato in tmpCampeonatos:

		varParams = {
			'id': tmpCampeonato,
		}

		jsonCampeonatos = funRequest( varURL, varParams )

		# with open( 'JSONS/campeonatos.json', 'a' ) as arquivoJSON:
		# 	json.dump( jsonCampeonatos, arquivoJSON, indent=4 )

		varErro = jsonCampeonatos['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False
			jsonCampeonatos = funRequest( varURL, varParams )

		for campeonato in jsonCampeonatos['response']:

			league = campeonato['league']
			country = campeonato['country']
			seasons = campeonato['seasons']
			
			campeonato_dict = {
				'ID': league['id'],
				'Nome': league['name'],
				'Logo': league['logo'],
				'País': country['name']
			}
			for season in seasons:
				if season['current']:
					campeonato_dict['Temporada Atual'] = season['year']
			
			# Adicionar o dicionário à lista
			listaCampeonatos.append(campeonato_dict)

	if not listaCampeonatos:
		return True

	with varEngine.begin() as engine:

		vStep = int( ( 65535 / len( listaCampeonatos[0] ) ) ) 

		if vStep == 0:
			vStep = 1

		for chunk in range(0, len( listaCampeonatos ), vStep):

			print( 'Chunk: ', chunk, '  --  vStep: ', vStep )

			varInsert = insert( tbCampeonatos ).values( listaCampeonatos[ chunk:chunk+vStep ] )
			varInsertOrUpdate = varInsert\
				.on_conflict_do_update(
					constraint=tbCampeonatos.primary_key,
					set_={
						'Nome': varInsert.excluded.Nome,
						'Logo':varInsert.excluded.Logo,
						'País':varInsert.excluded.País,
						'Temporada Atual':varInsert.excluded['Temporada Atual']
					}
				)

			engine.execute( varInsertOrUpdate )

	return True


def funAtualizaEquipes():

	varURL = 'https://v3.football.api-sports.io/teams'

	with varEngine.begin() as engine:
		listaCampeonatos = engine.execute( Select( tbCampeonatos.c.ID, tbCampeonatos.c['Temporada Atual'] ) ).all()

	# Lista para armazenar os resultados
	listaEquipes = []

	for lista in listaCampeonatos:

		campeonato, temporada = lista

		varParams = {
			'league': campeonato,
			'season': temporada
		}

		jsonEquipes = funRequest( varURL, varParams )

		with open( 'JSONS/equipes.json', 'a' ) as arquivoJSON:
			json.dump( jsonEquipes, arquivoJSON, indent=2 )

		varErro = jsonEquipes['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False
			jsonEquipes = funRequest( varURL, varParams )

		for varEquipe in jsonEquipes['response']:

			equipe = varEquipe['team']
			
			# Criar um dicionário para a jogo
			equipe_dict = {
				'ID': equipe['id'],
				'Nome': equipe['name'],
				'Sigla': equipe['code'],
				'País': equipe['country'],
				'Logo': equipe['logo'],
			}
			
			# Adicionar o dicionário à lista
			listaEquipes.append(equipe_dict)

	st.json( listaEquipes )

	if not listaEquipes:
		return True

	with varEngine.begin() as engine:

		vStep = int( ( 65535 / len( listaEquipes[0] ) ) ) 

		if vStep == 0:
			vStep = 1

		for chunk in range(0, len( listaEquipes ), vStep):

			print( 'Chunk: ', chunk, '  --  vStep: ', vStep )

			varInsert = insert( tbEquipes ).values( listaEquipes[ chunk:chunk+vStep ] )
			varInsertOrUpdate = varInsert\
				.on_conflict_do_update(
					constraint=tbEquipes.primary_key,
					set_={
						'Nome': varInsert.excluded.Nome,
						'Sigla': varInsert.excluded.Sigla,
						'País': varInsert.excluded.País,
						'Logo':varInsert.excluded.Logo
		   			}
				)

			engine.execute( varInsertOrUpdate )

	return True
