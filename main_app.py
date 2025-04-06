import streamlit as st
import os
import pandas as pd

# Import project modules
from utils import config, database, pdf_parser, email_sender
from agents import jd_agent, cv_agent
from utils import matcher # Corrected import path

# --- Page Config ---
st.set_page_config(page_title="AI Recruitment Assistant", layout="wide")

# --- Helper Functions ---
def load_jd_list():
    """Loads job descriptions from the database."""
    return database.get_all_jds()

# --- Initialize Session State ---
if 'current_jd_id' not in st.session_state:
    st.session_state.current_jd_id = None
if 'current_jd_title' not in st.session_state:
    st.session_state.current_jd_title = None
if 'jd_summary' not in st.session_state:
    st.session_state.jd_summary = None
if 'candidates_df' not in st.session_state:
    st.session_state.candidates_df = pd.DataFrame()


# --- Sidebar ---
st.sidebar.title("Recruitment Actions")

# Select or Add Job Description
st.sidebar.header("1. Job Description")
jd_list = load_jd_list()
jd_options = {jd['id']: jd['title'] for jd in jd_list}
selected_jd_id = st.sidebar.selectbox(
    "Select Existing JD",
    options=list(jd_options.keys()),
    format_func=lambda x: jd_options[x],
    index=None, # No default selection
    key="jd_selector"
)

# If a JD is selected from dropdown, update session state
if selected_jd_id and selected_jd_id != st.session_state.current_jd_id:
    st.session_state.current_jd_id = selected_jd_id
    st.session_state.current_jd_title = jd_options[selected_jd_id]
    st.session_state.jd_summary = database.get_jd_summary(selected_jd_id)
    # Load candidates for this JD
    candidates_data = database.get_candidates_for_jd(selected_jd_id)
    if candidates_data:
        st.session_state.candidates_df = pd.DataFrame([dict(row) for row in candidates_data])
    else:
        st.session_state.candidates_df = pd.DataFrame()


st.sidebar.markdown("---")
st.sidebar.subheader("Add New JD")
new_jd_title = st.sidebar.text_input("Job Title")
new_jd_text = st.sidebar.text_area("Paste Job Description Text Here", height=200)

if st.sidebar.button("Summarize & Add JD"):
    if new_jd_title and new_jd_text:
        with st.spinner("Summarizing Job Description..."):
            summary = jd_agent.summarize_job_description(new_jd_text)
            if "Error:" not in summary:
                jd_id = database.add_job_description(new_jd_title, new_jd_text, summary)
                if jd_id:
                    st.sidebar.success(f"JD '{new_jd_title}' added successfully!")
                    # Update state to reflect the new JD
                    st.session_state.current_jd_id = jd_id
                    st.session_state.current_jd_title = new_jd_title
                    st.session_state.jd_summary = summary
                    st.session_state.candidates_df = pd.DataFrame() # Reset candidates for new JD
                    st.rerun() # Rerun to update dropdown and main page
                else:
                    st.sidebar.error("Failed to save JD to database.")
            else:
                st.sidebar.error(f"Failed to summarize JD: {summary}")
    else:
        st.sidebar.warning("Please provide both Job Title and Description.")

st.sidebar.markdown("---")
st.sidebar.header("2. Process Resumes")
st.sidebar.info(f"Place PDF resumes in the:\n`{os.path.basename(config.RESUME_FOLDER)}` folder.")

if st.sidebar.button("Process Resumes & Match"):
    if st.session_state.current_jd_id and st.session_state.jd_summary:
        resume_files = [f for f in os.listdir(config.RESUME_FOLDER) if f.lower().endswith(".pdf")]
        if not resume_files:
            st.sidebar.warning("No PDF resumes found in the folder.")
        else:
            progress_bar = st.sidebar.progress(0)
            status_text = st.sidebar.empty()
            processed_count = 0
            total_files = len(resume_files)

            for i, filename in enumerate(resume_files):
                status_text.text(f"Processing {filename}...")
                pdf_path = os.path.join(config.RESUME_FOLDER, filename)

                # a. Parse PDF
                cv_text = pdf_parser.extract_text_from_pdf(pdf_path)
                if not cv_text:
                    st.warning(f"Could not extract text from {filename}. Skipping.")
                    continue

                # b. Extract CV Details using CV Agent
                extracted_data = cv_agent.extract_cv_details(cv_text)
                if extracted_data.get("error"):
                     st.warning(f"CV Parsing Error for {filename}: {extracted_data['error']}")
                     # Continue processing but may lack some data

                if not extracted_data.get('email'):
                     st.warning(f"Could not extract email for {filename}. Skipping match.")
                     # We need email to uniquely identify and contact candidate
                     continue


                # c. Add/Update Candidate in DB
                candidate_id = database.add_candidate(
                    name=extracted_data.get('name'),
                    email=extracted_data['email'], # Email is required now
                    phone=extracted_data.get('phone'),
                    cv_filename=filename,
                    cv_text=cv_text,
                    skills=extracted_data.get('skills'),
                    experience=extracted_data.get('experience'),
                    education=extracted_data.get('education')
                )

                if not candidate_id:
                     st.error(f"Failed to add/update candidate {extracted_data['email']} from {filename} to DB.")
                     continue

                # d. Calculate Match Score using Matcher
                score = matcher.calculate_match_score(st.session_state.jd_summary, extracted_data)
                if score == -1:
                    st.warning(f"Could not calculate match score for {filename}. Skipping match.")
                    continue

                # e. Determine Shortlisting & Add Match to DB
                is_shortlisted = score >= config.MATCH_THRESHOLD
                match_saved = database.add_or_update_match(
                    st.session_state.current_jd_id,
                    candidate_id,
                    score,
                    is_shortlisted
                )
                if not match_saved:
                     st.error(f"Failed to save match for candidate {candidate_id} / JD {st.session_state.current_jd_id}")

                processed_count += 1
                progress_bar.progress((i + 1) / total_files)
                status_text.text(f"Processed {processed_count}/{total_files} resumes.")

            status_text.success(f"Finished processing {processed_count} resumes.")
            progress_bar.empty()
            # Refresh candidate list after processing
            candidates_data = database.get_candidates_for_jd(st.session_state.current_jd_id)
            if candidates_data:
                st.session_state.candidates_df = pd.DataFrame([dict(row) for row in candidates_data])
            else:
                st.session_state.candidates_df = pd.DataFrame()
            st.rerun() # Rerun to display updated table

    else:
        st.sidebar.warning("Please select or add a Job Description first.")


# --- Main Page ---
st.title("🤖 AI Recruitment Assistant Dashboard")

if not st.session_state.current_jd_id:
    st.info("Select an existing Job Description or add a new one using the sidebar to get started.")
else:
    st.header(f"Job: {st.session_state.current_jd_title}")
    st.subheader("Job Description Summary")
    st.markdown(st.session_state.jd_summary if st.session_state.jd_summary else "_No summary available._")
    st.markdown("---")

    st.header("Candidate Matching & Shortlisting")

    if not st.session_state.candidates_df.empty:
        # Display Candidates Table
        st.subheader("Matched Candidates")

        # Prepare dataframe for display
        display_df = st.session_state.candidates_df[['name', 'email', 'match_score', 'is_shortlisted', 'interview_email_sent', 'cv_filename']].copy()
        display_df.rename(columns={
            'match_score': 'Score (%)',
            'is_shortlisted': 'Shortlisted',
            'interview_email_sent': 'Email Sent',
            'cv_filename': 'Resume File'
        }, inplace=True)

        st.dataframe(display_df, use_container_width=True)

        # --- Shortlisting & Emailing ---
        st.subheader("Interview Scheduling")
        shortlisted_candidates = st.session_state.candidates_df[
            (st.session_state.candidates_df['is_shortlisted'] == True) &
            (st.session_state.candidates_df['interview_email_sent'] == False)
        ]

        if not shortlisted_candidates.empty:
            st.write(f"Found **{len(shortlisted_candidates)}** shortlisted candidate(s) ready for interview invitation:")
            st.dataframe(shortlisted_candidates[['name', 'email', 'match_score']], use_container_width=True)

            if st.button("📧 Send Interview Emails to Shortlisted Candidates"):
                 if not config.EMAIL_ADDRESS or config.EMAIL_ADDRESS == "default_email@example.com" or not config.EMAIL_PASSWORD or config.EMAIL_PASSWORD == "default_password":
                      st.error("Email credentials not configured. Please set them in the `.env` file and restart.")
                 else:
                    send_count = 0
                    fail_count = 0
                    with st.spinner("Sending emails..."):
                         # Fetch fresh list just before sending
                         candidates_to_email = database.get_shortlisted_candidates_for_emailing(st.session_state.current_jd_id)

                         for candidate in candidates_to_email:
                            success = email_sender.send_interview_email(
                                recipient_email=candidate['email'],
                                candidate_name=candidate['name'],
                                job_title=st.session_state.current_jd_title
                            )
                            if success:
                                # Update status in database
                                database.update_email_sent_status(candidate['match_id'])
                                send_count += 1
                            else:
                                fail_count += 1

                    st.success(f"Sent {send_count} interview invitations.")
                    if fail_count > 0:
                        st.warning(f"Failed to send emails for {fail_count} candidates. Check console logs for errors.")

                    # Refresh data after sending
                    candidates_data = database.get_candidates_for_jd(st.session_state.current_jd_id)
                    if candidates_data:
                         st.session_state.candidates_df = pd.DataFrame([dict(row) for row in candidates_data])
                    else:
                         st.session_state.candidates_df = pd.DataFrame()
                    st.rerun()

        else:
            st.info("No shortlisted candidates pending interview invitations for this job.")

    else:
        st.info("No candidates processed for this job yet. Use the 'Process Resumes & Match' button in the sidebar.")

# --- Database Viewer (Optional) ---
st.markdown("---")
st.header("Database Contents (for debugging)")
show_db = st.checkbox("Show Raw Database Tables")
if show_db:
    try:
        conn = database.get_db_connection()
        st.subheader("Job Descriptions Table")
        jds_df = pd.read_sql_query("SELECT * FROM job_descriptions", conn)
        st.dataframe(jds_df)

        st.subheader("Candidates Table")
        cands_df = pd.read_sql_query("SELECT id, name, email, phone, cv_filename, timestamp FROM candidates", conn) # Avoid showing full CV text
        st.dataframe(cands_df)

        st.subheader("Matches Table")
        matches_df = pd.read_sql_query("SELECT * FROM matches", conn)
        st.dataframe(matches_df)
        conn.close()
    except Exception as e:
        st.error(f"Could not display database tables: {e}")