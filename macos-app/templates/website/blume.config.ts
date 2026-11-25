import { defineConfig } from "blume";

const site = "https://__HOMEPAGE__";

export default defineConfig({
  title: "__APP_NAME__",
  description: "__DESC__",
  feedback: false,
  logo: { image: "/icon.png", text: "__APP_NAME__" },
  deployment: {
    site,
  },
  github: {
    owner: "__GH_OWNER__",
    repo: "__GH_NAME__",
    dir: "website",
  },
  // Add a page here when you add its file in docs/ (for example /how-it-works, /privacy, /glossary).
  navigation: {
    sidebar: ["/overview", "/install", "/build", "/release"],
  },
  theme: {
    fonts: { body: "geist", display: "geist", mono: "geist-mono" },
    radius: "sm",
  },
});
