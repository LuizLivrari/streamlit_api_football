import urllib.parse
from sqlalchemy import create_engine
import urllib.parse

varStringConexao = f'postgresql+psycopg://{urllib.parse.quote_plus('postgres')}:{urllib.parse.quote_plus('ApiF9137')}@177.16.165.92:8080/novo_banco'

varEngine = create_engine( varStringConexao, echo=False )

HEADERS = {
	'x-rapidapi-host': 'v3.football.api-sports.io',
	'x-rapidapi-key': '6fae569f8142f8ad0bc5936831103948'
}

CSS = """
	<style>

		.stAppViewBlockContainer{
			max-width: 70%;
			padding: 2.8rem 0rem;
		}

        #31d86dc4{
			text-align: center;
        }

        h2 {
			padding: 0rem 0rem;
        }

		hr {
			margin: 1rem 0rem;	
		}

	</style>
"""