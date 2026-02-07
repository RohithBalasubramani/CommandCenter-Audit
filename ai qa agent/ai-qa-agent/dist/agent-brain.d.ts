import type { AgentAction, PageObservation, TestScenario, ActionLogEntry, FailureCategory, GoalLedger, PerceptionEntry } from './types';
import type { AgentConfig } from './config';
export declare class AgentBrain {
    private config;
    private systemPrompt;
    private recentHistory;
    private actionHistory;
    private stepCount;
    private maxRetries;
    private maxHistoryLines;
    private ledger;
    private perceptionLog;
    private lastUrl;
    private lastElementCount;
    private lastHeading;
    private sameScreenCount;
    private actionCache;
    private currentActionSequence;
    private persona;
    private lessons;
    private stepsSinceCritic;
    private criticInterval;
    private scenarioId;
    private qaProfile;
    private scenarioMaxActions;
    private actionSignatures;
    private targetUseCount;
    private targetFailureCount;
    constructor(agentConfig: AgentConfig);
    /** Initialize the brain with a test scenario */
    initScenario(scenario: TestScenario): void;
    /** Decide the next action based on current page state */
    decideAction(observation: PageObservation): Promise<AgentAction>;
    /** Feed action result back to the brain */
    recordResult(action: AgentAction, result: {
        success: boolean;
        error?: string;
    }, duration: number): void;
    /** Save action cache and lessons after scenario completes */
    finalizeScenario(success: boolean): void;
    /** Categorize a failure for structured reporting */
    categorizeFailure(error?: string, actionLog?: ActionLogEntry[]): FailureCategory;
    getActionHistory(): ActionLogEntry[];
    getPerceptionLog(): PerceptionEntry[];
    getLedger(): GoalLedger;
    getConversation(): Array<{
        role: string;
        content: string;
    }>;
    private detectStuckState;
    private updateLedger;
    private buildReplanPrompt;
    private runCritic;
    private buildSystemPrompt;
    private inferProfileFromConfig;
    private getProfilePolicy;
    /** Persona modifiers */
    private getPersonaText;
    private buildObservationText;
    private buildPrompt;
    private trimHistory;
    /**
     * Call Claude CLI asynchronously using spawn.
     */
    private callClaude;
    /** Lightweight Claude call for critic */
    private callClaudeLightweight;
    /** Async spawn wrapper */
    private spawnClaudeAsync;
    private parseAction;
    private decideWithRetries;
    private shouldUseConsensus;
    private tryConsensusSampling;
    private scoreCandidate;
    private normalizeAction;
    private enforceDoneGate;
    private shouldDiversify;
    private buildDiversifiedAction;
    private buildWaitFallback;
    private inferExpectedSignal;
    private buildActionSignature;
    private buildTargetKey;
    private getRemainingOutcomes;
    private markOutcomesFromObservation;
    private markOutcomesFromText;
    private extractKeywords;
    private normalizeText;
    private guessEvidenceKeyword;
    private isLikelyProgressAction;
    private isTargetPresent;
    private shuffleArray;
    private getCachedHint;
    private loadActionCache;
    private saveActionCache;
    private getLessonsForScenario;
    private extractLesson;
    private loadLessons;
    private saveLessons;
}
//# sourceMappingURL=agent-brain.d.ts.map