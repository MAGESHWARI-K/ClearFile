import os, uuid
from pathlib import Path
import streamlit as st
import pandas as pd
from dotenv import load_dotenv
from agents.document_extractor import extract_fields
from agents.consistency_checker import compare_documents
from agents.anomaly_analyst import analyse
from agents.memo_writer import create_memo
from utils.document_reader import read_uploaded_file
from utils.graph_builder import build_graph
from utils.storage import init_db, save_application, get_all_applications, get_application, save_review

load_dotenv(Path(__file__).resolve().parent / '.env')
st.set_page_config(page_title='ClearFile | Applicant Verification', page_icon='📑', layout='wide')
init_db()
BURGUNDY='#6E1724'; CREAM='#F8F3EA'; SAGE='#71806A'; GOLD='#C4A15A'; INK='#302B29'; MUTED='#756D68'

st.markdown(f'''<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@600;700&display=swap');
html, body, [class*="css"] {{font-family:'DM Sans',sans-serif;color:{INK};}}
.stApp {{background:{CREAM};}}
.block-container {{padding-top:1.6rem; max-width:1400px;}}
header[data-testid="stHeader"] {{background:transparent;}}
.brand {{display:flex;align-items:center;gap:12px;margin-bottom:8px;}}
.brand-mark {{width:48px;height:48px;border-radius:14px;background:{BURGUNDY};display:flex;align-items:center;justify-content:center;}}
.brand-title {{font-family:'Playfair Display',serif;font-size:29px;font-weight:700;color:{BURGUNDY};line-height:1.1;}}
.brand-sub {{font-size:12px;color:{MUTED};letter-spacing:1.2px;text-transform:uppercase;}}
.hero {{background:{BURGUNDY};color:white;padding:25px 28px;border-radius:18px;margin:12px 0 22px;}}
.hero h1,.hero h2,.hero p,.hero span {{color:white!important;}}
.hero h1 {{font-family:'Playfair Display',serif;font-size:30px;margin:0 0 7px;}}
.hero p {{opacity:.9;margin:0;}}
.dashboard-panel {{background:#fff;border:1px solid #E8DED2;border-radius:16px;padding:20px 22px;min-height:150px;}}
.dashboard-panel h3 {{color:{BURGUNDY};margin:0 0 8px;font-size:18px;}}
.dashboard-kicker {{font-size:11px;letter-spacing:1.2px;text-transform:uppercase;color:{SAGE};font-weight:700;}}
.workflow-step {{display:flex;gap:12px;align-items:flex-start;padding:11px 0;border-bottom:1px solid #EFE7DD;}}
.workflow-step:last-child {{border-bottom:0;}}
.step-no {{background:#F2E8E5;color:{BURGUNDY};font-weight:700;border-radius:9px;padding:5px 8px;font-size:12px;}}
.ai-callout {{background:#F0E8DC;border:1px solid #E2D5C6;border-radius:16px;padding:18px 20px;margin:16px 0;}}
.ai-callout h3 {{color:{BURGUNDY};margin:0 0 6px;}}
div[data-testid='stChatMessage'] {{border-radius:14px;}}
@media(max-width:800px) {{.dashboard-grid {{grid-template-columns:1fr;}}}}
div.stButton>button {{border-radius:10px;border:1px solid #D8CDC0;background:white;color:{BURGUNDY};font-weight:600;}}
div.stButton>button[kind="primary"] {{background:{BURGUNDY};color:white;border:1px solid {BURGUNDY};}}
div.stButton>button:hover {{border-color:{GOLD};color:{BURGUNDY};}}
[data-testid="stMetric"] {{background:white;padding:17px 18px;border:1px solid #E8DED2;border-radius:14px;}}
[data-testid="stMetricLabel"] p {{color:{MUTED}!important;}}
[data-testid="stMetricValue"] {{color:{BURGUNDY}!important;}}
section[data-testid="stSidebar"] {{background:#F0E8DC;}}
section[data-testid="stSidebar"] * {{color:{INK};}}
.card {{background:white;border:1px solid #E9DFD3;border-radius:14px;padding:18px 20px;margin:8px 0;}}
.about-agent-card {{height:190px;min-height:190px;box-sizing:border-box;display:flex;flex-direction:column;justify-content:flex-start;overflow:hidden;}}
.about-agent-card h3 {{min-height:56px;margin:10px 0 8px;font-size:20px;line-height:1.25;}}
.about-agent-card p {{margin-top:0;line-height:1.5;}}
.pill {{display:inline-block;background:#E7EDE4;color:#40543C;padding:4px 10px;border-radius:20px;font-size:12px;font-weight:700;}}
.small-muted {{color:{MUTED};font-size:13px;}}
.chat-user {{background:#F0E8DC;padding:12px 15px;border-radius:14px;margin:8px 0 8px 14%;}}
.chat-ai {{background:white;border:1px solid #E7DDD1;padding:13px 15px;border-radius:14px;margin:8px 14% 8px 0;}}
hr {{border-color:#E7DDD1;}}
</style>''', unsafe_allow_html=True)

logo='''<svg width="32" height="32" viewBox="0 0 64 64" fill="none" xmlns="http://www.w3.org/2000/svg"><rect x="9" y="7" width="35" height="43" rx="5" stroke="#F8F3EA" stroke-width="4"/><rect x="20" y="14" width="35" height="43" rx="5" fill="#6E1724" stroke="#F8F3EA" stroke-width="4"/><path d="M29 35L36 42L48 28" stroke="#C4A15A" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"/><path d="M27 23H45" stroke="#F8F3EA" stroke-width="3" stroke-linecap="round"/></svg>'''
st.markdown(f'<div class="brand"><div class="brand-mark">{logo}</div><div><div class="brand-title">ClearFile</div><div class="brand-sub">Applicant document verification</div></div></div>',unsafe_allow_html=True)

pages=['Dashboard','New Application','Reports','ClearFile AI','About']
if 'page' not in st.session_state: st.session_state.page='Dashboard'
nav=st.columns(len(pages))
for col,p in zip(nav,pages):
    with col:
        if st.button(('✦ ' if st.session_state.page==p else '')+p,key='nav_'+p,use_container_width=True): st.session_state.page=p; st.rerun()
st.markdown('<hr>',unsafe_allow_html=True)

def hero(title, subtitle):
    st.markdown(f'<div class="hero"><h1>{title}</h1><p>{subtitle}</p></div>',unsafe_allow_html=True)

def run_verification(app_id, uploaded):
    extracted={}; texts={}; display={}
    for f in uploaded:
        raw=read_uploaded_file(f)
        if raw.startswith('OCR_ERROR:'): st.warning(f"Could not OCR {f.name}. Check Tesseract installation."); continue
        texts[f.name]=raw; extracted[f.name]=extract_fields(raw); display[f.name]=len(raw)
    findings=compare_documents(extracted); anomalies=analyse(findings)
    memo=create_memo(app_id,findings,anomalies,list(extracted.keys()))
    save_application(app_id,display,extracted,findings,anomalies,memo)
    st.session_state.last_app=app_id

apps=get_all_applications()
if st.session_state.page=='Dashboard':
    hero('A clearer way to review applicant documents.','One workspace to compare financial documents, understand evidence and keep every decision with a human reviewer.')
    verified=sum(a['review_status']=='Verified' for a in apps)
    pending=sum(a['review_status']=='Pending review' for a in apps)
    flagged=sum(len(a.get('anomalies',[])) for a in apps)
    c=st.columns(4)
    c[0].metric('Total applications',len(apps))
    c[1].metric('Verified by officers',verified)
    c[2].metric('Awaiting review',pending)
    c[3].metric('Potential mismatches',flagged)

    left,right=st.columns([1.35,.85],gap='large')
    with left:
        st.markdown(f'<div class="dashboard-panel"><div class="dashboard-kicker">Workspace overview</div><h3>Document review, made clearer.</h3><p style="color:{MUTED};margin-bottom:14px">Bring payslips, bank statements and tax forms together. ClearFile extracts shared details, highlights differences and prepares a memo for officer review.</p></div>',unsafe_allow_html=True)
        st.markdown('')
        a1,a2=st.columns(2)
        with a1:
            if st.button('＋  Start new application',type='primary',use_container_width=True): st.session_state.page='New Application'; st.rerun()
        with a2:
            if st.button('View verification reports',use_container_width=True): st.session_state.page='Reports'; st.rerun()
    with right:
        st.markdown(f'<div class="ai-callout"><div class="dashboard-kicker">ClearFile Intelligence</div><h3>Need help understanding a report?</h3><p style="color:{INK};font-size:14px">Ask questions in plain language. The assistant can explain extracted evidence, compare findings and suggest what an officer should review next.</p></div>',unsafe_allow_html=True)
        if st.button('✦  Chat with ClearFile AI',type='primary',use_container_width=True): st.session_state.page='ClearFile AI'; st.rerun()

    left,right=st.columns([1.15,.85],gap='large')
    with left:
        st.subheader('Recent applications')
        if apps:
            rows=[{'Application ID':a['application_id'],'Last updated':a['updated_at'],'Review status':a['review_status'],'Documents':len(a['documents']),'Potential mismatches':len(a.get('anomalies',[]))} for a in apps[:6]]
            st.dataframe(pd.DataFrame(rows),use_container_width=True,hide_index=True)
            if st.button('Open all reports →',use_container_width=False): st.session_state.page='Reports'; st.rerun()
        else:
            st.info('No applications have been saved yet. Start a new application to see activity here.')
    with right:
        st.subheader('How ClearFile works')
        steps=[('01','Upload supporting documents'),('02','Extract available information'),('03','Compare shared fields'),('04','Highlight missing or conflicting values'),('05','Prepare a verification memo'),('06','Officer reviews the evidence')]
        for n,label in steps:
            st.markdown(f'<div class="workflow-step"><span class="step-no">{n}</span><span style="color:{INK};font-weight:600;padding-top:3px">{label}</span></div>',unsafe_allow_html=True)
    st.caption('ClearFile supports human review. It does not automatically approve or reject applications.')
elif st.session_state.page=='New Application':
    hero('New application','Upload payslips, bank statements, tax forms or other supported files.')
    app_id=st.text_input('Application ID',value=f"CF-{pd.Timestamp.now().year}-{len(apps)+1:03d}")
    uploaded=st.file_uploader('Upload applicant documents',type=['pdf','txt','png','jpg','jpeg'],accept_multiple_files=True,help='PDF, TXT, PNG and JPG. Maximum 200 MB per file.')
    st.caption('Image and scanned-file OCR requires Tesseract OCR to be installed on your computer.')
    with st.expander('Use included sample document sets'):
        st.write('Three fictional test sets are included. Open the matching folder in sample_documents and upload all files in that folder together.')
        sample_sets = [('All match', 'sample_documents/all_match'), ('Partial match', 'sample_documents/partial_match'), ('Mismatches', 'sample_documents/mismatches')]
        for label, folder in sample_sets:
            st.markdown(f'**{label}**')
            for f in sorted(Path(folder).glob('*.txt')):
                st.code(str(f))
    if st.button('Run verification',type='primary',disabled=not uploaded):
        if not app_id.strip(): st.error('Enter an application ID.')
        else:
            with st.spinner('Reading documents and comparing available fields…'):
                run_verification(app_id.strip(),uploaded)
            st.success('Verification completed and saved.')
            st.rerun()
    target=st.session_state.get('last_app')
    if target:
        a=get_application(target)
        if a:
            st.divider(); st.subheader(f"Verification results · {target}")
            x=st.columns(3); x[0].metric('Documents processed',len(a['extracted'])); x[1].metric('Fields compared',len(a['findings'])); x[2].metric('Potential mismatches',len(a['anomalies']))
            t1,t2,t3,t4=st.tabs(['Comparison','Extracted details','Verification memo','Officer review'])
            with t1:
                if a['findings']:
                    for f in a['findings']:
                        icon='✓' if f['status']=='Match' else '⚠'
                        st.markdown(f"**{icon} {f['field']} — {f['status']}**")
                        st.caption('; '.join(f"{k}: {v}" for k,v in f['values'].items()))
                else: st.info('No shared fields could be compared. Check that uploaded documents contain readable labels and values.')
                st.subheader('Verification at a glance')
                counts = {'Match': sum(1 for item in a['findings'] if item['status']=='Match'), 'Mismatch': sum(1 for item in a['findings'] if item['status']=='Mismatch'), 'Not available': sum(1 for item in a['findings'] if item['status']=='Not Available')}
                g1,g2,g3=st.columns(3)
                g1.metric('✓ Matching fields', counts['Match'])
                g2.metric('⚠ Conflicting fields', counts['Mismatch'])
                g3.metric('— Missing information', counts['Not available'])
                st.caption('How to read this: Match = same value found; Mismatch = different values found; Not available = a document did not contain that detail.')
                for item in a['findings']:
                    badge = '🟢' if item['status']=='Match' else ('🔴' if item['status']=='Mismatch' else '🟡')
                    with st.expander(f"{badge} {item['field']} · {item['status']}"):
                        for doc_name, value in item['values'].items():
                            st.write(f'**{doc_name}:** {value}')
            with t2: st.json(a['extracted'])
            with t3: st.text_area('Verification memo',a['memo'],height=300); st.download_button('Download memo',a['memo'],file_name=f'{target}_memo.txt')
            with t4:
                status=st.selectbox('Review status',['Pending review','Verified','Needs clarification'],index=['Pending review','Verified','Needs clarification'].index(a['review_status']))
                notes=st.text_area('Officer notes',a['review_notes'])
                if st.button('Save officer review'): save_review(target,status,notes); st.success('Review saved.')
elif st.session_state.page=='Reports':
    hero('Verification reports','Search saved applications, review findings and download verification memos.')
    query=st.text_input('Search by application ID')
    filtered=[a for a in apps if query.lower() in a['application_id'].lower()]
    st.caption(f'{len(filtered)} report(s)')
    for a in filtered:
        with st.expander(f"{a['application_id']}  ·  {a['review_status']}  ·  {a['updated_at']}",expanded=False):
            m=st.columns(3); m[0].metric('Documents',len(a['documents'])); m[1].metric('Fields compared',len(a['findings'])); m[2].metric('Mismatches',len(a['anomalies']))
            for f in a['findings']:
                st.markdown(f"**{'✓' if f['status']=='Match' else '⚠'} {f['field']} — {f['status']}**")
                st.caption('; '.join(f"{k}: {v}" for k,v in f['values'].items()))
            st.download_button('Download report',a['memo'],file_name=f"{a['application_id']}_memo.txt",key='dl_'+a['application_id'])
            status=st.selectbox('Officer review status',['Pending review','Verified','Needs clarification'],index=['Pending review','Verified','Needs clarification'].index(a['review_status']),key='status_'+a['application_id'])
            notes=st.text_area('Officer notes',a['review_notes'],key='notes_'+a['application_id'])
            if st.button('Save review',key='save_'+a['application_id']): save_review(a['application_id'],status,notes); st.success('Review saved.'); st.rerun()
elif st.session_state.page=='ClearFile AI':
    hero('ClearFile Intelligence','An AI assistant for understanding verification evidence and preparing human review.')
    st.info('You can chat generally without an application. Select an application when you want answers grounded in its saved verification evidence.')

    selected = None
    current = None
    if apps:
        ids=[a['application_id'] for a in apps]
        selected=st.selectbox('Choose application context (optional)', ['General chat'] + ids)
        if selected != 'General chat':
            current=get_application(selected)
            if current:
                st.caption(f"Using {selected}: {len(current['documents'])} document(s), {len(current['findings'])} compared field(s), {len(current['anomalies'])} potential mismatch(es).")
    else:
        st.caption('No saved applications yet. You can still ask general questions; create an application to enable evidence-based report explanations.')

    st.markdown('#### Ask ClearFile anything')
    st.caption('Type naturally. Ask general questions or ask about the selected application. You do not need to choose a suggested question.')

    # Keep a real multi-turn conversation for each application context.
    chat_key = 'chat_history_' + (selected or 'general').replace('-', '_').replace(' ', '_')
    if chat_key not in st.session_state:
        st.session_state[chat_key] = []

    clear_col, status_col = st.columns([1, 4])
    with clear_col:
        if st.button('Clear chat', key='clear_ai_chat'):
            st.session_state[chat_key] = []
            st.rerun()
    with status_col:
        st.caption('Talk naturally. You can ask follow-up questions without repeating the context.')

    for role, msg in st.session_state[chat_key]:
        with st.chat_message(role):
            st.markdown(msg)

    # Use a visible form-based composer instead of Streamlit's bottom-pinned chat_input.
    # This keeps the message box visible in the ClearFile page on different Streamlit layouts.
    with st.form(key='clearfile_message_form', clear_on_submit=True):
        input_col, send_col = st.columns([8, 1])
        with input_col:
            typed_message = st.text_input(
                'Your message',
                placeholder='Type your question here…',
                label_visibility='collapsed',
                key='clearfile_message_text'
            )
        with send_col:
            send_message = st.form_submit_button('Send', use_container_width=True, type='primary')

    prompt = typed_message.strip() if send_message and typed_message.strip() else None
    if not prompt and st.session_state.get('pending_clearfile_prompt'):
        prompt = st.session_state.pop('pending_clearfile_prompt')

    if prompt:
        st.session_state[chat_key].append(('user', prompt))
        with st.chat_message('user'):
            st.markdown(prompt)

        api_key = os.getenv('GEMINI_API_KEY', '').strip()
        if not api_key or api_key == 'your_gemini_api_key_here':
            answer = 'I’m ready to chat, but the Gemini API key is not configured yet. Add your private GEMINI_API_KEY to the project .env file and restart ClearFile.'
        else:
            try:
                from google import genai
                from google.genai import types

                client = genai.Client(api_key=api_key)
                configured_model = os.getenv('GEMINI_MODEL', '').strip().strip('"\'').replace('\r', '').replace('\n', '').strip()
                if configured_model.startswith('models/'):
                    configured_model = configured_model.split('/', 1)[1]

                # Discover models actually available to this API key instead of guessing model IDs.
                available_models = st.session_state.get('_clearfile_available_models')
                if available_models is None:
                    available_models = []
                    try:
                        for model_info in client.models.list():
                            model_name = getattr(model_info, 'name', '') or ''
                            model_name = model_name.replace('models/', '').strip()
                            actions = getattr(model_info, 'supported_actions', []) or []
                            if model_name and (not actions or 'generateContent' in actions):
                                available_models.append(model_name)
                    except Exception:
                        available_models = []
                    st.session_state['_clearfile_available_models'] = available_models

                model_candidates = []
                if configured_model:
                    model_candidates.append(configured_model)
                # Prefer available Flash models; this avoids repeated calls to invalid guessed IDs.
                flash_models = sorted([m for m in available_models if 'flash' in m.lower()], key=lambda m: ('lite' not in m.lower(), m))
                for candidate in flash_models:
                    if candidate not in model_candidates:
                        model_candidates.append(candidate)
                if not model_candidates:
                    model_candidates = [configured_model or 'gemini-2.5-flash']
                model_candidates = model_candidates[:2]

                system_instruction = (
                    'You are ClearFile AI, a warm, natural, conversational assistant. '
                    'Speak like a helpful person, not like a formal report generator. '
                    'Reply to greetings naturally. Answer the actual question first. '
                    'Keep ordinary replies short and clear; explain more only when asked. '
                    'Mirror the user’s language: if they write in Tamil or Tanglish, reply in simple Tamil/Tanglish; '
                    'if they write in English, reply in clear, friendly English. '
                    'Ask one short clarifying question only when genuinely needed. '
                    'Remember and use the conversation history; understand short follow-ups like "why?", "how?", '
                    '"that one", and "explain more" from earlier turns. Do not restart the conversation each turn. '
                    'You may answer general questions too. For applicant-specific questions, use only the supplied '
                    'saved application evidence. Never invent facts, claim to have read unavailable documents, '
                    'infer fraud, or automatically approve/reject an applicant. Distinguish Match, Mismatch, and '
                    'Not Available accurately. Mask tax IDs and account numbers. Recommend human review for decisions.'
                )

                context_text = (
                    'No application is selected. Answer general questions normally. '
                    'Do not claim that you have checked any applicant documents.'
                )
                if current:
                    evidence = {
                        'application_id': selected,
                        'extracted_fields': current['extracted'],
                        'comparison_findings': current['findings'],
                        'potential_anomalies': current['anomalies'],
                        'review_status': current['review_status']
                    }
                    context_text = (
                        'SELECTED APPLICATION EVIDENCE — use this as the only source for '
                        'applicant-specific facts.\n' + str(evidence)
                    )

                history_items = []
                for old_role, old_message in st.session_state[chat_key][:-1][-12:]:
                    history_items.append(types.Content(
                        role='user' if old_role == 'user' else 'model',
                        parts=[types.Part(text=old_message)]
                    ))

                answer = None
                last_error = None
                for model_name in model_candidates:
                    try:
                        chat = client.chats.create(
                            model=model_name,
                            history=history_items,
                            config=types.GenerateContentConfig(
                                system_instruction=system_instruction + '\n\n' + context_text,
                                temperature=0.65, max_output_tokens=900
                            )
                        )
                        response = chat.send_message(prompt)
                        answer = (response.text or '').strip()
                        if answer:
                            break
                        last_error = RuntimeError('The model returned an empty response.')
                    except Exception as model_error:
                        last_error = model_error
                        err = str(model_error).lower()
                        retryable = any(token in err for token in (
                            '404', 'not found', '503', 'unavailable',
                            'high demand', '429', 'resource_exhausted'
                        ))
                        if not retryable:
                            raise

                if not answer:
                    raise last_error or RuntimeError('No Gemini model returned a response.')

            except Exception as e:
                error_text = str(e).lower()
                if any(x in error_text for x in ('401', '403', 'api key', 'permission')):
                    answer = 'I couldn’t connect to Gemini with this API key. Please check that the key in your .env file is active and restart ClearFile.'
                elif any(x in error_text for x in ('429', '503', 'unavailable', 'high demand', 'resource_exhausted')):
                    answer = 'Gemini is busy or the request limit has been reached. Please wait a little and try sending that message again.'
                elif '404' in error_text or 'model' in error_text or 'not found' in error_text:
                    answer = 'I could not find a model available to this API key. Please check the model name in .env or verify the models enabled for this Gemini API key.'
                else:
                    answer = 'I’m having trouble reaching the AI service right now. Please check your internet connection and try again.'
                with st.expander('Technical details (for troubleshooting)'):
                    st.code(str(e)[:1200])

        st.session_state[chat_key].append(('assistant', answer))
        with st.chat_message('assistant'):
            st.markdown(answer)
    st.caption('Privacy note: when Gemini is enabled, your question and, if selected, the saved application context are sent to Google Gemini. Use fictional data for demonstrations.')
elif st.session_state.page=='About':
    hero('A clearer way to verify documents.','A multi-agent applicant document verification prototype built to support careful human review.')
    cols=st.columns(4)
    agents=[('01','Document Extractor','Reads supported applicant details from uploaded files.'),('02','Consistency Checker','Compares common fields across documents.'),('03','Anomaly Analyst','Highlights conflicting values for review.'),('04','Memo Writer','Summarizes evidence in a verification memo.')]
    for col,(n,title,desc) in zip(cols,agents):
        with col: st.markdown(f'<div class="card about-agent-card"><div style="color:{GOLD};font-weight:700">AGENT {n}</div><h3 style="color:{BURGUNDY}">{title}</h3><p>{desc}</p></div>',unsafe_allow_html=True)
    st.subheader('Technology'); st.write('Python · Streamlit · SQLite · Pandas · Plotly · PyMuPDF · Tesseract OCR · Google Gemini API')
    st.subheader('Responsible use'); st.write('ClearFile is a student prototype, not a production banking system. It supports human decision-making and does not automatically approve or reject applications. Review original documents before making decisions.')

st.markdown('<hr>',unsafe_allow_html=True)
st.markdown(f'<div style="text-align:center;color:{MUTED};font-size:12px;padding:8px">ClearFile · Applicant Document Verification · Human review required</div>',unsafe_allow_html=True)
