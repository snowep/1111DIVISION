# System Health Checks

## Purpose

Automated and manual health checks to verify system integrity, structure, and operational readiness.

---

## Structural Health

### Agent Backbone Validation

```bash
# Verify all required directories exist
.check_dirs() {
  dirs=(
    ".agent/orion/knowledge"
    ".agent/orion/skills"
    ".agent/orion/evolution"
    ".agent/personas/_template/knowledge"
    ".agent/personas/_template/skills"
    ".agent/personas/_template/experience"
    ".agent/personas/researcher/knowledge"
    ".agent/personas/researcher/skills"
    ".agent/personas/researcher/experience"
    ".agent/personas/developer/knowledge"
    ".agent/personas/developer/skills"
    ".agent/personas/developer/experience"
    ".agent/personas/designer/knowledge"
    ".agent/personas/designer/skills"
    ".agent/personas/designer/experience"
    ".agent/personas/analyst/knowledge"
    ".agent/personas/analyst/skills"
    ".agent/personas/analyst/experience"
    ".agent/shared/memory"
    ".agent/shared/knowledge"
    ".agent/shared/experience"
    ".agent/tasks"
    ".agent/sessions"
    ".agent/system"
  )
}
```

### Required Files Check

```bash
.check_files() {
  files=(
    ".agent/orion/identity.md"
    ".agent/orion/memory.md"
    ".agent/orion/experience.md"
    ".agent/system/config.md"
    ".agent/system/permissions.md"
    ".agent/system/version.md"
    ".agent/system/index.md"
    ".agent/system/health.md"
  )
}
```

---

## Functional Health

### ORION Core
- [ ] `orion.core` imports without error
- [ ] `ORION()` instantiates successfully
- [ ] Tool registry loads (23 tools)
- [ ] Permissions engine loads (47 rules)

### Permissions
- [ ] `PermissionEngine` evaluates correctly
- [ ] Levels: AUTONOMOUS, NOTIFY, CONFIRM, DENY
- [ ] Categories: FILES, CODE, WEB, TERMINAL, GIT, APIS, DATABASE

### Persona System
- [ ] Template structure valid
- [ ] Activation protocol accessible
- [ ] Registry reads correctly

### Memory/Knowledge
- [ ] Private directories accessible
- [ ] Shared directories accessible
- [ ] Promotion log exists

---

## Runtime Health

### Git
- [ ] Working directory clean
- [ ] Origin reachable
- [ ] Branch tracking configured

### Tools
- [ ] Filesystem operations functional
- [ ] Terminal execution functional
- [ ] Web search functional (if configured)

---

## Last Check

*Run `python -m .agent.system.health` to execute full health check suite.*

---

## Health Check Script Template

```python
#!/usr/bin/env python3
"""
.agent/system/health.py
System health check runner
"""
import os
from pathlib import Path

ROOT = Path("D:/Project/1111DIVISION")

def check_structure():
    """Verify backbone directory structure exists."""
    required_dirs = [
        ".agent/orion/knowledge",
        ".agent/orion/skills",
        ".agent/orion/evolution",
        ".agent/personas/_template/knowledge",
        ".agent/personas/_template/skills",
        ".agent/personas/_template/experience",
        # ... all persona dirs
    ]
    missing = []
    for d in required_dirs:
        if not (ROOT / d).exists():
            missing.append(d)
    return missing

def check_files():
    """Verify required files exist."""
    required_files = [
        ".agent/orion/identity.md",
        ".agent/orion/memory.md",
        ".agent/orion/experience.md",
        ".agent/system/config.md",
        ".agent/system/permissions.md",
        ".agent/system/version.md",
    ]
    missing = []
    for f in required_files:
        if not (ROOT / f).exists():
            missing.append(f)
    return missing

def check_orion_imports():
    """Verify ORION module loads."""
    try:
        from .agent.orion import ORION
        orion = ORION()
        return len(orion.registry.tools) == 23
    except Exception as e:
        return f"Import failed: {e}"

if __name__ == "__main__":
    print("=== System Health Check ===")
    print(f"Root: {ROOT}")
    print(f"Structure: {'OK' if not check_structure() else 'MISSING: ' + str(check_structure())}")
    print(f"Files: {'OK' if not check_files() else 'MISSING: ' + str(check_files())}")
    print(f"ORION: {check_orion_imports()}")
```