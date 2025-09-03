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
import osfexport
import shutil
from datetime import datetime
import os

api_host = "https://api.osf.io/v2"

st.set_page_config(page_title="OSF PDF Export Tool", layout="centered")
st.title("🔄 OSF Project to PDF")

# Track if single project had visibility checked across page refreshes
if 'has_status_checked' not in st.session_state:
    st.session_state.has_status_checked = False
st.write(st.session_state)

#REMOVE THE SETTING OPTIONS
st.markdown("""
    <style>
        .reportview-container {
            margin-top: -2em;
        }
        #MainMenu {visibility: hidden;}
        .stDeployButton {display:none;}
        footer {visibility: hidden;}
        #stDecoration {display:none;}
    </style>
""", unsafe_allow_html=True)

# Choose to export multiple or single project - ask for id if needed
st.subheader("🔐 OSF Project Type")
project_groups = st.radio("Choose projects to export:", ["All projects where I'm a Contributor", "Single Project"])

project_id = ''
is_public = False
if project_groups == "Single Project":
    project_url = st.text_input("📁 Enter OSF Project URL or ID:", placeholder="e.g. 'https://osf.io/abcde/' OR 'abcde'")
    project_id = osfexport.extract_project_id(project_url) if project_url else ''
    if project_id:
        st.info(f"Exporting Project with ID: {project_id}")
    # Update session state on click
    is_id_check_ready = st.button(
        "Check Project is Public", type="secondary",
        key="has_status_checked",
        disabled=False if project_id else True
    )
    if is_id_check_ready:
        is_public = osfexport.is_public(f'{api_host}/nodes/{project_id}/')


# Request a PAT if getting multiple projects or a private project
pat = ''

if project_groups == "All projects where I'm a Contributor":
    st.info("To export all projects, you will need to provide a Personal Access Token (PAT).")
    st.subheader("🔑 OSF Token")
    pat = st.text_input("Enter your OSF API token:", type="password")

# Only show this section if user has clicked button to check visibility
# i.e. when session state variable is True
if project_groups == "Single Project" and st.session_state.has_status_checked:
    if not is_public:
        st.info("To export a private project, you will need to provide a Personal Access Token (PAT).")
        st.subheader("🔑 OSF Token")
        pat = st.text_input("Enter your OSF API token:", type="password")
    else:
        st.success("The project is public, no token is required.")

submitted = st.button("Export to PDF", type="secondary")

# Only do exporting if using local JSON files for a test run or exporting a single public project
is_private_single = project_groups == "Single Project" and not is_public
is_exporting_all = project_groups == "All projects where I'm a Contributor"
if submitted:
   if not pat and (is_exporting_all or is_private_single):
       st.warning("Please provide a Personal Access Token unless using dry run mode.")
   else:
    with st.spinner("Generating PDF... Please wait."):
        projects, root_nodes = osfexport.get_nodes(
            pat=pat,
            project_id=project_id
        )
        if not root_nodes:
            st.error("No projects found.")

        # Step 2: Generate the PDFs to a temp folder
        with tempfile.TemporaryDirectory() as tmpdir:
            pdf_count = 0  # Track number of files for better user messages
            paths = []
            for root_idx in root_nodes:
                pdf_obj, pdf_path = osfexport.write_pdf(
                    projects,
                    root_idx=root_idx,
                    folder=tmpdir
                )
                pdf_count += 1
                paths.append(pdf_path)
                
            
            # Step 3: Create zip file/PDF and display download link
            if pdf_count > 1:
                timestamp = datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
                zip_filename = f'osf_projects_exported_{timestamp}'
                archive = shutil.make_archive(zip_filename, 'zip', base_dir=tmpdir)
                st.info(f"📦 {pdf_count} PDF{'s' if pdf_count > 1 else ''} generated and compressed")
                with open(archive, "rb") as file:
                    st.download_button(
                        label=f"📄 Download {'all PDFs' if pdf_count > 1 else 'PDF'} as ZIP",
                        data=file,
                        file_name=f"{zip_filename}.zip",
                        mime="application/zip"
                    )
            else:
                with open(paths[0], "rb") as f:
                    st.download_button(
                        label=f"📄 Download PDF for {projects[0]['metadata']['title']}",
                        data=f,
                        file_name=os.path.basename(paths[0]),
                        mime="application/pdf"
                    )
        st.success("✅ PDFs Generated!")