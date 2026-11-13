"""Locks the results page with a password, so the public link shows nothing without it.

    python lock_page.py <results.html> <out/index.html> [file to download ...]

The page and the files are encrypted (AES-256-GCM, key from the password with PBKDF2-SHA256, 250,000 rounds).
The phone opens the link, asks the password once (it can remember it), and unlocks everything in the browser.
The password comes from the environment variable PAGE_PASSWORD (a GitHub secret) and is never written anywhere.
"""
import base64
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ROUNDS = 250_000
TYPES = {".xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", ".html": "text/html"}


def seal(key: bytes, data: bytes) -> str:
    iv = os.urandom(12)
    return base64.b64encode(iv + AESGCM(key).encrypt(iv, data, None)).decode()


def main():
    password = os.environ.get("PAGE_PASSWORD", "")
    if len(password) < 6:
        sys.exit("PAGE_PASSWORD is missing or shorter than 6 characters: add it in Settings > Secrets and variables > Actions")
    page, out, files = Path(sys.argv[1]), Path(sys.argv[2]), [Path(f) for f in sys.argv[3:] if Path(f).exists()]
    salt = os.urandom(16)
    key = PBKDF2HMAC(algorithm=hashes.SHA256(), length=32, salt=salt, iterations=ROUNDS).derive(password.encode())
    blob = {"salt": base64.b64encode(salt).decode(), "rounds": ROUNDS, "page": seal(key, page.read_bytes()),
            "files": [{"name": f.name, "type": TYPES.get(f.suffix, "application/octet-stream"), "data": seal(key, f.read_bytes())}
                      for f in files],
            "made": datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")}
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(LOCK.replace("__BLOB__", json.dumps(blob)), encoding="utf-8")
    print(f"locked page written: {out} ({out.stat().st_size / 1e6:.1f} MB, {len(files)} files inside)")


LOCK = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex,nofollow">
<title>PREDICT/90</title>
<style>
:root{--bg:#f6f5f1;--card:#fff;--ink:#16161a;--mut:#6b6a66;--line:#e2e0d9;--acc:#1f6f43;--bad:#b3261e}
@media (prefers-color-scheme:dark){:root{--bg:#141413;--card:#1f1f1d;--ink:#f0efea;--mut:#a3a19a;--line:#34332f;--acc:#57b884;--bad:#f2867c}}
*{box-sizing:border-box}body{margin:0;min-height:100vh;display:grid;place-items:center;background:var(--bg);color:var(--ink);
font:16px/1.5 system-ui,-apple-system,Segoe UI,Roboto,sans-serif;padding:16px}
.card{width:100%;max-width:380px;background:var(--card);border:1px solid var(--line);border-radius:14px;padding:26px 22px}
h1{margin:0 0 4px;font-size:22px;letter-spacing:.5px}p{margin:0 0 18px;color:var(--mut);font-size:14px}
input[type=password]{width:100%;padding:12px 14px;font-size:17px;border:1px solid var(--line);border-radius:10px;background:transparent;color:var(--ink)}
button{width:100%;margin-top:12px;padding:12px;font-size:16px;font-weight:600;border:0;border-radius:10px;background:var(--acc);color:#fff;cursor:pointer}
label{display:flex;gap:8px;align-items:center;margin-top:12px;font-size:14px;color:var(--mut)}
#msg{min-height:22px;margin-top:10px;font-size:14px;color:var(--bad)}
</style></head><body>
<form class="card" id="f" autocomplete="on">
<h1>PREDICT/90</h1><p id="made"></p>
<input type="text" name="username" value="predict90" autocomplete="username" hidden>
<input type="password" id="pw" placeholder="Password" autocomplete="current-password" required>
<label><input type="checkbox" id="keep" checked> Remember on this device</label>
<button type="submit" id="go">Open</button><div id="msg"></div>
</form>
<script>
const B = __BLOB__;
const $ = id => document.getElementById(id);
$("made").textContent = "Updated " + B.made;
const bytes = s => Uint8Array.from(atob(s), c => c.charCodeAt(0));
async function key(pw) {
  const base = await crypto.subtle.importKey("raw", new TextEncoder().encode(pw), "PBKDF2", false, ["deriveKey"]);
  return crypto.subtle.deriveKey({name: "PBKDF2", salt: bytes(B.salt), iterations: B.rounds, hash: "SHA-256"},
                                 base, {name: "AES-GCM", length: 256}, false, ["decrypt"]);
}
async function open_(k, s) { const b = bytes(s); return new Uint8Array(await crypto.subtle.decrypt({name: "AES-GCM", iv: b.slice(0, 12)}, k, b.slice(12))); }
function b64(u8) { let s = ""; for (let i = 0; i < u8.length; i += 32768) s += String.fromCharCode.apply(null, u8.subarray(i, i + 32768)); return btoa(s); }
async function unlock(pw, remember) {
  const k = await key(pw);
  const page = new TextDecoder().decode(await open_(k, B.page));
  let bar = "";
  for (const f of B.files) {
    const d = await open_(k, f.data);
    bar += `<a download="${f.name}" href="data:${f.type};base64,${b64(d)}" style="color:#fff;margin-left:14px">${f.name.replace(/_\d{4}-\d\d-\d\d|\.xlsx/g, "").replace(/_/g, " ")}</a>`;
  }
  try { remember ? localStorage.setItem("p90pw", pw) : localStorage.removeItem("p90pw"); } catch (e) {}
  const top = bar ? `<div style="background:#1f6f43;color:#fff;font:14px system-ui,sans-serif;padding:8px 12px">Download:${bar}</div>` : "";
  document.open(); document.write(page.replace(/<body[^>]*>/i, m => m + top)); document.close();
}
$("f").addEventListener("submit", async e => {
  e.preventDefault(); $("msg").textContent = ""; $("go").textContent = "Opening...";
  try { await unlock($("pw").value, $("keep").checked); }
  catch (err) { $("go").textContent = "Open"; $("msg").textContent = "Wrong password, try again."; }
});
(async () => { let pw = null; try { pw = localStorage.getItem("p90pw"); } catch (e) {}
  if (pw) { $("go").textContent = "Opening..."; try { await unlock(pw, true); } catch (e) { $("go").textContent = "Open"; try { localStorage.removeItem("p90pw"); } catch (x) {} } } })();
</script></body></html>
"""

if __name__ == "__main__":
    main()
