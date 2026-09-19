/**
 * ORION Versioning System (TypeScript)
 * 
 * Semantic versioning tied to evolution milestones.
 */

import fs from "node:fs/promises";
import path from "node:path";

export interface VersionInfo {
  version: string;
  major: number;
  minor: number;
  patch: number;
  tier: number;
  build: number;
  codename: string;
  releasedAt: string;
  evolutionMilestones: EvolutionMilestone[];
}

export interface EvolutionMilestone {
  version: string;
  milestone: string;
  date?: string;
}

export interface VersionBumpResult {
  version: VersionInfo;
  bumped: "major" | "minor" | "patch" | "tier" | "build";
}

const CODENAMES = [
  "INITIATE", "SYNTHESIS", "CATALYST", "VERTEX", "NEXUS",
  "APEX", "ZENITH", "HORIZON", "EQUINOX", "SOLSTICE",
  "MERIDIAN", "AZIMUTH", "POLARIS", "VEGA", "SIRIUS",
  "RIGEL", "BETELGEUSE", "ANTARES", "ALDEBARAN", "PROCYON"
];

function getOrionEvolutionDir(): string {
  const root = process.env.ORION_WORKSPACE_ROOT
    ? path.resolve(process.env.ORION_WORKSPACE_ROOT)
    : process.cwd();
  return path.join(root, ".agent", "orion", "evolution");
}

function getVersionFile(): string {
  return path.join(getOrionEvolutionDir(), "version.json");
}

function getDefaultVersion(): VersionInfo {
  return {
    version: "0.1.0-0.1",
    major: 0,
    minor: 1,
    patch: 0,
    tier: 0,
    build: 1,
    codename: CODENAMES[0],
    releasedAt: new Date().toISOString(),
    evolutionMilestones: [
      { version: "0.1.0", milestone: "Project initialized", date: new Date().toISOString() },
    ],
  };
}

function parseVersion(versionStr: string): { major: number; minor: number; patch: number; tier: number; build: number } | null {
  // Format: v<major>.<minor>.<patch>-<tier>.<build> or <major>.<minor>.<patch>-<tier>.<build>
  const match = versionStr.match(/^v?(\d+)\.(\d+)\.(\d+)-(\d+)\.(\d+)$/);
  if (!match) return null;
  return {
    major: parseInt(match[1], 10),
    minor: parseInt(match[2], 10),
    patch: parseInt(match[3], 10),
    tier: parseInt(match[4], 10),
    build: parseInt(match[5], 10),
  };
}

function formatVersion(v: { major: number; minor: number; patch: number; tier: number; build: number }): string {
  return `v${v.major}.${v.minor}.${v.patch}-${v.tier}.${v.build}`;
}

export class VersionManager {
  private versionFile: string;
  private version: VersionInfo;

  constructor(versionFile?: string) {
    this.versionFile = versionFile || getVersionFile();
    this.version = this.loadVersion();
  }

  private loadVersion(): VersionInfo {
    try {
      const content = require("node:fs").readFileSync(this.versionFile, "utf-8");
      return JSON.parse(content);
    } catch {
      const def = getDefaultVersion();
      this.saveVersion(def);
      return def;
    }
  }

  private async saveVersion(version: VersionInfo): Promise<void> {
    await fs.mkdir(path.dirname(this.versionFile), { recursive: true });
    await fs.writeFile(this.versionFile, JSON.stringify(version, null, 2), "utf-8");
  }

  getVersion(): VersionInfo {
    return { ...this.version };
  }

  getVersionString(): string {
    return this.version.version;
  }

  /**
   * Bump version based on evolution tier completion.
   * tier 0 (stable) -> build++
   * tier 1 (proposed) -> tier = 1
   * tier 2 (testing passed) -> minor++, tier = 0
   * tier 3 (integrated, breaking) -> major++, minor = 0, patch = 0, tier = 0
   */
  async bumpVersion(bumpType: "build" | "tier1" | "tier2" | "tier3"): Promise<VersionBumpResult> {
    const v = { ...this.version };
    let bumped: VersionBumpResult["bumped"] = "build";

    switch (bumpType) {
      case "build":
        v.build += 1;
        bumped = "build";
        break;
      case "tier1":
        v.tier = 1;
        bumped = "tier";
        break;
      case "tier2":
        v.minor += 1;
        v.patch = 0;
        v.tier = 0;
        v.build += 1;
        bumped = "minor";
        break;
      case "tier3":
        v.major += 1;
        v.minor = 0;
        v.patch = 0;
        v.tier = 0;
        v.build += 1;
        bumped = "major";
        break;
    }

    // Update codename on minor/major bumps
    if (bumped === "minor" || bumped === "major") {
      const codenameIndex = (v.minor + v.major * 10) % CODENAMES.length;
      v.codename = CODENAMES[codenameIndex];
    }

    v.version = formatVersion(v);
    v.releasedAt = new Date().toISOString();

    this.version = v;
    await this.saveVersion(v);

    return { version: v, bumped };
  }

  /**
   * Record an evolution milestone.
   */
  async recordMilestone(milestone: string, versionStr?: string): Promise<VersionInfo> {
    const v = { ...this.version };
    const version = versionStr || v.version.replace(/^v/, "");
    v.evolutionMilestones.push({
      version,
      milestone,
      date: new Date().toISOString(),
    });
    this.version = v;
    await this.saveVersion(v);
    return v;
  }

  /**
   * Set tier explicitly (for proposal tracking).
   */
  async setTier(tier: number): Promise<VersionInfo> {
    if (tier < 0 || tier > 3) {
      throw new Error("Tier must be 0-3");
    }
    const v = { ...this.version };
    v.tier = tier;
    v.version = formatVersion(v);
    this.version = v;
    await this.saveVersion(v);
    return v;
  }

  /**
   * Reset to initial version (for testing).
   */
  async reset(): Promise<VersionInfo> {
    const v = getDefaultVersion();
    this.version = v;
    await this.saveVersion(v);
    return v;
  }
}

let versionManagerInstance: VersionManager | null = null;

export function getVersionManager(): VersionManager {
  if (!versionManagerInstance) {
    versionManagerInstance = new VersionManager();
  }
  return versionManagerInstance;
}