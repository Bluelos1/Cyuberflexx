from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
import httpx, re, html
from datetime import datetime
from urllib.parse import quote_plus
from typing import List

PS = "https://psbdmp.ws/api/v3/search/{}"

class Result(BaseModel):
    snippet: str
    link: str
    date: datetime

def cut(text: str, phrase: str, w: int = 40) -> str:
    text = re.sub(r"\s+", " ", text.strip())
    if not text:
        return ""
    i = text.lower().find(phrase.lower())
    frag = text[: 2 * w] if i == -1 else text[max(0, i - w): i + len(phrase) + w]
    return html.unescape(frag)

app = FastAPI()

@app.get("/search", response_model=List[Result])
async def search(q: str = Query(..., min_length=1, max_length=64)) -> List[Result]:
    try:
        async with httpx.AsyncClient(timeout=15) as c:
            items = (await c.get(PS.format(quote_plus(q)))).json()
    except Exception as e:
        raise HTTPException(502, str(e))

    items.sort(key=lambda x: x.get("time", ""), reverse=True)
    out: list[Result] = []
    for it in items:
        k = it.get("id")
        if not k:
            continue
        try:
            dt = datetime.strptime(it.get("time", "1970-01-01 00:00"), "%Y-%m-%d %H:%M")
        except ValueError:
            dt = datetime.utcnow()
        out.append(Result(snippet=cut(it.get("text", ""), q), link=f"https://pastebin.com/{k}", date=dt))
    return out

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
