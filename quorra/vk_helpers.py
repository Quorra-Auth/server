def vk_session(session_id: str) -> str:
    return "session:{}".format(session_id)

def vk_oidc_code(code: str) -> str:
    return "oidc-code:{}".format(code)
