"""Resume o stream-json do Claude Code: ferramentas usadas, erros e a resposta final."""
import json, sys

linhas = []
for bruto in open(sys.argv[1], encoding="utf-8", errors="ignore"):
    try:
        ev = json.loads(bruto)
    except Exception:
        continue
    t = ev.get("type")
    if t == "assistant":
        for c in ev.get("message", {}).get("content", []):
            if c.get("type") == "tool_use":
                ent = json.dumps(c.get("input", {}), ensure_ascii=False)[:200]
                linhas.append(f"🔧 {c.get('name')} {ent}")
            elif c.get("type") == "text" and c.get("text", "").strip():
                linhas.append("💬 " + c["text"].strip()[:600])
    elif t == "user":
        for c in (ev.get("message", {}).get("content") or []):
            if isinstance(c, dict) and c.get("type") == "tool_result" and c.get("is_error"):
                linhas.append("❌ " + str(c.get("content"))[:400])
    elif t == "result":
        linhas.append(f"\n=== resultado: {ev.get('subtype')} | turnos {ev.get('num_turns')} | "
                      f"{ev.get('duration_ms', 0) // 1000}s | erro={ev.get('is_error')}")
        linhas.append(str(ev.get("result", ""))[:3000])
print("\n".join(linhas))
