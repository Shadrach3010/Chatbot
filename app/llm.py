from typing import Tuple
from app.config import get_settigs
from openai import OpenAI

settings = get_settigs()
client = OpenAI(api_key=settings.OPENAI_API_KEY)

def ask_llm(user_text: str, system_text: str | None = None) -> Tuple[str, dict]:
     """
    Sends user_text to OpenAI and returns (reply, usage_dict).
    usage_dict may include prompt_tokens, completion_tokens, total_tokens.
    """
     
     system_msg = system_text or "You are a helpful, concise assistant."
     resp = client.chat.completions.create(
          model=settings.OPENAI_MODEL,
          messages=[
               {"role": "system", "content": system_msg},
               {"role": "user", "content": user_text},
          ],
          temperature=0.7,
          max_tokens=400,
          
     )
     reply = resp.choices[0].message.content
     usage =  getattr(resp, "usage", None)
     usage_dict = {
          "prompt_tokens": getattr(usage, "prompt_tokens", None),
          "completion_tokens": getattr(usage, "completion_tokens", None),
          "total_tokens": getattr(usage, "total_tokens", None),
     }
     return reply, usage_dict
