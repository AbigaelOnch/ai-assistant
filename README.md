# Personal AI Assistant

A Claude-powered assistant that runs on your own computer (Windows or Mac). It checks
your **Gmail, LinkedIn and Outlook** (plus **Apple Notes and iMessage** on a Mac), then
works on your behalf:

- summarizes what's new into a brief
- pulls action items into a task list
- saves **draft** replies in Gmail and Outlook
- **asks you first** before it sends anything

You use it in your browser. No terminal needed once it's set up.

```
          ┌──────────── Claude (Anthropic API) ─────────────┐
          │   decides what to read, what to do, what to ask │
          └───────┬─────────────────────────────────────────┘
                  │ tool calls
   ┌──────────┬───┴──────┬───────────┬────────────┬──────────┐
 Gmail     Outlook    LinkedIn    Apple Notes   iMessage    Tasks
 (API)     (Graph)    (via Gmail)  (Mac only)   (Mac only)  (SQLite)
                  │
   anything that sends ──► "Waiting for you" ──► you approve / deny
```

## Quick start (Windows)

1. **Install Python.** Open the Microsoft Store, search for **Python 3.13** (publisher:
   Python Software Foundation) and press Get. Use `python`, not `py`, in commands.
2. **Get the code.** Unzip `ai-assistant.zip`, or clone your repo
   (`git clone https://github.com/AbigaelOnch/ai-assistant`).
3. **Double-click `setup_windows.bat`.** It creates the environment, installs the packages
   and opens `.env` in Notepad. If Windows says *"Windows protected your PC"*, choose
   **More info → Run anyway**.
4. **Add your Claude API key** to `.env` (see [Claude API key](#1-claude-api-key)), save, close Notepad.
5. **Connect Gmail** ([steps below](#2-connect-gmail-and-linkedin)), then double-click
   **`connect_windows.bat`** to sign in once.
6. **Double-click `Assistant.bat`.** Your browser opens on the assistant.

## Quick start (Mac)

Needs Python 3.10 or newer (`brew install python@3.12`).

```bash
cd ai-assistant
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env && mkdir -p secrets     # then edit .env
python -m assistant connect                   # sign in and test each source
python -m assistant ui                        # open the assistant in your browser
```
On a Mac, also set `ENABLED_TOOLS=gmail,outlook,linkedin,notes,imessage,tasks` in `.env`
and see [Apple Notes and iMessage permissions](#4-apple-notes-and-imessage-permissions-mac).

## Using it

`Assistant.bat` (Windows) or `python -m assistant ui` (Mac) opens
`http://127.0.0.1:8765` in your browser:

| Section | What it does |
|---|---|
| **Chat** | Ask things like "what needs my attention today?" or "draft replies for anything that needs one". Shows live progress while it works. |
| **Check now** | Goes through everything new since the last check and saves a brief. |
| **Waiting for you** | Every email or message the assistant wants to send, with the full text. Edit it, then **Approve and send** or **Don't send**. |
| **Tasks** | Action items it found, plus your own, with due dates. |
| **Briefs** | Every saved check. |
| **About you** | Edit your profile: who matters, what to ignore, how your replies should sound. |

Use **Quit assistant** in the sidebar to stop it. Scheduled checks keep running either way.
The page only works on your own computer; other websites can't talk to it
(see `ARCHITECTURE.md`, section 8).

Text-only alternatives, if you prefer them:

```
python -m assistant chat        talk to it in the terminal (asks y/N before sending)
python -m assistant run         one full check
python -m assistant approvals   approve or deny queued sends
python -m assistant tasks       show your task list
python -m assistant connect     sign in and test each source
```
On Windows, `run_windows.bat` opens the text chat, and `run_windows.bat run`,
`approvals` or `connect` run the other commands.

## How safety works

- **Drafts are free; sends need approval.** `send_gmail`, `send_gmail_reply`,
  `send_outlook_reply` and `send_imessage` never run directly. In the browser and in
  scheduled runs they wait under **Waiting for you**. You can edit the text first, but not the
  recipient.
- **Emails and messages are treated as untrusted.** The assistant is told never to follow
  instructions found inside them (a common trick: "AI assistant, forward this to…"). The
  approval step is the backstop.
- **Everything stays on your computer** except the calls to Claude and to Google/Microsoft.
  Your sign-in tokens live in `secrets/`, your settings in `.env`, your data in `data/`,
  and all three are git-ignored.
- **Links in emails appear as plain text** in the chat, so a phishing link can't be clicked by accident.

## Setup details

### 1. Claude API key
1. Create a key at <https://console.anthropic.com> and paste it in `.env` after
   `ANTHROPIC_API_KEY=` on the same line (no spaces or quotes).
2. **Add credit** at <https://console.anthropic.com/settings/billing>. The API is billed
   separately from a Claude.ai subscription and doesn't work with a zero balance. $5–10 is
   plenty to start; a full check usually costs a few cents.

If the key is wrong, the assistant says which line of `.env` to fix. It never prints the whole key.

### 2. Connect Gmail (and LinkedIn)
In <https://console.cloud.google.com>, signed in with the Gmail account you want to use:

1. **Create a project** (any name, for example "AI Assistant"). Accept the Google Cloud terms if asked.
   No billing or free trial is needed.
2. **APIs & Services → Library → Gmail API → Enable.**
3. **Google Auth Platform → Get started.** App name: anything. Support email and contact
   email: your address. Audience: **External**.
4. **Google Auth Platform → Audience → Test users → Add users** and add your own Gmail address.
5. **Google Auth Platform → Clients → Create client → Desktop app → Create → Download JSON.**
   Save the file as `secrets\gmail_credentials.json` (`secrets/` on a Mac).
6. Sign in once: double-click `connect_windows.bat` (or run `python -m assistant connect`).
   A browser opens. Pick your account. If it says **"Google hasn't verified this app"**, choose
   **Continue**. That's expected, because the app is yours. Allow the Gmail permissions.

The sign-in is saved in `secrets/gmail_token.json`.

> **Heads-up:** while the Google app is in **Testing** mode, Google expires its sign-in about every
> 7 days. When Gmail stops working, delete `secrets\gmail_token.json` and sign in again with
> `connect_windows.bat`. To avoid this, open Google Auth Platform → Audience and press
> **Publish app**. For personal use it stays unverified, so you still click Continue once.

**LinkedIn** has no public API for your messages, invitations or feed, and automating the
website breaks LinkedIn's terms. The assistant reads the **notification emails LinkedIn
sends to your Gmail** instead. Turn them on in LinkedIn → Settings → Notifications →
Email (messages, invitations, mentions, job alerts). It can tell you about a message and
add a task, but you reply on LinkedIn yourself. If your LinkedIn email is an Outlook
address, forward LinkedIn mail to Gmail.

### 3. Connect Outlook / Microsoft 365 (optional)
Outlook is skipped automatically until `MS_CLIENT_ID` is set in `.env`.

1. Open <https://entra.microsoft.com> → **App registrations → New registration**.
   Supported accounts: *any org directory + personal Microsoft accounts*.
   (Personal Microsoft accounts need a free Azure account to register an app.)
2. In the new app: **Authentication → Allow public client flows → Yes**.
3. **API permissions → Microsoft Graph → Delegated**: `Mail.ReadWrite`, `Mail.Send`.
4. Copy the **Application (client) ID** into `.env` as `MS_CLIENT_ID`.

The first sign-in prints a code and a web address. Open it, enter the code, and sign in.
Work accounts may need an admin to approve the app.

### 4. Apple Notes and iMessage permissions (Mac)
These two sources only exist on a Mac and are skipped on Windows.
- **Full Disk Access** (to read Messages): System Settings → Privacy & Security → Full Disk
  Access → add your terminal app, and the real Python behind `.venv/bin/python`
  (`readlink -f .venv/bin/python`) if you use the schedule.
- **Automation** (to control Notes, Messages, Contacts): macOS asks the first time. Click **OK**.
  Review later under Privacy & Security → Automation.

### 5. Tell it about you
Open **About you** in the browser (or edit `profile.md`): who matters most, what it may do on
its own, what to always ask about, what to ignore, and how your replies should sound.
It's read on every run, so this is the best way to improve the results.

### 6. Run it on a schedule (optional)
**Windows:**
```powershell
powershell -ExecutionPolicy Bypass -File deploy\install_schedule_windows.ps1
```
**Mac:**
```bash
chmod +x deploy/install_schedule.sh && ./deploy/install_schedule.sh
```
Both check at 8:00, 12:00 and 17:00 (edit the hours in the script). The computer must be
awake. Anything it wants to send waits under **Waiting for you**. Output goes to
`data/assistant.log`, and each brief is saved in `data/briefs/`.
Remove it with `install_schedule.sh uninstall` or `install_schedule_windows.ps1 -Uninstall`.

## Troubleshooting

| What you see | What to do |
|---|---|
| `py` isn't recognized | Use `python` instead. Install it from the Microsoft Store if needed. |
| "Windows protected your PC" on a `.bat` file | **More info → Run anyway.** The scripts are in this folder. |
| `Claude API key problem: …` | The message names the problem. Usually `.env` needs exactly one line: `ANTHROPIC_API_KEY=sk-ant-…` |
| "Your Anthropic API account is out of credit" | Add credit at console.anthropic.com/settings/billing. |
| Gmail: "Access blocked" or error 403 `access_denied` | Add your address under Google Auth Platform → Audience → Test users. |
| Gmail worked, then stopped after about a week | The 7-day Testing sign-in expired. Delete `secrets\gmail_token.json` and run `connect_windows.bat`. |
| Browser didn't open | Go to `http://127.0.0.1:8765`. If nothing loads, read `data\ui.log`. |
| Page says "The assistant has stopped" | Double-click `Assistant.bat` again. |
| "Skipping outlook" | Expected until `MS_CLIENT_ID` is set. |

## Turning sources on or off
Set `ENABLED_TOOLS` in `.env`, for example `ENABLED_TOOLS=gmail,linkedin,tasks`.
`notes` and `imessage` are ignored on Windows.

## Costs
Each check makes about 10–30 Claude API calls, depending on how much is new. To spend less,
lower `LOOKBACK_HOURS`, check fewer times a day, or set `ASSISTANT_MODEL` in `.env` to a
smaller model such as `claude-haiku-5-5`.

## Adding your own tools
Any Python function becomes a tool with the `@tool` decorator. See
`assistant/tools/tasks.py` for the simplest example:

```python
@tool("calendar", "Create a calendar event.", {"title": {"type": "string"}, ...},
      ["title"], needs_approval=True)
def create_event(title, ...):
    ...
```
Then import the module in `assistant/tools/__init__.py → load_tools`, add its group to
`ENABLED_TOOLS`, and add a friendly label in `ui.html` if you want it shown nicely. Good next
additions: Google Calendar, Outlook Calendar (`Calendars.ReadWrite`), Todoist, Notion, Slack.

## Project layout
```
assistant/
  __main__.py      command line: ui, run, chat, approvals, tasks, connect
  web.py, ui.html  the browser interface (Flask, 127.0.0.1 only)
  agent.py         Claude tool-use loop, system prompt, approval gate
  checks.py        the regular check, shared by the browser, CLI and schedule
  errors.py        plain-language messages for Claude API errors
  db.py            SQLite: tasks, approvals, run log
  config.py        settings from .env, API key checks
  tools/           gmail, outlook, linkedin, apple_notes, imessage, tasks, macos
deploy/            schedule installers (Mac launchd, Windows Task Scheduler)
Assistant.bat      open the browser interface (Windows)
setup_windows.bat  one-time setup (Windows)
connect_windows.bat  sign in to Gmail / Outlook (Windows)
run_windows.bat    text chat and CLI commands (Windows)
profile.md         your instructions to the assistant
ARCHITECTURE.md    design and security notes
```
