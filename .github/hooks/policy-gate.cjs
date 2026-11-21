/*
 * FulfillFlow AgentOps — GitHub Copilot preToolUse governance policy.
 *
 * This is a narrow defense-in-depth filter for recognized bash commands,
 * not a complete shell parser or a substitute for GitHub rulesets.
 * Shell commands in toolArgs are examined as text, never executed here.
 */

"use strict";

const fs = require("node:fs");
const path = require("node:path");

const logPath = path.join(__dirname, "tool-use.log");

function deny(rule, reason) {
  return { decision: "DENY", rule, reason };
}

function tokenize(command) {
  // A lightweight lexer for the simple command forms covered by this lab.
  // This is intentionally not represented as full bash parsing.
  const matches = command.match(/"(?:\\.|[^"\\])*"|'[^']*'|\S+/g) || [];
  return matches.map((token) => {
    if (
      (token.startsWith('"') && token.endsWith('"')) ||
      (token.startsWith("'") && token.endsWith("'"))
    ) {
      return token.slice(1, -1);
    }
    return token;
  });
}

function normalizePath(value) {
  return value
    .replace(/^\$\{PWD\}\//, "")
    .replace(/^\$PWD\//, "")
    .replace(/^\.\//, "")
    .replace(/\/+$/, "");
}

function isCodeownersTarget(value) {
  const target = normalizePath(value);
  return (
    target === ".github/CODEOWNERS" ||
    target.endsWith("/.github/CODEOWNERS")
  );
}

function isPolicyTarget(value) {
  const target = normalizePath(value);
  return (
    target === "policies" ||
    target.startsWith("policies/") ||
    target.endsWith("/policies") ||
    target.includes("/policies/")
  );
}

function isMainDestination(refspec) {
  return (
    refspec === "main" ||
    refspec === "refs/heads/main" ||
    /:(?:refs\/heads\/)?main$/.test(refspec)
  );
}

function evaluate(event) {
  if (event?.toolName !== "bash") {
    return { decision: "NO_DECISION" };
  }

  const command = event?.toolArgs?.command;
  if (typeof command !== "string" || !command.trim()) {
    return deny("POLICY-000", "Missing or invalid shell command");
  }

  const tokens = tokenize(command);

  // POLICY-004: Inline Python is an unsupported, opaque execution surface.
  // The lab deliberately denies this recognizable form rather than trying
  // to inspect arbitrary Python source for dangerous behavior.
  if (
    tokens.some((token, i) =>
      /^(?:python|python\d+(?:\.\d+)?)$/.test(token) &&
      tokens[i + 1] === "-c"
    )
  ) {
    return deny("POLICY-004", "Inline Python execution requires separate review");
  }

  for (let index = 0; index < tokens.length; index += 1) {
    if (tokens[index] === "unlink") {
      const args = tokens.slice(index + 1);
      if (args.some((arg) => isCodeownersTarget(arg))) {
        return deny("POLICY-002", "Deleting CODEOWNERS is prohibited");
      }
    }

    if (tokens[index] === "rm") {
      const args = tokens.slice(index + 1);
      const recursive = args.some((arg) =>
        arg === "--recursive" || /^-[a-zA-Z]*[rR]/.test(arg)
      );
      const targets = args.filter((arg) => !arg.startsWith("-"));

      if (recursive && targets.some(isPolicyTarget)) {
        return deny("POLICY-001", "Recursive deletion of policies/ is prohibited");
      }
      if (targets.some(isCodeownersTarget)) {
        return deny("POLICY-002", "Deleting CODEOWNERS is prohibited");
      }
    }

    if (tokens[index] === "git" && tokens[index + 1] === "push") {
      const args = tokens.slice(index + 2);
      const force = args.some((arg) =>
        arg === "-f" || arg === "--force" || arg.startsWith("--force-with-lease")
      );
      if (force && args.some(isMainDestination)) {
        return deny("POLICY-003", "Force-pushing main is prohibited");
      }
    }
  }

  return { decision: "NO_DECISION" };
}

function main() {
  const event = JSON.parse(fs.readFileSync(0, "utf8"));
  const result = evaluate(event);

  fs.appendFileSync(
    logPath,
    JSON.stringify({
      tool: event?.toolName ?? null,
      decision: result.decision,
      rule: result.rule ?? null,
    }) + "\n"
  );

  if (result.decision === "DENY") {
    process.stdout.write(
      JSON.stringify({
        permissionDecision: "deny",
        permissionDecisionReason: `${result.rule}: ${result.reason}`,
      }) + "\n"
    );
  } else {
    process.stdout.write("{}\n");
  }
}

try {
  main();
} catch (error) {
  // For malformed events, request denial instead of silently permitting.
  // Whether the host enforces this decision remains runtime-dependent.
  process.stdout.write(JSON.stringify({
    permissionDecision: "deny",
    permissionDecisionReason: "POLICY-000: Invalid governance hook input",
  }) + "\n");
  process.exitCode = 0;
}
