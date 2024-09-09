import streamlit as st

pagina = st.navigation(
	[
		st.Page(
			page='paginas/jogosdia.py',
		),
		st.Page(
			page='paginas/functions.py',
		),
	],
	position='hidden'
)

pagina.run()
