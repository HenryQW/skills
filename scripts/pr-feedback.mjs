#!/usr/bin/env node

import assert from "node:assert/strict";
import { spawnSync } from "node:child_process";
import { mkdirSync, readFileSync, writeFileSync } from "node:fs";
import { dirname, resolve } from "node:path";

const PR_FIELDS = "number,url,title,state,baseRefName,headRefName,headRefOid,headRepository";
const PR_URL = /^https:\/\/github\.com\/([^/]+)\/([^/]+)\/pull\/([1-9][0-9]*)$/;

const FEEDBACK_QUERY = `
query Feedback($owner:String!,$repo:String!,$number:Int!,$commentsCursor:String,$reviewsCursor:String,$threadsCursor:String){
  repository(owner:$owner,name:$repo){pullRequest(number:$number){
    comments(first:100,after:$commentsCursor){pageInfo{hasNextPage endCursor} nodes{id url body createdAt author{login}}}
    reviews(first:100,after:$reviewsCursor){pageInfo{hasNextPage endCursor} nodes{id url state body submittedAt author{login}}}
    reviewThreads(first:100,after:$threadsCursor){pageInfo{hasNextPage endCursor} nodes{
      id isResolved isOutdated path line diffSide startLine startDiffSide originalLine originalStartLine
      comments(first:100){pageInfo{hasNextPage endCursor} nodes{id url body createdAt author{login}}}
    }}
  }}
}`;

const THREAD_REPLIES_QUERY = `
query ThreadReplies($threadId:ID!,$cursor:String){node(id:$threadId){... on PullRequestReviewThread{
  comments(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{id url body createdAt author{login}}}
}}}`;

const THREAD_STATES_QUERY = `
query ThreadStates($owner:String!,$repo:String!,$number:Int!,$cursor:String){
  repository(owner:$owner,name:$repo){pullRequest(number:$number){
    reviewThreads(first:100,after:$cursor){pageInfo{hasNextPage endCursor} nodes{id isResolved}}
  }}
}`;

const RESOLVE_THREAD_MUTATION = `
mutation ResolveThread($threadId:ID!){resolveReviewThread(input:{threadId:$threadId}){thread{id isResolved}}}`;

class FeedbackError extends Error {}
class UsageError extends Error {}

function isRecord(value) {
  return value !== null && typeof value === "object" && !Array.isArray(value);
}

function text(value, label) {
  if (typeof value !== "string") throw new FeedbackError(`${label} must be a string`);
  return value;
}

function requiredText(value, label) {
  const result = text(value, label);
  if (!result) throw new FeedbackError(`${label} is missing`);
  return result;
}

function bool(value, label) {
  if (typeof value !== "boolean") throw new FeedbackError(`${label} must be a boolean`);
  return value;
}

function list(value, label) {
  if (!Array.isArray(value)) throw new FeedbackError(`${label} must be an array`);
  return value;
}

function run(program, args, input) {
  const result = spawnSync(program, args, {
    encoding: "utf8",
    input,
    maxBuffer: 64 * 1024 * 1024,
  });
  if (result.error) throw new FeedbackError(`${program} failed: ${result.error.message}`);
  if (result.status !== 0) {
    const detail = (result.stderr || result.stdout || "").trim();
    throw new FeedbackError(`${program} ${args.slice(0, 3).join(" ")} failed${detail ? `: ${detail}` : ""}`);
  }
  return result.stdout;
}

function jsonCommand(program, args, input) {
  const output = run(program, args, input);
  try {
    const value = JSON.parse(output);
    if (!isRecord(value)) throw new Error("root is not an object");
    return value;
  } catch (error) {
    throw new FeedbackError(`invalid JSON from ${program}: ${error.message}`);
  }
}

function git(...args) {
  return run("git", args).trim();
}

function requireGh() {
  run("gh", ["auth", "status"]);
}

function cleanHead() {
  git("rev-parse", "--show-toplevel");
  if (git("status", "--porcelain")) throw new FeedbackError("index and worktree must be clean");
  return requiredText(git("rev-parse", "HEAD"), "local HEAD");
}

function validatePrRef(pr) {
  if (pr === undefined) return;
  if (/^[1-9][0-9]*$/.test(pr) || PR_URL.test(pr)) return;
  throw new UsageError("--pr must be a positive PR number or https://github.com/OWNER/REPO/pull/NUMBER");
}

function readOpenPr(pr) {
  const args = ["pr", "view"];
  if (pr !== undefined) args.push(pr);
  args.push("--json", PR_FIELDS);
  const value = jsonCommand("gh", args);
  if (value.state !== "OPEN") throw new FeedbackError(`PR must be OPEN, got ${JSON.stringify(value.state)}`);

  const url = requiredText(value.url, "PR URL");
  const match = PR_URL.exec(url);
  if (!match) throw new FeedbackError(`unsupported PR URL: ${url}`);
  if (!Number.isInteger(value.number)) throw new FeedbackError("PR number must be an integer");
  requiredText(value.headRefName, "PR head ref");
  requiredText(value.headRefOid, "PR head OID");
  if (!isRecord(value.headRepository)) throw new FeedbackError("PR head repository identity is unavailable");
  requiredText(value.headRepository.nameWithOwner, "PR head repository");

  return {
    ...value,
    baseRepository: `${match[1]}/${match[2]}`,
  };
}

function requireMatchingHead(metadata, localHead) {
  if (metadata.headRefOid !== localHead) {
    throw new FeedbackError(`local HEAD ${localHead} does not match PR head ${metadata.headRefOid}`);
  }
}

function requireDiscoveryBranch(pr, metadata) {
  if (pr !== undefined) return;
  const branch = git("branch", "--show-current");
  if (branch !== metadata.headRefName) {
    throw new FeedbackError(`local branch ${JSON.stringify(branch)} does not match PR head branch ${JSON.stringify(metadata.headRefName)}`);
  }
}

function graphql(query, variables) {
  const args = ["api", "graphql", "-F", "query=@-"];
  for (const [name, value] of Object.entries(variables)) {
    if (value !== null && value !== undefined) args.push("-F", `${name}=${value}`);
  }
  const response = jsonCommand("gh", args, query);
  if (response.errors && (!Array.isArray(response.errors) || response.errors.length)) {
    throw new FeedbackError(`GitHub GraphQL errors: ${JSON.stringify(response.errors)}`);
  }
  if (!isRecord(response.data)) throw new FeedbackError("GitHub GraphQL response has no data");
  return response.data;
}

function pullRequest(data) {
  if (!isRecord(data.repository) || !isRecord(data.repository.pullRequest)) {
    throw new FeedbackError("pull request disappeared");
  }
  return data.repository.pullRequest;
}

function connection(value, label) {
  if (!isRecord(value) || !isRecord(value.pageInfo)) throw new FeedbackError(`invalid ${label} connection`);
  const nodes = list(value.nodes, `${label} nodes`);
  const hasNextPage = bool(value.pageInfo.hasNextPage, `${label} hasNextPage`);
  const endCursor = value.pageInfo.endCursor;
  if (hasNextPage && (typeof endCursor !== "string" || !endCursor)) {
    throw new FeedbackError(`missing pagination cursor for ${label}`);
  }
  return { nodes, hasNextPage, endCursor };
}

function collectFeedback(metadata, request = graphql) {
  const [owner, repo] = metadata.baseRepository.split("/", 2);
  const targets = [
    { key: "conversationComments", field: "comments", cursor: "commentsCursor", label: "conversation comments" },
    { key: "reviews", field: "reviews", cursor: "reviewsCursor", label: "reviews" },
    { key: "reviewThreads", field: "reviewThreads", cursor: "threadsCursor", label: "review threads" },
  ];
  const results = Object.fromEntries(targets.map(({ key }) => [key, []]));
  const cursors = Object.fromEntries(targets.map(({ key }) => [key, null]));
  const pending = new Set(targets.map(({ key }) => key));

  while (pending.size) {
    const data = request(FEEDBACK_QUERY, {
      owner,
      repo,
      number: metadata.number,
      commentsCursor: cursors.conversationComments,
      reviewsCursor: cursors.reviews,
      threadsCursor: cursors.reviewThreads,
    });
    const pr = pullRequest(data);
    for (const target of targets) {
      if (!pending.has(target.key)) continue;
      const page = connection(pr[target.field], target.label);
      results[target.key].push(...page.nodes);
      if (page.hasNextPage) {
        cursors[target.key] = page.endCursor;
      } else {
        pending.delete(target.key);
      }
    }
  }

  results.reviewThreads = results.reviewThreads.map((thread) => collectReplies(thread, request));
  return {
    pullRequest: metadata,
    conversationComments: results.conversationComments,
    reviews: results.reviews,
    reviewThreads: results.reviewThreads,
  };
}

function collectReplies(thread, request) {
  if (!isRecord(thread)) throw new FeedbackError("invalid review thread");
  const threadId = requiredText(thread.id, "review thread ID");
  let page = connection(thread.comments, `replies for ${threadId}`);
  const comments = [...page.nodes];
  while (page.hasNextPage) {
    const data = request(THREAD_REPLIES_QUERY, { threadId, cursor: page.endCursor });
    if (!isRecord(data.node)) throw new FeedbackError(`review thread disappeared: ${threadId}`);
    page = connection(data.node.comments, `replies for ${threadId}`);
    comments.push(...page.nodes);
  }
  return { ...thread, comments };
}

function collectThreadStates(metadata, request = graphql) {
  const [owner, repo] = metadata.baseRepository.split("/", 2);
  const states = new Map();
  let cursor = null;
  for (;;) {
    const data = request(THREAD_STATES_QUERY, { owner, repo, number: metadata.number, cursor });
    const page = connection(pullRequest(data).reviewThreads, "review threads");
    for (const thread of page.nodes) {
      if (!isRecord(thread)) throw new FeedbackError("invalid review thread state");
      states.set(requiredText(thread.id, "review thread ID"), bool(thread.isResolved, "review thread isResolved"));
    }
    if (!page.hasNextPage) return states;
    cursor = page.endCursor;
  }
}

function resolveThread(threadId) {
  const data = graphql(RESOLVE_THREAD_MUTATION, { threadId });
  const result = data.resolveReviewThread;
  if (!isRecord(result) || !isRecord(result.thread)) throw new FeedbackError(`failed to resolve ${threadId}`);
  if (result.thread.id !== threadId || result.thread.isResolved !== true) {
    throw new FeedbackError(`GitHub did not resolve ${threadId}`);
  }
}

function parsedSnapshot(raw, path) {
  let value;
  try {
    value = JSON.parse(raw);
  } catch (error) {
    throw new FeedbackError(`invalid feedback JSON ${path}: ${error.message}`);
  }
  if (!isRecord(value) || !isRecord(value.pullRequest) || !Array.isArray(value.reviews) || !Array.isArray(value.reviewThreads)) {
    throw new FeedbackError(`invalid feedback JSON ${path}`);
  }
  requiredText(value.pullRequest.url, "snapshot PR URL");
  return value;
}

function snapshot(path) {
  try {
    return parsedSnapshot(readFileSync(path, "utf8"), path);
  } catch (error) {
    if (error instanceof FeedbackError) throw error;
    throw new FeedbackError(`invalid feedback JSON ${path}: ${error.message}`);
  }
}

function previousSnapshot(path) {
  try {
    return parsedSnapshot(readFileSync(path, "utf8"), path);
  } catch (error) {
    if (error?.code === "ENOENT") return null;
    if (error instanceof FeedbackError) throw error;
    throw new FeedbackError(`invalid feedback JSON ${path}: ${error.message}`);
  }
}

function nodeIds(nodes, label) {
  return nodes.map((node, index) => {
    if (!isRecord(node)) throw new FeedbackError(`invalid ${label} ${index + 1}`);
    return requiredText(node.id, `${label} ID`);
  });
}

function login(author) {
  if (author === null) return "-";
  if (!isRecord(author)) throw new FeedbackError("comment author is invalid");
  return requiredText(author.login, "comment author login");
}

function location(thread) {
  const path = thread.path === null ? "-" : text(thread.path, "thread path");
  const line = Number.isInteger(thread.line)
    ? thread.line
    : Number.isInteger(thread.originalLine)
      ? thread.originalLine
      : "-";
  return `${path}:${line}`;
}

function printFetchSummary(data, previous, out) {
  if (previous && previous.pullRequest.url !== data.pullRequest.url) {
    throw new FeedbackError(`existing feedback JSON belongs to ${previous.pullRequest.url}, not ${data.pullRequest.url}`);
  }
  const oldReviewIds = new Set(previous ? nodeIds(previous.reviews, "previous review") : []);
  const newReviewIds = nodeIds(data.reviews, "review").filter((id) => !oldReviewIds.has(id));
  const resolved = [];
  const unresolved = [];
  for (const thread of data.reviewThreads) {
    if (!isRecord(thread)) throw new FeedbackError("invalid review thread");
    if (bool(thread.isResolved, "review thread isResolved")) resolved.push(thread);
    else unresolved.push(thread);
  }

  console.log(`snapshot=${out}`);
  console.log(`counts comments=${data.conversationComments.length} reviews=${data.reviews.length} threads=${data.reviewThreads.length} unresolved=${unresolved.length}`);
  console.log(`new_review_ids=${newReviewIds.join(",") || "-"}`);
  console.log("unresolved_threads=thread\tlocation\toutdated\tcomment\tauthor\tbody");
  if (!unresolved.length) console.log("-");
  for (const thread of unresolved) {
    const threadId = requiredText(thread.id, "review thread ID");
    const outdated = bool(thread.isOutdated, "review thread isOutdated") ? "yes" : "no";
    const comments = list(thread.comments, `replies for ${threadId}`);
    if (!comments.length) {
      console.log([threadId, location(thread), outdated, "-", "-", "-"].join("\t"));
      continue;
    }
    for (const comment of comments) {
      if (!isRecord(comment)) throw new FeedbackError(`invalid comment in ${threadId}`);
      console.log([
        threadId,
        location(thread),
        outdated,
        requiredText(comment.id, "comment ID"),
        login(comment.author),
        JSON.stringify(text(comment.body, "comment body")),
      ].join("\t"));
    }
  }
  console.log(`resolved_thread_ids=${nodeIds(resolved, "resolved review thread").join(",") || "-"}`);
}

function writeSnapshot(path, data) {
  const destination = resolve(path);
  mkdirSync(dirname(destination), { recursive: true });
  writeFileSync(destination, `${JSON.stringify(data)}\n`);
  return destination;
}

function fetchFeedback(options) {
  requireGh();
  const out = resolve(options.out);
  const previous = previousSnapshot(out);
  const localHead = cleanHead();
  const initial = readOpenPr(options.pr);
  if (previous && previous.pullRequest.url !== initial.url) {
    throw new FeedbackError(`existing feedback JSON belongs to ${previous.pullRequest.url}, not ${initial.url}`);
  }
  requireMatchingHead(initial, localHead);
  requireDiscoveryBranch(options.pr, initial);
  const data = collectFeedback(initial);
  const current = readOpenPr(initial.url);
  if (current.headRefOid !== initial.headRefOid) {
    throw new FeedbackError(`PR head changed during fetch: ${initial.headRefOid} -> ${current.headRefOid}`);
  }
  requireMatchingHead(current, localHead);
  const saved = writeSnapshot(out, { ...data, pullRequest: current });
  printFetchSummary({ ...data, pullRequest: current }, previous, saved);
}

function currentExpectedHead(pr, expectedHead) {
  const localHead = cleanHead();
  if (localHead !== expectedHead) {
    throw new FeedbackError(`local HEAD ${localHead} does not match expected head ${expectedHead}`);
  }
  const metadata = readOpenPr(pr);
  if (metadata.headRefOid !== expectedHead) {
    throw new FeedbackError(`PR head ${metadata.headRefOid} does not match expected head ${expectedHead}`);
  }
  return metadata;
}

function resolveFeedback(options) {
  requireGh();
  let metadata = currentExpectedHead(options.pr, options.expectedHead);
  const states = collectThreadStates(metadata);
  const requested = options.threads;
  const missing = requested.filter((threadId) => !states.has(threadId));
  if (missing.length) throw new FeedbackError(`review thread IDs not found: ${missing.join(",")}`);

  metadata = currentExpectedHead(metadata.url, options.expectedHead);
  for (const threadId of requested) {
    if (!states.get(threadId)) resolveThread(threadId);
  }

  metadata = currentExpectedHead(metadata.url, options.expectedHead);
  const verified = collectThreadStates(metadata);
  const unresolved = requested.filter((threadId) => verified.get(threadId) !== true);
  if (unresolved.length) throw new FeedbackError(`resolution verification failed: ${unresolved.join(",")}`);
  console.log(`resolved_thread_ids=${requested.join(",")}`);
}

function githubRemote(url) {
  const scp = /^(?:[^@]+@)?github\.com:([^/]+)\/([^/]+?)(?:\.git)?$/i.exec(url);
  if (scp) return `${scp[1]}/${scp[2]}`.toLowerCase();
  try {
    const parsed = new URL(url);
    if (parsed.hostname.toLowerCase() !== "github.com") return null;
    const parts = parsed.pathname.replace(/^\/+|\/+$/g, "").split("/");
    if (parts.length !== 2 || !parts[0] || !parts[1]) return null;
    return `${parts[0]}/${parts[1].replace(/\.git$/i, "")}`.toLowerCase();
  } catch {
    return null;
  }
}

function pushRemote(repository) {
  const target = requiredText(repository, "PR head repository").toLowerCase();
  const matches = git("remote").split("\n").filter(Boolean).filter((remote) => {
    const urls = run("git", ["remote", "get-url", "--push", "--all", remote]).trim().split("\n");
    return urls.some((url) => githubRemote(url) === target);
  });
  if (matches.length !== 1) {
    throw new FeedbackError(`expected one push remote for ${repository}, found ${matches.length}: ${matches.join(",") || "-"}`);
  }
  return matches[0];
}

function pushHead(options) {
  requireGh();
  const saved = snapshot(resolve(options.snapshot));
  const initial = saved.pullRequest;
  const initialHead = requiredText(initial.headRefOid, "snapshot PR head");
  const localHead = cleanHead();
  const current = readOpenPr(initial.url);
  if (current.headRefOid !== initialHead) {
    throw new FeedbackError(`PR head changed since feedback fetch: ${initialHead} -> ${current.headRefOid}`);
  }
  if (localHead === current.headRefOid) throw new FeedbackError("local HEAD already matches PR head; no push needed");
  const remote = pushRemote(current.headRepository.nameWithOwner);
  run("git", ["push", remote, `HEAD:${current.headRefName}`]);
  const pushed = readOpenPr(current.url);
  if (pushed.headRefOid !== localHead) {
    throw new FeedbackError(`push did not update PR head to local HEAD: ${pushed.headRefOid} != ${localHead}`);
  }
  console.log(`pushed_head=${localHead} remote=${remote} branch=${current.headRefName}`);
}

function page(nodes, hasNextPage = false, endCursor = null) {
  return { nodes, pageInfo: { hasNextPage, endCursor } };
}

function selfTest() {
  assert.equal(githubRemote("git@github.com:Owner/Repo.git"), "owner/repo");
  assert.equal(githubRemote("ssh://git@github.com/Owner/Repo.git"), "owner/repo");
  assert.equal(githubRemote("https://github.com/Owner/Repo.git"), "owner/repo");
  assert.equal(githubRemote("https://example.com/Owner/Repo.git"), null);

  let feedbackPages = 0;
  const request = (query) => {
    if (query === THREAD_REPLIES_QUERY) return { node: { comments: page([{ id: "reply-2" }]) } };
    assert.equal(query, FEEDBACK_QUERY);
    feedbackPages += 1;
    const first = feedbackPages === 1;
    return {
      repository: {
        pullRequest: {
          comments: page([{ id: first ? "comment-1" : "comment-2" }], first, first ? "comments-2" : null),
          reviews: page([{ id: "review-1" }]),
          reviewThreads: page([{
            id: first ? "thread-1" : "thread-2",
            isResolved: false,
            isOutdated: false,
            comments: page([{ id: "reply-1" }], first, first ? "replies-2" : null),
          }], first, first ? "threads-2" : null),
        },
      },
    };
  };
  const metadata = { baseRepository: "owner/repo", number: 1 };
  const fetched = collectFeedback(metadata, request);
  assert.deepEqual(nodeIds(fetched.conversationComments, "comment"), ["comment-1", "comment-2"]);
  assert.deepEqual(nodeIds(fetched.reviews, "review"), ["review-1"]);
  assert.deepEqual(nodeIds(fetched.reviewThreads, "thread"), ["thread-1", "thread-2"]);
  assert.deepEqual(nodeIds(fetched.reviewThreads[0].comments, "reply"), ["reply-1", "reply-2"]);

  let statePages = 0;
  const stateRequest = () => {
    statePages += 1;
    return { repository: { pullRequest: { reviewThreads: page(
      [{ id: `thread-${statePages}`, isResolved: true }],
      statePages === 1,
      statePages === 1 ? "states-2" : null,
    ) } } };
  };
  assert.deepEqual([...collectThreadStates(metadata, stateRequest)], [["thread-1", true], ["thread-2", true]]);

  assert.throws(
    () => collectFeedback(metadata, () => ({ repository: { pullRequest: {
      comments: page([], true), reviews: page([]), reviewThreads: page([]),
    } } })),
    /missing pagination cursor for conversation comments/,
  );
  console.log("pr-feedback self-test ok");
}

function usage() {
  return `usage:
  node scripts/pr-feedback.mjs fetch [--pr PR] --out FILE
  node scripts/pr-feedback.mjs push --snapshot FILE
  node scripts/pr-feedback.mjs resolve [--pr PR] --expected-head SHA --thread ID [--thread ID ...]
  node scripts/pr-feedback.mjs self-test`;
}

function parse(command, args) {
  const allowed = {
    fetch: new Set(["--pr", "--out"]),
    push: new Set(["--snapshot"]),
    resolve: new Set(["--pr", "--expected-head", "--thread"]),
  }[command];
  if (!allowed) throw new UsageError(`unknown command: ${command}`);
  const values = { threads: [] };
  for (let index = 0; index < args.length; index += 1) {
    const flag = args[index];
    if (!allowed.has(flag)) throw new UsageError(`unsupported ${flag} for ${command}`);
    const value = args[index + 1];
    if (value === undefined || value.startsWith("--")) throw new UsageError(`${flag} needs a value`);
    index += 1;
    if (flag === "--thread") {
      values.threads.push(value);
      continue;
    }
    const key = flag.slice(2).replace(/-([a-z])/g, (_, letter) => letter.toUpperCase());
    if (values[key] !== undefined) throw new UsageError(`${flag} was supplied twice`);
    values[key] = value;
  }
  validatePrRef(values.pr);
  if (command === "fetch" && values.out === undefined) throw new UsageError("fetch needs --out");
  if (command === "push" && values.snapshot === undefined) throw new UsageError("push needs --snapshot");
  if (command === "resolve") {
    if (values.expectedHead === undefined) throw new UsageError("resolve needs --expected-head");
    if (!values.threads.length) throw new UsageError("resolve needs at least one --thread");
    if (new Set(values.threads).size !== values.threads.length) throw new UsageError("duplicate --thread");
  }
  return values;
}

function main(argv) {
  if (!argv.length || argv.includes("--help") || argv.includes("-h")) {
    console.log(usage());
    return 0;
  }
  const [command, ...args] = argv;
  if (command === "self-test") {
    if (args.length) throw new UsageError("self-test takes no arguments");
    selfTest();
    return 0;
  }
  const options = parse(command, args);
  if (command === "fetch") fetchFeedback(options);
  if (command === "push") pushHead(options);
  if (command === "resolve") resolveFeedback(options);
  return 0;
}

try {
  process.exitCode = main(process.argv.slice(2));
} catch (error) {
  console.error(`error: ${error.message}`);
  if (error instanceof UsageError) console.error(usage());
  process.exitCode = error instanceof UsageError ? 2 : 1;
}
