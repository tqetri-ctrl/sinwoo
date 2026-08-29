"""
Google Gemini API 연동 서비스 (Search Grounding, 멀티모달 파일 분석, 블로그 생성)
"""

import os
import re
from prompts.blog_templates import TONE_PRESETS, SYSTEM_PROMPT_TEMPLATE
from services.file_parser import extract_text_from_file

DEFAULT_MODEL = "gemini-3.5-flash"
SECTION_TITLES = "[제목 후보]"
SECTION_BODY = "[블로그 본문]"
SECTION_TAGS = "[네이버 블로그 추천 태그]"
DEFAULT_FALLBACK_TITLE = "공인중개사가 전하는 부동산 핵심 소식과 현황 브리핑"
DEFAULT_FALLBACK_TAGS = ["#부동산", "#공인중개사", "#부동산소식", "#부동산현황", "#부동산정보"]


def _format_emoji_instruction(density: str) -> str:
    """이모지 밀도 옵션 문구 반환"""
    if density == "high":
        return "\n- 이모지 강도: 이모지와 이모티콘을 풍성하고 다채롭게 적극 사용하여 활기찬 느낌을 강조하세요."
    if density == "low":
        return "\n- 이모지 강도: 이모지는 소제목이나 핵심 포인트에만 절제하여 최소한으로 깔끔하게 사용하세요."
    return "\n- 이모지 강도: 각 문단과 포인트마다 읽기 좋고 자연스러운 수준으로 이모지를 배치하세요."


def _format_office_info(config: dict) -> str:
    """중개사무소 서명 및 안내 문구 조립"""
    if not config.get("include_office_info", True):
        return "포스팅 마지막 맺음말에 독자의 공감과 댓글/이웃 추가를 유도하는 따뜻한 마무리 인사를 작성하세요."

    field_map = [
        ("office_name", "- 중개사무소 상호: "),
        ("agent_name", "- 대표/담당 공인중개사: "),
        ("office_phone", "- 상담 및 문의 전화: "),
        ("office_location", "- 사무소 위치/주소: "),
        ("custom_signature", "- 추가 서명/안내 문구: "),
    ]
    parts = [f"{prefix}{config[key]}" for key, prefix in field_map if config.get(key)]

    if not parts:
        return "포스팅 마지막 맺음말에 독자의 공감과 댓글/이웃 추가를 유도하는 따뜻한 마무리 인사를 작성하세요."

    return "포스팅 마지막 맺음말 부분에 아래의 공인중개사 정보를 신뢰감 있고 친절하게 안내하며 독자의 상담/문의를 유도하세요:\n" + "\n".join(parts)


def _extract_titles(text: str) -> list:
    """생성된 텍스트에서 제목 후보 리스트 추출"""
    if SECTION_TITLES not in text:
        return [DEFAULT_FALLBACK_TITLE]

    part = text.split(SECTION_TITLES, 1)[1]
    if SECTION_BODY in part:
        part = part.split(SECTION_BODY, 1)[0]

    titles = []
    for raw_line in part.strip().splitlines():
        line = raw_line.strip()
        if not line:
            continue
        cleaned = re.sub(r'^\d+[\.\)\s\-]+', '', line).replace('**', '').replace('"', '').strip()
        if cleaned:
            titles.append(cleaned)

    return titles or [DEFAULT_FALLBACK_TITLE]


def _extract_tags(text: str) -> list:
    """생성된 텍스트에서 추천 태그 추출"""
    if SECTION_TAGS not in text:
        return DEFAULT_FALLBACK_TAGS

    block = text.split(SECTION_TAGS, 1)[1].strip()
    found = re.findall(r'#([^\s#]+)', block)
    if found:
        return [f"#{t}" for t in found]

    tags = [t.strip() for t in block.split() if t.strip()]
    return tags or DEFAULT_FALLBACK_TAGS


def _extract_body(text: str) -> str:
    """생성된 텍스트에서 본문 마크다운 추출"""
    if SECTION_BODY in text:
        body_part = text.split(SECTION_BODY, 1)[1]
        if SECTION_TAGS in body_part:
            body_part = body_part.split(SECTION_TAGS, 1)[0]
        return body_part.strip()

    cleaned = text
    if SECTION_TITLES in cleaned:
        parts = cleaned.split(SECTION_TITLES, 1)
        if len(parts) > 1:
            cleaned = parts[1]
    return cleaned.strip()


class GeminiBlogService:
    def __init__(self, api_key: str = "", model_name: str = DEFAULT_MODEL):
        self.api_key = api_key
        self.model_name = self._sanitize_model_name(model_name)

    def _sanitize_model_name(self, model_name: str) -> str:
        """모델명 정리 및 기본값 폴백"""
        if not model_name or "2.5" in model_name:
            return DEFAULT_MODEL
        return model_name

    def set_api_key(self, api_key: str):
        self.api_key = api_key

    def set_model(self, model_name: str):
        self.model_name = self._sanitize_model_name(model_name)

    def _build_system_prompt(self, tone_key: str, config: dict) -> str:
        """선택된 톤앤매너 및 사무소 정보로 시스템 프롬프트 조립"""
        tone_info = TONE_PRESETS.get(tone_key, TONE_PRESETS["neighbor"])
        tone_instruction = tone_info["instruction"] + _format_emoji_instruction(config.get("emoji_density", "normal"))
        office_instruction = _format_office_info(config)

        return SYSTEM_PROMPT_TEMPLATE.format(
            tone_instruction=tone_instruction,
            office_info_instruction=office_instruction
        )

    def _prepare_user_content(self, mode: str, topic: str, file_path: str = None):
        """작성 모드에 따른 사용자 프롬프트 및 파일 데이터 구성"""
        if mode == "file" and file_path:
            file_data = extract_text_from_file(file_path)
            if file_data["type"] == "image":
                mime = "image/jpeg" if file_data["extension"] == ".jpg" else f"image/{file_data['extension'].replace('.', '')}"
                topic_text = topic if topic else "첨부된 자료의 핵심 내용을 분석하여 부동산 브리핑 글을 작성해주세요."
                return [
                    f"다음 제공된 이미지/자료와 요청 주제를 정밀 분석하여 네이버 블로그 글을 작성해주세요.\n\n[요청 주제 및 메모]:\n{topic_text}",
                    {"mime_type": mime, "data": file_data["content"]}
                ]
            
            topic_text = topic if topic else "첨부자료 핵심 요약 및 부동산 분석 브리핑"
            return (
                f"다음 첨부파일({file_data['filename']})의 내용을 꼼꼼히 파악하여 네이버 블로그 글을 작성해주세요.\n\n"
                f"[요청 주제 및 작성 방향]:\n{topic_text}\n\n"
                f"[첨부파일 본문 내용]:\n{file_data['content'][:15000]}"
            )

        if mode == "news":
            return (
                f"최신 인터넷 뉴스 기사, 언론 보도, 부동산 정책 발표 자료를 검색 및 바탕으로 하여 다음 주제에 대한 네이버 블로그 글을 작성해주세요.\n\n"
                f"[작성 주제]: {topic}\n\n"
                f"최신 팩트와 시장 상황, 실제 부동산 거래 및 매수/임차인에게 미치는 영향을 명확히 짚어주세요."
            )

        return f"다음 주제 및 내용으로 네이버 블로그 글을 작성해주세요:\n\n[주제/메모]: {topic}"

    def generate_blog_post(self, mode: str, topic: str, file_path: str = None, tone_key: str = "neighbor", config: dict = None) -> dict:
        """블로그 글 생성 메인 함수"""
        if not self.api_key:
            raise ValueError("Gemini API 키가 설정되지 않았습니다. 상단 'API 키 설정'에서 키를 입력해주세요.")

        cfg = config or {}
        system_instruction = self._build_system_prompt(tone_key, cfg)
        user_content = self._prepare_user_content(mode, topic, file_path)

        raw_text = self._call_gemini_api(system_instruction, user_content, enable_grounding=(mode == "news"))

        return {
            "titles": _extract_titles(raw_text),
            "body": _extract_body(raw_text),
            "tags": _extract_tags(raw_text),
            "raw": raw_text
        }

    def _call_gemini_api(self, system_prompt: str, user_content, enable_grounding: bool = False) -> str:
        """google-genai 최신 SDK 우선 호출, 필요 시 레거시 SDK 폴백"""
        try:
            return self._call_google_genai_sdk(system_prompt, user_content, enable_grounding)
        except Exception as err_sdk1:
            try:
                return self._call_legacy_genai_sdk(system_prompt, user_content)
            except Exception as err_sdk2:
                raise RuntimeError(f"Gemini API 호출 오류:\n1) {err_sdk1}\n2) {err_sdk2}")

    def _call_google_genai_sdk(self, system_prompt: str, user_content, enable_grounding: bool) -> str:
        """최신 google.genai SDK 실행"""
        # pyrefly: ignore [missing-import]
        from google import genai
        # pyrefly: ignore [missing-import]
        from google.genai import types

        client = genai.Client(api_key=self.api_key)
        tools = [types.Tool(google_search=types.GoogleSearch())] if enable_grounding else None
        gen_config = types.GenerateContentConfig(
            system_instruction=system_prompt,
            temperature=0.7,
            tools=tools
        )

        if isinstance(user_content, list):
            contents = [
                user_content[0],
                types.Part.from_bytes(data=user_content[1]["data"], mime_type=user_content[1]["mime_type"])
            ]
        else:
            contents = user_content

        target_model = self.model_name if self.model_name.startswith("gemini-") else DEFAULT_MODEL
        response = client.models.generate_content(
            model=target_model,
            contents=contents,
            config=gen_config
        )

        if response and response.text:
            return response.text
        raise RuntimeError("google.genai SDK에서 텍스트 응답을 받지 못했습니다.")

    def _call_legacy_genai_sdk(self, system_prompt: str, user_content) -> str:
        """레거시 google.generativeai SDK 폴백 실행"""
        # pyrefly: ignore [missing-import]
        import google.generativeai as legacy_genai
        legacy_genai.configure(api_key=self.api_key)

        model = legacy_genai.GenerativeModel(
            model_name=self.model_name if "gemini" in self.model_name else "gemini-1.5-flash",
            generation_config={"temperature": 0.7},
            system_instruction=system_prompt
        )

        if isinstance(user_content, list):
            import io
            # pyrefly: ignore [missing-import]
            from PIL import Image
            img = Image.open(io.BytesIO(user_content[1]["data"]))
            res = model.generate_content([user_content[0], img])
        else:
            res = model.generate_content(user_content)

        if res and res.text:
            return res.text
        raise RuntimeError("레거시 google.generativeai SDK에서 텍스트 응답을 받지 못했습니다.")
