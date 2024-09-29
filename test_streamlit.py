import streamlit as st

header=st.header('Header')

text = st.text('Button Not Pressed')


if st.button('Press ME'):
    st.write('Why hello there')
    header.header('Pressed')
    text.text("Button PRessed")
else:
    st.write('Goodbye')
