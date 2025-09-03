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

API_HOST = "https://api.osf.io/v2"
PROJECT_GROUPS = ["All projects where I'm a Contributor", "Single Project"]
pat = ''
project_id = ''

st.set_page_config(page_title="OSF PDF Export Tool", layout="centered")
st.title("🔄 OSF Project to PDF")

# Store if ID changes to ensure form for single projects resets in this case
if 'current_id' not in st.session_state:
    st.session_state.current_id = ''
# Store if user has checked visibility to avoid disappearing PAT section
if 'checked_if_public' not in st.session_state:
    st.session_state.checked_if_public = False
# Store result of the is_public check to avoid repeating API calls
if 'is_public' not in st.session_state:
    st.session_state.is_public = False

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


def check_visibility():
    st.session_state.is_public = osfexport.is_public(f'{API_HOST}/nodes/{project_id}/')
    st.session_state.checked_if_public = True


# Choose to export multiple or single project - ask for id if needed
st.subheader("🔐 OSF Project Type")
project_group = st.radio("Choose projects to export:", PROJECT_GROUPS)

if project_group == PROJECT_GROUPS[1]:
    project_url = st.text_input(
        "📁 Enter OSF Project URL or ID:",
        placeholder="e.g. 'https://osf.io/abcde/' OR 'abcde'"
    )
    project_id = osfexport.extract_project_id(project_url) if project_url else ''
    if project_id:
        st.info(f"Exporting Project with ID: {project_id}")
    # Check if ID has changed and require rechecking visibility if it has
    if st.session_state.current_id != project_id:
        st.session_state.checked_if_public = False
        st.session_state.is_public = False
        st.session_state.current_id = project_id

    is_id_check_ready = st.button(
        "Check Project is Public", type="secondary",
        disabled=False if project_id else True,
        on_click=check_visibility
    )

if project_group == PROJECT_GROUPS[1] and st.session_state.checked_if_public:
    if not st.session_state.is_public:
        st.info("To export a private project, you will need to provide a Personal Access Token (PAT).")
        st.subheader("🔑 OSF Token")
        pat = st.text_input("Enter your OSF API token:", type="password")
    else:
        st.success("The project is public, no token is required.")

if project_group == PROJECT_GROUPS[0]:
    st.info("To export all projects, you will need to provide a Personal Access Token (PAT).")
    st.subheader("🔑 OSF Token")
    pat = st.text_input("Enter your OSF API token:", type="password")

# Valid states for exporting:
# Export multiple AND PAT given
# Export single AND public
# Export single AND not public and PAT given
valid_export_all = project_group == PROJECT_GROUPS[0] and pat
valid_export_public = project_group == PROJECT_GROUPS[1] and st.session_state.is_public
valid_export_private = project_group == PROJECT_GROUPS[1] and pat
valid_export_state = valid_export_all or valid_export_public or valid_export_private
submitted = st.button(
    "Export to PDF", type="secondary",
    disabled=False if valid_export_state else True
)

if submitted:
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