import streamlit as st
import requests

API_URL = "http://localhost:8000/upload"

st.set_page_config(page_title="Prescription OCR Test", page_icon="💊")

st.title("💊 Prescription OCR Testing Tool")
st.write("Upload a prescription image to test the OCR backend directly.")

uploaded_file = st.file_uploader("Choose an image...", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    st.image(uploaded_file, caption='Uploaded Image', use_column_width=True)
    
    if st.button("Extract Data"):
        with st.spinner("Processing OCR..."):
            files = {"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)}
            try:
                response = requests.post(API_URL, files=files)
                if response.status_code == 200:
                    data = response.json()
                    st.success("Extraction Complete!")
                    
                    st.subheader("Extracted Fields")
                    fields = data.get("extracted_fields", {})
                    st.json(fields)
                    
                    st.subheader("Raw Text")
                    st.text_area("OCR Output", value=data.get("raw_text", ""), height=300)
                else:
                    st.error(f"Error: Server returned status code {response.status_code}")
            except Exception as e:
                st.error(f"Failed to connect to API: {e}")
