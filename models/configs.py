import urllib.parse
from sqlalchemy import create_engine
import urllib.parse

varStringConexao = f'postgresql+psycopg://{urllib.parse.quote_plus('postgres')}:{urllib.parse.quote_plus('ApiF@9137')}@localhost:5435/novo_banco'

varEngine = create_engine( varStringConexao, echo=True )

apiKey = '6fae569f8142f8ad0bc5936831103948'

CSS = """
	<style>

		.appview-container .main .block-container {
			# max-width: 95%;
			padding-top: 2.8rem;
		}

        #31d86dc4{
			text-align: center;
        }

        #sports-soccer-jogos-do-dia-today{
			# text-align: center;
        }

        h2 {
			padding: 0rem 0rem;
        }

		hr {
			margin: 1rem 0rem;	
		}

		# /* Estilos para o botão de login */
		# button {
		# 	background-color: #4CAF50;
		# 	color: white;
		# 	padding: 15px 20px;
		# 	margin: 10px 0;
		# 	border: none;
		# 	cursor: pointer;
		# 	width: 100%;
		# 	border-radius: 4px;
		# 	font-size: 16px;
		# }

		# button:hover {
		# 	background-color: #45a049;
		# }

	</style>
"""