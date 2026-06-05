#!/usr/bin/env node
import fs from "node:fs";
import path from "node:path";
import { performance } from "node:perf_hooks";
import { fileURLToPath } from "node:url";

export type MemoryRecord = {
  id: string;
  priority: number;
  content: string;
  queries?: string[];
  must_include?: string[];
  status?: string;
  tags?: string[];
  aliases?: string[];
  keywords?: string[];
  source?: string;
  created_at?: string;
  updated_at?: string;
  retired_at?: string;
  retired_reason?: string;
  _path?: string;
};

export type MemoryCandidate = MemoryRecord & {
  queries: string[];
  must_include: string[];
};

export type MemoryTestCase = {
  memory_id: string;
  priority: number;
  queries: string[];
  must_include: string[];
};

export type SearchMatch = {
  id: string;
  priority: number;
  score: number;
  content: string;
  tags: string[];
  source?: string;
};

export type SearchResult = {
  query: string;
  matches: SearchMatch[];
};

export type MultiSearchResult = {
  queries: SearchResult[];
};

export function isMemoryProject(projectRoot: string): boolean {
  return fs.existsSync(path.join(projectRoot, "memory.config.json")) || fs.existsSync(path.join(projectRoot, "memories"));
}

export function resolveMemoryRoot(start = process.cwd()): string {
  let current = path.resolve(start);
  if (isMemoryProject(current)) return current;
  const nested = path.join(current, ".memory");
  if (isMemoryProject(nested)) return nested;
  while (true) {
    const candidate = path.join(current, ".memory");
    if (isMemoryProject(candidate)) return candidate;
    const parent = path.dirname(current);
    if (parent === current) return path.resolve(start);
    current = parent;
  }
}

export let root = resolveMemoryRoot();
export let memoryDir = path.join(root, "memories");
export let testCaseDir = path.join(root, "test-cases");
export let configPath = path.join(root, "memory.config.json");

export function setPaths(nextRoot: string): void {
  root = resolveMemoryRoot(nextRoot);
  memoryDir = path.join(root, "memories");
  testCaseDir = path.join(root, "test-cases");
  configPath = path.join(root, "memory.config.json");
}

export function memoryProjectExists(): boolean {
  return isMemoryProject(root);
}

function missingProjectError() {
  return {
    error: "memory_project_not_found",
    path: root,
    message: "No memory project found. Run from a memory project or a parent directory containing .memory."
  };
}

function readJson<T>(filePath: string): T {
  return JSON.parse(fs.readFileSync(filePath, "utf8")) as T;
}

function writeJson(filePath: string, data: unknown): void {
  fs.mkdirSync(path.dirname(filePath), { recursive: true });
  fs.writeFileSync(filePath, `${JSON.stringify(data, null, 2)}\n`, "utf8");
}

export function loadConfig() {
  if (!fs.existsSync(configPath)) {
    return {
      priority_thresholds: { blocking_failure: 80, warning_failure: 40 },
      performance_budget_ms: { p95_search: 200, full_test_suite: 5000 }
    };
  }
  return readJson<{
    priority_thresholds: { blocking_failure: number; warning_failure: number };
    performance_budget_ms: { p95_search: number; full_test_suite: number };
  }>(configPath);
}

export function tokenize(text: string): string[] {
  return String(text).toLowerCase().split(/[^\p{L}\p{N}_]+/u).filter(Boolean);
}

export function loadMemories(): MemoryRecord[] {
  if (!fs.existsSync(memoryDir)) return [];
  return fs.readdirSync(memoryDir)
    .filter((name) => name.endsWith(".json"))
    .sort()
    .map((name) => {
      const filePath = path.join(memoryDir, name);
      return { ...readJson<MemoryRecord>(filePath), _path: filePath };
    });
}

export function activeMemories(): MemoryRecord[] {
  return loadMemories().filter((memory) => (memory.status ?? "active") !== "retired");
}

export function loadTestCases(): MemoryTestCase[] {
  if (!fs.existsSync(testCaseDir)) return [];
  const activeIds = new Set(activeMemories().map((memory) => memory.id));
  return fs.readdirSync(testCaseDir)
    .filter((name) => name.endsWith(".json"))
    .sort()
    .map((name) => readJson<MemoryTestCase>(path.join(testCaseDir, name)))
    .filter((testCase) => activeIds.has(testCase.memory_id));
}

export function memoryPath(memoryId: string): string {
  const found = loadMemories().find((memory) => memory.id === memoryId);
  return found?._path ?? path.join(memoryDir, `${memoryId}.json`);
}

export function publicMemory(memory: MemoryRecord): Omit<MemoryRecord, "_path"> {
  const { _path, ...rest } = memory;
  return rest;
}

export function initProject(targetRoot = root) {
  const memories = path.join(targetRoot, "memories");
  const testCases = path.join(targetRoot, "test-cases");
  const config = path.join(targetRoot, "memory.config.json");
  fs.mkdirSync(memories, { recursive: true });
  fs.mkdirSync(testCases, { recursive: true });
  if (!fs.existsSync(config)) {
    writeJson(config, {
      priority_thresholds: { blocking_failure: 80, warning_failure: 40 },
      performance_budget_ms: { p95_search: 200, full_test_suite: 5000 }
    });
  }
  return { status: "initialized", root: targetRoot, memories, test_cases: testCases };
}

export function listMemories() {
  const memories = loadMemories().map((memory) => ({
    id: memory.id,
    priority: memory.priority ?? 0,
    status: memory.status ?? "active",
    tags: memory.tags ?? [],
    source: memory.source
  }));
  memories.sort((a, b) => (b.priority - a.priority) || String(b.id ?? "").localeCompare(String(a.id ?? "")));
  return { memories };
}

export function showMemory(memoryId: string) {
  const memory = loadMemories().find((item) => item.id === memoryId);
  return memory ? { memory: publicMemory(memory) } : { error: "not_found", id: memoryId };
}

export function validateMemory(memory: Partial<MemoryRecord>) {
  const missing = ["id", "priority", "content", "queries", "must_include"].filter((field) => !(field in memory));
  if (missing.length) return { valid: false, missing };
  if (!Array.isArray(memory.queries) || memory.queries.length === 0) return { valid: false, missing: ["queries"] };
  return { valid: true, missing: [] };
}

export function scoreMemory(memory: MemoryRecord, query: string): number {
  const queryTokens = tokenize(query);
  if (!queryTokens.length) return 0;
  const fields: Array<[string, number]> = [
    [memory.content ?? "", 3],
    [(memory.tags ?? []).join(" "), 2],
    [(memory.aliases ?? []).join(" "), 2],
    [(memory.keywords ?? []).join(" "), 2],
    [memory.id ?? "", 1]
  ];
  let score = 0;
  for (const token of queryTokens) {
    for (const [value, weight] of fields) {
      const text = String(value).toLowerCase();
      const tokens = tokenize(text);
      if (tokens.includes(token)) score += weight;
      else if (text.includes(token)) score += Math.max(1, weight - 1);
    }
  }
  if (String(memory.content ?? "").toLowerCase().includes(String(query).toLowerCase())) score += 8;
  return score;
}

export function search(query: string): SearchResult {
  const matches = activeMemories()
    .map((memory) => ({ memory, score: scoreMemory(memory, query) }))
    .filter((item) => item.score > 0)
    .map(({ memory, score }) => ({
      id: memory.id,
      priority: memory.priority ?? 0,
      score,
      content: memory.content ?? "",
      tags: memory.tags ?? [],
      source: memory.source
    }));
  matches.sort((a, b) => (b.priority - a.priority) || (b.score - a.score));
  return { query, matches };
}

export function searchMany(queries: string[]): MultiSearchResult {
  return { queries: queries.map((query) => search(query)) };
}

export function checkConflicts(candidate: MemoryCandidate) {
  const validation = validateMemory(candidate);
  if (!validation.valid) return { valid: false, conflicts: [], missing: validation.missing };
  const conflicts = [];
  for (const query of candidate.queries ?? []) {
    const matchingIds = search(query).matches
      .filter((item) => item.id !== candidate.id)
      .filter((item) => (candidate.must_include ?? []).some((phrase) => item.content.toLowerCase().includes(String(phrase).toLowerCase())))
      .map((item) => item.id);
    if (matchingIds.length) conflicts.push({ query, matching_ids: matchingIds });
  }
  return { valid: true, conflicts };
}

export function addMemory(candidate: MemoryCandidate, force = false) {
  const conflicts = checkConflicts(candidate);
  if (!conflicts.valid) return { status: "invalid", ...conflicts };
  if (conflicts.conflicts.length && !force) return { status: "conflict", ...conflicts };
  const target = memoryPath(candidate.id);
  if (fs.existsSync(target) && !force) return { status: "exists", id: candidate.id, path: target };
  const { queries, must_include: mustInclude, ...memory } = candidate;
  writeJson(target, memory);
  writeJson(path.join(testCaseDir, `${candidate.id}.json`), {
    memory_id: candidate.id,
    priority: candidate.priority ?? 0,
    queries: queries ?? [],
    must_include: mustInclude ?? []
  });
  return { status: "added", id: candidate.id, path: target };
}

export function updateMemory(memoryId: string, updates: Partial<MemoryRecord>) {
  const target = memoryPath(memoryId);
  if (!fs.existsSync(target)) return { status: "not_found", id: memoryId };
  const memory = { ...readJson<MemoryRecord>(target), ...updates, id: memoryId, updated_at: new Date().toISOString().slice(0, 10) };
  writeJson(target, memory);
  return { status: "updated", id: memoryId, path: target };
}

export function retireMemory(memoryId: string, reason?: string) {
  const updates: Partial<MemoryRecord> = { status: "retired", retired_at: new Date().toISOString().slice(0, 10) };
  if (reason) updates.retired_reason = reason;
  const result = updateMemory(memoryId, updates);
  return result.status === "updated" ? { ...result, status: "retired" } : result;
}

export function runTests() {
  const started = performance.now();
  const blockingPriority = loadConfig().priority_thresholds.blocking_failure;
  const failures = [];
  let total = 0;
  for (const testCase of loadTestCases()) {
    for (const query of testCase.queries ?? []) {
      total += 1;
      const result = search(query);
      const matched = result.matches.find((item) =>
        item.id === testCase.memory_id && (testCase.must_include ?? []).every((phrase) => item.content.toLowerCase().includes(String(phrase).toLowerCase()))
      );
      if (!matched) {
        failures.push({
          memory_id: testCase.memory_id,
          priority: testCase.priority ?? 0,
          query,
          expected: testCase.must_include ?? [],
          found_ids: result.matches.map((item) => item.id)
        });
      }
    }
  }
  return {
    total,
    failed: failures.length,
    blocking_failed: failures.filter((failure) => failure.priority >= blockingPriority).length,
    elapsed_ms: Number((performance.now() - started).toFixed(3)),
    failures
  };
}

function percentile(values: number[], percent: number): number {
  if (!values.length) return 0;
  const ordered = [...values].sort((a, b) => a - b);
  return ordered[Math.round((ordered.length - 1) * percent)];
}

export function bench() {
  const started = performance.now();
  const latencies = [];
  const testCases = loadTestCases();
  for (const testCase of testCases) {
    for (const query of testCase.queries ?? []) {
      const queryStarted = performance.now();
      search(query);
      latencies.push(performance.now() - queryStarted);
    }
  }
  return {
    memories: activeMemories().length,
    test_cases: testCases.length,
    queries: latencies.length,
    p50_search_ms: latencies.length ? Number(percentile(latencies, 0.5).toFixed(3)) : 0,
    p95_search_ms: Number(percentile(latencies, 0.95).toFixed(3)),
    full_suite_ms: Number((performance.now() - started).toFixed(3)),
    budget_ms: loadConfig().performance_budget_ms
  };
}

function usage(): string {
  return "usage: memory-cli <init|search|check-conflicts|add|list|show|update|retire|test|bench>";
}

export function main(argv = process.argv.slice(2)): number {
  const [command, ...args] = argv;
  let result: unknown;
  let code = 0;
  if (command !== "init" && !memoryProjectExists()) {
    console.log(JSON.stringify(missingProjectError(), null, 2));
    return 1;
  }
  if (command === "init") result = initProject(valueAfter(args, "--path") ?? ".");
  else if (command === "search") result = args.length === 1 ? search(args[0]) : searchMany(args);
  else if (command === "check-conflicts") result = checkConflicts(readJson<MemoryCandidate>(requiredValue(args, "--file")));
  else if (command === "add") {
    result = addMemory(readJson<MemoryCandidate>(requiredValue(args, "--file")), args.includes("--force"));
    if (["conflict", "invalid", "exists"].includes(String((result as { status: string }).status))) code = 1;
  } else if (command === "list") result = listMemories();
  else if (command === "show") {
    result = showMemory(args[0]);
    if ("error" in (result as Record<string, unknown>)) code = 1;
  } else if (command === "update") {
    result = updateMemory(args[0], readJson<Partial<MemoryRecord>>(requiredValue(args, "--file")));
    if ((result as { status: string }).status === "not_found") code = 1;
  } else if (command === "retire") {
    result = retireMemory(args[0], valueAfter(args, "--reason"));
    if ((result as { status: string }).status === "not_found") code = 1;
  } else if (command === "test") {
    result = runTests();
    if ((result as { blocking_failed: number }).blocking_failed) code = 1;
  } else if (command === "bench") result = bench();
  else {
    console.error(usage());
    return 2;
  }
  console.log(JSON.stringify(result, null, 2));
  return code;
}

function valueAfter(args: string[], flag: string): string | undefined {
  const index = args.indexOf(flag);
  return index >= 0 ? args[index + 1] : undefined;
}

function requiredValue(args: string[], flag: string): string {
  const value = valueAfter(args, flag);
  if (!value) throw new Error(`${flag} is required`);
  return value;
}

const executedPath = process.argv[1] ? path.resolve(process.argv[1]) : "";
if (executedPath === fileURLToPath(import.meta.url)) {
  process.exitCode = main();
}
