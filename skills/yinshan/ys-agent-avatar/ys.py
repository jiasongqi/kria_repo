#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""ys — ys-agent 数字员工平台轻量 CLI(单文件,纯标准库,跨平台)。

覆盖问答闭环:login / whoami / askto / inbox(show/reply/escalate)/ sent / kb(push/list/search/edit/rm)。
登录态自动续期:token 过期自动用保存的账号重登,只需登录一次。

用法示例:
    python ys.py login --phone AI_274 --password 'xxx'
    python ys.py askto YS-000224 "ES 查询返回空怎么排查?"
    python ys.py inbox
    python ys.py inbox reply 1 "答案..."
    python ys.py kb list
"""
import argparse
import base64
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_SERVER = "https://agent-app.adapundi.com"
CONFIG_PATH = os.path.join(os.path.expanduser("~"), ".ys", "config.json")


# ── 配置 ──────────────────────────────────────────────────────

def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(cfg):
    os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, ensure_ascii=False, indent=2)
    try:
        os.chmod(CONFIG_PATH, 0o600)  # 含密码,POSIX 下收紧权限;Windows 忽略
    except OSError:
        pass


# ── HTTP ──────────────────────────────────────────────────────

class ApiError(Exception):
    pass


IMG_EXTS = {".png": "image/png", ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
            ".webp": "image/webp", ".gif": "image/gif"}
TEXT_EXTS = {".txt", ".log", ".md", ".json", ".yaml", ".yml", ".xml", ".csv", ".html",
             ".htm", ".js", ".ts", ".py", ".java", ".sql", ".sh", ".ini", ".conf",
             ".properties", ".stack", ".trace", ".out"}


def upload_attachment(cfg, path, biz_type="ASK"):
    """上传图片/文本附件,返回嵌入消息的 markdown 引用。"""
    p = os.path.expanduser(path)
    if not os.path.isfile(p):
        raise ApiError(f"附件不存在: {path}")
    ext = os.path.splitext(p)[1].lower()
    if ext in IMG_EXTS:
        ctype = IMG_EXTS[ext]
    elif ext in TEXT_EXTS:
        ctype = "text/plain"
    else:
        raise ApiError(f"不支持的附件类型 {ext}(支持图片 png/jpg/webp/gif 与文本 log/txt/md/json 等)")
    size = os.path.getsize(p)
    server = (os.environ.get("YS_SERVER") or cfg.get("server") or DEFAULT_SERVER).rstrip("/")
    token = cfg.get("token")
    if not token:
        token = relogin(cfg, server)

    boundary = "----ysAttach" + uuid.uuid4().hex
    fname = os.path.basename(p).encode("ascii", "replace").decode()
    with open(p, "rb") as f:
        content = f.read()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{fname}"\r\n'
        f"Content-Type: {ctype}\r\n\r\n"
    ).encode("utf-8") + content + (
        f"\r\n--{boundary}\r\n"
        f'Content-Disposition: form-data; name="bizType"\r\n\r\n{biz_type}\r\n'
        f"--{boundary}--\r\n"
    ).encode("utf-8")

    req = urllib.request.Request(server + "/api/ask/attachment", data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            data = json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            raise ApiError(json.loads(e.read().decode("utf-8")).get("message") or str(e))
        except json.JSONDecodeError:
            raise ApiError(str(e))
    if data.get("code") != 200:
        raise ApiError(data.get("message") or "上传失败")
    info("[附件] " + os.path.basename(p) + f" ({size}B) 已上传")
    return data["data"]["markdown"]


def attach_refs(cfg, imgs, files, biz_type="ASK"):
    """把 --img/--file 列表转成 markdown 引用串(空则空串)。"""
    refs = []
    for p in (imgs or []):
        refs.append(upload_attachment(cfg, p, biz_type))
    for p in (files or []):
        refs.append(upload_attachment(cfg, p, biz_type))
    return ("\n\n" + "\n".join(refs)) if refs else ""


def http_json(server, method, path, body=None, token=None, timeout=30):
    url = server.rstrip("/") + path
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Content-Type", "application/json")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            msg = err.get("message") or err.get("msg") or str(e)
        except Exception:
            msg = str(e)
        raise ApiError(f"HTTP {e.code}: {msg}")
    except urllib.error.URLError as e:
        raise ApiError(f"连接失败: {e.reason} (server={server})")


def jwt_claims(token):
    """解码 JWT payload(不验签,只看过期与身份);失败返回 {}。"""
    try:
        seg = token.split(".")[1]
        seg += "=" * (-len(seg) % 4)
        return json.loads(base64.urlsafe_b64decode(seg))
    except Exception:
        return {}


def api(cfg, method, path, body=None, _retried=False):
    """带自动续期的请求:token 缺失/过期/401 → 用保存的账号静默重登一次。"""
    server = os.environ.get("YS_SERVER") or cfg.get("server") or DEFAULT_SERVER
    token = cfg.get("token")
    claims = jwt_claims(token) if token else {}
    exp = claims.get("exp") or 0
    if token and exp and exp < time.time() + 60:  # 快过期就提前续
        token = None
    if not token:
        token = relogin(cfg, server)
    try:
        resp = http_json(server, method, path, body, token)
    except ApiError as e:
        if _retried or "HTTP 401" not in str(e):
            raise
        token = relogin(cfg, server)  # 服务端提前吊销 → 重登重试一次
        resp = http_json(server, method, path, body, token)
    code = resp.get("code", 200)
    if code != 200:
        raise ApiError(resp.get("message") or f"code={code}")
    return resp.get("data")


def relogin(cfg, server):
    if not cfg.get("phone") or not cfg.get("password"):
        raise ApiError("未登录(且没有保存的账号可自动重登):请先 python ys.py login")
    resp = http_json(server, "POST", "/api/auth/login",
                     {"phone": cfg["phone"], "password": cfg["password"],
                      "country": cfg.get("country", "ID")})
    data = resp.get("data") or {}
    token = data.get("token")
    if not token:
        raise ApiError("自动重登失败:登录接口未返回 token,请手动重新 login")
    cfg["token"] = token
    cfg["server"] = server
    save_config(cfg)
    return token


# ── 输出 ──────────────────────────────────────────────────────

def info(msg):
    print(f"\033[36m{msg}\033[0m")


def ok(msg):
    print(f"\033[32m{msg}\033[0m")


def err(msg):
    print(f"\033[31m{msg}\033[0m", file=sys.stderr)


def table(headers, rows):
    cols = [[str(h) for h in headers]]
    cols += [[r[i] if i < len(r) else "" for i in range(len(headers))] for r in rows]
    widths = [max(len(c[i]) for c in cols) for i in range(len(headers))]
    for i, row in enumerate(cols):
        line = "  ".join(c.ljust(w) for c, w in zip(row, widths)).rstrip()
        print(line)
        if i == 0:
            print("  ".join("-" * w for w in widths))


def truncate(s, n):
    s = s or ""
    return s[:n] + "…" if len(s) > n else s


# ── 命令 ──────────────────────────────────────────────────────

def cmd_login(args):
    server = args.server or os.environ.get("YS_SERVER") or DEFAULT_SERVER
    cfg = {"server": server, "phone": args.phone, "country": args.country}
    resp = http_json(server, "POST", "/api/auth/login",
                     {"phone": args.phone, "password": args.password,
                      "country": args.country})
    data = resp.get("data") or {}
    token = data.get("token")
    if not token:
        err("登录失败:接口未返回 token")
        return 1
    cfg["token"] = token
    cfg["password"] = args.password  # 保存用于自动续登;文件权限已收紧
    save_config(cfg)
    claims = jwt_claims(token)
    ok("登录成功!")
    print(f"  用户:   {claims.get('name', args.phone)}")
    print(f"  Server: {server}")
    me = http_json(server, "GET", "/api/auth/me", token=token).get("data") or {}
    if me.get("employeeNo"):
        print(f"  工号:   {me['employeeNo']}")
    else:
        info("  注意: 当前账号未绑定工号(提问/收件需要工号,请联系管理员绑定)")
    print(f"  配置:   {CONFIG_PATH}")
    return 0


def cmd_whoami(args):
    cfg = load_config()
    token = cfg.get("token")
    claims = jwt_claims(token) if token else {}
    if not claims:
        err("未登录:请先 python ys.py login")
        return 1
    if claims.get("exp") and claims["exp"] < time.time():
        relogin(cfg, cfg.get("server") or DEFAULT_SERVER)
        claims = jwt_claims(cfg["token"])
    print("━" * 3, "Current User", "━" * 3)
    print(f"账号:   {cfg.get('phone')}")
    print(f"用户:   {claims.get('name')}")
    print(f"角色:   {claims.get('role')}")
    me = api(cfg, "GET", "/api/auth/me") or {}
    print(f"工号:   {me.get('employeeNo') or '(未绑定)'}")
    print(f"Server: {cfg.get('server') or DEFAULT_SERVER}")
    exp = claims.get("exp")
    if exp:
        print(f"过期:   {time.strftime('%Y-%m-%d %H:%M UTC', time.gmtime(exp))} (过期自动续登)")
    return 0


def cmd_logout(args):
    cfg = load_config()
    cfg.pop("token", None)
    cfg.pop("password", None)
    save_config(cfg)
    ok("已退出(清除本地凭据)。")
    return 0


def cmd_askto(args):
    cfg = load_config()
    to = args.to
    question = " ".join(args.question).strip()
    if not question:
        err('用法: python ys.py askto <工号> "问题"')
        return 1
    question += attach_refs(cfg, args.img, args.file)
    q = api(cfg, "POST", "/api/ask", {"to": to, "question": question}) or {}
    if getattr(args, "json", False):
        import json as _json
        print(_json.dumps(q, ensure_ascii=False, indent=2))
        return 0
    status = q.get("status")
    if status == "AUTO_ANSWERED":
        info(f"🤖 {to} 的分身命中知识库(kb#{q.get('kbEntryId', '-')}),代答:")
        print(q.get("answer") or "")
        print()
        qid = q.get('id')
        info(f"回答来自其知识库。验证后请务必反馈(流程最后一步): "
             f"python ys.py feedback {qid} helpful|not")
        info(f"not 会把命中的知识转待复核;需要真人再答可 python ys.py inbox escalate {qid}")
    elif status == "CANDIDATES":
        info(f"未强命中,给出 {len(q.get('candidates') or [])} 个候选(供你/你的 agent 挑选):")
        for i, c in enumerate(q.get("candidates") or [], 1):
            print(f"  [{i}] kb#{c.get('id')} hits={c.get('hitCount', 0)} {truncate(c.get('question'), 50)}")
        qid = q.get("id")
        print()
        info(f"挑选: python ys.py pick {qid} <kbId> | 自行多轮检索: python ys.py kb search \"关键词\" --owner {to}")
        info(f"都不合适则保持待答(#{qid}),专家稍后回复")
    else:
        info(f"已进入 {to} 的收件箱(问题 #{q.get('id', '-')}),等专家回复。"
             f"你的 agent 可先自助检索: python ys.py kb search \"关键词\" --owner {to}")
    return 0


_PS_TOAST = r"""
[Windows.UI.Notifications.ToastNotificationManager, Windows.UI.Notifications, ContentType=WindowsRuntime] | Out-Null
$template = [Windows.UI.Notifications.ToastNotificationManager]::GetTemplateContent([Windows.UI.Notifications.ToastTemplateType]::ToastText02)
$t = $template.GetElementsByTagName('text')
$t.Item(0).AppendChild($template.CreateTextNode($title)) | Out-Null
$t.Item(1).AppendChild($template.CreateTextNode($body)) | Out-Null
$template.DocumentElement.SetAttribute('activationType', 'protocol')
$template.DocumentElement.SetAttribute('launch', $url)
[Windows.UI.Notifications.ToastNotificationManager]::CreateToastNotifier(
    '{1AC14E77-02E7-4E5D-B744-2EB1AE5198B7}\WindowsPowerShell\v1.0\powershell.exe'
).Show([Windows.UI.Notifications.ToastNotification]::new($template))
"""


WEB_INBOX_URL = "https://agent-web.adapundi.com/ask"


def _ps_single_quoted(v):
    """PowerShell 单引号字面量:内部 ' 翻倍;控制字符剔除(通知文本用)。"""
    return "'" + "".join(c for c in v.replace("'", "''") if c >= ' ') + "'"


def _desktop_notify(title, body, url=WEB_INBOX_URL):
    """跨平台原生通知中心(纯 stdlib,失败静默):
    Windows: WinRT toast,点击直接打开工作台收件页(protocol launch);失败降级 Popup。
    macOS: osascript 通知(正文带工作台地址);Linux: notify-send。
    """
    import subprocess
    try:
        if sys.platform.startswith("win"):
            cmd = (f"$title={_ps_single_quoted(title)}; $body={_ps_single_quoted(body)}; "
                   f"$url={_ps_single_quoted(url)}; " + _PS_TOAST)
            subprocess.Popen(
                ["powershell", "-NoProfile", "-Command", cmd],
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                creationflags=0x08000000)
        elif sys.platform == "darwin":
            safe_t = title.replace('"', '')
            safe_b = f"{body} · {url}".replace('"', '')
            subprocess.Popen(["osascript", "-e",
                              f'display notification "{safe_b}" with title "{safe_t}" subtitle "ys"'])
        else:
            subprocess.Popen(["notify-send", "-a", "ys", title, f"{body}\n{url}"])
    except Exception:
        pass


def _filter_new_pending(items):
    """返回 (新 PENDING 列表, 是否首次运行)。last_inbox_id 记在 config,见过的不再提醒。"""
    cfg = load_config()
    first = "last_inbox_id" not in cfg
    last = cfg.get("last_inbox_id") or 0
    new = [q for q in items if q.get("status") == "PENDING" and q.get("id", 0) > last]
    max_id = max((q.get("id", 0) for q in items), default=last)
    if max_id > last:
        cfg["last_inbox_id"] = max_id
        save_config(cfg)
    return new, first



def cmd_inbox(args):
    cfg = load_config()
    items = api(cfg, "GET", f"/api/ask/inbox?limit={args.limit}") or []
    if getattr(args, "notify", False):
        new, first = _filter_new_pending(items)
        if new:
            info(f"🔔 收到 {len(new)} 个新问题:")
            for q in new:
                print(f"  #{q['id']} {q.get('askerNo')} {truncate(q.get('question'), 40)}")
            print(f"  处理入口: 工作台 {WEB_INBOX_URL} | 终端: ys inbox show <id>")
            print('  交给本地 agent: 对它说「处理 ys inbox 新问题:逐条 inbox show --save-attachments 导材料,'
                  '生成答案草稿给我审,不要自动回复」')
            preview = truncate(new[0].get("question"), 36)
            _desktop_notify(f"ys 收件箱 · {len(new)} 个新问题待答",
                            f"{preview}(点击打开工作台处理)")
        return 0
    if not items:
        info("收件箱为空:没有待答问题,也没有分身代答记录。")
        return 0
    rows = [[str(q.get("id", "")), q.get("askerNo", ""), q.get("status", ""),
             truncate(q.get("question"), 40),
             f"kb#{q.get('kbEntryId')}" if q.get("status") == "AUTO_ANSWERED" else "-"]
            for q in items]
    table(["ID", "FROM", "STATUS", "QUESTION", "HIT"], rows)
    print()
    print('操作: python ys.py inbox show <id> / reply <id> "答案" / escalate <id>')
    return 0


def _parse_attachment_refs(text):
    """从 markdown 里解析附件引用 -> [(name, key)]。"""
    import re
    out = []
    for m in re.finditer(r"!?\[([^\]\n]*)\]\(/api/ask/attachment/([0-9a-fA-F-]{8,})\)", text or ""):
        out.append((m.group(1) or m.group(2), m.group(2)))
    return out


def _download_attachment(cfg, name, key, directory):
    server = (os.environ.get("YS_SERVER") or cfg.get("server") or DEFAULT_SERVER).rstrip("/")
    token = cfg.get("token")
    req = urllib.request.Request(f"{server}/api/ask/attachment/{key}")
    if token:
        req.add_header("Authorization", "Bearer " + token)
    safe = "".join(c if c.isalnum() or c in "._-" else "_" for c in name)[:120] or key
    path = os.path.join(directory, safe)
    with urllib.request.urlopen(req, timeout=60) as resp, open(path, "wb") as f:
        f.write(resp.read())
    return path


def cmd_inbox_show(args):
    cfg = load_config()
    q = api(cfg, "GET", f"/api/ask/{args.id}") or {}
    print(f"ID: {q.get('id')}")
    print(f"FROM: {q.get('askerNo')}  TO: {q.get('addresseeNo')}")
    print(f"STATUS: {q.get('status')}")
    print("QUESTION:")
    print(q.get("question") or "")
    if q.get("answer"):
        print("ANSWER:")
        print(q["answer"])
    refs = _parse_attachment_refs((q.get("question") or "") + "\n" + (q.get("answer") or ""))
    if refs:
        print()
        info(f"附件 {len(refs)} 个:")
        for name, key in refs:
            print(f"  - {name}  (key={key})")
        if getattr(args, "save_attachments", None):
            d = args.save_attachments
            os.makedirs(d, exist_ok=True)
            saved = [_download_attachment(cfg, n, k, d) for n, k in refs]
            info("已导出材料目录(可直接交给你的 AI agent 处理):")
            for p in saved:
                print("  " + p)
    return 0


def cmd_inbox_reply(args):
    cfg = load_config()
    answer = " ".join(args.answer).strip()
    if not answer:
        err('用法: python ys.py inbox reply <id> "答案"')
        return 1
    answer += attach_refs(cfg, args.img, args.file)
    q = api(cfg, "POST", f"/api/ask/{args.id}/reply", {"answer": answer}) or {}
    ok(f"已回复 #{args.id},回答已沉淀进知识库(kb#{q.get('kbEntryId', '-')})。")
    return 0


def cmd_inbox_escalate(args):
    cfg = load_config()
    api(cfg, "POST", f"/api/ask/{args.id}/escalate", {})
    ok(f"已转人工,问题 #{args.id} 重新进入专家收件箱;命中条目已标记待复核。")
    return 0


def cmd_pick(args):
    cfg = load_config()
    q = api(cfg, "POST", f"/api/ask/{args.id}/pick", {"kbEntryId": args.kbId}) or {}
    ok(f"已采纳 kb#{args.kbId} 作为问题 #{args.id} 的答案(hit_count+1)。")
    print(truncate(q.get("answer") or "", 120))
    info("验证后必须反馈(不许静默结束): python ys.py feedback "
         + str(args.id) + " helpful|not")
    return 0


def cmd_feedback(args):
    cfg = load_config()
    helpful = args.verdict == "helpful"
    api(cfg, "POST", f"/api/ask/{args.id}/feedback",
        {"helpful": helpful, "comment": args.comment or None})
    if helpful:
        ok(f"已反馈有帮助(#{args.id}),谢谢!")
    else:
        ok(f"已反馈无帮助(#{args.id});命中的知识条目已转待复核,专家会修正。")
    return 0


def cmd_sent(args):
    cfg = load_config()
    items = api(cfg, "GET", f"/api/ask/sent?limit={args.limit}") or []
    if not items:
        info("还没有提问记录。")
        return 0
    rows = [[str(q.get("id", "")), q.get("addresseeNo", ""), q.get("status", ""),
             truncate(q.get("question"), 32), truncate(q.get("answer") or "-", 40),
             q.get("feedback") or "-"]
            for q in items]
    table(["ID", "TO", "STATUS", "QUESTION", "ANSWER", "FEEDBACK"], rows)
    unfed = [q for q in items
             if q.get("status") in ("ANSWERED", "AUTO_ANSWERED") and not q.get("feedback")]
    if unfed:
        print()
        info(f"⚠ {len(unfed)} 条已答未反馈(反馈是流程最后一步,帮专家校准知识):")
        for q in unfed[:5]:
            print(f"  python ys.py feedback {q['id']} helpful|not   #{q['id']} "
                  f"{truncate(q.get('question'), 30)}")
    return 0


def cmd_kb_push(args):
    cfg = load_config()
    answer = args.answer + attach_refs(cfg, args.img, args.file, biz_type="KB")
    body = {"question": args.question, "answer": answer,
            "tags": args.tags,
            "questionAlts": args.alts.replace("|", "\n") if args.alts else None,
            "visibility": args.visibility}
    e = api(cfg, "POST", "/api/kb", body) or {}
    ok(f"已入库 kb#{e.get('id')} [{args.visibility.upper()}]")
    return 0


def cmd_kb_list(args):
    cfg = load_config()
    path = f"/api/kb?limit={args.limit}" + (f"&status={args.status}" if args.status else "")
    items = api(cfg, "GET", path) or []
    if not items:
        info("知识库为空。")
        return 0
    rows = [[str(e.get("id", "")), e.get("visibility", ""),
             str(e.get("hitCount", 0)), truncate(e.get("question"), 42), e.get("tags") or ""]
            for e in items]
    table(["ID", "VIS", "HITS", "QUESTION", "TAGS"], rows)
    return 0


def cmd_kb_search(args):
    cfg = load_config()
    owner = getattr(args, "owner", None)
    path = f"/api/kb/search?q={urllib.parse.quote(args.q)}&limit={args.limit}"
    if owner:
        path += f"&owner={urllib.parse.quote(owner)}"
    items = api(cfg, "GET", path) or []
    if getattr(args, "json", False):
        import json as _json
        print(_json.dumps(items, ensure_ascii=False, indent=2))
        return 0
    if not items:
        info("无命中。换几个关键词再试(检索无副作用,可多轮)。")
        return 0
    for e in items:
        print(f"kb#{e.get('id')} [{e.get('visibility')}] owner={e.get('ownerNo')} "
              f"hits={e.get('hitCount', 0)}")
        print(f"  Q: {truncate(e.get('question'), 60)}")
        print(f"  A: {truncate(e.get('answer'), 80)}")
        print()
    return 0


def cmd_kb_show(args):
    cfg = load_config()
    e = api(cfg, "GET", f"/api/kb/{args.id}") or {}
    if getattr(args, "save", None):
        md = (f"---\nid: {e.get('id')}\nowner: {e.get('ownerNo')}\ntags: {e.get('tags') or ''}\n"
              f"visibility: {e.get('visibility')}\nstatus: {e.get('status')}\nhit_count: {e.get('hitCount')}\n---\n\n"
              f"# {e.get('question')}\n\n{e.get('answer') or ''}\n")
        with open(args.save, "w", encoding="utf-8") as f:
            f.write(md)
        ok(f"已导出 {args.save}")
        return 0
    print(f"kb#{e.get('id')} [{e.get('visibility')}] hits={e.get('hitCount')} status={e.get('status')}")
    print(f"Q: {e.get('question')}")
    print(f"A: {e.get('answer')}")
    if e.get("questionAlts"):
        print(f"变体: {e.get('questionAlts')}")
    return 0


def cmd_kb_edit(args):
    cfg = load_config()
    body = {k: v for k, v in [("question", args.question), ("answer", args.answer),
                              ("tags", args.tags), ("visibility", args.visibility),
                              ("status", args.status)] if v is not None}
    if not body:
        err("至少指定一个要改的字段(-q/-a/--tags/--visibility/--status)")
        return 1
    api(cfg, "PUT", f"/api/kb/{args.id}", body)
    ok(f"已更新 kb#{args.id}")
    return 0


def cmd_kb_rm(args):
    cfg = load_config()
    api(cfg, "DELETE", f"/api/kb/{args.id}")
    ok(f"已删除 kb#{args.id}")
    return 0


# ── 入口 ──────────────────────────────────────────────────────

def build_parser():
    p = argparse.ArgumentParser(prog="ys", description="ys-agent 数字员工平台轻量 CLI")
    sub = p.add_subparsers(dest="cmd", required=True)

    s = sub.add_parser("login", help="登录并保存凭据(自动续登,只需一次)")
    s.add_argument("--phone", required=True)
    s.add_argument("--password", required=True)
    s.add_argument("--country", default="ID")
    s.add_argument("--server", help=f"默认 {DEFAULT_SERVER}")
    s.set_defaults(fn=cmd_login)

    s = sub.add_parser("whoami", help="当前登录身份与工号")
    s.set_defaults(fn=cmd_whoami)

    s = sub.add_parser("logout", help="清除本地凭据")
    s.set_defaults(fn=cmd_logout)

    s = sub.add_parser("askto", help="向专家数字分身提问")
    s.add_argument("to", metavar="employeeNo")
    s.add_argument("question", nargs="+")
    s.add_argument("--img", action="append", help="图片附件路径(可重复)")
    s.add_argument("--file", action="append", help="文本附件路径(可重复)")
    s.add_argument("--json", action="store_true", help="输出完整 JSON(供本地 AI agent 消费)")
    s.set_defaults(fn=cmd_askto)

    s = sub.add_parser("sent", help="我提过的问题与回复")
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_sent)

    s = sub.add_parser("pick", help="采纳知识条目为问题答案(候选或自行检索所得)")
    s.add_argument("id", type=int, help="问题 id")
    s.add_argument("kbId", type=int, help="知识条目 id")
    s.set_defaults(fn=cmd_pick)

    s = sub.add_parser("feedback", help="反馈答案是否有帮助")
    s.add_argument("id", type=int)
    s.add_argument("verdict", choices=["helpful", "not"])
    s.add_argument("--comment", help="补充说明")
    s.set_defaults(fn=cmd_feedback)

    inbox = sub.add_parser("inbox", help="我的收件箱(待答+分身代答)")
    inbox_sub = inbox.add_subparsers(dest="sub")

    inbox.add_argument("--notify", action="store_true",
                       help="定时任务模式:仅新 PENDING 时桌面通知(无新则静默,适合 cron)")
    inbox.set_defaults(fn=cmd_inbox, limit=20)
    s = inbox_sub.add_parser("list", help="列出收件箱(默认行为)")
    s.add_argument("--limit", type=int, default=20)
    s.add_argument("--notify", action="store_true",
                   help="定时任务模式:仅新 PENDING 时桌面通知")
    s.set_defaults(fn=cmd_inbox)

    s = inbox_sub.add_parser("show", help="看单条问题全文")
    s.add_argument("id", type=int)
    s.add_argument("--save-attachments", dest="save_attachments", metavar="DIR",
                   help="导出附件到目录(材料目录可交给本地 AI agent 做多模态识别)")
    s.set_defaults(fn=cmd_inbox_show)

    s = inbox_sub.add_parser("reply", help="回复(自动沉淀知识库)")
    s.add_argument("id", type=int)
    s.add_argument("answer", nargs="+")
    s.add_argument("--img", action="append", help="图片附件路径(可重复)")
    s.add_argument("--file", action="append", help="文本附件路径(可重复)")
    s.set_defaults(fn=cmd_inbox_reply)

    s = inbox_sub.add_parser("escalate", help="对代答不满意转人工")
    s.add_argument("id", type=int)
    s.set_defaults(fn=cmd_inbox_escalate)

    kb = sub.add_parser("kb", help="个人知识库管理")
    kb_sub = kb.add_subparsers(dest="sub")

    kb.set_defaults(fn=cmd_kb_list, limit=50, status=None)
    s = kb_sub.add_parser("push", help="新增一条知识")
    s.add_argument("-q", "--question", required=True)
    s.add_argument("-a", "--answer", required=True)
    s.add_argument("--tags")
    s.add_argument("--alts", help="变体问题,| 分隔")
    s.add_argument("--img", action="append", help="答案图片附件(可重复)")
    s.add_argument("--file", action="append", help="答案文本附件(可重复)")
    s.add_argument("--visibility", default="PRIVATE", choices=["PRIVATE", "DEPARTMENT", "PUBLIC"])
    s.set_defaults(fn=cmd_kb_push)

    s = kb_sub.add_parser("list", help="我的知识库")
    s.add_argument("--status", choices=["ACTIVE", "NEEDS_REVIEW", "ARCHIVED"])
    s.add_argument("--limit", type=int, default=50)
    s.set_defaults(fn=cmd_kb_list)

    s = kb_sub.add_parser("search", help="检索(我的+PUBLIC;--owner 检索指定专家)")
    s.add_argument("q")
    s.add_argument("--owner", help="检索该工号专家的知识库(ask 代答同款暴露面)")
    s.add_argument("--limit", type=int, default=10)
    s.add_argument("--json", action="store_true", help="输出 JSON(供本地 AI agent 消费)")
    s.set_defaults(fn=cmd_kb_search)

    s = kb_sub.add_parser("show", help="查看单条全文/导出 md")
    s.add_argument("id", type=int)
    s.add_argument("--save", metavar="FILE", help="导出为 md 文件")
    s.set_defaults(fn=cmd_kb_show)

    s = kb_sub.add_parser("edit", help="编辑一条知识")
    s.add_argument("id", type=int)
    s.add_argument("-q", "--question")
    s.add_argument("-a", "--answer")
    s.add_argument("--tags")
    s.add_argument("--visibility", choices=["PRIVATE", "DEPARTMENT", "PUBLIC"])
    s.add_argument("--status", choices=["ACTIVE", "NEEDS_REVIEW", "ARCHIVED"])
    s.set_defaults(fn=cmd_kb_edit)

    s = kb_sub.add_parser("rm", help="删除一条知识")
    s.add_argument("id", type=int)
    s.set_defaults(fn=cmd_kb_rm)

    return p


def main(argv):
    if os.name == "nt":
        os.system("")  # 启用 Windows 终端 ANSI
    try:
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")
    except Exception:
        pass
    args = build_parser().parse_args(argv)
    try:
        return args.fn(args)
    except ApiError as e:
        err(str(e))
        return 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
