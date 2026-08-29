import io
import os
import re
from prompts.blog_templates import TONE_PRESETS, SYSTEM_PROMPT_TEMPLATE, PROPERTY_PROMPT_TEMPLATE
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

    return "포스팅 마지막 맺음말 부분에 아래의 공인중개사 정보를 신뢰감 있고 친절하게 안내하며 독자의 상담/방문 예약을 유도하세요:\n" + "\n".join(parts)


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


def _get_image_mime(extension: str) -> str:
    ext = extension.lower().replace(".", "")
    if ext in ["jpg", "jpeg"]:
        return "image/jpeg"
    if ext == "png":
        return "image/png"
    if ext == "webp":
        return "image/webp"
    return f"image/{ext}"


def _extract_images(file_paths: list) -> list:
    """파일 목록에서 이미지 데이터 추출"""
    image_parts = []
    for path in file_paths:
        if not os.path.exists(path):
            continue
        try:
            file_data = extract_text_from_file(path)
            if file_data["type"] == "image":
                mime = _get_image_mime(file_data["extension"])
                image_parts.append({"mime_type": mime, "data": file_data["content"], "name": file_data["filename"]})
        except Exception:
            continue
    return image_parts


def _prepare_property_content(property_info: dict, topic: str, file_paths: list):
    """매물 소개 모드 프롬프트 조립"""
    p_info = property_info or {}
    deal_type = p_info.get("deal_type", "매매/전세/월세")
    p_type = p_info.get("property_type", "부동산 매물")
    loc = p_info.get("location", "위치 미지정")
    price = p_info.get("price", "협의 가능")
    area = p_info.get("area_structure", "상세 면적 및 구조")
    features = p_info.get("features", "")
    memo = p_info.get("memo", topic)

    prompt_lines = [
        "다음 제공된 부동산 매물 스펙과 첨부된 현장 사진들을 면밀히 분석하여, 네이버 블로그에 최적화된 생생한 룸투어 매물 소개 포스팅을 작성해주세요.",
        "",
        "### [등록된 매물 정보]",
        f"- **거래 형태**: {deal_type}",
        f"- **매물 종류**: {p_type}",
        f"- **소재지/위치**: {loc}",
        f"- **가격 조건**: {price}",
        f"- **면적 및 구조/층수**: {area}",
    ]
    if features:
        prompt_lines.append(f"- **핵심 특장점 및 옵션**: {features}")
    if memo:
        prompt_lines.append(f"- **추가 전달 메모**: {memo}")

    image_parts = _extract_images(file_paths)
    if image_parts:
        prompt_lines.append("")
        prompt_lines.append(f"### [현장 사진 안내 (총 {len(image_parts)}장)]")
        prompt_lines.append("첨부된 사진들의 순서(사진 1, 사진 2, ...)를 파악하여, 각 사진에 담긴 공간(외관, 거실, 주방, 룸, 욕실, 뷰 등)의 실제 시각적 장점을 본문 곳곳에 `[📸 사진 1: 거실 - ...]` 형식의 사진 플레이스홀더와 함께 자세히 서술해주세요.")
        return ["\n".join(prompt_lines)] + image_parts

    return "\n".join(prompt_lines)


def _prepare_file_content(file_paths: list, topic: str):
    """일반 문서/첨부파일 모드 프롬프트 조립"""
    image_parts = []
    text_docs = []

    for path in file_paths:
        if not os.path.exists(path):
            continue
        try:
            file_data = extract_text_from_file(path)
            if file_data["type"] == "image":
                mime = _get_image_mime(file_data["extension"])
                image_parts.append({"mime_type": mime, "data": file_data["content"], "name": file_data["filename"]})
            else:
                text_docs.append(f"--- [파일: {file_data['filename']}] ---\n{file_data['content'][:12000]}")
        except Exception as e:
            text_docs.append(f"[파일 {os.path.basename(path)} 읽기 오류: {e}]")

    topic_text = topic if topic else "첨부된 자료의 핵심 내용을 분석하여 네이버 블로그 부동산 브리핑 글을 작성해주세요."
    prompt_header = f"다음 제공된 첨부 자료와 요청 주제를 정밀 분석하여 네이버 블로그 글을 작성해주세요.\n\n[요청 주제 및 메모]:\n{topic_text}"

    if text_docs:
        prompt_header += "\n\n[첨부 문서 본문 내용]:\n" + "\n\n".join(text_docs)

    if image_parts:
        return [prompt_header] + image_parts

    return prompt_header


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

    def _build_system_prompt(self, tone_key: str, config: dict, is_property: bool = False) -> str:
        """선택된 톤앤매너 및 사무소 정보로 시스템 프롬프트 조립"""
        tone_info = TONE_PRESETS.get(tone_key, TONE_PRESETS["neighbor"])
        tone_instruction = tone_info["instruction"] + _format_emoji_instruction(config.get("emoji_density", "normal"))
        office_instruction = _format_office_info(config)

        template = PROPERTY_PROMPT_TEMPLATE if is_property else SYSTEM_PROMPT_TEMPLATE
        return template.format(
            tone_instruction=tone_instruction,
            office_info_instruction=office_instruction
        )

    def _prepare_user_content(self, mode: str, topic: str = "", file_paths: list = None, property_info: dict = None):
        """작성 모드에 따른 사용자 프롬프트 및 다중 파일/이미지 데이터 구성"""
        file_paths = file_paths or []

        if mode == "property":
            return _prepare_property_content(property_info, topic, file_paths)

        if mode == "file" and file_paths:
            return _prepare_file_content(file_paths, topic)

        if mode == "news":
            return (
                f"최신 인터넷 뉴스 기사, 언론 보도, 부동산 정책 발표 자료를 검색 및 바탕으로 하여 다음 주제에 대한 네이버 블로그 글을 작성해주세요.\n\n"
                f"[작성 주제]: {topic}\n\n"
                f"최신 팩트와 시장 상황, 실제 부동산 거래 및 매수/임차인에게 미치는 영향을 명확히 짚어주세요."
            )

        return f"다음 주제 및 내용으로 네이버 블로그 글을 작성해주세요:\n\n[주제/메모]: {topic}"

    def generate_blog_post(
        self,
        mode: str,
        topic: str = "",
        file_paths: list = None,
        file_path: str = None,
        property_info: dict = None,
        tone_key: str = "neighbor",
        config: dict = None
    ) -> dict:
        """블로그 글 생성 메인 함수"""
        if not self.api_key:
            raise ValueError("Gemini API 키가 설정되지 않았습니다. 상단 '환경 설정'에서 키를 입력해주세요.")

        # 단일 file_path 지원 호환성 처리
        paths = list(file_paths) if file_paths else []
        if file_path and file_path not in paths:
            paths.insert(0, file_path)

        cfg = config or {}
        is_property_mode = (mode == "property")
        system_instruction = self._build_system_prompt(tone_key, cfg, is_property=is_property_mode)
        user_content = self._prepare_user_content(mode, topic=topic, file_paths=paths, property_info=property_info)

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
            # 첫 번째는 텍스트 프롬프트, 나머지는 이미지 파트들
            contents = [user_content[0]]
            for item in user_content[1:]:
                if isinstance(item, dict) and "data" in item:
                    contents.append(types.Part.from_bytes(data=item["data"], mime_type=item["mime_type"]))
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
            # pyrefly: ignore [missing-import]
            from PIL import Image
            contents = [user_content[0]]
            for item in user_content[1:]:
                if isinstance(item, dict) and "data" in item:
                    img = Image.open(io.BytesIO(item["data"]))
                    contents.append(img)
            res = model.generate_content(contents)
        else:
            res = model.generate_content(user_content)

        if res and res.text:
            return res.text
        raise RuntimeError("레거시 google.generativeai SDK에서 텍스트 응답을 받지 못했습니다.")

