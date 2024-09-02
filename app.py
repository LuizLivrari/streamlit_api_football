import streamlit as st

pagina = st.navigation(
	[
		st.Page(
			page='pages/jogosdia.py',
		),
		st.Page(
			page='pages/functions.py',
		),
	],
	position='hidden'
)

pagina.run()
