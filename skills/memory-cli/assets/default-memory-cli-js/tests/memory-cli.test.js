import assert from "node:assert/strict";
import fs from "node:fs";
import os from "node:os";
import path from "node:path";
import test from "node:test";
import * as memoryCli from "../src/cli.js";

function withProject(fn) {
  const root = fs.mkdtempSync(path.join(os.tmpdir(), "memory-cli-js-"));
  const oldRoot = memoryCli.root;
  memoryCli.setPaths(root);
  fs.mkdirSync(memoryCli.memoryDir);
  fs.writeFileSync(memoryCli.configPath, JSON.stringify({
    priority_thresholds: { blocking_failure: 80, warning_failure: 40 },
    performance_budget_ms: { p95_search: 200, full_test_suite: 5000 }
  }));
  try {
    fn(root);
  } finally {
    memoryCli.setPaths(oldRoot);
    fs.rmSync(root, { recursive: true, force: true });
  }
}

function writeMemory(name, data) {
  fs.writeFileSync(path.join(memoryCli.memoryDir, `${name}.json`), JSON.stringify(data));
}

test("search returns all matches ordered by priority before score", () => withProject(() => {
  writeMemory("high", { id: "high", priority: 90, content: "alpha durable preference", queries: ["alpha"], must_include: ["durable"] });
  writeMemory("low", { id: "low", priority: 20, content: "alpha alpha alpha noisy detail", queries: ["alpha alpha alpha"], must_include: ["noisy"] });

  assert.deepEqual(memoryCli.search("alpha alpha alpha").matches.map((item) => item.id), ["high", "low"]);
}));

test("searchMany returns matches grouped by input keyword order", () => withProject(() => {
  writeMemory("shared", {
    id: "shared",
    priority: 70,
    content: "durable memory about local editors and shell setup",
    queries: ["editors", "shell setup"],
    must_include: ["shell setup"],
    keywords: ["editors", "shell setup"]
  });
  writeMemory("shell", {
    id: "shell",
    priority: 90,
    content: "shell setup prefers powershell commands",
    queries: ["shell setup"],
    must_include: ["powershell"],
    keywords: ["shell setup"]
  });

  const result = memoryCli.searchMany(["editors", "shell setup"]);

  assert.deepEqual(result.queries.map((item) => item.query), ["editors", "shell setup"]);
  assert.deepEqual(result.queries[0].matches.map((item) => item.id), ["shared"]);
  assert.deepEqual(result.queries[1].matches.map((item) => item.id), ["shell", "shared"]);
}));

test("main search accepts multiple keyword arguments", () => withProject(() => {
  writeMemory("shared", {
    id: "shared",
    priority: 70,
    content: "durable memory about local editors and shell setup",
    queries: ["editors", "shell setup"],
    must_include: ["shell setup"],
    keywords: ["editors", "shell setup"]
  });
  const lines = [];
  const originalLog = console.log;
  console.log = (line) => lines.push(line);
  try {
    assert.equal(memoryCli.main(["search", "editors", "shell setup"]), 0);
  } finally {
    console.log = originalLog;
  }

  const result = JSON.parse(lines[0]);
  assert.deepEqual(result.queries.map((item) => item.query), ["editors", "shell setup"]);
}));

test("search does not score test queries as runtime content", () => withProject(() => {
  writeMemory("runtime-memory", { id: "runtime-memory", priority: 90, content: "durable runtime content", queries: ["verification-only phrase"], must_include: ["runtime content"] });

  assert.deepEqual(memoryCli.search("verification-only phrase").matches, []);
}));

test("memory tests pass when expected content appears anywhere in results", () => withProject(() => {
  writeMemory("related", { id: "related", priority: 95, content: "python python related implementation note", queries: ["python memory"], must_include: ["implementation note"] });
  writeMemory("expected", { id: "expected", priority: 60, content: "remember exact expected content for python memory", queries: ["python memory"], must_include: ["exact expected content"] });

  assert.deepEqual(memoryCli.runTests().failures, []);
}));

test("management commands add update retire and exclude retired memories", () => withProject(() => {
  const candidate = { id: "mem-new", priority: 60, content: "new standalone memory", queries: ["standalone"], must_include: ["standalone"] };

  assert.equal(memoryCli.addMemory(candidate).status, "added");
  assert.equal(memoryCli.updateMemory("mem-new", { priority: 90 }).status, "updated");
  assert.equal(memoryCli.retireMemory("mem-new", "stale").status, "retired");
  assert.deepEqual(memoryCli.search("standalone").matches, []);
  assert.equal(memoryCli.runTests().total, 0);
}));

test("init creates memory project files", () => withProject((root) => {
  const emptyRoot = path.join(root, "empty");

  assert.equal(memoryCli.initProject(emptyRoot).status, "initialized");
  assert.equal(fs.existsSync(path.join(emptyRoot, "memories")), true);
  assert.equal(fs.existsSync(path.join(emptyRoot, "memory.config.json")), true);
}));

test("commands discover dot memory project from parent directory", () => withProject((root) => {
  const repoRoot = path.join(root, "repo");
  const projectRoot = path.join(repoRoot, ".memory");
  const memoryDir = path.join(projectRoot, "memories");
  fs.mkdirSync(memoryDir, { recursive: true });
  fs.writeFileSync(path.join(projectRoot, "memory.config.json"), JSON.stringify({
    priority_thresholds: { blocking_failure: 80, warning_failure: 40 },
    performance_budget_ms: { p95_search: 200, full_test_suite: 5000 }
  }));
  fs.writeFileSync(path.join(memoryDir, "hongloumeng.json"), JSON.stringify({
    id: "hongloumeng-context",
    priority: 80,
    content: "贾宝玉 lives in 荣国府 near 宁国府",
    queries: ["贾宝玉 荣国府 宁国府"],
    must_include: ["荣国府"]
  }));

  memoryCli.setPaths(repoRoot);

  assert.equal(memoryCli.root, projectRoot);
  assert.deepEqual(memoryCli.listMemories().memories.map((item) => item.id), ["hongloumeng-context"]);
  assert.deepEqual(memoryCli.search("贾宝玉 荣国府 宁国府").matches.map((item) => item.id), ["hongloumeng-context"]);
}));
