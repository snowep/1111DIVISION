/**
 * ORION Self-Evaluation System (TypeScript)
 * 
 * Evaluator as a logical role separate from Builder.
 * Ported from Python EvaluatorEngine with identical semantics.
 */

export type EvaluationVerdict = "PASS" | "FAIL" | "WARNING";
export type EvaluationFindingSeverity = "CRITICAL" | "WARNING" | "INFO";
export type CriterionType = "objective" | "quality" | "security" | "process";

export interface EvaluationCriterion {
  key: string;
  name: string;
  description: string;
  weight: number;
  type: CriterionType;
  requiredEvidence: boolean;
  threshold: number; // 0-1, minimum score for this criterion to pass
}

export interface EvaluationFinding {
  criterion: string;
  severity: EvaluationFindingSeverity;
  message: string;
  evidence: string;
  suggestion?: string;
  resolved: boolean;
}

export interface EvaluationResult {
  verdict: EvaluationVerdict;
  score: number;
  criterionScores: Record<string, number>;
  findings: EvaluationFinding[];
  requiresCorrection: boolean;
  correctionBudgetRemaining: number;
  evaluatedAt: string;
  evaluationCycle: number;
  notes: string;
}

export interface EvaluatorConfig {
  criteria: EvaluationCriterion[];
  passThreshold: number;
  warningThreshold: number;
  maxCorrectionCycles: number;
  requireVerification: boolean;
  requireNoCriticalFindings: boolean;
  scoringWeights: Record<string, number>;
}

export const DEFAULT_EVALUATION_CRITERIA: EvaluationCriterion[] = [
  {
    key: "objective_met",
    name: "Objective Met",
    description: "Task objective fully satisfied with measurable outcome",
    weight: 1.0,
    type: "objective",
    requiredEvidence: true,
    threshold: 0.8,
  },
  {
    key: "verification_evidence",
    name: "Verification Evidence",
    description: "Concrete proof of completion (tests, outputs, logs)",
    weight: 1.0,
    type: "quality",
    requiredEvidence: true,
    threshold: 0.8,
  },
  {
    key: "no_critical_issues",
    name: "No Critical Issues",
    description: "No CRITICAL-severity findings from verification/critique",
    weight: 1.5,
    type: "quality",
    requiredEvidence: true,
    threshold: 1.0,
  },
  {
    key: "code_quality",
    name: "Code Quality",
    description: "Lint, type-check, and pattern compliance pass",
    weight: 0.8,
    type: "quality",
    requiredEvidence: false,
    threshold: 0.7,
  },
  {
    key: "test_coverage",
    name: "Test Coverage",
    description: "Tests exist for new/changed code and pass",
    weight: 0.8,
    type: "quality",
    requiredEvidence: false,
    threshold: 0.7,
  },
  {
    key: "documentation",
    name: "Documentation",
    description: "Changes documented (README, comments, changelog)",
    weight: 0.5,
    type: "process",
    requiredEvidence: false,
    threshold: 0.5,
  },
  {
    key: "security_safety",
    name: "Security & Safety",
    description: "No security vulnerabilities or safety violations",
    weight: 1.2,
    type: "security",
    requiredEvidence: true,
    threshold: 1.0,
  },
  {
    key: "performance",
    name: "Performance",
    description: "Meets performance targets (latency, throughput, memory)",
    weight: 0.5,
    type: "quality",
    requiredEvidence: false,
    threshold: 0.6,
  },
];

function normalizeCriteria(criteria: EvaluationCriterion[]): EvaluationCriterion[] {
  let totalWeight = criteria.reduce((sum, c) => sum + c.weight, 0);
  if (totalWeight === 0) totalWeight = 1;
  return criteria.map((c) => ({ ...c, weight: c.weight / totalWeight }));
}

export function createEvaluatorConfig(overrides: Partial<EvaluatorConfig> = {}): EvaluatorConfig {
  const criteria = overrides.criteria || DEFAULT_EVALUATION_CRITERIA;
  const normalized = normalizeCriteria(criteria);
  
  const config: EvaluatorConfig = {
    criteria: normalized,
    passThreshold: overrides.passThreshold ?? 0.8,
    warningThreshold: overrides.warningThreshold ?? 0.6,
    maxCorrectionCycles: overrides.maxCorrectionCycles ?? 3,
    requireVerification: overrides.requireVerification ?? true,
    requireNoCriticalFindings: overrides.requireNoCriticalFindings ?? true,
    scoringWeights: overrides.scoringWeights ?? {},
  };
  
  // Apply scoring weights
  if (config.scoringWeights) {
    for (const criterion of config.criteria) {
      if (criterion.key in config.scoringWeights) {
        criterion.weight = config.scoringWeights[criterion.key];
      }
    }
    // Re-normalize after weight overrides
    config.criteria = normalizeCriteria(config.criteria);
  }
  
  // Validate thresholds
  if (!(0 <= config.warningThreshold && config.warningThreshold <= config.passThreshold && config.passThreshold <= 1)) {
    throw new Error("Thresholds must satisfy 0 <= warning <= pass <= 1");
  }
  if (config.maxCorrectionCycles < 0) {
    throw new Error("maxCorrectionCycles cannot be negative");
  }
  
  return config;
}

export interface TaskContext {
  objective: string;
  plan: string[];
  executionLog: Array<{ action: string; result: string; success: boolean }>;
  verificationResults: Array<{ overall: string; checks: Record<string, boolean> }>;
  critiqueFindings: string[];
  corrections: Array<{ finding: string; action: string; resolved: boolean }>;
  persona?: string;
}

export class EvaluatorEngine {
  private config: EvaluatorConfig;
  private root: string;

  constructor(config: EvaluatorConfig, root: string) {
    this.config = config;
    this.root = root;
  }

  evaluate(
    task: TaskContext,
    verification: { overall: string; checks: Record<string, boolean> },
    critiqueFindings: string[],
    correctionBudgetRemaining: number,
    evaluationCycle: number = 1
  ): EvaluationResult {
    const criterionScores: Record<string, number> = {};
    const findings: EvaluationFinding[] = [];

    // Evaluate each criterion
    for (const criterion of this.config.criteria) {
      const score = this.scoreCriterion(criterion, task, verification, critiqueFindings);
      criterionScores[criterion.key] = score;

      // Generate findings for low scores
      if (score < criterion.threshold) {
        const severity = this.determineSeverity(criterion, score);
        findings.push({
          criterion: criterion.key,
          severity,
          message: this.generateFindingMessage(criterion, score, task),
          evidence: this.gatherEvidence(criterion, task, verification),
          suggestion: this.generateSuggestion(criterion, score),
          resolved: false,
        });
      }
    }

    // Calculate weighted overall score
    const weightedScore = this.config.criteria.reduce(
      (sum, c) => sum + criterionScores[c.key] * c.weight,
      0
    );

    // Determine verdict
    let verdict: EvaluationVerdict;
    const hasCriticalFindings = findings.some((f) => f.severity === "CRITICAL");
    
    if (this.config.requireNoCriticalFindings && hasCriticalFindings) {
      verdict = "FAIL";
    } else if (weightedScore >= this.config.passThreshold) {
      verdict = "PASS";
    } else if (weightedScore >= this.config.warningThreshold) {
      verdict = "WARNING";
    } else {
      verdict = "FAIL";
    }

    // Check verification requirement
    if (this.config.requireVerification && verification.overall !== "PASS") {
      verdict = "FAIL";
      findings.push({
        criterion: "verification_evidence",
        severity: "CRITICAL",
        message: "Verification did not pass; required for EXP eligibility",
        evidence: JSON.stringify(verification.checks),
        suggestion: "Fix failing verification checks before re-evaluation",
        resolved: false,
      });
    }

    const requiresCorrection = verdict === "FAIL" && correctionBudgetRemaining > 0;

    return {
      verdict,
      score: Math.round(weightedScore * 10000) / 10000,
      criterionScores,
      findings,
      requiresCorrection,
      correctionBudgetRemaining: requiresCorrection ? correctionBudgetRemaining - 1 : correctionBudgetRemaining,
      evaluatedAt: new Date().toISOString(),
      evaluationCycle,
      notes: requiresCorrection ? `Correction cycle ${evaluationCycle} of ${this.config.maxCorrectionCycles}` : "",
    };
  }

  private scoreCriterion(
    criterion: EvaluationCriterion,
    task: TaskContext,
    verification: { overall: string; checks: Record<string, boolean> },
    critiqueFindings: string[]
  ): number {
    switch (criterion.key) {
      case "objective_met":
        return this.scoreObjectiveMet(task);
      case "verification_evidence":
        return this.scoreVerificationEvidence(verification);
      case "no_critical_issues":
        return this.scoreNoCriticalIssues(critiqueFindings);
      case "code_quality":
        return this.scoreCodeQuality(task);
      case "test_coverage":
        return this.scoreTestCoverage(task);
      case "documentation":
        return this.scoreDocumentation(task);
      case "security_safety":
        return this.scoreSecuritySafety(task, critiqueFindings);
      case "performance":
        return this.scorePerformance(task);
      default:
        return 0.5;
    }
  }

  private scoreObjectiveMet(task: TaskContext): number {
    // Heuristic: check if execution log shows completion actions
    const completedSteps = task.executionLog.filter((e) => e.success).length;
    const totalSteps = task.plan.length;
    if (totalSteps === 0) return 0.5;
    return Math.min(completedSteps / totalSteps, 1.0);
  }

  private scoreVerificationEvidence(verification: { overall: string; checks: Record<string, boolean> }): number {
    if (verification.overall === "PASS") return 1.0;
    if (verification.overall === "PARTIAL") return 0.6;
    const passed = Object.values(verification.checks).filter((v) => v).length;
    const total = Object.keys(verification.checks).length;
    return total > 0 ? passed / total : 0.3;
  }

  private scoreNoCriticalIssues(critiqueFindings: string[]): number {
    const criticalKeywords = ["critical", "blocker", "security", "vulnerability", "data loss", "crash"];
    const hasCritical = critiqueFindings.some((f) =>
      criticalKeywords.some((kw) => f.toLowerCase().includes(kw))
    );
    return hasCritical ? 0.0 : 1.0;
  }

  private scoreCodeQuality(task: TaskContext): number {
    // Check for lint/type errors in execution log
    const hasErrors = task.executionLog.some(
      (e) => !e.success && (e.result.includes("error") || e.result.includes("Error"))
    );
    return hasErrors ? 0.4 : 0.8;
  }

  private scoreTestCoverage(task: TaskContext): number {
    // Check if tests were run
    const testsRun = task.executionLog.some(
      (e) => e.action.toLowerCase().includes("test") && e.success
    );
    return testsRun ? 0.9 : 0.5;
  }

  private scoreDocumentation(task: TaskContext): number {
    const docsUpdated = task.executionLog.some(
      (e) =>
        e.action.toLowerCase().includes("doc") ||
        e.action.toLowerCase().includes("readme") ||
        e.action.toLowerCase().includes("changelog")
    );
    return docsUpdated ? 0.8 : 0.5;
  }

  private scoreSecuritySafety(task: TaskContext, critiqueFindings: string[]): number {
    const securityKeywords = ["secret", "password", "token", "key", "credential", "inject", "xss", "csrf"];
    const hasSecurityIssue = [...critiqueFindings, ...task.executionLog.map((e) => e.result)].some((f) =>
      securityKeywords.some((kw) => f.toLowerCase().includes(kw))
    );
    return hasSecurityIssue ? 0.0 : 0.9;
  }

  private scorePerformance(task: TaskContext): number {
    // Placeholder - would need actual metrics
    return 0.7;
  }

  private determineSeverity(criterion: EvaluationCriterion, score: number): EvaluationFindingSeverity {
    if (score === 0 || (criterion.requiredEvidence && score < 0.5)) {
      return "CRITICAL";
    }
    if (score < criterion.threshold) {
      return "WARNING";
    }
    return "INFO";
  }

  private generateFindingMessage(
    criterion: EvaluationCriterion,
    score: number,
    task: TaskContext
  ): string {
    const pct = Math.round(score * 100);
    return `${criterion.name} scored ${pct}% (threshold: ${Math.round(criterion.threshold * 100)}%) - ${criterion.description}`;
  }

  private gatherEvidence(
    criterion: EvaluationCriterion,
    task: TaskContext,
    verification: { overall: string; checks: Record<string, boolean> }
  ): string {
    switch (criterion.key) {
      case "verification_evidence":
        return JSON.stringify(verification.checks, null, 2);
      case "objective_met":
        return `Plan: ${task.plan.length} steps, Executed: ${task.executionLog.length} steps, Success: ${task.executionLog.filter(e => e.success).length}`;
      case "no_critical_issues":
        return task.critiqueFindings.join("; ");
      case "code_quality":
        return task.executionLog.filter((e) => !e.success).map((e) => e.result).join("; ");
      default:
        return "";
    }
  }

  private generateSuggestion(criterion: EvaluationCriterion, score: number): string {
    const suggestions: Record<string, string> = {
      objective_met: "Complete remaining plan steps or clarify objective",
      verification_evidence: "Run verification checks and provide concrete outputs",
      no_critical_issues: "Address all CRITICAL findings before re-evaluation",
      code_quality: "Run linter/type-check and fix reported issues",
      test_coverage: "Add tests for new/changed functionality",
      documentation: "Update relevant documentation (README, comments, changelog)",
      security_safety: "Remove secrets, fix vulnerabilities, validate inputs",
      performance: "Profile and optimize bottlenecks",
    };
    return suggestions[criterion.key] || "Review and improve";
  }
}