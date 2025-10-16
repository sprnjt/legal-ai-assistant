## AI Legal Team Agents

An interactive Streamlit app that analyzes uploaded legal documents using a team of specialized AI agents (LegalAdvisor, ContractAnalyst, LegalStrategist, and Team Lead). It searches an embedded knowledge base (ChromaDB) built from your PDF and produces concise, actionable insights.

### Key Features
- **Document ingestion**: Upload a PDF; content is chunked and embedded into ChromaDB.
- **Multi‑agent analysis**: Research, contract review, risk assessment, compliance checks.
- **Concise Custom Query**: In the “Custom Query” mode, the agent answers strictly and concisely (3–5 sentences) without long analysis.
- **Structured results**: Executive summary, critical clauses by risk level, strengths, weaknesses, and actionable recommendations.

### Requirements
- Python 3.10+
- A Google Gemini API key (set as `GOOGLE_API_KEY`)

### Setup (Windows PowerShell)
```powershell
1) Create and activate a virtual environment
python -m venv legal-venv
./legal-venv/Scripts/Activate.ps1

2) Install dependencies
pip install -r requirements.txt

3) Use the Google Gemini API key once localhost is live

4) Run the app
streamlit run legal_team.py
```

If PowerShell blocks script execution, run PowerShell as Administrator and temporarily enable scripts:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Usage
1. Start the app: `streamlit run legal_team.py`.
2. Enter your API key in the sidebar when prompted.
3. Upload a legal PDF.
4. Pick an analysis type:
   - **Contract Review / Legal Research / Risk Assessment / Compliance Check**: Click “Analyze” to generate the multi‑agent report with tabs.
   - **Custom Query**: Ask a question about the uploaded document. The agent replies directly and briefly, avoiding long legal analysis.

### Output Overview
- **Analysis** tab: Executive summary; critical clauses highlighted by risk.
- **Key Points** tab: Strengths and weaknesses listed without colored backgrounds.
- **Recommendations** tab: Actionable items listed plainly (no colored backgrounds).

### Project Structure
```
legal-assistant-final/
  ├─ legal_team.py           # Streamlit app
  ├─ requirements.txt        # Python dependencies
  └─ tmp/                    # Local ChromaDB and contents DB storage
```

### Troubleshooting
- Missing `agno.*` imports: Ensure you installed from `requirements.txt` inside the active virtual environment.
- No results after upload: Verify the PDF is text‑extractable (not image‑only) and try again.

### Notes
- The app uses Google Gemini for both embeddings and generation.
- Data is stored locally in `tmp/` for persistence across runs.

Live link:

Project Screenshots:

Main Page:
![main](https://github.com/sprnjt/legal-assistant-final/blob/main/assets/main.png)

After upload of Google Gemini API key and Legal Doc:
![post upload](https://github.com/sprnjt/legal-assistant-final/blob/main/assets/post%20upload.png)

Contract Analysis of Receiving Party(Client):
![receiving party](https://github.com/sprnjt/legal-assistant-final/blob/main/assets/receiving%20party.png)

Contract Analysis of Issuing Party:
![issuing party](https://github.com/sprnjt/legal-assistant-final/blob/main/assets/issuing%20party.png)

Key Points:
![key points](https://github.com/sprnjt/legal-assistant-final/blob/main/assets/key%20points.png)

Actionable Recommendations:
![actionable recommendations](https://github.com/sprnjt/legal-assistant-final/blob/main/assets/recommendations.png)

Custom Query Chat:
![custom query chat](https://github.com/sprnjt/legal-assistant-final/blob/main/assets/custom%20query%20chat.png)