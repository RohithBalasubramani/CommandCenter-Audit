#!/usr/bin/env npx tsx
"use strict";
/**
 * Command Center — AI QA Agent Runner
 *
 * Main entry point for running the AI testing agent against
 * the Command Center industrial dashboard.
 *
 * Usage:
 *   npx tsx src/cc-runner.ts                     # Run all 40 scenarios
 *   npx tsx src/cc-runner.ts --tag smoke          # Smoke tests only
 *   npx tsx src/cc-runner.ts --category "Core UI"  # Single category
 *   npx tsx src/cc-runner.ts --id text-query-001   # Single scenario
 *   npx tsx src/cc-runner.ts --priority critical    # Critical priority only
 *   npx tsx src/cc-runner.ts --headed               # Show browser
 */
var __createBinding = (this && this.__createBinding) || (Object.create ? (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    var desc = Object.getOwnPropertyDescriptor(m, k);
    if (!desc || ("get" in desc ? !m.__esModule : desc.writable || desc.configurable)) {
      desc = { enumerable: true, get: function() { return m[k]; } };
    }
    Object.defineProperty(o, k2, desc);
}) : (function(o, m, k, k2) {
    if (k2 === undefined) k2 = k;
    o[k2] = m[k];
}));
var __setModuleDefault = (this && this.__setModuleDefault) || (Object.create ? (function(o, v) {
    Object.defineProperty(o, "default", { enumerable: true, value: v });
}) : function(o, v) {
    o["default"] = v;
});
var __importStar = (this && this.__importStar) || (function () {
    var ownKeys = function(o) {
        ownKeys = Object.getOwnPropertyNames || function (o) {
            var ar = [];
            for (var k in o) if (Object.prototype.hasOwnProperty.call(o, k)) ar[ar.length] = k;
            return ar;
        };
        return ownKeys(o);
    };
    return function (mod) {
        if (mod && mod.__esModule) return mod;
        var result = {};
        if (mod != null) for (var k = ownKeys(mod), i = 0; i < k.length; i++) if (k[i] !== "default") __createBinding(result, mod, k[i]);
        __setModuleDefault(result, mod);
        return result;
    };
})();
Object.defineProperty(exports, "__esModule", { value: true });
const fs = __importStar(require("fs"));
const path = __importStar(require("path"));
const test_1 = require("@playwright/test");
const test_runner_js_1 = require("./test-runner.js");
const cc_config_js_1 = require("./cc-config.js");
const cc_scenarios_js_1 = require("./cc-scenarios.js");
function parseArgs() {
    const args = process.argv.slice(2);
    const parsed = {};
    for (let i = 0; i < args.length; i++) {
        switch (args[i]) {
            case '--category':
                parsed.category = args[++i];
                break;
            case '--id':
                parsed.id = args[++i];
                break;
            case '--tag':
                parsed.tag = args[++i];
                break;
            case '--priority':
                parsed.priority = args[++i];
                break;
            case '--headed':
                parsed.headed = true;
                break;
            case '--list':
                parsed.list = true;
                break;
            case '--dry-run':
                parsed.dryRun = true;
                break;
            case '--help':
            case '-h':
                printUsage();
                process.exit(0);
        }
    }
    return parsed;
}
function printUsage() {
    console.log(`
Command Center — AI QA Agent
═════════════════════════════

Usage: npx tsx src/cc-runner.ts [options]

Options:
  --category <name>    Run scenarios in a specific category
  --id <id>            Run a single scenario by ID
  --tag <tag>          Run scenarios with a specific tag (e.g., smoke, voice)
  --priority <level>   Run scenarios with a specific priority (critical, high, medium, low)
  --headed             Show the browser window
  --list               List all scenarios and exit
  --dry-run            Show which scenarios would run, don't execute
  --help, -h           Show this help

Examples:
  npx tsx src/cc-runner.ts                          # All 40 scenarios
  npx tsx src/cc-runner.ts --tag smoke              # Smoke tests
  npx tsx src/cc-runner.ts --category "Core UI Navigation"
  npx tsx src/cc-runner.ts --id text-query-001
  npx tsx src/cc-runner.ts --priority critical --headed
`);
}
// ─── Health Checks ───────────────────────────────────────────────────
async function checkServerHealth(url, name) {
    try {
        const controller = new AbortController();
        const timeout = setTimeout(() => controller.abort(), 5000);
        const resp = await fetch(url, { signal: controller.signal });
        clearTimeout(timeout);
        // Accept any response (even redirects) — the server is alive
        return resp.status < 500;
    }
    catch {
        return false;
    }
}
async function ensureServersRunning() {
    console.log('Checking server health...');
    const frontendOk = await checkServerHealth('http://localhost:3100', 'Frontend');
    const backendOk = await checkServerHealth('http://localhost:8100/api/layer2/health/', 'Backend');
    // Fallback: try backend root if health endpoint doesn't exist
    const backendAlive = backendOk || await checkServerHealth('http://localhost:8100/', 'Backend');
    if (frontendOk) {
        console.log('  Frontend (localhost:3100): UP');
    }
    else {
        console.error('  Frontend (localhost:3100): DOWN');
    }
    if (backendAlive) {
        console.log('  Backend  (localhost:8100): UP');
    }
    else {
        console.error('  Backend  (localhost:8100): DOWN');
    }
    if (!frontendOk || !backendAlive) {
        console.error(`
One or more servers are not running. Start them with:

  cd /home/rohith/desktop/CommandCenter && bash scripts/dev.sh

Then re-run this agent:
  npx tsx src/cc-runner.ts
`);
        return false;
    }
    console.log('  All servers healthy.\n');
    return true;
}
// ─── Scenario Filtering ─────────────────────────────────────────────
function filterScenarios(scenarios, args) {
    let filtered = [...scenarios];
    if (args.id) {
        filtered = filtered.filter(s => s.id === args.id);
        if (filtered.length === 0) {
            console.error(`No scenario found with id: ${args.id}`);
            console.log('Available IDs:');
            scenarios.forEach(s => console.log(`  ${s.id} — ${s.name}`));
            process.exit(1);
        }
    }
    if (args.category) {
        const cat = args.category.toLowerCase();
        filtered = filtered.filter(s => s.category?.toLowerCase().includes(cat));
    }
    if (args.tag) {
        filtered = filtered.filter(s => s.tags?.includes(args.tag));
    }
    if (args.priority) {
        filtered = filtered.filter(s => s.priority === args.priority);
    }
    return filtered;
}
function listScenarios(scenarios) {
    const categories = new Map();
    for (const s of scenarios) {
        const cat = s.category || 'Uncategorized';
        if (!categories.has(cat))
            categories.set(cat, []);
        categories.get(cat).push(s);
    }
    console.log(`\nCommand Center AI QA — ${scenarios.length} Scenarios\n`);
    for (const [cat, items] of categories) {
        console.log(`${cat} (${items.length})`);
        for (const s of items) {
            const tags = s.tags?.length ? ` [${s.tags.join(', ')}]` : '';
            const pri = s.priority ? ` (${s.priority})` : '';
            console.log(`  ${s.id.padEnd(28)} ${s.name}${pri}${tags}`);
        }
        console.log();
    }
}
// ─── Main Execution ──────────────────────────────────────────────────
async function main() {
    const args = parseArgs();
    console.log(`
╔══════════════════════════════════════════════════════╗
║   Command Center — AI QA Agent                       ║
║   Claude-powered autonomous testing                  ║
╚══════════════════════════════════════════════════════╝
`);
    // List mode
    if (args.list) {
        listScenarios(cc_scenarios_js_1.ccScenarios);
        process.exit(0);
    }
    // Filter scenarios
    const scenarios = filterScenarios(cc_scenarios_js_1.ccScenarios, args);
    if (scenarios.length === 0) {
        console.error('No scenarios match the given filters.');
        process.exit(1);
    }
    // Dry run mode
    if (args.dryRun) {
        console.log(`Would run ${scenarios.length} scenarios:\n`);
        scenarios.forEach(s => {
            console.log(`  ${s.id.padEnd(28)} ${s.name}`);
        });
        process.exit(0);
    }
    // Health check
    const serversOk = await ensureServersRunning();
    if (!serversOk) {
        process.exit(1);
    }
    console.log(`Running ${scenarios.length} scenario(s)...\n`);
    // Create evidence directory
    const evidenceDir = path.resolve(cc_config_js_1.ccAgentConfig.evidenceDir || './evidence/cc');
    fs.mkdirSync(evidenceDir, { recursive: true });
    // Launch browser
    const browser = await test_1.chromium.launch({
        headless: !args.headed && !cc_config_js_1.ccRunnerConfig.headed,
        slowMo: cc_config_js_1.ccRunnerConfig.slowMo,
    });
    const context = await browser.newContext({
        viewport: cc_config_js_1.ccRunnerConfig.viewport || { width: 1440, height: 900 },
        permissions: cc_config_js_1.ccRunnerConfig.permissions,
        ignoreHTTPSErrors: cc_config_js_1.ccRunnerConfig.ignoreHTTPSErrors,
        locale: cc_config_js_1.ccRunnerConfig.locale,
        timezoneId: cc_config_js_1.ccRunnerConfig.timezone,
        ...(cc_config_js_1.ccRunnerConfig.recordVideo ? { recordVideo: { dir: path.join(evidenceDir, 'videos') } } : {}),
    });
    // Start tracing if enabled
    if (cc_config_js_1.ccRunnerConfig.recordTrace) {
        await context.tracing.start({ screenshots: true, snapshots: true });
    }
    const page = await context.newPage();
    // Collect results
    const results = [];
    let passCount = 0;
    let failCount = 0;
    try {
        // Run scenarios sequentially using the runScenarios utility
        const allResults = await (0, test_runner_js_1.runScenarios)(page, scenarios, {
            agent: cc_config_js_1.ccAgentConfig,
            evidenceBaseDir: evidenceDir,
            screenshotEveryStep: cc_config_js_1.ccAgentConfig.screenshotEveryStep,
            actionDelay: cc_config_js_1.ccAgentConfig.actionDelay,
        }, {
            maxRetries: cc_config_js_1.ccRunnerConfig.maxRetries || 1,
            onScenarioComplete: (result) => {
                results.push(result);
                if (result.status === 'pass') {
                    passCount++;
                    console.log(`  PASS [${passCount}/${scenarios.length}]`);
                }
                else {
                    failCount++;
                    console.log(`  FAIL [${passCount + failCount}/${scenarios.length}] — ${result.error?.slice(0, 80) || result.status}`);
                }
            },
        });
        // Use allResults if onScenarioComplete didn't populate (defensive)
        if (results.length === 0 && allResults.length > 0) {
            results.push(...allResults);
            passCount = allResults.filter(r => r.status === 'pass').length;
            failCount = allResults.length - passCount;
        }
    }
    catch (err) {
        console.error(`\nFatal error during execution: ${err.message}`);
        console.error(err.stack);
    }
    finally {
        // Stop tracing
        if (cc_config_js_1.ccRunnerConfig.recordTrace) {
            const tracePath = path.join(evidenceDir, 'trace.zip');
            await context.tracing.stop({ path: tracePath });
            console.log(`  Trace saved: ${tracePath}`);
        }
        await page.close().catch(() => { });
        await context.close().catch(() => { });
        await browser.close().catch(() => { });
    }
    // Generate audit report
    const report = (0, test_runner_js_1.generateAuditReport)(results, 'Command Center', '1.0.0');
    // Save report
    const reportPath = path.join(evidenceDir, 'audit-report.json');
    fs.writeFileSync(reportPath, JSON.stringify(report, null, 2));
    const summaryPath = path.join(evidenceDir, 'audit-summary.txt');
    fs.writeFileSync(summaryPath, report.summary);
    // Print summary
    console.log(`\n${'═'.repeat(60)}`);
    console.log(report.summary);
    console.log(`${'═'.repeat(60)}`);
    console.log(`\nEvidence: ${evidenceDir}`);
    console.log(`Report:   ${reportPath}`);
    // Failure breakdown
    if (report.failureBreakdown) {
        const failures = Object.entries(report.failureBreakdown).filter(([, count]) => count > 0);
        if (failures.length > 0) {
            console.log('\nFailure Breakdown:');
            failures.forEach(([category, count]) => {
                console.log(`  ${category}: ${count}`);
            });
        }
    }
    // Flaky tests
    const flakyTests = results.filter(r => r.wasFlaky);
    if (flakyTests.length > 0) {
        console.log(`\nFlaky Tests (${flakyTests.length}):`);
        flakyTests.forEach(r => {
            console.log(`  ${r.scenarioId} — ${r.scenarioName} (attempt ${r.attempt})`);
        });
    }
    // Exit code
    const exitCode = failCount === 0 ? 0 : 1;
    console.log(`\nExit code: ${exitCode} (${passCount} passed, ${failCount} failed)\n`);
    process.exit(exitCode);
}
// Run
main().catch(err => {
    console.error('Unhandled error:', err);
    process.exit(2);
});
//# sourceMappingURL=cc-runner.js.map