from sqlalchemy import MetaData, Table
from models.configs import varEngine

metadata = MetaData()

metadata.reflect( bind=varEngine )

tbCampeonatos = Table( 'campeonatos', metadata )

tbJogos = Table( 'partidas', metadata )

tbPaises = Table( 'paises', metadata )

tbEstatisticas = Table( 'partidas_estatisticas', metadata )

tbEquipes = Table( 'equipes', metadata )

tbStatus = Table( 'status', metadata )