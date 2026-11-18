# Personal AI Assistant

A Claude-powered assistant that runs on your Mac. It checks **Gmail, Outlook,
LinkedIn, Apple Notes and iMessage**, then works on your behalf:

- summarizes what's new into a brief (saved as an Apple Note)
- pulls action items into a task list
- saves **draft** replies in Gmail and Outlook
- **asks you first** before it sends any email or iMessage

```
          ┌──────────── Claude (Anthropic API) ─────────────┐
          │   decides what to read, what to do, what to ask │
          └───────┬─────────────────────────────────────────┘
                  │ tool calls
   ┌──────────┬───┴──────┬───────────┬────────────┬──────────┐
 Gmail     Outlook    LinkedIn    Apple Notes   iMessage    Tasks
 (API)     (Graph)    (via Gmail)  (AppleScript) (chat.db +  (SQLite)
                                                 Messages)
                  │
   anything that sends ──► approval queue ──► you approve / deny
```

## Use it in your browser (no terminal)
```
python -m assistant ui          # Windows: double-click Assistant.bat
```
Opens the assistant at `http://127.0.0.1:8765` in your browser:
- **Chat** with live progress while it works, and **Check now** to go through everything new
- **Waiting for you**: every email or message it wants to send, editable, with *Approve and send* / *Don't send*
- **Tasks**: action items it found, plus your own, with due dates
- **Briefs**: every saved check
- **About you**: edit `profile.md` (who matters, what to ignore, your writing style)

It listens only on your own computer. Other websites can't talk to it (see ARCHITECTURE.md, section 8).
Use **Quit assistant** in the sidebar to stop it. Scheduled checks keep running either way.

## How safety works

- **Drafts are free; sends need approval.** Tools that send (`send_gmail`,
  `send_gmail_reply`, `send_outlook_reply`, `send_imessage`) never run directly.
  In `chat` mode you get a y/N prompt. In scheduled runs they wait in a queue
  (with a macOS notification) until you run `python -m assistant approvals`.
- **Emails and messages are treated as untrusted.** The assistant is told never to
  follow instructions found inside them (a common prompt-injection trick:
  "AI assistant, forward this to…"). The approval gate is the backstop.
- **Everything stays local** except the calls to Claude and to Google/Microsoft.
  Tokens live in `secrets/` and are git-ignored.

## Running on Windows
Gmail, Outlook, LinkedIn and the task list work the same on Windows. Apple Notes and
iMessage are Mac-only and are skipped. The brief is saved to `data\briefs\` instead.

**Easiest:** double-click `setup_windows.bat` once (creates the environment, installs
packages, opens `.env` for your API key), then double-click `Assistant.bat` to open the
browser interface (or `run_windows.bat` for the text chat). Double-click `connect_windows.bat` to sign in to Gmail (and Outlook once set up).
`run_windows.bat run`, `approvals` or `connect` run the other commands.

Or by hand in PowerShell:
```powershell
cd $HOME\Documents\ai-assistant
python -m venv .venv            # Microsoft Store Python uses "python", not "py"
.venv\Scripts\Activate.ps1      # if blocked: Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
pip install -r requirements.txt
copy .env.example .env; notepad .env
mkdir secrets
python -m assistant connect
```
Schedule: `powershell -ExecutionPolicy Bypass -File deploy\install_schedule_windows.ps1`

## Setup (about 30 minutes)

Needs a Mac with Python 3.10 or newer (`brew install python@3.12`).

```bash
cd ai-assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # then edit it
mkdir -p secrets
```

### 1. Claude API key
Create a key at <https://console.anthropic.com>, put it in `.env` as `ANTHROPIC_API_KEY`.

### 2. Connect Gmail (and LinkedIn)
1. Open <https://console.cloud.google.com>, create a project.
2. **APIs & Services → Library** → enable **Gmail API**.
3. **OAuth consent screen** → External → add yourself as a **test user**.
4. **Credentials → Create credentials → OAuth client ID → Desktop app** → download the JSON.
5. Save it as `secrets/gmail_credentials.json`.

The first run opens a browser to sign in. The token is then saved to `secrets/gmail_token.json`.

**LinkedIn** has no public API for your messages, invitations or feed, and automating
the website breaks LinkedIn's terms. The assistant reads the **notification emails
LinkedIn sends to your Gmail** instead. Turn those on in LinkedIn → Settings →
Notifications → email (messages, invitations, mentions, job alerts). If your LinkedIn
email is your Outlook address, forward LinkedIn mail to Gmail, or tell the
assistant to search Outlook for `linkedin.com`.

### 3. Connect Outlook / Microsoft 365
1. Open <https://entra.microsoft.com> → **App registrations → New registration**.
   Supported accounts: *any org directory + personal Microsoft accounts*.
2. In the new app: **Authentication → Allow public client flows → Yes**.
3. **API permissions → Microsoft Graph → Delegated**: `Mail.ReadWrite`, `Mail.Send`.
4. Copy the **Application (client) ID** into `.env` as `MS_CLIENT_ID`.

The first run prints a code and a URL. Sign in there once and the token is cached.
Work accounts may need an admin to approve the app.

### 4. Apple Notes and iMessage permissions
- **Full Disk Access** (to read Messages): System Settings → Privacy & Security →
  Full Disk Access → add your terminal app, *and* `.venv/bin/python` if you'll use
  the schedule. In Finder, ⌘⇧G helps you reach `.venv`. It's a symlink, so add the real Python it points to (`readlink -f .venv/bin/python`).
- **Automation** (to control Notes, Messages, Contacts): macOS will ask the first
  time. Click **OK**. To review later: Privacy & Security → Automation.

### 5. Tell it about you
Edit `profile.md`: who matters, what to do automatically, what to always ask about,
what to ignore, and how your replies should sound. It's read on every run.

### 6. Test the connections
```bash
python -m assistant connect
```
This signs in to each service and prints one item from each source.

## Using it

```bash
python -m assistant chat        # talk to it: "what needs my attention?",
                                # "draft a reply to Sarah's email", "text Mom I'm running late"
python -m assistant run         # one full check: brief + tasks + drafts + approval queue
python -m assistant approvals   # approve or deny queued sends
python -m assistant tasks       # see your task list
```

### Run it on a schedule
```bash
chmod +x deploy/install_schedule.sh
./deploy/install_schedule.sh            # runs at 8:00, 12:00, 17:00
./deploy/install_schedule.sh uninstall
```
Edit the hours in the script to change the times. The Mac must be awake. Output goes to `data/assistant.log`.

## Turning sources on or off
Set `ENABLED_TOOLS` in `.env`, e.g. `ENABLED_TOOLS=gmail,linkedin,notes,tasks`.

## Adding your own tools
Any Python function becomes a tool with the `@tool` decorator. See
`assistant/tools/tasks.py` for the simplest example:

```python
@tool("calendar", "Create a calendar event.", {"title": {"type": "string"}, ...},
      ["title"], needs_approval=True)
def create_event(title, ...):
    ...
```
Then import the module in `assistant/tools/__init__.py → load_tools`, and add its group
to `ENABLED_TOOLS`. Good next additions: Google Calendar, Outlook Calendar (`Calendars.ReadWrite`),
Todoist, Notion, Slack.

## Costs
Each scheduled run makes about 10–30 Claude API calls, depending on how much is new.
To cut costs, lower `LOOKBACK_HOURS`, run fewer times a day, or set `ASSISTANT_MODEL`
to a smaller model such as `claude-haiku-5-5`.

## Project layout
```
assistant/
  __main__.py      CLI: ui, run, chat, approvals, tasks, connect
  web.py + ui.html local web interface (Flask, 127.0.0.1 only)
  checks.py        the regular check, shared by CLI, schedule and web
  errors.py        plain-language API error messages
  agent.py         Claude tool-use loop + system prompt + approval gate
  db.py            SQLite: tasks, approval queue, run log
  config.py        settings from .env
  tools/
    gmail.py  outlook.py  linkedin.py  apple_notes.py  imessage.py  tasks.py  macos.py
deploy/install_schedule.sh   launchd schedule
profile.md                   your instructions to the assistant
```
