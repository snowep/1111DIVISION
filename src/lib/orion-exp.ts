/**
 * ORION EXP (Experience Points) System (TypeScript)
 * 
 * EXP measures verified useful experience, not activity volume.
 * Ported from Python EXPManager with identical semantics.
 */

import fs from "node:fs/promises";
import path from "node:path";

export type EXPEventResult = "AWARDED" | "REJECTED" | "DUPLICATE";

export interface EXPLevel {
  name: string;
  minExp: number;
  description: string;
}

export interface EXPRecord {
  taskId: string;
  expAwarded: number;
  event: string;
  outcome: string;
  lesson: string;
  source: string;
  awardedAt: string;
  verificationScore: number;
  metadata: Record<string, unknown>;
}

export interface EXPState {
  totalExp: number;
  level: string;
  tasksVerified: number;
  lastAwardedAt?: string;
  records: EXPRecord[];
}

export interface EXPProgress {
  totalExp: number;
  level: EXPLevel;
  nextLevel: EXPLevel | null;
  progressToNext: number;
  tasksVerified: number;
}

const DEFAULT_LEVELS: EXPLevel[] = [
  { name: "Novice", minExp: 0, description: "Beginning to build verified experience." },
  { name: "Experienced", minExp: 100, description: "Consistently produces verified useful work." },
  { name: "Reliable", minExp: 500, description: "Dependable across repeated task types." },
  { name: "Specialized", minExp: 1500, description: "Deep verified experience in specific domains." },
  { name: "Advanced", minExp: 5000, description: "Highly experienced with strong verification history." },
  { name: "Master", minExp: 15000, description: "Recognized authority, guides evolution." },
  { name: "Architect", minExp: 50000, description: "Shapes system architecture, proposes evolution." },
];

const DEFAULT_AWARDS: Record<string, number> = {
  simple_verified: 10,
  normal_verified: 25,
  complex_verified: 50,
  major_contribution: 100,
  recovery: 10,
  reusable_improvement: 10,
  important_discovery: 10,
  exceptional_verification: 10,
};

function getOrionExpDir(): string {
  const root = process.env.ORION_WORKSPACE_ROOT
    ? path.resolve(process.env.ORION_WORKSPACE_ROOT)
    : process.cwd();
  return path.join(root, ".agent", "orion", "exp");
}

function getStateFile(): string {
  return path.join(getOrionExpDir(), "state.json");
}

function getRecordsFile(): string {
  return path.join(getOrionExpDir(), "records.json");
}

export class EXPManager {
  private levels: EXPLevel[];
  private awards: Record<string, number>;
  private stateFile: string;
  private recordsFile: string;
  private state: EXPState;

  constructor(
    levels: EXPLevel[] = DEFAULT_LEVELS,
    awards: Record<string, number> = DEFAULT_AWARDS,
    stateFile?: string
  ) {
    this.levels = levels;
    this.awards = awards;
    this.stateFile = stateFile || getStateFile();
    this.recordsFile = getRecordsFile();
    this.state = this.loadState();
  }

  private loadState(): EXPState {
    try {
      const content = require("node:fs").readFileSync(this.stateFile, "utf-8");
      return JSON.parse(content);
    } catch {
      return {
        totalExp: 0,
        level: this.levels[0].name,
        tasksVerified: 0,
        records: [],
      };
    }
  }

  private async saveState(): Promise<void> {
    await fs.mkdir(path.dirname(this.stateFile), { recursive: true });
    await fs.writeFile(this.stateFile, JSON.stringify(this.state, null, 2), "utf-8");
    await this.saveRecords();
  }

  private async saveRecords(): Promise<void> {
    await fs.mkdir(path.dirname(this.recordsFile), { recursive: true });
    await fs.writeFile(this.recordsFile, JSON.stringify(this.state.records, null, 2), "utf-8");
  }

  getLevelForExp(totalExp: number): EXPLevel {
    let current = this.levels[0];
    for (const level of this.levels) {
      if (totalExp >= level.minExp) {
        current = level;
      }
    }
    return current;
  }

  getCurrentLevel(): EXPLevel {
    return this.getLevelForExp(this.state.totalExp);
  }

  /**
   * Determine whether work qualifies for EXP.
   * EXP requires: passed evaluation, score >= 0.8, verification evidence exists.
   */
  isVerifiedUseful(evaluation: { passed: boolean; score: number }): boolean {
    return evaluation.passed && evaluation.score >= 0.8;
  }

  /**
   * Award EXP for a verified task.
   */
  async award(
    taskId: string,
    evaluation: { passed: boolean; score: number },
    event: string = "task_completed",
    outcome: string = "success",
    lesson: string = "",
    metadata: Record<string, unknown> = {}
  ): Promise<EXPEventResult> {
    if (!this.isVerifiedUseful(evaluation)) {
      return "REJECTED";
    }

    if (this.hasTaskRecord(taskId)) {
      return "DUPLICATE";
    }

    const amount = this.calculateAmount(evaluation, event);
    if (amount <= 0) {
      return "REJECTED";
    }

    const record: EXPRecord = {
      taskId,
      expAwarded: amount,
      event,
      outcome,
      lesson,
      source: "task",
      awardedAt: new Date().toISOString(),
      verificationScore: Math.round(evaluation.score * 10000) / 10000,
      metadata,
    };

    this.state.records.push(record);
    this.state.totalExp += amount;
    this.state.tasksVerified += 1;
    this.state.level = this.getLevelForExp(this.state.totalExp).name;
    this.state.lastAwardedAt = new Date().toISOString();

    await this.saveState();
    return "AWARDED";
  }

  private calculateAmount(evaluation: { score: number }, event: string): number {
    const base = this.awards[event] || this.awards.normal_verified || 0;
    const qualityMultiplier = 1.0 + Math.max(0.0, evaluation.score - 0.8);
    return Math.max(base, Math.floor(base * qualityMultiplier));
  }

  private hasTaskRecord(taskId: string): boolean {
    return this.state.records.some((r) => r.taskId === taskId);
  }

  getRecords(): EXPRecord[] {
    return [...this.state.records];
  }

  getTotalExp(): number {
    return this.state.totalExp;
  }

  getProgress(): EXPProgress {
    const total = this.getTotalExp();
    const current = this.getCurrentLevel();
    const nextLevels = this.levels.filter((l) => l.minExp > current.minExp);
    const nextLevel = nextLevels[0] || null;

    return {
      totalExp: total,
      level: current,
      nextLevel,
      progressToNext: nextLevel
        ? (total - current.minExp) / (nextLevel.minExp - current.minExp)
        : 1.0,
      tasksVerified: this.state.tasksVerified,
    };
  }

  async reset(): Promise<void> {
    this.state = {
      totalExp: 0,
      level: this.levels[0].name,
      tasksVerified: 0,
      records: [],
    };
    await this.saveState();
  }
}

// Singleton instance
let expManagerInstance: EXPManager | null = null;

export function getExpManager(): EXPManager {
  if (!expManagerInstance) {
    expManagerInstance = new EXPManager();
  }
  return expManagerInstance;
}