# How I Built Read-Tube on Weekends and Late Nights

*A personal note on making something useful, learning in public, and finding a way into coding through AI.*

---

## A Different Way Into Coding

There was a time when I had the chance to insist on a more traditional path into Computer Science, but I did not stay on that road. Even so, I never lost my interest in what coding can give a person.

What I love most about coding is not only the technical side. I love the creativity inside it. I love that a few lines of logic can remove repetitive work, save time, and return energy back to people so they can focus on deeper thinking, better ideas, and more meaningful creation.

For me, vibe coding with AI opened a gate.

It gave me a way to build before I felt fully qualified. It made the distance between "I have an idea" and "I can make this real" much shorter. Instead of waiting until I knew everything, I started learning by building an actual product.

That product became **Read-Tube**.

---

## Built in Weekend Blocks and Night Sessions

This web app was not made in a perfect studio setup or inside a polished startup schedule. It was built in small pieces of time: weekends, late evenings, and the leftover hours after the rest of life had already taken its share.

Sometimes progress looked exciting: a new page finally worked, a result view became readable, or a useful feature came together. Sometimes progress looked much smaller: fixing one broken API call, understanding why a database query failed, or learning how to connect a domain correctly.

But that is exactly why this project matters to me.

I did not learn these concepts as abstract vocabulary. I learned them while trying to make something useful from scratch:

- how the frontend and backend talk to each other
- how a database connection actually supports a real product
- how a domain points to a live app
- how small design and workflow decisions shape a user's experience

Before building this site, ideas like "frontend," "backend," and "database" felt more distant. After building it piece by piece, they became much clearer because I could finally see how they worked together inside one real system.

---

## What Read-Tube Is For

Read-Tube is a web app for people who want to understand video and audio content faster.

Instead of forcing everything into passive watching, the site helps turn content into something easier to scan, read, revisit, and think with. A user can paste a YouTube link or upload audio/video, then get a more readable result with structured text, summaries, and a cleaner way to revisit key ideas.

I wanted it to feel practical first. Not noisy. Not overloaded. Just useful.

### Screenshot Placeholder 1: Homepage / Usage Entry

```text
+----------------------------------------------------------------------------------+
| SCREENSHOT PLACEHOLDER 1                                                         |
| Suggested page: Home page (`/`)                                                  |
| Suggested content: search bar, trending keywords, content list / discovery feed  |
| Purpose: show the first impression of the product and how people enter the site  |
+----------------------------------------------------------------------------------+
```

### Screenshot Placeholder 2: Result Page / Reading Experience

```text
+------------------------------------------------------------------------------------------------+
| SCREENSHOT PLACEHOLDER 2                                                                       |
| Suggested page: Result page (`/result/[id]`)                                                   |
| Suggested content: player + summary + synced transcript paragraph area                         |
| Purpose: show how the product turns a video into a readable, navigable experience              |
+------------------------------------------------------------------------------------------------+
```

---

## What I Learned By Building It

This project taught me more than how to ship a website.

It taught me how to stay with confusion long enough for it to become understanding. It taught me that building is one of the fastest ways to learn. And it reminded me that you do not need a perfect background to make something real and useful.

AI did not replace the learning for me. It accelerated the learning. It gave me a partner for trying, failing, debugging, rewriting, and continuing. That is why I think vibe coding matters: it lowers the wall around creation and gives more people access to building tools they once thought were beyond them.

---

## Structure and Workflow Placeholders

### ASCII Placeholder 1: Project Structure

```text
Read-Tube
├── frontend/
│   ├── app/              # pages, homepage, result page, dashboard
│   ├── components/       # shared UI pieces
│   └── utils/            # API + Supabase helpers
├── backend/
│   ├── main.py           # API entry
│   ├── process_task.py   # task orchestration
│   ├── downloader.py     # media fetching / preparation
│   ├── worker.py         # processing worker
│   └── supabase/         # migrations / schema
└── dev_docs/
    └── ...               # planning notes and documentation
```

### ASCII Placeholder 2: Product Workflow

```text
User pastes link / uploads file
             |
             v
      Frontend (Next.js)
             |
             v
      Backend API (FastAPI)
             |
             +--------------------------+
             |                          |
             v                          v
   Download / media prep         Database / auth state
             |
             v
   Transcription + LLM processing
             |
             v
   Summary + keywords + readable text
             |
             v
   Result page with synced reading experience
```

---

## Still Learning, Still Building

I am still learning from this project, and that is one of the best parts of it.

Every improvement helps me understand the craft better. Every comment from users helps me see what is missing, what is confusing, and what could become more beautiful or more useful. I genuinely appreciate that feedback, because this site is not only something I built. It is also something that is teaching me back.

If you use Read-Tube, I hope it saves you time. I hope it makes long videos easier to understand. And I hope this project shows that sometimes a useful product can begin in a very ordinary place: a few weekends, a few late nights, a lot of curiosity, and the decision to keep building anyway.
