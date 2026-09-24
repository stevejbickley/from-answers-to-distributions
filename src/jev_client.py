from __future__ import annotations
import os, requests
from dataclasses import dataclass
from typing import Any
from .utils import retry_call

@dataclass
class JevResult:
    probabilities: dict[str, float]
    answer: dict[str, Any]
    model: str | None
    usage: dict[str, Any]
    raw: dict[str, Any]

class JevClient:
    def __init__(self, api_key=None, base_url=None, model=None, timeout=120, retries=6):
        self.api_key = api_key or os.environ.get('TYPESAFE_API_KEY')
        if not self.api_key:
            raise RuntimeError('Set TYPESAFE_API_KEY')
        self.base_url = (base_url or os.getenv('TYPESAFE_BASE_URL','https://api.typesafe.ai')).rstrip('/')
        self.model = model if model is not None else os.getenv('TYPESAFE_MODEL','')
        self.timeout = timeout
        self.retries = retries
    @property
    def headers(self):
        return {'Authorization': f'Bearer {self.api_key}', 'Content-Type':'application/json'}
    def models(self):
        r = requests.get(f'{self.base_url}/v1/models', headers=self.headers, timeout=self.timeout)
        r.raise_for_status(); return r.json()
    def systemone(self, state: str, questions: dict[str, Any]):
        if not self.model:
            available = self.models().get('models', [])
            if not available:
                raise RuntimeError('TypeSafe GET /v1/models returned no available models')
            self.model = available[0]['name']
        payload = {'state': state, 'questions': questions, 'model': self.model}
        def call():
            r = requests.post(f'{self.base_url}/v1/systemone', headers=self.headers, json=payload, timeout=self.timeout)
            r.raise_for_status(); return r.json()
        return retry_call(call, retries=self.retries)
    def choice(self, state: str, question_id: str, instructions: str, criteria: dict[str,str]):
        raw = self.systemone(state, {question_id:{'type':'choice','instructions':instructions,'criteria':criteria}})
        ans = raw['answers'][question_id]
        probs = {str(k): float(v) for k,v in ans['probabilities'].items()}
        s=sum(probs.values())
        if s <= 0: raise RuntimeError('Jev returned non-positive probability mass')
        probs={k:v/s for k,v in probs.items()}
        return JevResult(probs, ans, raw.get('model'), raw.get('usage') or {}, raw)

    def score(self, state: str, question_id: str, instructions: str, criteria: list[str]):
        raw = self.systemone(state, {question_id:{'type':'score','instructions':instructions,'criteria':criteria}})
        ans = raw['answers'][question_id]
        probs = {str(k): float(v) for k,v in ans['probabilities'].items()}
        total=sum(probs.values())
        probs={k:v/total for k,v in probs.items()} if total>0 else probs
        return JevResult(probs, ans, raw.get('model'), raw.get('usage') or {}, raw)

    def noul_batch(self, state: str, questions: dict[str,str]):
        payload = {}
        for qid, instruction in questions.items():
            payload[qid]={'type':'noul','instructions':instruction}
        return self.systemone(state, payload)
