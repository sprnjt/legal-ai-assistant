# Agents - Legal Team
import os
import streamlit as st
import asyncio
import tempfile
from agno.agent import Agent
from agno.models.google import Gemini
from agno.models.xai import xAI
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.vectordb.chroma import ChromaDb
from agno.knowledge.knowledge import Knowledge
from agno.knowledge.reader.pdf_reader import PDFReader
from agno.knowledge.chunking.document import DocumentChunking
from agno.knowledge.embedder.google import GeminiEmbedder
from agno.db.json.json_db import JsonDb


# Initialize Streamlit
# Customizing the page title and header
st.set_page_config(page_title="AI Legal Team Agents", page_icon="⚖️", layout="wide")

# Title with emojis for visual appeal
st.markdown("<h1 style='text-align: center; color: #2176ff;'>👨 AI Legal Team Agents</h1>", unsafe_allow_html=True)

# Adding a short, stylish description with a bit of color
st.markdown("""
    <div style='text-align: center; font-size: 18px; color: #33a1fd;'>
        Upload your legal document and let the <b>AI LegalAdvisor</b>, <b>AI ContractsAnalyst</b>, 
        <b>AI LegalStrategist</b>, and <b>AI Team Lead</b> do the work for you. You can also ask 
        questions in between for enhanced collaboration and insights.
    </div>
""", unsafe_allow_html=True)

# Initialize session state
if "vector_db" not in st.session_state:
    # Ensure persistent storage directory exists for ChromaDB
    os.makedirs("tmp/chromadb", exist_ok=True)
    try:
        st.session_state.vector_db = ChromaDb(
            collection="law",
            path="tmp/chromadb",
            persistent_client=True,
            embedder=GeminiEmbedder(),
            tenant="default",
            database="default",
        )
        # Touch client to trigger initialization early
        _ = st.session_state.vector_db.client
    except Exception:
        # Fallback to ephemeral client to keep the app usable
        st.session_state.vector_db = ChromaDb(
            collection="law",
            persistent_client=False,
            embedder=GeminiEmbedder(),
        )

if "knowledge_base" not in st.session_state:
    st.session_state.knowledge_base = None

if "processed_files" not in st.session_state:
    st.session_state.processed_files = set()

# Initialize chat history
if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = []

# Sidebar for API Config & File Upload
with st.sidebar:

    # Set a title for the sidebar
    st.header("Configuration")

    # Add a text input to the sidebar for the API key
    api_key = st.sidebar.text_input(
        label="Enter your API Key:",
        type="password",  # Masks the input for security
        help="Your personal API key for accessing the service."
    )

    # Set API Key
    if api_key:
        os.environ["GOOGLE_API_KEY"] = api_key 
        st.success("API key entered successfully!")

    # Proceed with using the API key
    else:
        st.warning("Please enter your API key to proceed.")


    chunk_size_in = st.sidebar.number_input("Chunk Size", min_value=1, max_value=5000, value=1000)
    overlap_in = st.sidebar.number_input("Overlap", min_value=1, max_value=1000, value=200)

    st.header("📄 Document Upload")

    uploaded_file = st.file_uploader("Upload a Legal Document (PDF)", type=["pdf"])
    
    if uploaded_file:
        if uploaded_file.name not in st.session_state.processed_files:
            with st.spinner("Processing document..."):
                try:
                    # Save to a temp file
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                        temp_file.write(uploaded_file.getvalue())
                        temp_path = temp_file.name
                    
                    # Process the uploaded document into knowledge base
                    # Ensure contents DB directory exists
                    os.makedirs("tmp/contents_db", exist_ok=True)
                    try:
                        # Prefer a stable name for the knowledge base to enable contents DB
                        st.session_state.knowledge_base = Knowledge(
                            vector_db=st.session_state.vector_db,
                            name="law",
                            contents_db=JsonDb(db_path="tmp/contents_db", knowledge_table="law")
                        )
                    except TypeError:
                        # Fallback for older/newer API variants
                        try:
                            st.session_state.knowledge_base = Knowledge(
                                vector_db=st.session_state.vector_db,
                                knowledge_base="law",
                                contents_db=JsonDb(db_path="tmp/contents_db", knowledge_table="law")
                            )
                        except TypeError:
                            st.session_state.knowledge_base = Knowledge(
                                vector_db=st.session_state.vector_db,
                                contents_db=JsonDb(db_path="tmp/contents_db", knowledge_table="law")
                            )
                    
                    # Add content to knowledge base
                    st.session_state.knowledge_base.add_content(
                        reader=PDFReader(
                            chunking_strategy=DocumentChunking(chunk_size=chunk_size_in, overlap=overlap_in)
                        ),
                        path=temp_path
                    )

                    # Verify content was added
                    try:
                        # Try to search the knowledge base to verify content
                        search_results = st.session_state.knowledge_base.search("contract")
                        if search_results:
                            st.success(f"✅ Document processed and stored in knowledge base! Found {len(search_results)} chunks.")
                        else:
                            st.warning("⚠️ Document uploaded but no content found in search. Check if PDF is readable.")
                    except Exception as search_error:
                        st.success("✅ Document processed and stored in knowledge base!")
                        st.info(f"Note: Could not verify content ({search_error})")

                    st.session_state.processed_files.add(uploaded_file.name)
                    
                    # Clean up temp file
                    try:
                        os.unlink(temp_path)
                    except:
                        pass

                except Exception as e:
                    st.error(f"Error processing document: {e}")
                    
# Initialize AI Agents (After Document Upload)
if st.session_state.knowledge_base:
    legal_researcher = Agent(
        name="LegalAdvisor",
        model=Gemini(id="gemini-2.5-flash"),
        knowledge=st.session_state.knowledge_base,
        search_knowledge=True,
        description="Legal Researcher AI - Finds and cites relevant legal cases, regulations, and precedents using all data in the knowledge base.",
        instructions=[
        "Act like Harvey Specter — extremely sharp, confident, and strategic lawyer.",
        "You have access to a knowledge base containing uploaded legal documents. ALWAYS search this knowledge base first before responding.",
        "Extract and explain only the most relevant legal cases, statutes, and precedents from the uploaded documents. Focus on what actually impacts the matter.",
        "Be concise, structured, and high-value — avoid fluff or repetition.",
        "Highlight critical points that must not be missed.",
        "Summarize in a way that is easy to read, clear, and actionable, without losing essential detail.",
        "Always cite sources and document references clearly.",
        "If needed, use DuckDuckGo for additional legal references."
        ], 
        tools=[DuckDuckGoTools()],
        markdown=True
    )

    contract_analyst = Agent(
        name="ContractAnalyst",
        model=Gemini(id="gemini-2.5-flash"),
        knowledge=st.session_state.knowledge_base,
        search_knowledge=True,
        description="Contract Analyst AI - Reviews contracts and identifies key clauses, risks, and obligations using the full document data.",
        instructions=[
            "You have access to uploaded legal documents in the knowledge base. ALWAYS search this knowledge base to find the contract content.",
            "Analyze the contract like a top corporate lawyer — focus on key clauses, obligations, and risks that truly matter.",
            "Identify ambiguities, hidden obligations, or potential pitfalls from the actual contract text.",
            "Keep analysis concise, structured, and highly actionable.",
            "Highlight critical sections clearly — nothing essential should be lost.",
            "Use bullet points or structured format for readability, but ensure it's meaningful, not just superficial."
        ],
        markdown=True
    )

    legal_strategist = Agent(
        name="LegalStrategist",
        model=Gemini(id="gemini-2.5-flash"),
        knowledge=st.session_state.knowledge_base,
        search_knowledge=True,
        description="Legal Strategist AI - Provides comprehensive risk assessment and strategic recommendations based on all the available data from the contract.",
        instructions=[
            "You have access to uploaded legal documents in the knowledge base. ALWAYS search this knowledge base to find the contract content.",
            "Act like a strategic, top-of-class lawyer analyzing a contract for risks, opportunities, and leverage points.",
            "Prioritize the most important legal risks and potential gains from the actual contract text.",
            "Provide concise, actionable recommendations that a lawyer would actually use to make decisions.",
            "Highlight critical points clearly and avoid unnecessary details.",
            "Ensure recommendations are legally sound and aligned with best practices."
        ],
        markdown=True
    )

    team_lead = Agent(
        name="teamlead",
        model=Gemini(id="gemini-2.5-flash"),
        description="Team Lead AI - Integrates responses from the Legal Researcher, Contract Analyst, and Legal Strategist into a comprehensive report.",
        instructions=[
        "Filter and prioritize the responses of the LegalAdvisor, ContractAnalyst, and LegalStrategist.",
        "Do not include every point they mention. Summarize only the most critical insights.",
        "Structure the output as: Executive Summary, Critical Clauses & Obligations, Risks & Weak Points, Recommendations.",
        "Write in the tone of a top lawyer: sharp, concise, and meaningful. No fluff, no robotic repetition."

        ],
        markdown=True
    )
    def get_team_response(query):
        # First check if knowledge base has content
        try:
            test_search = st.session_state.knowledge_base.search("contract agreement terms")
            if not test_search:
                return "No document content found in knowledge base. Please upload a PDF document first."
            
            # Debug: Show what was found
            st.info(f"🔍 Knowledge base search found {len(test_search)} results. First result preview: {str(test_search[0])[:200]}...")
            
        except Exception as e:
            return f"Error accessing knowledge base: {e}. Please ensure document was uploaded successfully."
        
        research_response = legal_researcher.run(query)
        contract_response = contract_analyst.run(query)
        strategy_response = legal_strategist.run(query)

        final_response = team_lead.run(
        f"Summarize and integrate the following insights gathered using the full contract data:\n\n"
        f"Legal Researcher:\n{research_response}\n\n"
        f"Contract Analyst:\n{contract_response}\n\n"
        f"Legal Strategist:\n{strategy_response}\n\n"
        "Provide a structured legal analysis report that includes key terms, obligations, risks, and recommendations, with references to the document."
        )
        return final_response

# Analysis Options
if st.session_state.knowledge_base:
    st.header("🔍 Select Analysis Type")
    analysis_type = st.selectbox(
        "Choose Analysis Type:",
        ["Contract Review", "Legal Research", "Risk Assessment", "Compliance Check", "Custom Query"]
    )

    query = None
    if analysis_type == "Custom Query":
        st.subheader("💬 Custom Query Chat")

        # Clear chat button
        if st.button("Clear chat"):
            st.session_state.chat_messages = []
            st.rerun()

        # Render history
        for message in st.session_state.chat_messages:
            with st.chat_message(message.get("role", "assistant")):
                st.markdown(message.get("content", ""))

        # Input and response
        user_prompt = st.chat_input("Ask a legal question about your uploaded document...")
        if user_prompt:
            st.session_state.chat_messages.append({"role": "user", "content": user_prompt})
            with st.spinner("Answering..."):
                directive = (
                    "Answer the user's question strictly and concisely based on the uploaded document. "
                    "Provide only the direct answer in 3-5 sentences and avoid a long legal analysis. "
                    "Cite document sections briefly if essential."
                )
                chat_response = legal_researcher.run(f"{directive}\n\nQuestion: {user_prompt}")
            assistant_text = getattr(chat_response, "content", None) or str(chat_response)
            st.session_state.chat_messages.append({"role": "assistant", "content": assistant_text})
            with st.chat_message("assistant"):
                st.markdown(assistant_text)
    else:
        predefined_queries = {
            "Contract Review": (
                "SEARCH the knowledge base for the uploaded contract document. Analyze the contract content you find and identify key terms, obligations, and risks in detail. "
                "Provide specific quotes from the contract text to support your analysis."
            ),
            "Legal Research": (
                "SEARCH the knowledge base for the uploaded legal document. Using the document content you find, identify relevant legal cases and precedents. "
                "Provide detailed references and sources from the document."
            ),
            "Risk Assessment": (
                "SEARCH the knowledge base for the uploaded document content. Extract the contract text and identify potential legal risks. "
                "Detail specific risk areas and reference exact sections or clauses from the document."
            ),
            "Compliance Check": (
                "SEARCH the knowledge base for the uploaded contract document. Evaluate the contract content for compliance with legal regulations. "
                "Highlight any areas of concern and suggest corrective actions, citing specific contract provisions."
            )
        }
        query = predefined_queries[analysis_type]

    # if st.button("Analyze"):
    #     if not query:
    #         st.warning("Please enter a query.")
    #     else:
    #         with st.spinner("Analyzing..."):
    #             response = get_team_response(query)

    #             # Display results using Tabs
    #             tabs = st.tabs(["Analysis", "Key Points", "Recommendations"])

    #             with tabs[0]:
    #                 st.subheader("📑 Detailed Analysis")
    #                 st.markdown(response.content if response.content else "No response generated.")

    #             with tabs[1]:
    #                 st.subheader("📌 Key Points Summary")
    #                 key_points_response = team_lead.run(
    #                     f"Summarize the key legal points from this analysis:\n{response.content}"
    #                 )
    #                 st.markdown(key_points_response.content if key_points_response.content else "No summary generated.")

    #             with tabs[2]:
    #                 st.subheader("📋 Recommendations")
    #                 recommendations_response = team_lead.run(
    #                     f"Provide specific legal recommendations based on this analysis:\n{response.content}"
    #                 )
    #                 st.markdown(recommendations_response.content if recommendations_response.content else "No recommendations generated.")
    if st.button("Analyze"):
        if not query:
            st.warning("Please enter a query.")
        else:
            with st.spinner("Analyzing..."):
                response = get_team_response(query)

        if response:
            # Handle both string responses and object responses with .content attribute
            response_content = getattr(response, 'content', None) or str(response)
            if response_content:
                # ----------------------------
                # Party Perspective Tabs
                # ----------------------------
                party_tabs = st.tabs(["👤 Receiving Party (Client)", "🏢 Issuing Party"])

                with party_tabs[0]:
                    st.subheader("📑 Receiving Party (Client) Perspective")
                    client_view = team_lead.run(
                        f"Rewrite this analysis focusing only on the receiving party (client)'s perspective:\n{response_content}"
                    )
                    client_view_content = getattr(client_view, 'content', None) or str(client_view)
                    st.markdown(client_view_content or "No client-specific analysis.")

                with party_tabs[1]:
                    st.subheader("📑 Issuing Party Perspective")
                    issuing_view = team_lead.run(
                        f"Rewrite this analysis focusing only on the issuing party's perspective:\n{response_content}"
                    )
                    issuing_view_content = getattr(issuing_view, 'content', None) or str(issuing_view)
                    st.markdown(issuing_view_content or "No issuing-party-specific analysis.")

                # ----------------------------
                # Section Tabs (Analysis / Key Points / Recommendations)
                # ----------------------------
                tabs = st.tabs(["📑 Analysis", "📌 Key Points", "📋 Recommendations"])

                # --- Analysis Section ---
                with tabs[0]:
                    with st.expander("🔍 Executive Summary", expanded=True):
                        st.markdown(response_content or "No response generated.")

                    with st.expander("📜 Critical Clauses"):
                        clauses = team_lead.run(
                            f"Extract the most critical clauses from this legal document. "
                            f"Categorize them into High Risk, Medium Risk, and Low Risk. Format as bullet points:\n{response_content}"
                        )
                        clauses_content = getattr(clauses, 'content', None) or str(clauses)
                        if clauses_content:
                            for line in clauses_content.split("\n"):
                                if "High Risk" in line:
                                    st.markdown(
                                        f"<div style='padding:10px; border-radius:8px; background:#fee2e2; border-left:5px solid #dc2626; margin:5px 0;'>"
                                        f"🔴 {line}</div>", unsafe_allow_html=True
                                    )
                                elif "Medium Risk" in line or "Risk" in line:
                                    st.markdown(
                                        f"<div style='padding:10px; border-radius:8px; background:#fef9c3; border-left:5px solid #ca8a04; margin:5px 0;'>"
                                        f"⚠️ {line}</div>", unsafe_allow_html=True
                                    )
                                elif "Low Risk" in line or "Safe" in line:
                                    st.markdown(
                                        f"<div style='padding:10px; border-radius:8px; background:#dcfce7; border-left:5px solid #16a34a; margin:5px 0;'>"
                                        f"✅ {line}</div>", unsafe_allow_html=True
                                    )
                                else:
                                    st.markdown(line)
                        else:
                            st.markdown("No critical clauses identified.")

                # --- Key Points Section ---
                with tabs[1]:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("### ✅ Strengths")
                        strengths = team_lead.run(
                            f"List only the strengths from this analysis:\n{response_content}"
                        )
                        strengths_content = getattr(strengths, 'content', None) or str(strengths)
                        if strengths_content:
                            for s in strengths_content.split("\n"):
                                if s.strip():
                                    st.markdown(f"✅ {s}")
                        else:
                            st.markdown("No strengths found.")

                    with col2:
                        st.markdown("### ⚠️ Weaknesses")
                        weaknesses = team_lead.run(
                            f"List only the weaknesses from this analysis:\n{response_content}"
                        )
                        weaknesses_content = getattr(weaknesses, 'content', None) or str(weaknesses)
                        if weaknesses_content:
                            for w in weaknesses_content.split("\n"):
                                if w.strip():
                                    st.markdown(f"⚠️ {w}")
                        else:
                            st.markdown("No weaknesses found.")

                # --- Recommendations Section ---
                with tabs[2]:
                    st.markdown("### 🎯 Actionable Recommendations")
                    recommendations_response = team_lead.run(
                        f"Provide specific, actionable legal recommendations in bullet points based on this analysis:\n{response_content}"
                    )
                    recommendations_content = getattr(recommendations_response, 'content', None) or str(recommendations_response)
                    if recommendations_content:
                        for rec in recommendations_content.split("\n"):
                            if rec.strip():
                                st.markdown(f"💡 {rec}")
                    else:
                        st.markdown("No recommendations generated.")

