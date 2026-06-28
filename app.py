import streamlit as st

st.set_page_config(page_title="CAT Programme Assistant", layout="wide")

st.title("CAT Programme Assistant")
st.caption("Clinical Administration Transformation — University Hospitals Birmingham")

mode = st.radio(
    "Select mode:",
    ["Ask a Question", "Process Minutes", "Draft Document"],
    horizontal=True,
)

st.divider()

if mode == "Ask a Question":
    st.info("Query mode — coming in Week 1")

elif mode == "Process Minutes":
    st.info("Minutes processing mode — coming in Week 2")

elif mode == "Draft Document":
    st.info("Document drafting mode — coming in Week 3")
