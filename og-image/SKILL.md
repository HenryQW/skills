---
name: og-image
description: Generate a restrained branded 1200×630 Open Graph PNG from a personal avatar, secondary product mark, title, tagline, owner label, and site URL. Use when creating, replacing, or polishing an og.png or social preview image for a website.
---

# OG Image

Create one legible social card with clear identity and minimal copy. Reuse the
site's existing avatar, logo, colors, and wording; do not invent branding.

## Workflow

1. Inspect current metadata, favicon/avatar sources, product logo, and theme
   colors. Prefer the highest-resolution square avatar source over `.ico`.
2. Keep the hierarchy fixed:
   - personal avatar and owner in the top-left;
   - site URL in the top-right;
   - title and one tagline as the main copy;
   - product mark as the secondary visual;
   - one short accent rule and, when useful, one brief footer label.
3. Keep the title under 22 characters and tagline under 46 characters. If copy
   exceeds either limit, shorten it with the user or make a deliberate custom
   layout instead of silently shrinking text.
4. Create a temporary JSON config with absolute paths:

   ```json
   {
     "title": "Henry Pi Harness",
     "tagline": "Built on Pi. Tuned by Henry.",
     "owner": "Henry Wang",
     "descriptor": "Personal Pi harness",
     "site": "pi.henry.wang",
     "footer": "Extensions for Pi",
     "avatar": "/absolute/path/avatar.png",
     "mark": "/absolute/path/product-logo.svg",
     "output": "/absolute/path/public/og.png",
     "colors": {
       "background": "#101828",
       "foreground": "#f0eee9",
       "muted": "#cdd1d9",
       "border": "#394152",
       "accent": "#1d4ed8"
     }
   }
   ```

5. Run the bundled renderer from the target project root:

   ```sh
   node "$SKILL_DIR/scripts/render-og.mjs" /tmp/og-image.json
   ```

   The target project must already provide `sharp`. Reuse it when present. Do
   not add a dependency without approval; use the project's existing image
   renderer when Sharp is unavailable.
6. Open the PNG and inspect it at full size. Check safe margins, text clipping,
   avatar clarity, mark prominence, and contrast. Revise once only when a
   visible issue exists.
7. Wire the absolute public URL into `og:image` and `twitter:image`, including
   width `1200`, height `630`, and useful alt text. Build the site and inspect
   generated metadata.

Keep the editable source assets. Never use an SVG directly as the social image;
render a PNG for broad crawler support.
