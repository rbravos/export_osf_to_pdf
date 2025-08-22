'''
## =================================================================================================
## Title: Streamlit App to Download OSF Project to PDF                                            ##
## Project:                                                                                       ##
##      Export OSF Project to PDF - Centre for Open Science (CoS) & University of Manchester (UoM)##
## UoM Team:                                                                                      ##
##      Ramiro Bravo, Sarah Jaffa, Benito Matischen                                               ##
## Author(s):                                                                                     ##
##       Ramiro Bravo - ramiro.bravo@manchester.ac.uk - ramirobravo@gmail.com                     ##
## Create date:                                                                                   ##
##       July-2025                                                                                ##
## Description:                                                                                   ##
##      The Streamlit app serves as the front end application allowing users to download OSF      ##
##      project in PDF format.                                                                    ##
## Parameters:                                                                                    ##
##      OSF Project URL: Provide the URL of the project fro exapmle: https://osf.io/kzc68/        ##
##      Select API environment: Production or Test                                                ##
##      Token Source: Provided via .env file or entering the OSF API token.                       ##
##      OSF API Key: Allows users to enter (paste) the API key for private repositories           ##
## Running App locally: Recomended to use a python virtual environment                            ##
##    $ source ./venv/bin/activate                                                                ##
##    $ streamlit run app_export_OSF_toPDF.py                                                     ##
##                                                                                                ##
## =================================================================================================
'''

import streamlit as st
import tempfile
import os
import osfexport

st.set_page_config(page_title="OSF PDF Export Tool", layout="centered")
st.title("🔄 OSF Project to PDF")

project_url = st.text_input("📁 Enter OSF Project URL:", placeholder="e.g. https://osf.io/abcde/")
project_id = osfexport.extract_project_id(project_url) if project_url else ''
st.write("Project ID: ", project_id)

st.subheader("🔐 OSF Project type")
project_type = st.radio("Select Project Type:", ["Public", "Private"])
if project_type == "Private":
   # Token input
   st.subheader("🔑 OSF Token")
   pat = st.text_input("Enter your OSF API token:", type="password")
else:
   st.info("Public projects do not require a token.")
   pat = ''

# --- Form input section ---
with st.form("export_form"):   
   dryrun = st.checkbox("Use test/mock data (Dry run)?", value=True)
   usetest = st.checkbox("Use OSF Test API?", value=True)
   submitted = st.form_submit_button("Export to PDF")

if submitted:
   if not pat and not dryrun and project_type == "Private":
       st.warning("Please provide a Personal Access Token unless using dry run mode.")
   else:
       with st.spinner("Generating PDF... Please wait."):
           try:
               # Step 1: Get project data
               projects, root_nodes = osfexport.get_nodes(
                   pat=pat,
                   dryrun=dryrun,
                   project_id=project_id,
                   usetest=usetest
               )
               if not root_nodes:
                   st.error("No projects found.")
               else:
                   root_idx = root_nodes[0]  # Export first root node

                   # Step 2: Generate the PDF to a temp folder
                   with tempfile.TemporaryDirectory() as tmpdir:
                       pdf_obj, pdf_path = osfexport.write_pdf(
                           projects,
                           root_idx=root_idx,
                           folder=tmpdir
                       )

                       # Step 3: Display the download link
                       with open(pdf_path, "rb") as f:
                           st.success("✅ PDF Generated!")
                           st.download_button(
                               label="📄 Download PDF",
                               data=f,
                               file_name=os.path.basename(pdf_path),
                               mime="application/pdf"
                           )
           except Exception as e:
               st.error(f"❌ An error occurred: {str(e)}")