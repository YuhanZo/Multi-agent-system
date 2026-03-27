"""FastAPI server with SSE streaming for company analysis."""
import json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

from app.agent.graph import main_graph

app = FastAPI(title="Research Agent API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Vite dev server
    allow_methods=["*"],
    allow_headers=["*"],
)


class AnalyzeRequest(BaseModel):
    company: str


# Node labels shown to the frontend during streaming
NODE_LABELS = {
    "research:product_researcher": "Researching product...",
    "research:market_researcher":  "Researching market...",
    "research:business_researcher": "Researching business...",
    "research:profile_synthesizer": "Synthesizing company profile...",
    "analysis:extractor":          "Extracting structured data...",
    "analysis:scorer":             "Scoring dimensions...",
    "analysis:advisor":            "Writing investment advice...",
    "analysis:report_generator":   "Generating report...",
    "analysis:evaluator":          "Evaluating report quality...",
}


@app.post("/analyze")
async def analyze(body: AnalyzeRequest):
    async def event_stream():
        async for event in main_graph.astream(
            {"company_name": body.company},
            stream_mode="updates",
        ):
            for node_name, node_output in event.items():
                label = NODE_LABELS.get(node_name, node_name)
                payload = {"node": node_name, "label": label, "data": node_output}
                yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(event_stream(), media_type="text/event-stream")


@app.get("/health")
def health():
    return {"status": "ok"}
