import json
import re
import logging
from openai import OpenAI
from config import OPENAI_API_KEY

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

def summarize_reviews(reviews, sample_size=50):
    """
    리뷰 리스트를 받아서 전체적인 평가 요약을 JSON 형태로 반환
    - positive_negative: 긍정/부정 의견 핵심
    - features: 자주 언급된 특징
    - cautions: 소비자가 주의해야 할 점
    """
    text = "\n".join(reviews[:sample_size])

    prompt = f"""
    다음은 어떤 상품에 대한 리뷰 모음입니다.
    이를 읽고 다음 항목에 따라 요약하세요.
    - positive_negative: 긍정/부정 핵심의견을 통한 전반적인 평가를 구체적으로 해주세요.
    - features: 자주 언급되는 제품의 장점 3가지
    - cautions: 소비자들이 주의해야 할 점 3가지

    리뷰:
    {text}

    반드시 아래 JSON 형식으로만 출력하세요. 다른 설명은 하지 마세요.
    {{
        "positive_negative": "긍/부정 의견 핵심 요약",
        "features": ["특징1", "특징2", "특징3"],
        "cautions": ["주의사항1", "주의사항2" ,"주의사항3"]
    }}
    """

    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful review analysis assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=600
        )
        content = response.choices[0].message.content.strip()

        match = re.search(r"\{.*\}", content, re.S)
        if match:
            content = match.group()

        return json.loads(content)

    except Exception as e:
        logging.error(f"요약 분석 실패: {e}")
        return {
            "positive_negative": "⚠️ 요약 실패",
            "features": [],
            "cautions": []
        }
    
def summarize_size_and_fit(reviews, sample_size=80):
    text = "\n".join(reviews[:sample_size])
    prompt = f"""
    아래는 어떤 신발에 대한 사용자 리뷰입니다. '사이즈 체감/착화감'만 요약하세요.
    - size_summary: 한 문장 요약(예: '정사이즈 경향, 발볼 넓으면 반 사이즈 업 권장')
    - recommendations: 소비자에게 줄 구체 조언 3가지(사이즈 선택, 발볼/발등, 양말 두께/끈 조절 등)
    리뷰:
    {text}
    반드시 아래 JSON만 출력:
    {{
      "size_summary": "문장",
      "recommendations": ["조언1","조언2","조언3"]
    }}
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"You are a concise sizing assistant."},
                      {"role":"user","content":prompt}],
            max_tokens=400
        )
        import json, re
        s = resp.choices[0].message.content.strip()
        m = re.search(r"\{.*\}", s, re.S)
        if m: s = m.group()
        return json.loads(s)
    except Exception:
        return {"size_summary":"요약 실패","recommendations":[]}

def summarize_coordination(reviews, sample_size=80):
    text = "\n".join(reviews[:sample_size])
    prompt = f"""
    아래 리뷰를 바탕으로 '코디/활용'만 요약하세요.
    - coord_summary: 한 문장 요약(예: '캐주얼·데일리에 적합, 슬랙스/데님 매치 좋음')
    - outfit_tips: 코디 팁 3가지(스타일/계절/활동/컬러 등)
    리뷰:
    {text}
    반드시 아래 JSON만 출력:
    {{
      "coord_summary": "문장",
      "outfit_tips": ["팁1","팁2","팁3"]
    }}
    """
    try:
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"You are a styling assistant."},
                      {"role":"user","content":prompt}],
            max_tokens=400
        )
        import json, re
        s = resp.choices[0].message.content.strip()
        m = re.search(r"\{.*\}", s, re.S)
        if m: s = m.group()
        return json.loads(s)
    except Exception:
        return {"coord_summary":"요약 실패","outfit_tips":[]}
