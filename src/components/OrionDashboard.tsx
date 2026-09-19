"use client";

import { useEffect, useMemo, useState } from "react";
import {
  AppBar, Box, Card, CardContent, Chip, Divider, Grid, List, ListItem,
  ListItemText, Stack, Toolbar, Typography
} from "@mui/material";
import MemoryIcon from "@mui/icons-material/Memory";
import HubIcon from "@mui/icons-material/Hub";
import StorageIcon from "@mui/icons-material/Storage";
import PsychologyIcon from "@mui/icons-material/Psychology";
import FolderOpenIcon from "@mui/icons-material/FolderOpen";
import type { OrionEvent, WorkspaceSnapshot } from "@/lib/types";
import { createTransitionEvents } from "@/lib/orion-events";

const initialEvents: OrionEvent[] = [{
  id: "boot",
  time: "--:--:--",
  stage: "SYSTEM",
  message: "ORION TypeScript transition runtime initialized",
  status: "complete"
}];

export default function OrionDashboard() {
  const [workspace, setWorkspace] = useState<WorkspaceSnapshot | null>(null);
  const [events, setEvents] = useState<OrionEvent[]>(initialEvents);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
    setEvents((current) => current.map((e) =>
      e.id === "boot" ? { ...e, time: new Date().toLocaleTimeString() } : e
    ));
  }, []);

  const task = "Inspect the local workspace and explain what ORION can currently see.";

  useEffect(() => {
    fetch("/api/workspace")
      .then((response) => response.json())
      .then(setWorkspace)
      .catch((error) => setEvents((current) => [...current, {
        id: crypto.randomUUID(),
        time: new Date().toLocaleTimeString(),
        stage: "WORKSPACE",
        message: String(error),
        status: "error"
      }]));
  }, []);

  const visibleFiles = useMemo(() => workspace?.files.slice(0, 12) ?? [], [workspace]);

  return (
    <Box>
      <AppBar position="static">
        <Toolbar>
          <MemoryIcon sx={{ mr: 2 }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>ORION</Typography>
          <Chip label="TRANSITION" color="secondary" />
        </Toolbar>
      </AppBar>

      <Box component="main" sx={{ p: 3 }}>
        <Stack spacing={3}>
          <Box>
            <Typography variant="h4" gutterBottom>
              Orchestrated Reasoning & Intelligence Operating Network
            </Typography>
            <Typography color="text.secondary">
              TypeScript runtime + local Markdown workspace + Material UI interface.
            </Typography>
          </Box>

          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 4 }}>
              <Card><CardContent><Stack spacing={2}>
                <HubIcon />
                <Typography variant="h6">ORION Runtime</Typography>
                <Chip label="ONLINE" color="success" />
                <Typography color="text.secondary">
                  The runtime reads the same local filesystem that contains the existing architecture.
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
                  <Chip label={`${workspace?.markdown.length ?? 0} MD`} />
                  <Chip label={`${workspace?.agentFiles.length ?? 0} agent files`} />
                </Stack>
              </Stack></CardContent></Card>
            </Grid>
          </Grid>

          <Grid container spacing={3}>
            <Grid size={{ xs: 12, md: 7 }}>
              <Card><CardContent><Stack spacing={2}>
                <Typography variant="h6">Live ORION Event Stream</Typography>
                <Typography color="text.secondary">
                  Operational telemetry only — not private model chain-of-thought.
                </Typography>
                <Divider />
                <List>
                  {events.slice().reverse().map((event) => (
                    <ListItem key={event.id} disableGutters>
                      <ListItemText
                        primary={<Stack direction="row" spacing={1} sx={{ alignItems: "center" }}>
                          <Chip size="small" label={event.stage} />
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
          </Grid>

          <Card><CardContent><Stack spacing={2}>
            <Typography variant="h6">Transition Test</Typography>
            <Typography color="text.secondary">
              local files → workspace scanner → ORION event stream → UI
            </Typography>
            <Typography>{task}</Typography>
            <Chip
              label="Run transition trace"
              color="primary"
              clickable
              onClick={() => setEvents((current) => [...current, ...createTransitionEvents(task)])}
            />
          </Stack></CardContent></Card>
        </Stack>
      </Box>
    </Box>
  );
}
