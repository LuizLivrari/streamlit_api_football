import requests
from models.configs import apiKey, varEngine#, OpenAIClient, MODEL
from models.models import tbJogos, tbCampeonatos, tbJogosEstatisticas, tbPaises, tbEquipes, tbStatus
from datetime import datetime
import json
import pandas as pd
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy import Select
import streamlit as st
import time

# def funOpenAIjogo( varJSON ):

# 	file = OpenAIClient.files.create(
# 		file=open("fixtures.json", "rb"),
# 		purpose='assistants'
# 	)

# 	Assistente = OpenAIClient.beta.assistants.retrieve(
# 		assistant_id= 'asst_EqsyIophT1BoP4wAoE4CPBqY'
# 	)

# 	thread = OpenAIClient.beta.threads.create(
# 		messages=[
# 			{
# 				"role": "user",
# 				"content": "Por favor, trate e retorne os dados do arquivo JSON enviado anexo.",
# 				"attachments": [
# 					{
# 						"file_id": file.id,
# 						"tools": [
# 							{ "type": "code_interpreter" }
# 						]
# 					}
# 				]
# 			}
# 		]
# 	)

# 	run = OpenAIClient.beta.threads.runs.create_and_poll(
# 		thread_id= thread.id,
# 		assistant_id= Assistente.id
# 	)


# 	import time

# 	while run.status in ['queued', 'in_progress', 'cancelling']:
# 		time.sleep(1)
# 		run = OpenAIClient.beta.threads.runs.retrieve(
# 			thread_id= thread.id,
# 			run_id= run.id
# 		)

# 	if run.status == 'completed': 
# 		classResposta = OpenAIClient.beta.threads.messages.list(
# 			thread_id=thread.id,
# 			limit= 1
# 		)
# 		with open( 'resposta.json', 'w' ) as Arquivo:
# 			Arquivo.write( classResposta.to_json )
# 		# print(classResposta.data[0].content[0].text.value)
# 	else:
# 		print(run.status)


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



def funAtualizaJogos():

	varURL = 'https://v3.football.api-sports.io/fixtures'

	headers = {
		'x-rapidapi-host': 'v3.football.api-sports.io',
		'x-rapidapi-key': apiKey
	}

	with varEngine.begin() as engine:
		listaCampeonatos = engine.execute( Select( tbCampeonatos.columns['ID', 'Temporada Atual'] ) ).all()

	for varCampeonato, varTemporada in listaCampeonatos:
	
		varParams = {
			'league': varCampeonato,
			'season': varTemporada
		}

		jsonJogos = requests.request("GET", varURL, params=varParams, headers=headers )

		jsonJogos = jsonJogos.json()

		with open( 'JSONS/fixtures.json', 'w' ) as arquivoJSON:
			json.dump( jsonJogos, arquivoJSON, indent=4 )

		varErro = jsonJogos['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False

		# Lista para armazenar os resultados
		listaJogos = []
		
		# Iterar sobre as jogos
		for jogo in jsonJogos['response']:

			fixture = jogo['fixture']
			league = jogo['league']
			teams = jogo['teams']
			
			# Criar um dicionário para a jogo
			fixture_dict = {
				'ID': fixture['id'],
				'Data': datetime.fromtimestamp(fixture['timestamp']), #.strftime('%Y-%m-%d %H:%M:%S'),
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

	with varEngine.begin() as engine:

		vStep = int( ( 65535 / len( listaJogos[0] ) ) ) 

		if vStep == 0:
			vStep = 1

		for chunk in range(0, len( listaJogos ), vStep):

			print( 'Chunk: ', chunk, '  --  vStep: ', vStep )

			varInsert = insert( tbJogos ).values( listaJogos[ chunk:chunk+vStep ] )
			varInsertOrUpdate = varInsert\
				.on_conflict_do_update(
					constraint=tbJogos.primary_key,
					set_={
						'Data': varInsert.excluded.Data,
						'Status':varInsert.excluded.Status
		   			}
				)

			engine.execute( varInsertOrUpdate )

	return True


def funAtualizaEstatisticas():

	varURL = 'https://v3.football.api-sports.io/fixtures'

	headers = {
		'x-rapidapi-host': 'v3.football.api-sports.io',
		'x-rapidapi-key': apiKey
	}

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

		print( 'Total:', len( dfjogos ), '  --  Chunk:', chunkParitdas, '  --  vStep:', varQtdejogos )

		varIDs = '-'.join( dfjogos[ chunkParitdas:chunkParitdas+varQtdejogos ][ 'ID' ].astype( str ) )

		print( 'varIDs:', varIDs )

		varParams = {
			'ids': varIDs
		}

		jsonEstatisticas = requests.request("GET", varURL, params=varParams, headers=headers )

		jsonEstatisticas = jsonEstatisticas.json()

		with open( 'estatisticas.json', 'w' ) as arquivoJSON:
			json.dump( jsonEstatisticas, arquivoJSON, indent=4 )

		varErro = jsonEstatisticas['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False

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
					'Posse de Bole': dicEstatistica['Ball Possession'].replace( '%','' ) if dicEstatistica['Ball Possession'] else 0,
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

		with varEngine.begin() as engine:

			vStep = int( ( 65535 / len( listaEstatisticas[0] ) ) ) 

			if vStep == 0:
				vStep = 1

			for chunk in range(0, len( listaEstatisticas ), vStep):

				print( 'Total:', len( listaEstatisticas ), '  --  Chunk:', chunk, '  --  vStep:', vStep )

				varInsert = insert( tbJogosEstatisticas ).values( listaEstatisticas[ chunk:chunk+vStep ] )

				engine.execute( varInsert )

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

	headers = {
		'x-rapidapi-host': 'v3.football.api-sports.io',
		'x-rapidapi-key': apiKey
	}

	# print( dfjogos.to_dict(orient= 'records') )

	for jogo in dfjogos.to_dict(orient= 'records'):

		varParams = {
			'fixture': jogo['fixture_id']
		}

		jsonPrediction = requests.request("GET", varURL, params=varParams, headers=headers )

		jsonPrediction = jsonPrediction.json()

		with open( 'predictions.json', 'a' ) as arquivoJSON:
			json.dump( jsonPrediction, arquivoJSON, indent=4 )

		varErro = jsonPrediction['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False

		print( 'jogo:', jogo )
		print( '		Predictions:', jsonPrediction )

	return True


def funJogosDia():

	dfPaises = pd.read_sql_table( tbPaises.name, varEngine )
	dfCampeonatos = pd.read_sql_table( tbCampeonatos.name, varEngine )
	dfjogos = pd.read_sql_table( tbJogos.name, varEngine )
	dfEquipes = pd.read_sql_table( tbEquipes.name, varEngine )
	dfStatus = pd.read_sql_table( tbStatus.name, varEngine )

	dfjogosDia= dfjogos[ dfjogos['Data'].dt.date == datetime.today().date() ]

	# return dfjogosDia.sort_values(by='Data')

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
	dfFinal = dfFinal[ [ 'Data', 'País', 'Sigla', 'Bandeira', 'Campeonato', 'Logo', 'Status', 'Logo Casa', 'Equipe Casa', 'X', 'Equipe Fora', 'Logo Fora', 'ID Equipe Casa', 'ID Equipe Fora' ] ]
	dfFinal.sort_index( ascending=True, inplace=True )

	return dfFinal


def funAtualizaPaises():

	varURL = 'https://v3.football.api-sports.io/countries'

	headers = {
		'x-rapidapi-host': 'v3.football.api-sports.io',
		'x-rapidapi-key': apiKey
	}

	jsonPaises = requests.request("GET", varURL, headers=headers )

	jsonPaises = jsonPaises.json()

	with open( 'paises.json', 'w' ) as arquivoJSON:
		json.dump( jsonPaises, arquivoJSON, indent=2 )

	varErro = jsonPaises['errors']

	if varErro:
		continua = funErros( varErro )
		if not continua:
			return False

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

	headers = {
		'x-rapidapi-host': 'v3.football.api-sports.io',
		'x-rapidapi-key': apiKey
	}

	tmpCampeonatos = [ 39, 40, 61, 62, 71, 72, 78, 79, 135, 136, 140, 141 ]

  	# Lista para armazenar os resultados
	listaCampeonatos = []
  
	for tmpCampeonato in tmpCampeonatos:

		varParams = {
			'id': tmpCampeonato,
		}

		jsonCampeonatos = requests.request("GET", varURL, params=varParams, headers=headers )

		jsonCampeonatos = jsonCampeonatos.json()

		# with open( 'JSONS/campeonatos.json', 'a' ) as arquivoJSON:
		# 	json.dump( jsonCampeonatos, arquivoJSON, indent=4 )

		varErro = jsonCampeonatos['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False

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

	headers = {
		'x-rapidapi-host': 'v3.football.api-sports.io',
		'x-rapidapi-key': apiKey
	}

	with varEngine.begin() as engine:
		listaCampeonatos = engine.execute( Select( tbCampeonatos.columns['ID', 'Temporada Atual'] ) ).all()

	for lista in listaCampeonatos:

		campeonato, temporada = lista

		varParams = {
			'league': campeonato,
			'season': temporada
		}

		jsonEquipes = requests.request("GET", varURL, params=varParams, headers=headers )

		jsonEquipes = jsonEquipes.json()

		with open( 'fixtures.json', 'w' ) as arquivoJSON:
			json.dump( jsonEquipes, arquivoJSON, indent=2 )

		varErro = jsonEquipes['errors']

		if varErro:
			continua = funErros( varErro )
			if not continua:
				return False

		# Lista para armazenar os resultados
		listaEquipes = []
    
		# Iterar sobre as jogos
		for varEquipe in jsonEquipes['response']:

			equipe = equipe['team']
			
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

