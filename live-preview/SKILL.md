---
name: live-preview
description: Start, verify, or stop a private Tailscale preview of a website or static artifact from the current worktree. Use when the user wants a live review link they can open on another device.
---

# Live preview

Give the reviewer a working link to the requested change. Keep the server attached to an existing process owner.

1. Identify the worktree, the page to review, and one visible detail that distinguishes this change. Reuse an existing preview only when its owner identifies this worktree and the page passes the check below.
2. Choose the project's documented development command for live edits. For static files, serve only the public output directory. Check that its contents and symlinks are suitable for sharing. A static preview shows changes when the output files change.
3. From that worktree, run the server in the foreground through the available managed terminal or session shell. Pass its argument list through `scripts/run.py` in this skill directory. The helper replaces the literal `{host}` argument with the active Tailscale address. Use the server's documented bind option. Let the server choose a free port when supported. Read the actual port from **this launch's output**. On a fixed-port conflict, select another supported port or report the conflict.

   For example, if `dist` contains the intended static output, run:

   ```sh
   python3 <skill-dir>/scripts/run.py python3 -u -m http.server 0 --bind '{host}' --directory dist
   ```

   For a project with a Vite `dev` script that uses pnpm, run:

   ```sh
   python3 <skill-dir>/scripts/run.py pnpm run dev --host '{host}'
   ```

4. Open the requested route at the printed Tailscale address and actual port. Verify the distinguishing detail in the rendered page. For a file download, compare the served bytes with the intended file. Fetch the same route from another authorized Tailscale device when available. If that request fails, check connectivity before sharing the link. If only the host check is possible, say so.
5. Give the user the direct page link and its lifetime. Keep the process handle for reuse or stop. In Herdr, `background_command` is bounded by its configured runtime. Declare write access when the server generates files. If review must outlast that limit, use an available owner with the required lifetime or state the limit.
6. On stop, use the owner's handle for this preview and confirm it exited. Leave other worktrees' servers running.
