"""Command line.

  python -m assistant run         one triage pass (what the schedule runs)
  python -m assistant chat        talk to the assistant; it asks before sending
  python -m assistant approvals   review and approve/deny queued actions
  python -m assistant tasks       show your task list
  python -m assistant connect     sign in to Gmail / Outlook and test each source
"""
import json
import sys
from datetime import datetime

from . import db
from .config import ENABLED_TOOLS, LOOKBACK_HOURS


def explain_error(e: Exception) -> str:
    """Turn API errors into one readable line instead of a traceback."""
    import anthropic
    msg = getattr(e, "message", None) or str(e)
    if isinstance(e, anthropic.APIStatusError):
        try:
            msg = e.body["error"]["message"]
        except Exception:
            pass
        if "credit balance" in msg:
            return ("⚠️  Your Anthropic API account is out of credit. Add credit at "
                    "https://console.anthropic.com/settings/billing, then try again.")
        if e.status_code == 401:
            return "⚠️  The API key was rejected. Create a new key and paste it into .env."
        if e.status_code == 404 and "model" in msg:
            return f"⚠️  Model not available to your account: {msg}. Change ASSISTANT_MODEL in .env."
        return f"⚠️  Claude API error {e.status_code}: {msg}"
    if isinstance(e, anthropic.APIConnectionError):
        return "⚠️  Couldn't reach the Claude API. Check your internet connection."
    return f"⚠️  {type(e).__name__}: {msg}"


def cmd_run():
    from .agent import Agent
    from .config import DATA_DIR
    from .tools import available_sources
    sources = available_sources(ENABLED_TOOLS)
    names = {"gmail": "Gmail (unread / important)", "outlook": "Outlook (unread / important)",
             "linkedin": "LinkedIn activity", "notes": "Apple Notes I've changed",
             "imessage": "iMessages"}
    checks = ", ".join(v for k, v in names.items() if k in sources)
    last = db.last_run_time()
    window = f"since {last}" if last else f"in the last {LOOKBACK_HOURS} hours"
    title = f"Brief — {datetime.now():%a %b %d, %H:%M}"
    save = (f"save it as an Apple Note titled '{title}' in a folder named 'Assistant'"
            if "notes" in sources else "reply with it in full (it will be saved to a file)")
    prompt = (f"Do my regular check of everything new {window}: {checks}. Add action items "
              "to my task list, save draft replies where a reply is clearly needed, queue "
              f"anything that needs my approval, then write today's brief and {save}.")
    print(f"[{datetime.now():%H:%M}] Running check ({', '.join(sorted(sources))})…")
    try:
        brief = Agent().ask(prompt)
    except Exception as e:
        print(explain_error(e))
        sys.exit(1)
    db.log_run(brief)
    briefs = DATA_DIR / "briefs"
    briefs.mkdir(exist_ok=True)
    path = briefs / f"{datetime.now():%Y-%m-%d_%H%M}.md"
    path.write_text(f"# {title}\n\n{brief}\n", encoding="utf-8")
    print("\n" + brief + f"\n\n(Saved to {path})")


def _ask_yes_no(name, args, reason):
    print(f"\n⚠️  The assistant wants to: {name}")
    if reason:
        print(f"   Why: {reason}")
    for k, v in args.items():
        print(f"   {k}: {v}")
    return input("   Approve? [y/N] ").strip().lower() == "y"


def cmd_chat():
    from .agent import Agent
    agent = Agent(approve_inline=_ask_yes_no)
    print("Chat with your assistant (Ctrl-C to quit). Try: 'what needs my attention today?'")
    while True:
        try:
            text = input("\nyou › ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if text:
            try:
                print("\nassistant › " + agent.ask(text))
            except Exception as e:
                agent.messages.clear()  # drop the half-finished turn
                print("\n" + explain_error(e))


def cmd_approvals():
    from .tools import load_tools
    tools = load_tools(ENABLED_TOOLS)
    items = db.pending_approvals()
    if not items:
        print("Nothing waiting for approval.")
        return
    for a in items:
        args = json.loads(a["args"])
        print(f"\n#{a['id']}  {a['tool']}  (queued {a['created_at']})")
        if a["reason"]:
            print(f"   Why: {a['reason']}")
        for k, v in args.items():
            print(f"   {k}: {v}")
        choice = input("   [a]pprove / [d]eny / [s]kip? ").strip().lower()
        if choice == "a":
            try:
                result = str(tools[a["tool"]].fn(**args))
                db.decide_approval(a["id"], "approved", result)
                print(f"   ✓ {result}")
            except Exception as e:
                db.decide_approval(a["id"], "failed", str(e))
                print(f"   ✗ Failed: {e}")
        elif choice == "d":
            db.decide_approval(a["id"], "denied")
            print("   Denied.")


def cmd_tasks():
    from .tools.tasks import list_tasks
    print(list_tasks("open"))


def cmd_connect():
    from .tools import available_sources, load_tools
    tools = load_tools(ENABLED_TOOLS)
    skipped = set(ENABLED_TOOLS) - available_sources(ENABLED_TOOLS)
    if skipped:
        print(f"Skipping {', '.join(sorted(skipped))}: these only work on a Mac.")
    checks = {
        "gmail": ("search_gmail", {"query": "newer_than:1d", "max_results": 1}),
        "outlook": ("search_outlook", {"max_results": 1}),
        "linkedin": ("linkedin_updates", {"newer_than_hours": 168}),
        "notes": ("list_notes", {"limit": 1}),
        "imessage": ("recent_imessages", {"hours": 24, "limit": 1}),
    }
    for group, (name, args) in checks.items():
        if group not in ENABLED_TOOLS or name not in tools:
            continue
        print(f"\n== {group} ==")
        try:
            print(str(tools[name].fn(**args))[:300])
        except Exception as e:
            print(f"✗ {type(e).__name__}: {e}")


COMMANDS = {"run": cmd_run, "chat": cmd_chat, "approvals": cmd_approvals,
            "tasks": cmd_tasks, "connect": cmd_connect}

if __name__ == "__main__":
    for stream in (sys.stdout, sys.stderr):  # Windows consoles default to cp1252
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8", errors="replace")
    cmd = sys.argv[1] if len(sys.argv) > 1 else "chat"
    if cmd not in COMMANDS:
        print(__doc__)
        sys.exit(1)
    if cmd in ("run", "chat"):
        from .config import api_key_problem
        problem = api_key_problem()
        if problem:
            print("Claude API key problem: " + problem)
            sys.exit(1)
        import os
        k = os.environ["ANTHROPIC_API_KEY"]
        print(f"API key loaded ({k[:10]}…{k[-4:]}, {len(k)} characters).")
    COMMANDS[cmd]()
