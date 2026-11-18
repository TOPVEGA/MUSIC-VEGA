# • ترخيص بواسطه : @TopVeGa
# • علامة تجارية : VEGA & Sound
# • حرية التعديل و النشر ©2015 - 2026

import io
import os
import re
import sys
import uuid
import traceback
from html import escape
from typing import Any, Optional, Tuple

from pyrogram import filters, types

from anony import anon, app, config, db, lang, userbot
from anony.helpers import format_exception, meval

# ========== كلمات محظورة في الكود (حماية أساسية) ==========
FORBIDDEN_PATTERNS = [
    r"\bos\.system\b",
    r"\bos\.popen\b",
    r"\bos\.exec[lv]",
    r"\bsubprocess\b",
    r"\b__import__\b",
    r"\beval\s*\(",
    r"\bexec\s*\(",
    r"\bcompile\s*\(",
    r"\bopen\s*\(",
    r"\bshutil\.rmtree\b",
    r"\bsys\.exit\b",
    r"\bos\._exit\b",
    r"\bapp\.stop\b",
    r"\bapp\.restart\b",
    r"\bdb\.db\.drop",
    r"\bpickle\b",
    r"\bmarshal\b",
    r"\bctypes\b",
]


def _is_code_safe(code: str) -> Tuple[bool, Optional[str]]:
    """فحص أساسي للكود قبل التنفيذ"""
    for pattern in FORBIDDEN_PATTERNS:
        if re.search(pattern, code):
            return False, f"❌ الكود يحتوي على كلمة محظورة: `{pattern}`"
    return True, None


@app.on_message(filters.command(["eval", "exec"]) & filters.user(app.owner))
@app.on_edited_message(filters.command(["eval", "exec"]) & filters.user(app.owner))
@lang.language()
async def eval_handler(_, message: types.Message):
    if len(message.command) < 2:
        return await message.reply_text(message.lang["eval_inp"])

    code = message.text.split(None, 1)[1]

    # ✅ فحص الأمان
    safe, err = _is_code_safe(code)
    if not safe:
        return await message.reply_text(err)

    out_buf = io.StringIO()

    async def _eval_code() -> Tuple[str, Optional[str]]:
        async def send(*args: Any, **kwargs: Any) -> types.Message:
            return await message.reply_text(*args, **kwargs)

        def _print(*args: Any, **kwargs: Any) -> None:
            kwargs.setdefault("file", out_buf)
            print(*args, **kwargs)

        eval_vars = {
            "m": message,
            "r": message.reply_to_message,
            "chat": message.chat,
            "user": message.from_user,
            "app": app,
            "anon": anon,
            "db": db,
            "client": app,
            "ub": userbot,
            "ikb": types.InlineKeyboardButton,
            "ikm": types.InlineKeyboardMarkup,
            "send": send,
            "config": config,
            "print": _print,
            "os": os,
            "re": re,
            "sys": sys,
            "tb": traceback,
        }

        try:
            result = await meval(code, globals(), **eval_vars)
            return "", result
        except Exception as e:
            tb = traceback.extract_tb(e.__traceback__)
            snippet_tb = next(
                (i for i, f in enumerate(tb) if f.filename == "<string>"), -1
            )
            formatted_tb = format_exception(
                e, tb[snippet_tb:] if snippet_tb != -1 else tb
            )
            return message.lang["eval_error"], formatted_tb

    _, result = await _eval_code()

    if result is not None or not out_buf.getvalue():
        print(result, file=out_buf)

    output = out_buf.getvalue().strip()
    response = message.lang["eval_out"].format(escape(output))

    if len(response) > 4096:
        with io.BytesIO(output.encode()) as out_file:
            out_file.name = f"{uuid.uuid4().hex[:8].lower()}.txt"
            return await message.reply_document(
                document=out_file, disable_notification=True
            )

    await message.reply_text(response)