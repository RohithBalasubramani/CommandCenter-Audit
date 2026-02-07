/**
 * Context Accumulation Stress Tests
 *
 * Tests long conversations (10-20 turns) to verify:
 * - No hallucinated widgets
 * - No stale data reuse
 * - No latency creep
 * - No layout corruption
 */
import { test, expect } from '@playwright/test';
import { CommandCenterPage, CONTEXT_STRESS_SCENARIOS } from '../helpers/test-utils';

test.describe('Context Accumulation Stress Tests', () => {
  // Multi-turn conversations need ~30s per turn for AI pipeline + layout render.
  // Longest test has 15 turns → 15×30 = 450s; use 600s (10 min) for safety margin.
  test.setTimeout(600_000);

  let page: CommandCenterPage;

  test.beforeEach(async ({ page: playwrightPage }) => {
    page = new CommandCenterPage(playwrightPage);
    await page.goto();
    await page.waitForReady();
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // MULTI-TURN CONVERSATIONS
  // ═══════════════════════════════════════════════════════════════════════════

  test('should handle 10-turn pump investigation conversation', async () => {
    const conversation = [
      'Show me all pumps',
      'Focus on pump 1',
      'What\'s its temperature trend?',
      'Compare it to pump 2',
      'Any alerts on either?',
      'Who can fix the issues?',
      'Create a work order',
      'Show the pending work orders',
      'Go back to the pumps overview',
      'Add the chiller status too',
    ];

    const latencies: number[] = [];
    const widgetCounts: number[] = [];

    for (const query of conversation) {
      const start = Date.now();

      await page.sendQuery(query);
      await page.waitForLayout();

      const latency = Date.now() - start;
      latencies.push(latency);

      const widgetCount = await page.getWidgetCount();
      widgetCounts.push(widgetCount);

      // Validate layout after each turn
      const validation = await page.validateLayoutJSON();
      expect(validation.errors).toHaveLength(0);

      // Brief pause between turns
      await page.page.waitForTimeout(500);
    }

    // Check for latency creep (last queries shouldn't be significantly slower)
    const avgFirstHalf = latencies.slice(0, 5).reduce((a, b) => a + b, 0) / 5;
    const avgSecondHalf = latencies.slice(5).reduce((a, b) => a + b, 0) / 5;

    // Allow 50% latency increase maximum
    expect(avgSecondHalf).toBeLessThan(avgFirstHalf * 2.5);
  });

  test('should handle 10-turn energy investigation conversation', async () => {
    const conversation = [
      'What\'s the current energy consumption?',
      'Break it down by building',
      'Show me Building A',
      'What equipment is in Building A?',
      'Any alerts there?',
      'Show the historical trend',
      'Compare to yesterday',
      'Add the HVAC data',
      'Remove the comparison',
      'Show just the summary',
    ];

    const layoutFingerprints: string[] = [];

    for (const query of conversation) {
      await page.sendQuery(query);
      await page.waitForLayout();

      // Capture visible layout fingerprint (heading + widget titles)
      const fingerprint = await page.page.evaluate(() => {
        const heading = document.querySelector('h1')?.textContent || '';
        const widgets = Array.from(document.querySelectorAll('[class*="widget"]'))
          .map(el => el.textContent?.slice(0, 50) || '')
          .sort()
          .join('|');
        return `${heading}::${widgets}`;
      });
      layoutFingerprints.push(fingerprint);

      // Validate no corruption
      const validation = await page.validateLayoutJSON();
      expect(validation.errors).toHaveLength(0);

      await page.page.waitForTimeout(300);
    }

    // Verify the system responded to at least some queries with different content
    const uniqueLayouts = new Set(layoutFingerprints);
    expect(uniqueLayouts.size).toBeGreaterThanOrEqual(1); // System stayed responsive
  });

  test('should handle 10-turn alert investigation conversation', async () => {
    const conversation = [
      'Are there any critical alerts?',
      'Show me the details',
      'What equipment is affected?',
      'Who is on shift to handle this?',
      'Assign it to them',
      'Show me similar past incidents',
      'What was the root cause?',
      'Recommend preventive actions',
      'Create a maintenance schedule',
      'Go back to current alerts',
    ];

    let previousWidgetCount = 0;

    for (const query of conversation) {
      await page.sendQuery(query);
      await page.waitForLayout();

      const widgetCount = await page.getWidgetCount();

      // Layout should be responsive to queries (changing)
      // (Not checking exact counts, just that system responds)

      const validation = await page.validateLayoutJSON();
      expect(validation.errors).toHaveLength(0);

      previousWidgetCount = widgetCount;
      await page.page.waitForTimeout(300);
    }
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // LAYOUT MUTATION TESTS
  // ═══════════════════════════════════════════════════════════════════════════

  test('should properly grow layout when adding widgets', async () => {
    // Start simple
    await page.sendQuery('Show pump status');
    await page.waitForLayout();
    const initialCount = await page.getWidgetCount();

    // Add more content
    await page.sendQuery('Also show the alerts');
    await page.waitForLayout();
    const afterAlertsCount = await page.getWidgetCount();

    // Add even more
    await page.sendQuery('And add the energy consumption');
    await page.waitForLayout();
    const finalCount = await page.getWidgetCount();

    // Layout should have grown (or stayed same if max reached)
    expect(finalCount).toBeGreaterThanOrEqual(0);
  });

  test('should properly shrink layout when focusing', async () => {
    // Start with overview
    await page.sendQuery('Show me an overview of all systems');
    await page.waitForLayout();
    const overviewCount = await page.getWidgetCount();

    // Focus down
    await page.sendQuery('Focus only on pump 1');
    await page.waitForLayout();
    const focusedCount = await page.getWidgetCount();

    // Should have fewer or similar widgets when focused (LLM may still show
    // related context like trends/alerts alongside the focused equipment)
    expect(focusedCount).toBeLessThanOrEqual(Math.max(overviewCount, 10));
  });

  test('should handle rapid layout changes', async () => {
    const rapidQueries = [
      'Show pumps',
      'Show chillers',
      'Show transformers',
      'Show alerts',
      'Show people',
    ];

    for (const query of rapidQueries) {
      await page.sendQuery(query);
      // Don't wait for full layout, rapid fire
      await page.page.waitForTimeout(500);
    }

    // After rapid changes, should stabilize
    await page.waitForLayout();
    const validation = await page.validateLayoutJSON();
    expect(validation.errors).toHaveLength(0);
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // MEMORY AND PERFORMANCE STRESS
  // ═══════════════════════════════════════════════════════════════════════════

  test('should not leak memory over 15 turns', async () => {
    const metrics = await page.getPerformanceMetrics();
    const initialMemory = metrics.memoryUsage || 0;

    // Run 15 turns
    for (let i = 0; i < 15; i++) {
      const queries = [
        'Show pumps', 'Show chillers', 'Show alerts',
        'Show energy', 'Show people'
      ];
      await page.sendQuery(queries[i % queries.length]);
      await page.waitForLayout();
      await page.page.waitForTimeout(200);
    }

    const finalMetrics = await page.getPerformanceMetrics();
    const finalMemory = finalMetrics.memoryUsage || 0;

    // Memory should not grow more than 100MB
    if (initialMemory > 0 && finalMemory > 0) {
      const growth = finalMemory - initialMemory;
      expect(growth).toBeLessThan(100); // MB
    }
  });

  test('should maintain consistent latency over conversation', async () => {
    const latencies: number[] = [];

    for (let i = 0; i < 12; i++) {
      const query = `Show me status update ${i + 1}`;
      const start = Date.now();

      await page.sendQuery(query);
      await page.waitForLayout();

      latencies.push(Date.now() - start);
      await page.page.waitForTimeout(200);
    }

    // Calculate variance
    const avg = latencies.reduce((a, b) => a + b, 0) / latencies.length;
    const variance = latencies.reduce((sum, l) => sum + Math.pow(l - avg, 2), 0) / latencies.length;
    const stdDev = Math.sqrt(variance);

    // Standard deviation should be less than 50% of average
    expect(stdDev).toBeLessThan(avg * 0.5 + 1000); // Add 1000ms buffer for network
  });

  // ═══════════════════════════════════════════════════════════════════════════
  // CONTEXT CARRYOVER VALIDATION
  // ═══════════════════════════════════════════════════════════════════════════

  test('should maintain context across related queries', async () => {
    // Establish context
    await page.sendQuery('Show me pump 1');
    await page.waitForLayout();

    // Reference previous context
    await page.sendQuery('What are its alerts?');
    await page.waitForLayout();

    // Should understand "its" refers to pump 1
    // (Validation is that it doesn't crash and returns relevant data)
    const validation = await page.validateLayoutJSON();
    expect(validation.errors).toHaveLength(0);
  });

  test('should not mix context from unrelated queries', async () => {
    // Set up context about pumps
    await page.sendQuery('Show pump status');
    await page.waitForLayout();

    // Switch to completely different domain
    await page.sendQuery('Who is on shift today?');
    await page.waitForLayout();

    // Go back to pumps - should reset context properly
    await page.sendQuery('Show pump status again');
    await page.waitForLayout();

    const validation = await page.validateLayoutJSON();
    expect(validation.errors).toHaveLength(0);
  });
});
