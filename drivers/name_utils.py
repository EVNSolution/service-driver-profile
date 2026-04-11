import re


_NON_HANGUL_PATTERN = re.compile(r"[^가-힣\s]+")
_WHITESPACE_PATTERN = re.compile(r"\s+")


def derive_driver_name_from_external_user_name(external_user_name: str) -> str:
    normalized_external_name = external_user_name.strip()
    hangul_only_name = _WHITESPACE_PATTERN.sub(
        " ",
        _NON_HANGUL_PATTERN.sub(" ", normalized_external_name),
    ).strip()
    return hangul_only_name or normalized_external_name


def should_normalize_driver_name(current_name: str, external_user_name: str) -> bool:
    normalized_current_name = current_name.strip()
    normalized_external_name = external_user_name.strip()
    if not normalized_external_name:
        return False
    if not normalized_current_name:
        return True
    return normalized_current_name == normalized_external_name
