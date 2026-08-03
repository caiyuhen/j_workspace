from fastapi import FastAPI

app = FastAPI(title="MedA Agent Core")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "meda-agent-core"}
