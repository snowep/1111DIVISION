"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AppBar, Box, Card, CardContent, Chip, Divider, Grid, List, ListItem,
  ListItemText, Stack, Toolbar, Typography, Button, IconButton, Tabs, Tab,
  Paper, TextField, InputAdornment, CircularProgress, Alert, AlertTitle,
  Accordion, AccordionSummary, AccordionDetails, Table, TableBody, TableCell,
  TableContainer, TableHead, TableRow, LinearProgress, Tooltip, Avatar,
  Badge, Menu, MenuItem, Select, FormControl, InputLabel, Dialog, DialogTitle,
  DialogContent, DialogActions, Slide
} from "@mui/material";
import {
  Memory as MemoryIcon, Hub as HubIcon, Storage as StorageIcon,
  Psychology as PsychologyIcon, FolderOpen as FolderOpenIcon,
  Person as PersonIcon, EmojiEvents as ExpIcon, Code as VersionIcon,
  Assessment as EvalIcon, Settings as SettingsIcon, Add as AddIcon,
  PlayArrow as PlayIcon, Refresh as RefreshIcon, Search as SearchIcon,
  Visibility as VisibilityIcon, Edit as EditIcon, Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon, ChevronLeft as ChevronLeftIcon,
  ChevronRight as ChevronRightIcon, AutoAwesome as AutoAwesomeIcon,
  Timeline as TimelineIcon, LibraryBooks as LibraryIcon, PersonAdd as PersonAddIcon
} from "@mui/icons-material";
import type { OrionEvent, WorkspaceSnapshot } from "@/lib/types";
import { createTransitionEvents } from "@/lib/orion-events";

// Types for new features
interface PersonaInfo {
  name: string;
  role: string;
  purpose: string;
  level: number;
  tools: number;
  knowledgeDomains: number;
  skills: number;
}

interface EXPProgress {
  totalExp: number;
  level: { name: string; minExp: number; description: string };
  nextLevel: { name: string; minExp: number; description: string } | null;
  progressToNext: number;
  tasksVerified: number;
}

interface VersionInfo {
  version: string;
  major: number;
  minor: number;
  patch: number;
  tier: number;
  build: number;
  codename: string;
  releasedAt: string;
  evolutionMilestones: { version: string; milestone: string; date?: string }[];
}

interface TaskRecord {
  taskId: string;
  status: string;
  persona?: string;
  evaluation?: { verdict: string; score: number };
  expResult?: { result: string; progress: EXPProgress };
  version?: VersionInfo;
  error?: string;
}

interface MemoryFile {
  path: string;
  content: string;
}

const initialEvents: OrionEvent[] = [{
  id: "boot",
  time: "--:--:--",
  stage: "SYSTEM",
  message: "ORION TypeScript transition runtime initialized",
  status: "complete"
}];

// TransitionSlide for Dialog
const TransitionSlide = Slide;

export default function OrionDashboard() {
  // Core state
  const [workspace, setWorkspace] = useState<WorkspaceSnapshot | null>(null);
  const [events, setEvents] = useState<OrionEvent[]>(initialEvents);
  const [mounted, setMounted] = useState(false);
  
  // Persona state
  const [personas, setPersonas] = useState<PersonaInfo[]>([]);
  const [activePersona, setActivePersona] = useState<PersonaInfo | null>(null);
  const [personaLoading, setPersonaLoading] = useState(false);
  const [showCreatePersona, setShowCreatePersona] = useState(false);
  const [newPersonaForm, setNewPersonaForm] = useState({
    name: "", role: "", purpose: "", boundaries: "", style: "",
    tools: "", knowledge: "", skills: "", evaluationCriteria: "", level: "1"
  });
  
  // EXP state
  const [expProgress, setExpProgress] = useState<EXPProgress | null>(null);
  const [expLoading, setExpLoading] = useState(false);
  
  // Version state
  const [version, setVersion] = useState<VersionInfo | null>(null);
  const [versionLoading, setVersionLoading] = useState(false);
  
  // Task history state
  const [tasks, setTasks] = useState<TaskRecord[]>([]);
  const [tasksLoading, setTasksLoading] = useState(false);
  
  // Memory browser state
  const [memoryFiles, setMemoryFiles] = useState<MemoryFile[]>([]);
  const [memoryLoading, setMemoryLoading] = useState(false);
  const [memoryStore, setMemoryStore] = useState<"memory" | "knowledge" | "experience">("memory");
  const [selectedMemoryFile, setSelectedMemoryFile] = useState<MemoryFile | null>(null);
  const [showMemoryViewer, setShowMemoryViewer] = useState(false);
  const [memoryEditorContent, setMemoryEditorContent] = useState("");
  const [editingMemory, setEditingMemory] = useState(false);
  
  // UI state
  const [tabIndex, setTabIndex] = useState(0);
  const [taskInput, setTaskInput] = useState("Inspect the local workspace and explain what ORION can currently see.");
  const [runningTask, setRunningTask] = useState(false);

  // Initialize on mount
  useEffect(() => {
    setMounted(true);
    setEvents((current) => current.map((e) =>
      e.id === "boot" ? { ...e, time: new Date().toLocaleTimeString() } : e
    ));
    loadPersonas();
    loadExpProgress();
    loadVersion();
    loadTasks();
    loadMemoryFiles();
  }, []);

  // Update boot event time on mount
  useEffect(() => {
    if (mounted) {
      setEvents((current) => current.map((e) =>
        e.time === "--:--:--" ? { ...e, time: new Date().toLocaleTimeString() } : e
      ));
    }
  }, [mounted]);

  // API helpers
  const apiCall = async <T,>(url: string, options?: RequestInit): Promise<T> => {
    const response = await fetch(url, {
      headers: { "Content-Type": "application/json" },
      ...options
    });
    if (!response.ok) {
      const error = await response.json().catch(() => ({ error: "Unknown error" }));
      throw new Error(error.error || `HTTP ${response.status}`);
    }
    return response.json();
  };

  // Persona functions
  const loadPersonas = async () => {
    setPersonaLoading(true);
    try {
      const data = await apiCall<{ personas: PersonaInfo[] }>("/api/orion/personas");
      setPersonas(data.personas);
    } catch (error) {
      console.error("Failed to load personas:", error);
    } finally {
      setPersonaLoading(false);
    }
  };

  const activatePersona = async (personaName: string) => {
    setPersonaLoading(true);
    try {
      const data = await apiCall<{ context: string; personaName: string; activated: boolean; contextTokensEstimate: number }>(
        "/api/orion/personas",
        { method: "POST", body: JSON.stringify({ action: "activate", personaName }) }
      );
      const persona = personas.find(p => p.name === personaName) || null;
      setActivePersona(persona);
      addEvent("PERSONA", `Activated ${personaName} (${data.contextTokensEstimate} tokens)`, "complete");
    } catch (error) {
      addEvent("PERSONA", `Failed to activate ${personaName}: ${error}`, "error");
    } finally {
      setPersonaLoading(false);
    }
  };

  const createPersona = async () => {
    try {
      await apiCall("/api/orion/personas", {
        method: "POST",
        body: JSON.stringify({
          action: "create",
          ...newPersonaForm,
          boundaries: newPersonaForm.boundaries.split("\n").filter(Boolean),
          tools: newPersonaForm.tools.split("\n").filter(Boolean),
          knowledge: newPersonaForm.knowledge.split("\n").filter(Boolean),
          skills: newPersonaForm.skills.split("\n").filter(Boolean),
          evaluationCriteria: newPersonaForm.evaluationCriteria.split("\n").filter(Boolean),
          level: parseInt(newPersonaForm.level, 10)
        })
      });
      setShowCreatePersona(false);
      setNewPersonaForm({ name: "", role: "", purpose: "", boundaries: "", style: "", tools: "", knowledge: "", skills: "", evaluationCriteria: "", level: "1" });
      await loadPersonas();
      addEvent("PERSONA", `Created persona: ${newPersonaForm.name}`, "complete");
    } catch (error) {
      addEvent("PERSONA", `Failed to create persona: ${error}`, "error");
    }
  };

  // EXP functions
  const loadExpProgress = async () => {
    setExpLoading(true);
    try {
      const data = await apiCall<{ progress: EXPProgress }>("/api/orion/exp");
      setExpProgress(data.progress);
    } catch (error) {
      console.error("Failed to load EXP:", error);
    } finally {
      setExpLoading(false);
    }
  };

  // Version functions
  const loadVersion = async () => {
    setVersionLoading(true);
    try {
      const data = await apiCall<{ version: VersionInfo }>("/api/orion/version");
      setVersion(data.version);
    } catch (error) {
      console.error("Failed to load version:", error);
    } finally {
      setVersionLoading(false);
    }
  };

  // Task functions
  const loadTasks = async () => {
    setTasksLoading(true);
    try {
      const data = await apiCall<{ tasks: TaskRecord[] }>("/api/orion/task");
      setTasks(data.tasks);
    } catch (error) {
      console.error("Failed to load tasks:", error);
    } finally {
      setTasksLoading(false);
    }
  };

  const runTask = async () => {
    if (!taskInput.trim() || runningTask) return;
    
    setRunningTask(true);
    addEvent("TASK", `Starting: ${taskInput.slice(0, 80)}...`, "running");
    
    try {
      const data = await apiCall<TaskRecord>("/api/orion/task", {
        method: "POST",
        body: JSON.stringify({
          objective: taskInput,
          persona: activePersona?.name,
          budget: "standard",
          autoEvaluate: true
        })
      });
      
      addEvent("TASK", `Completed: ${data.taskId} (${data.status})`, data.status === "completed" ? "complete" : "error");
      
      if (data.evaluation) {
        addEvent("EVAL", `Verdict: ${data.evaluation.verdict} (${(data.evaluation.score * 100).toFixed(0)}%)`, 
          data.evaluation.verdict === "PASS" ? "complete" : "warning");
      }
      
      if (data.expResult) {
        addEvent("EXP", `Awarded: ${data.expResult.result} | Total: ${data.expResult.progress.totalExp} XP`, "complete");
        setExpProgress(data.expResult.progress);
      }
      
      if (data.version) {
        setVersion(data.version);
        addEvent("VERSION", `Bumped to ${data.version.version}`, "info");
      }
      
      await loadTasks();
    } catch (error) {
      addEvent("TASK", `Failed: ${error}`, "error");
    } finally {
      setRunningTask(false);
    }
  };

  // Memory browser functions
  const loadMemoryFiles = async () => {
    setMemoryLoading(true);
    try {
      const data = await apiCall<{ files: string[] }>(`/api/orion/memory?action=list&store=${memoryStore}`);
      setMemoryFiles(data.files.map(f => ({ path: f, content: "" })));
    } catch (error) {
      console.error("Failed to load memory files:", error);
    } finally {
      setMemoryLoading(false);
    }
  };

  const readMemoryFile = async (file: MemoryFile) => {
    try {
      const data = await apiCall<{ content: string }>(`/api/orion/memory?action=read&path=${encodeURIComponent(file.path)}`);
      const updated = { ...file, content: data.content };
      setSelectedMemoryFile(updated);
      setMemoryEditorContent(data.content);
      setShowMemoryViewer(true);
    } catch (error) {
      addEvent("MEMORY", `Failed to read ${file.path}: ${error}`, "error");
    }
  };

  const saveMemoryFile = async () => {
    if (!selectedMemoryFile) return;
    try {
      await apiCall("/api/orion/memory", {
        method: "POST",
        body: JSON.stringify({
          action: "write",
          path: selectedMemoryFile.path,
          content: memoryEditorContent,
          type: memoryStore
        })
      });
      setEditingMemory(false);
      setShowMemoryViewer(false);
      addEvent("MEMORY", `Saved ${selectedMemoryFile.path}`, "complete");
    } catch (error) {
      addEvent("MEMORY", `Failed to save: ${error}`, "error");
    }
  };

  // Event helper
  const addEvent = (stage: string, message: string, status: OrionEvent["status"]) => {
    setEvents((current) => [...current, {
      id: crypto.randomUUID(),
      time: new Date().toLocaleTimeString(),
      stage,
      message,
      status
    }]);
  };

  const visibleFiles = useMemo(() => workspace?.files.slice(0, 12) ?? [], [workspace]);

  // Format version string
  const formatVersion = (v: VersionInfo | null) => {
    if (!v) return "—";
    return `${v.version} (${v.codename})`;
  };

  // Format EXP level
  const formatLevel = (level: EXPProgress["level"] | null) => {
    if (!level) return "—";
    return `${level.name} (${level.minExp} XP)`;
  };

  return (
    <Box>
      <AppBar position="static" elevation={2}>
        <Toolbar>
          <MemoryIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
            ORION
          </Typography>
          <Badge badgeContent={version?.tier > 0 ? version.tier : ""} color="error" overlap="circular">
            <VersionIcon sx={{ mr: 1 }} />
          </Badge>
          <Typography variant="body2" sx={{ mr: 2, minWidth: 180 }}>
            {formatVersion(version)}
          </Typography>
          <Tooltip title="Total EXP">
            <Box sx={{ display: "flex", alignItems: "center", mr: 2 }}>
              <ExpIcon sx={{ mr: 0.5, color: "warning.main" }} />
              <Typography variant="body2" sx={{ minWidth: 80 }}>
                {expProgress?.totalExp ?? 0} XP
              </Typography>
            </Box>
          </Tooltip>
          <Tooltip title="Current Level">
            <Chip
              label={expProgress?.level.name ?? "Novice"}
              size="small"
              color="primary"
              variant="outlined"
            />
          </Tooltip>
          <Chip label="TRANSITION" color="secondary" size="small" />
        </Toolbar>
      </AppBar>

      <Box component="main" sx={{ p: 3 }}>
        <Stack spacing={3}>
          {/* Header */}
          <Box>
            <Typography variant="h4" gutterBottom>
              Orchestrated Reasoning & Intelligence Operating Network
            </Typography>
            <Typography color="text.secondary">
              Multi-persona • Persistent memory • Self-evaluation • EXP gamification • Controlled evolution
            </Typography>
          </Box>

          {/* Tab Navigation */}
          <Paper elevation={1} sx={{ p: 1 }}>
            <Tabs
              value={tabIndex}
              onChange={(_, v) => setTabIndex(v)}
              variant="scrollable"
              scrollButtons="auto"
              sx={{ minWidth: 0 }}
            >
              <Tab icon={<HubIcon />} label="Overview" />
              <Tab icon={<PersonIcon />} label="Personas" />
              <Tab icon={<AutoAwesomeIcon />} label="EXP & Levels" />
              <Tab icon={<VersionIcon />} label="Version" />
              <Tab icon={<TimelineIcon />} label="Tasks" />
              <Tab icon={<LibraryIcon />} label="Memory" />
              <Tab icon={<EvalIcon />} label="Evaluation" />
              <Tab icon={<SettingsIcon />} label="Settings" />
            </Tabs>
          </Paper>

          {/* Tab Panels */}
          {tabIndex === 0 && (
            // OVERVIEW TAB
            <>
              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card><CardContent><Stack spacing={2}>
                    <HubIcon />
                    <Typography variant="h6">ORION Runtime</Typography>
                    <Chip label="ONLINE" color="success" />
                    <Typography color="text.secondary">
                      TypeScript runtime with persona routing, memory retrieval, evaluation, EXP, and evolution.
                    </Typography>
                  </Stack></CardContent></Card>
                </Grid>
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card><CardContent><Stack spacing={2}>
                    <StorageIcon />
                    <Typography variant="h6">Workspace</Typography>
                    <Typography variant="h4">{workspace?.files.length ?? "—"}</Typography>
                    <Typography color="text.secondary">files visible to ORION</Typography>
                  </Stack></CardContent></Card>
                </Grid>
                <Grid size={{ xs: 12, md: 4 }}>
                  <Card><CardContent><Stack spacing={2}>
                    <PsychologyIcon />
                    <Typography variant="h6">Memory / Knowledge</Typography>
                    <Typography>Markdown remains the persistent source of truth.</Typography>
                    <Stack direction="row" spacing={1}>
                      <Chip label={`${workspace?.markdown.length ?? 0} MD`} size="small" />
                      <Chip label={`${workspace?.agentFiles.length ?? 0} agent files`} size="small" />
                      <Chip label={`${personas.length} personas`} size="small" color="primary" />
                    </Stack>
                  </Stack></CardContent></Card>
                </Grid>
              </Grid>

              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 7 }}>
                  <Card><CardContent><Stack spacing={2}>
                    <Typography variant="h6">Live ORION Event Stream</Typography>
                    <Typography color="text.secondary">
                      Operational telemetry — not private model chain-of-thought.
                    </Typography>
                    <Divider />
                    <List>
                      {events.slice().reverse().map((event) => (
                        <ListItem key={event.id} disableGutters>
                          <ListItemText
                            primary={<Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                              <Chip size="small" label={event.stage} 
                                color={event.status === "error" ? "error" : event.status === "warning" ? "warning" : event.status === "running" ? "primary" : "default"} />
                              <Typography variant="body2">{event.message}</Typography>
                            </Stack>}
                            secondary={event.time}
                          />
                        </ListItem>
                      ))}
                    </List>
                  </Stack></CardContent></Card>
                </Grid>

                <Grid size={{ xs: 12, md: 5 }}>
                  <Card><CardContent><Stack spacing={2}>
                    <Typography variant="h6">Quick Actions</Typography>
                    <Button 
                      variant="contained" 
                      startIcon={<PlayIcon />} 
                      fullWidth
                      onClick={runTask}
                      disabled={runningTask || !taskInput.trim()}
                    >
                      {runningTask ? "Running..." : "Run Task"}
                    </Button>
                    <TextField
                      fullWidth
                      multiline
                      rows={3}
                      placeholder="Enter task objective..."
                      value={taskInput}
                      onChange={(e) => setTaskInput(e.target.value)}
                      label="Task Objective"
                    />
                    <Divider />
                    <Typography variant="body2" color="text.secondary">
                      Active Persona: <strong>{activePersona?.name ?? "None"}</strong>
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      EXP: {expProgress?.totalExp ?? 0} | Level: {expProgress?.level.name ?? "Novice"}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      Version: {formatVersion(version)}
                    </Typography>
                  </Stack></CardContent></Card>
                </Grid>
              </Grid>

              <Grid container spacing={3}>
                <Grid size={{ xs: 12, md: 7 }}>
                  <Card><CardContent><Stack spacing={2}>
                    <Typography variant="h6">Local Filesystem</Typography>
                    <Typography color="text.secondary">
                      {workspace?.root ?? "Resolving ORION_WORKSPACE_ROOT…"}
                    </Typography>
                    <Divider />
                    <List dense>
                      {visibleFiles.map((file) => (
                        <ListItem key={file.path} disableGutters>
                          <FolderOpenIcon sx={{ mr: 1 }} />
                          <ListItemText primary={file.path} secondary={`${file.kind} · ${file.size} bytes`} />
                        </ListItem>
                      ))}
                    </List>
                  </Stack></CardContent></Card>
                </Grid>

                <Grid size={{ xs: 12, md: 5 }}>
                  <Card><CardContent><Stack spacing={2}>
                    <Typography variant="h6">Transition Test</Typography>
                    <Typography color="text.secondary">
                      local files → workspace scanner → ORION event stream → UI
                    </Typography>
                    <Typography>{taskInput}</Typography>
                    <Chip
                      label="Run transition trace"
                      color="primary"
                      clickable
                      onClick={() => setEvents((current) => [...current, ...createTransitionEvents(taskInput)])}
                    />
                  </Stack></CardContent></Card>
                </Grid>
              </Grid>
            </>
          )}

          {tabIndex === 1 && (
            // PERSONAS TAB
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                    <Typography variant="h6">Available Personas</Typography>
                    <Button variant="contained" startIcon={<PersonAddIcon />} onClick={() => setShowCreatePersona(true)}>
                      Create Persona
                    </Button>
                  </Stack>
                  {personaLoading ? (
                    <CircularProgress size={24} />
                  ) : (
                    <List dense>
                      {personas.map((persona) => (
                        <ListItem 
                          key={persona.name} 
                          disableGutters
                          selected={activePersona?.name === persona.name}
                          sx={{ bgcolor: activePersona?.name === persona.name ? "primary.main" : "transparent", "&:hover": { bgcolor: "action.hover" }}}
                          onClick={() => activatePersona(persona.name)}
                        >
                          <PersonIcon sx={{ mr: 1, color: activePersona?.name === persona.name ? "primary.contrastText" : "inherit" }} />
                          <ListItemText
                            primary={<Typography variant="body1" sx={{ color: activePersona?.name === persona.name ? "primary.contrastText" : "inherit" }}>
                              {persona.name}
                            </Typography>}
                            secondary={
                              <Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                                <Chip label={persona.role} size="small" variant="outlined" />
                                <Chip label={`L${persona.level}`} size="small" color="primary" variant="outlined" />
                                <Chip label={`${persona.tools} tools`} size="small" variant="outlined" />
                              </Stack>
                            }
                          />
                        </ListItem>
                      ))}
                      {personas.length === 0 && (
                        <ListItem disableGutters>
                          <ListItemText primary="No personas found" secondary="Create your first persona to get started" />
                        </ListItem>
                      )}
                    </List>
                  )}
                </Stack></CardContent></Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Typography variant="h6">Active Persona Context</Typography>
                  {activePersona ? (
                    <Box>
                      <Typography variant="subtitle1">{activePersona.name}</Typography>
                      <Typography variant="body2" color="text.secondary">{activePersona.role}</Typography>
                      <Typography variant="body2" color="text.secondary">{activePersona.purpose}</Typography>
                      <Divider />
                      <Stack direction="row" spacing={1} sx={{ flexWrap: "wrap" }}>
                        <Chip label={`Level ${activePersona.level}`} size="small" color="primary" />
                        <Chip label={`${activePersona.tools} tools`} size="small" />
                        <Chip label={`${activePersona.knowledgeDomains} knowledge domains`} size="small" />
                        <Chip label={`${activePersona.skills} skills`} size="small" />
                      </Stack>
                      <Button variant="outlined" onClick={() => { setActivePersona(null); addEvent("PERSONA", "Deactivated persona", "info"); }} startIcon={<ChevronLeftIcon />}>
                        Deactivate
                      </Button>
                    </Box>
                  ) : (
                    <Typography color="text.secondary">No persona activated. Select one from the list.</Typography>
                  )}
                </Stack></CardContent></Card>
              </Grid>
            </Grid>
          )}

          {tabIndex === 2 && (
            // EXP & LEVELS TAB
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                    <Typography variant="h6">Experience Points</Typography>
                    <ExpIcon color="warning" />
                  </Stack>
                  
                  {expLoading ? (
                    <CircularProgress size={24} />
                  ) : expProgress ? (
                    <Box>
                      <Typography variant="h4" sx={{ fontWeight: 700 }}>
                        {expProgress.totalExp.toLocaleString()} XP
                      </Typography>
                      <Typography variant="h6" color="primary">
                        Level: {expProgress.level.name}
                      </Typography>
                      <Typography color="text.secondary" sx={{ mb: 2 }}>
                        {expProgress.level.description}
                      </Typography>
                      
                      <Box sx={{ mb: 2 }}>
                        <Typography variant="body2" sx={{ display: "flex", justifyContent: "space-between" }}>
                          <span>Progress to {expProgress.nextLevel?.name ?? "Max Level"}</span>
                          <span>{(expProgress.progressToNext * 100).toFixed(1)}%</span>
                        </Typography>
                        <LinearProgress 
                          variant="determinate" 
                          value={expProgress.progressToNext * 100} 
                          sx={{ height: 12, borderRadius: 6 }}
                          color="primary"
                        />
                      </Box>
                      
                      <Typography variant="body2">
                        Tasks Verified: <strong>{expProgress.tasksVerified}</strong>
                      </Typography>
                      
                      {expProgress.nextLevel && (
                        <Typography variant="caption" color="text.secondary">
                          {expProgress.nextLevel.minExp - expProgress.totalExp} XP to next level
                        </Typography>
                      )}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">Loading EXP data...</Typography>
                  )}
                </Stack></CardContent></Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Typography variant="h6">Level Progression</Typography>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Level</TableCell>
                          <TableCell align="right">Min XP</TableCell>
                          <TableCell>Description</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {[
                          { name: "Novice", minExp: 0, desc: "Beginning to build verified experience" },
                          { name: "Experienced", minExp: 100, desc: "Consistently produces verified useful work" },
                          { name: "Reliable", minExp: 500, desc: "Dependable across repeated task types" },
                          { name: "Specialized", minExp: 1500, desc: "Deep verified experience in specific domains" },
                          { name: "Advanced", minExp: 5000, desc: "Highly experienced with strong verification history" },
                          { name: "Master", minExp: 15000, desc: "Recognized authority, guides evolution" },
                          { name: "Architect", minExp: 50000, desc: "Shapes system architecture, proposes evolution" },
                        ].map((level, idx) => (
                          <TableRow 
                            key={level.name}
                            sx={{ 
                              fontWeight: expProgress?.level.name === level.name ? 700 : 400,
                              backgroundColor: expProgress?.level.name === level.name ? "primary.light" : "transparent",
                              opacity: (expProgress?.totalExp ?? 0) >= level.minExp ? 1 : 0.5
                            }}
                          >
                            <TableCell>
                              {level.name}
                              {expProgress?.level.name === level.name && <Badge badgeContent="CURRENT" color="primary" size="small" sx={{ ml: 1 }} />}
                            </TableCell>
                            <TableCell align="right">{level.minExp.toLocaleString()}</TableCell>
                            <TableCell>{level.desc}</TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </Stack></CardContent></Card>
              </Grid>
            </Grid>
          )}

          {tabIndex === 3 && (
            // VERSION TAB
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 6 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                    <Typography variant="h6">Version Information</Typography>
                    <VersionIcon />
                  </Stack>
                  
                  {versionLoading ? (
                    <CircularProgress size={24} />
                  ) : version ? (
                    <Box>
                      <Typography variant="h3" sx={{ fontWeight: 700, fontFamily: "monospace" }}>
                        {version.version}
                      </Typography>
                      <Typography variant="h6" color="primary">
                        Codename: {version.codename}
                      </Typography>
                      <Divider />
                      <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
                        <Chip label={`Major: ${version.major}`} size="small" />
                        <Chip label={`Minor: ${version.minor}`} size="small" />
                        <Chip label={`Patch: ${version.patch}`} size="small" />
                        <Chip label={`Tier: ${version.tier}`} size="small" color={version.tier > 0 ? "warning" : "success"} />
                        <Chip label={`Build: ${version.build}`} size="small" />
                      </Stack>
                      <Typography variant="body2" color="text.secondary">
                        Released: {new Date(version.releasedAt).toLocaleString()}
                      </Typography>
                    </Box>
                  ) : (
                    <Typography color="text.secondary">Loading version...</Typography>
                  )}
                </Stack></CardContent></Card>
              </Grid>

              <Grid size={{ xs: 12, md: 6 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Typography variant="h6">Evolution Milestones</Typography>
                  {version?.evolutionMilestones.length ? (
                    <List dense>
                      {version.evolutionMilestones.slice().reverse().map((m, i) => (
                        <ListItem key={i} disableGutters>
                          <ListItemText
                            primary={m.version}
                            secondary={m.milestone}
                          />
                          <Typography variant="caption" color="text.secondary">
                            {m.date ? new Date(m.date).toLocaleString() : "Unknown date"}
                          </Typography>
                        </ListItem>
                      ))}
                    </List>
                  ) : (
                    <Typography color="text.secondary">No milestones recorded</Typography>
                  )}
                </Stack></CardContent></Card>
              </Grid>

              <Grid size={{ xs: 12 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Typography variant="h6">Version Control</Typography>
                  <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
                    <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadVersion}>
                      Refresh
                    </Button>
                    <Button variant="contained" startIcon={<PlayIcon />} 
                      onClick={async () => {
                        const vm = await apiCall("/api/orion/version", {
                          method: "POST", body: JSON.stringify({ action: "bump", type: "build" })
                        });
                        setVersion(vm.version);
                        addEvent("VERSION", `Manual build bump to ${vm.version.version}`, "info");
                      }}>
                      Bump Build
                    </Button>
                    <Button variant="outlined" startIcon={<RefreshIcon />}
                      onClick={async () => {
                        const vm = await apiCall("/api/orion/version", {
                          method: "POST", body: JSON.stringify({ action: "bump", type: "tier2" })
                        });
                        setVersion(vm.version);
                        addEvent("VERSION", `Tier 2 bump to ${vm.version.version}`, "info");
                      }}>
                      Bump Minor (Tier 2)
                    </Button>
                  </Stack>
                </Stack></CardContent></Card>
              </Grid>
            </Grid>
          )}

          {tabIndex === 4 && (
            // TASKS TAB
            <Grid container spacing={3}>
              <Grid size={{ xs: 12 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                    <Typography variant="h6">Task History</Typography>
                    <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadTasks}>
                      Refresh
                    </Button>
                  </Stack>
                  
                  {tasksLoading ? (
                    <CircularProgress size={24} />
                  ) : tasks.length > 0 ? (
                    <TableContainer>
                      <Table size="small">
                        <TableHead>
                          <TableRow>
                            <TableCell>Task ID</TableCell>
                            <TableCell>Status</TableCell>
                            <TableCell>Persona</TableCell>
                            <TableCell>Evaluation</TableCell>
                            <TableCell>EXP</TableCell>
                            <TableCell>Version</TableCell>
                          </TableRow>
                        </TableHead>
                        <TableBody>
                          {tasks.map((task) => (
                            <TableRow key={task.taskId} hover>
                              <TableCell>
                                <Typography variant="body2" fontFamily="monospace">
                                  {task.taskId}
                                </Typography>
                              </TableCell>
                              <TableCell>
                                <Chip 
                                  label={task.status} 
                                  size="small" 
                                  color={task.status === "completed" ? "success" : task.status === "failed" ? "error" : "default"}
                                />
                              </TableCell>
                              <TableCell>{task.persona ?? "—"}</TableCell>
                              <TableCell>
                                {task.evaluation ? (
                                  <Chip 
                                    label={task.evaluation.verdict} 
                                    size="small" 
                                    color={task.evaluation.verdict === "PASS" ? "success" : task.evaluation.verdict === "FAIL" ? "error" : "warning"}
                                  />
                                ) : "—"}
                              </TableCell>
                              <TableCell>
                                {task.expResult ? (
                                  <Typography variant="body2" color={task.expResult.result === "AWARDED" ? "success.main" : "text.secondary"}>
                                    {task.expResult.result}
                                  </Typography>
                                ) : "—"}
                              </TableCell>
                              <TableCell>
                                {task.version ? (
                                  <Typography variant="body2" fontFamily="monospace">
                                    {task.version.version}
                                  </Typography>
                                ) : "—"}
                              </TableCell>
                            </TableRow>
                          ))}
                        </TableBody>
                      </Table>
                    </TableContainer>
                  ) : (
                    <Typography color="text.secondary">No tasks recorded yet. Run a task to see history.</Typography>
                  )}
                </Stack></CardContent></Card>
              </Grid>
            </Grid>
          )}

          {tabIndex === 5 && (
            // MEMORY TAB
            <Grid container spacing={3}>
              <Grid size={{ xs: 12, md: 4 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Stack direction="row" spacing={2} sx={{ alignItems: "center", justifyContent: "space-between" }}>
                    <Typography variant="h6">Memory Browser</Typography>
                    <Button variant="outlined" startIcon={<RefreshIcon />} onClick={loadMemoryFiles}>
                      Refresh
                    </Button>
                  </Stack>
                  
                  <FormControl size="small" sx={{ minWidth: 200 }}>
                    <InputLabel>Store</InputLabel>
                    <Select value={memoryStore} label="Store" onChange={(e) => { setMemoryStore(e.target.value as any); loadMemoryFiles(); }}>
                      <MenuItem value="memory">Memory</MenuItem>
                      <MenuItem value="knowledge">Knowledge</MenuItem>
                      <MenuItem value="experience">Experience</MenuItem>
                    </Select>
                  </FormControl>
                  
                  {memoryLoading ? (
                    <CircularProgress size={24} />
                  ) : (
                    <List dense>
                      {memoryFiles.map((file) => (
                        <ListItem key={file.path} disableGutters button onClick={() => readMemoryFile(file)}>
                          <FolderOpenIcon sx={{ mr: 1 }} />
                          <ListItemText primary={file.path} />
                        </ListItem>
                      ))}
                      {memoryFiles.length === 0 && (
                        <ListItem disableGutters>
                          <ListItemText primary="No files found" secondary="Create files via memory API or task execution" />
                        </ListItem>
                      )}
                    </List>
                  )}
                </Stack></CardContent></Card>
              </Grid>

              <Grid size={{ xs: 12, md: 8 }}>
                <Card><CardContent><Stack spacing={2}>
                  <Typography variant="h6">File Viewer</Typography>
                  {selectedMemoryFile ? (
                    <Box>
                      <Stack direction="row" spacing={1} sx={{ alignItems: "center", mb: 1 }}>
                        <Typography variant="body2" fontFamily="monospace">{selectedMemoryFile.path}</Typography>
                        <Button size="small" variant={editingMemory ? "contained" : "outlined"} onClick={() => setEditingMemory(!editingMemory)}>
                          {editingMemory ? "Cancel" : "Edit"}
                        </Button>
                        {editingMemory && (
                          <Button size="small" variant="contained" startIcon={<VisibilityIcon />} onClick={saveMemoryFile}>
                            Save
                          </Button>
                        )}
                      </Stack>
                      <Divider />
                      {editingMemory ? (
                        <TextField
                          fullWidth
                          multiline
                          rows={25}
                          value={memoryEditorContent}
                          onChange={(e) => setMemoryEditorContent(e.target.value)}
                          placeholder="Edit memory content..."
                        />
                      ) : (
                        <Box 
                          sx={{ 
                            fontFamily: "monospace", 
                            whiteSpace: "pre-wrap", 
                            maxHeight: 500, 
                            overflow: "auto",
                            p: 2,
                            bgcolor: "grey.50",
                            borderRadius: 1,
                            border: "1px solid",
                            borderColor: "divider"
                          }}
                        >
                          {selectedMemoryFile.content || "(empty)"}
                        </Box>
                      )}
                    </Box>
                  ) : (
                    <Typography color="text.secondary">Select a file from the browser to view its contents.</Typography>
                  )}
                </Stack></CardContent></Card>
              </Grid>
            </Grid>
          )}

          {tabIndex === 6 && (
            // EVALUATION TAB
            <Card><CardContent><Stack spacing={2}>
              <Typography variant="h6">Self-Critique / Evaluation System</Typography>
              <Typography color="text.secondary" sx={{ mb: 2 }}>
                The Evaluator is a logical role separate from the Builder. It evaluates results against explicit criteria
                and drives correction loops until PASS or correction budget exhausted.
              </Typography>
              
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Pipeline</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1}>
                    <Typography variant="body2"><strong>BUILDER</strong> executes task steps</Typography>
                    <Typography variant="body2"><strong>VERIFIER</strong> checks concrete outputs (tests, builds, lint)</Typography>
                    <Typography variant="body2"><strong>CRITIQUER</strong> identifies issues and gaps</Typography>
                    <Typography variant="body2"><strong>EVALUATOR</strong> scores against criteria → PASS/FAIL/WARNING</Typography>
                    <Typography variant="body2"><strong>CORRECTION LOOP</strong> Up to 3 cycles for FAIL findings</Typography>
                    <Typography variant="body2"><strong>REPORT</strong> Final result + EXP award + version bump</Typography>
                  </Stack>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Default Criteria (Weighted)</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <TableContainer>
                    <Table size="small">
                      <TableHead>
                        <TableRow>
                          <TableCell>Criterion</TableCell>
                          <TableCell align="right">Weight</TableCell>
                          <TableCell>Threshold</TableCell>
                          <TableCell>Required Evidence</TableCell>
                          <TableCell>Type</TableCell>
                        </TableRow>
                      </TableHead>
                      <TableBody>
                        {[
                          { key: "objective_met", weight: 1.0, threshold: 0.8, evidence: true, type: "objective" },
                          { key: "verification_evidence", weight: 1.0, threshold: 0.8, evidence: true, type: "quality" },
                          { key: "no_critical_issues", weight: 1.5, threshold: 1.0, evidence: true, type: "quality" },
                          { key: "code_quality", weight: 0.8, threshold: 0.7, evidence: false, type: "quality" },
                          { key: "test_coverage", weight: 0.8, threshold: 0.7, evidence: false, type: "quality" },
                          { key: "documentation", weight: 0.5, threshold: 0.5, evidence: false, type: "process" },
                          { key: "security_safety", weight: 1.2, threshold: 1.0, evidence: true, type: "security" },
                          { key: "performance", weight: 0.5, threshold: 0.6, evidence: false, type: "quality" },
                        ].map((c) => (
                          <TableRow key={c.key}>
                            <TableCell>{c.key}</TableCell>
                            <TableCell align="right">{c.weight}</TableCell>
                            <TableCell align="right">{(c.threshold * 100).toFixed(0)}%</TableCell>
                            <TableCell>{c.evidence ? "Yes" : "No"}</TableCell>
                            <TableCell><Chip label={c.type} size="small" variant="outlined" /></TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </TableContainer>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Verdict Logic</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1}>
                    <Typography variant="body2"><strong>PASS:</strong> Weighted score {">="} 0.80, no CRITICAL findings, verification passed</Typography>
                    <Typography variant="body2"><strong>WARNING:</strong> Score 0.60–0.79, no CRITICAL findings</Typography>
                    <Typography variant="body2"><strong>FAIL:</strong> Score {"<"} 0.60, or any CRITICAL finding, or verification failed</Typography>
                    <Typography variant="body2"><strong>Correction:</strong> FAIL triggers correction loop (max 3 cycles)</Typography>
                    <Typography variant="body2"><strong>EXP Eligibility:</strong> Only PASS with score {">="} 0.80 awards EXP</Typography>
                  </Stack>
                </AccordionDetails>
              </Accordion>

              <Divider />
              <Stack direction="row" spacing={2} sx={{ flexWrap: "wrap" }}>
                <Button variant="contained" startIcon={<PlayIcon />} 
                  onClick={async () => {
                    const result = await apiCall("/api/orion/evaluate", {
                      method: "POST",
                      body: JSON.stringify({
                        action: "evaluate",
                        task: { objective: "Test", plan: [], executionLog: [], verificationResults: [], critiqueFindings: [], corrections: [] },
                        verification: { overall: "PASS", checks: { objective_met: true, verification_evidence: true, no_critical_issues: true } },
                        critiqueFindings: [],
                        correctionBudgetRemaining: 3
                      })
                    });
                    addEvent("EVAL", `Test evaluation: ${result.result.verdict} (${(result.result.score * 100).toFixed(0)}%)`, "complete");
                  }}>
                  Run Test Evaluation
                </Button>
              </Stack>
            </Stack></CardContent></Card>
          )}

          {tabIndex === 7 && (
            // SETTINGS TAB
            <Card><CardContent><Stack spacing={3}>
              <Typography variant="h6">ORION Configuration</Typography>
              
              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Environment</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1}>
                    <Typography variant="body2"><strong>Workspace Root:</strong> {process.env.ORION_WORKSPACE_ROOT || process.cwd()}</Typography>
                    <Typography variant="body2"><strong>Node Version:</strong> {process.version}</Typography>
                    <Typography variant="body2"><strong>Platform:</strong> {process.platform}</Typography>
                  </Stack>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">API Endpoints</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1}>
                    <Typography variant="body2" fontFamily="monospace">POST /api/orion/task - Run full pipeline</Typography>
                    <Typography variant="body2" fontFamily="monospace">GET/POST /api/orion/memory - Memory/knowledge operations</Typography>
                    <Typography variant="body2" fontFamily="monospace">GET/POST /api/orion/personas - Persona management</Typography>
                    <Typography variant="body2" fontFamily="monospace">GET/POST /api/orion/exp - EXP system</Typography>
                    <Typography variant="body2" fontFamily="monospace">GET/POST /api/orion/version - Version control</Typography>
                    <Typography variant="body2" fontFamily="monospace">POST /api/orion/evaluate - Run evaluator</Typography>
                    <Typography variant="body2" fontFamily="monospace">GET /api/workspace - Scan workspace</Typography>
                  </Stack>
                </AccordionDetails>
              </Accordion>

              <Accordion>
                <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                  <Typography variant="subtitle1">Data Directories</Typography>
                </AccordionSummary>
                <AccordionDetails>
                  <Stack spacing={1}>
                    <Typography variant="body2" fontFamily="monospace">.agent/orion/memory/ - ORION shared memory</Typography>
                    <Typography variant="body2" fontFamily="monospace">.agent/orion/knowledge/ - ORION shared knowledge</Typography>
                    <Typography variant="body2" fontFamily="monospace">.agent/orion/experience/ - Verified task records</Typography>
                    <Typography variant="body2" fontFamily="monospace">.agent/orion/exp/ - EXP state (JSON)</Typography>
                    <Typography variant="body2" fontFamily="monospace">.agent/orion/evolution/ - Version + proposals</Typography>
                    <Typography variant="body2" fontFamily="monospace">.agent/orion/personas/definitions/ - Persona definitions</Typography>
                    <Typography variant="body2" fontFamily="monospace">.agent/shared/ - Cross-persona commons</Typography>
                  </Stack>
                </AccordionDetails>
              </Accordion>

              <Divider />
              <Typography variant="subtitle2">About ORION</Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                ORION — Orchestrated Reasoning & Intelligence Operating Network
                <br />
                A self-evolving, persona-driven agent runtime with persistent Markdown memory,
                token-efficient retrieval, self-evaluation loops, EXP gamification, and controlled evolution.
              </Typography>
              <Typography variant="caption" color="text.secondary">
                Design doc: ORION_DESIGN.md | Python core: .agent/orion/core.py
              </Typography>
            </Stack></CardContent></Card>
          )}

        </Stack>
      </Box>

      {/* Create Persona Dialog */}
      <Dialog open={showCreatePersona} onClose={() => setShowCreatePersona(false)} TransitionComponent={TransitionSlide} maxWidth="md" fullWidth>
        <DialogTitle>Create New Persona</DialogTitle>
        <DialogContent>
          <Stack spacing={2} sx={{ minWidth: 400 }}>
            <TextField fullWidth label="Name (e.g., researcher)" value={newPersonaForm.name} onChange={(e) => setNewPersonaForm({...newPersonaForm, name: e.target.value})} />
            <TextField fullWidth label="Role" value={newPersonaForm.role} onChange={(e) => setNewPersonaForm({...newPersonaForm, role: e.target.value})} />
            <TextField fullWidth multiline rows={3} label="Purpose" value={newPersonaForm.purpose} onChange={(e) => setNewPersonaForm({...newPersonaForm, purpose: e.target.value})} />
            <TextField fullWidth multiline rows={3} label="Boundaries (one per line)" value={newPersonaForm.boundaries} onChange={(e) => setNewPersonaForm({...newPersonaForm, boundaries: e.target.value})} />
            <TextField fullWidth label="Style" value={newPersonaForm.style} onChange={(e) => setNewPersonaForm({...newPersonaForm, style: e.target.value})} />
            <TextField fullWidth multiline rows={3} label="Tools (one per line)" value={newPersonaForm.tools} onChange={(e) => setNewPersonaForm({...newPersonaForm, tools: e.target.value})} />
            <TextField fullWidth multiline rows={3} label="Knowledge domains (one per line)" value={newPersonaForm.knowledge} onChange={(e) => setNewPersonaForm({...newPersonaForm, knowledge: e.target.value})} />
            <TextField fullWidth multiline rows={3} label="Skills (one per line)" value={newPersonaForm.skills} onChange={(e) => setNewPersonaForm({...newPersonaForm, skills: e.target.value})} />
            <TextField fullWidth multiline rows={3} label="Evaluation criteria (one per line)" value={newPersonaForm.evaluationCriteria} onChange={(e) => setNewPersonaForm({...newPersonaForm, evaluationCriteria: e.target.value})} />
            <TextField fullWidth label="Level" type="number" value={newPersonaForm.level} onChange={(e) => setNewPersonaForm({...newPersonaForm, level: e.target.value})} />
          </Stack>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreatePersona(false)}>Cancel</Button>
          <Button variant="contained" onClick={createPersona}>Create Persona</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}