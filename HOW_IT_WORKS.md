# How ClearTrail Works

A plain-language guide to understanding ClearTrail.

---

## The Problem We're Solving

When companies go through compliance audits (like SOC 2 or ISO 27001), auditors show up and say:

*"Prove to me that when your engineers made changes to your software, there was a proper review process. Show me the evidence for every month of the past year."*

Right now, this means someone (usually you or a security team) has to:
1. Dig through GitHub to find pull requests (code changes)
2. Dig through Jira to find the tickets that explain *why* those changes happened
3. Dig through Google Drive to find policy documents
4. Manually match everything up: "This PR relates to this ticket relates to this policy"
5. Put it all in a spreadsheet or folder
6. Hope you didn't miss anything
7. Repeat this panic every audit cycle

It's a nightmare. It takes weeks. Engineers get interrupted constantly with "hey, can you find that thing from March?"

---

## What ClearTrail Does

ClearTrail is like a librarian that:

1. **Connects to where your work already lives** - GitHub, Jira, Google Drive
2. **Automatically collects evidence** - pulls in PRs, tickets, documents
3. **Keeps track of where everything came from** - timestamps, links, who created it
4. **Helps you match evidence to requirements** - "this PR proves we do code reviews"
5. **Lets you approve things calmly** - not under audit pressure
6. **Packages it all up for auditors** - a neat folder with everything they need

The magic: by the time an audit comes, you just press "export." No scrambling.

---

## The Five Steps (The Flow)

Think of it like an assembly line:

```
Connect → Sync → Map → Approve → Export
```

### 1. Connect

You log into ClearTrail and connect your accounts - like when an app asks "Sign in with Google." You click a button, authorize access, and now ClearTrail can see your GitHub repos, Jira projects, or Google Drive folders.

### 2. Sync

ClearTrail reaches out to those services and pulls in "artifacts" - that's just a fancy word for "pieces of evidence." A pull request is an artifact. A Jira ticket is an artifact. A policy document is an artifact.

Each artifact gets a "fingerprint" (a unique code that proves the content hasn't been tampered with) and a timestamp of when it was created.

### 3. Map

This is where you connect the dots. Auditors care about "controls" - specific things you're supposed to do, like "CC7.1: You must have a change management process."

Mapping means saying "this GitHub PR is evidence that we follow control CC7.1."

ClearTrail can suggest mappings using AI ("hey, this PR looks like change management evidence") or you can do it manually.

### 4. Approve

Before evidence is "audit-ready," a human has to sign off. This creates an unchangeable record: "Jane approved this artifact on December 15th at 3:42 PM."

This matters because auditors want to know a real person reviewed the evidence, not just a machine.

### 5. Export

When it's audit time, you create an "evidence packet" - a collection of all the evidence for a specific audit period. ClearTrail bundles it up with a manifest (a table of contents showing what's included, what controls it covers, and that nothing is missing) and uploads it to Google Drive. You send the auditor a link. Done.

---

## The Pieces of the App

ClearTrail has two main parts:

### The Frontend (what you see and click)

This is the website/app interface. When you log in, see your evidence, click buttons - that's the frontend. It's built to feel clean and minimal, like Notion.

### The Backend (the brain behind the scenes)

This is the part you never see. When you click "sync my GitHub," the backend:
- Talks to GitHub's servers
- Downloads your pull requests
- Calculates fingerprints
- Saves everything to the database (where your information is stored)

The backend also handles:
- **User accounts** - logging in, security
- **Storing data** - all your evidence, mappings, approvals
- **Background tasks** - syncing can take a while, so it runs in the background without freezing your screen
- **AI features** - when the AI suggests mappings, the backend talks to OpenAI

---

## The Three Integrations

For the MVP, three connections need to work:

### GitHub
- **Pulls in:** Pull requests (code changes), commits, code reviews
- **Why it matters:** Proves your team reviews code before it goes live

### Jira
- **Pulls in:** Tickets, workflows, approvals
- **Why it matters:** Proves changes are planned and tracked, not random

### Google Drive
- **Pulls in:** Documents, policies
- **Why it matters:** Proves you have written policies (auditors love documents)

---

## How It All Fits Together

Here's a real scenario:

1. Your engineer creates a Jira ticket: "Add password requirements to login"
2. They write code and open a GitHub PR linked to that ticket
3. Another engineer reviews and approves the PR
4. The code goes live

With ClearTrail:
- The Jira ticket gets synced automatically
- The GitHub PR gets synced automatically
- ClearTrail notices they're linked
- AI suggests: "This looks like evidence for CC7.1 (change management)"
- You review and approve
- When the auditor asks "show me your change management process" - it's already there, already approved, already packaged

---

## Key Terms Glossary

| Term | Plain English |
|------|---------------|
| **Artifact** | A piece of evidence (a PR, ticket, document, etc.) |
| **Control** | A specific requirement auditors check for (like "you must review code") |
| **Mapping** | Connecting an artifact to a control ("this PR proves we do code review") |
| **Evidence Packet** | A bundle of all evidence for a specific audit period |
| **Sync** | Pulling in data from GitHub/Jira/Drive |
| **Fingerprint (hash)** | A unique code proving content hasn't been changed |
| **OAuth** | The "Sign in with Google" style login for connecting accounts |
| **Provenance** | The history of where something came from (who, when, where) |

---

## The Vision

**"Audits stop being events. They become exports."**

Instead of stressful, weeks-long scrambles before every audit, compliance becomes something that happens quietly in the background. When the auditor shows up, you press a button and hand them a complete, verified, organized package.

No more chasing engineers. No more hoping you didn't miss something. No more panic.
