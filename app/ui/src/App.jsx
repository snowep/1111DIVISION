import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  CssBaseline,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Paper,
  TextField,
  ThemeProvider,
  Toolbar,
  Tooltip,
  Typography,
  createTheme,
} from '@mui/material';
import SendIcon from '@mui/icons-material/Send';
import SmartToyIcon from '@mui/icons-material/SmartToy';
import PersonIcon from '@mui/icons-material/Person';
import LinkOffIcon from '@mui/icons-material/LinkOff';
import LinkIcon from '@mui/icons-material/Link';
import FolderOpenIcon from '@mui/icons-material/FolderOpen';
import FolderIcon from '@mui/icons-material/Folder';
import InsertDriveFileIcon from '@mui/icons-material/InsertDriveFile';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CloseIcon from '@mui/icons-material/Close';
import RefreshIcon from '@mui/icons-material/Refresh';

const theme = createTheme({
  palette: {
    mode: 'dark',
    primary: { main: '#00e5ff' },
    secondary: { main: '#ffb300' },
    background: { default: '#0a0e14', paper: '#11161f' },
    success: { main: '#4caf50' },
    error: { main: '#ff5252' },
  },
  shape: { borderRadius: 12 },
  typography: {
    fontFamily: `'Segoe UI', system-ui, -apple-system, sans-serif`,
  },
});

function StatusChip({ health, fsroot }) {
  if (!health) {
    return (
      <Chip
        icon={<CircularProgress size={14} />}
        label="checking link…"
        size="small"
        variant="outlined"
      />
    );
  }
  if (health.ok) {
    const liveRoute = health.availability || [];
    const primaryOk = liveRoute[0]?.available;
    const fallbackOk = liveRoute.some((a, i) => i > 0 && a.available);
    const fsOk = fsroot?.configured;
    return (
      <Tooltip
        title={`${health.model} · ${health.modelCount} NIM models reachable\nroute: ${(health.route || []).join(' → ')}\nfs: ${fsOk ? fsroot.root : 'not configured'}`}
      >
        <Chip
          icon={<LinkIcon />}
          label={
            fsOk
              ? primaryOk
                ? `linked · ${health.model} · files`
                : fallbackOk
                  ? `linked via fallback · files`
                  : `linked · ${health.model} · files`
              : primaryOk
                ? `linked · ${health.model}`
                : fallbackOk
                  ? `linked via fallback · ${health.model}`
                  : `linked · ${health.model}`
          }
          size="small"
          color={primaryOk && fsOk ? 'success' : primaryOk ? 'success' : 'warning'}
          variant="outlined"
        />
      </Tooltip>
    );
  }
  const label =
    health.status === 'no-key'
      ? 'NIM key missing — see server/.env'
      : health.status === 'nim-rejected'
        ? 'key rejected by NIM'
        : 'link failed';
  return (
    <Tooltip title={health.message || ''}>
      <Chip icon={<LinkOffIcon />} label={label} size="small" color="error" variant="outlined" />
    </Tooltip>
  );
}

function MessageBubble({ message }) {
  const isUser = message.role === 'user';
  return (
    <Box sx={{ display: 'flex', gap: 1.5, alignItems: 'flex-start', my: 1.5 }}>
      <Avatar
        sx={{
          width: 32,
          height: 32,
          bgcolor: isUser ? 'secondary.main' : 'primary.main',
        }}
      >
        {isUser ? <PersonIcon fontSize="small" /> : <SmartToyIcon fontSize="small" />}
      </Avatar>
      <Paper
        elevation={0}
        sx={{
          maxWidth: '78%',
          px: 2,
          py: 1.25,
          bgcolor: isUser ? 'primary.dark' : 'background.paper',
          border: '1px solid',
          borderColor: isUser ? 'secondary.main' : 'divider',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        {message.files && message.files.length > 0 && (
          <Box sx={{ mb: 1 }}>
            {message.files.map((f, i) => (
              <Chip
                key={i}
                icon={<InsertDriveFileIcon fontSize="small" />}
                label={`${f.path}${f.truncated ? ' (truncated)' : ''}`}
                size="small"
                variant="outlined"
                sx={{ mr: 0.5, mb: 0.5 }}
              />
            ))}
          </Box>
        )}
        {message.reasoning && (
          <Typography
            variant="body2"
            color="text.secondary"
            sx={{
              fontStyle: 'italic',
              opacity: 0.75,
              fontSize: '0.85rem',
              lineHeight: 1.45,
              mb: 0.75,
              whiteSpace: 'pre-wrap',
              wordBreak: 'break-word',
              borderLeft: '2px solid',
              borderColor: 'divider',
              pl: 1,
            }}
          >
            {message.reasoning}
          </Typography>
        )}
        <Typography variant="body1" component="div" sx={{ fontSize: '0.95rem', lineHeight: 1.55 }}>
          {message.content || (message.streaming && !message.reasoning ? '\u200b' : '')}
        </Typography>
        {message.streaming && (
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mt: 0.5 }}>
            <CircularProgress size={12} thickness={6} />
            <Typography variant="caption" color="text.secondary">
              thinking…
            </Typography>
          </Box>
        )}
      </Paper>
    </Box>
  );
}

function FileTree({ fsroot, onAttach, attached, currentPath, setCurrentPath, onRefresh }) {
  const [listing, setListing] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState(null);

  useEffect(() => {
    (async () => {
      setLoading(true);
      setErr(null);
      try {
        const res = await fetch(`/api/fs/list?path=${encodeURIComponent(currentPath || '')}`);
        const data = await res.json();
        if (!res.ok || data.error) throw new Error(data.error || `HTTP ${res.status}`);
        setListing(data);
      } catch (e) {
        setErr(e.message);
        setListing(null);
      } finally {
        setLoading(false);
      }
    })();
  }, [currentPath, onRefresh]);

  if (!fsroot?.configured) {
    return (
      <Box p={2}>
        <Typography variant="body2" color="text.secondary">
          Filesystem not configured. Set <code>FS_ROOT</code> in{' '}
          <code>server/.env</code> to enable file access.
        </Typography>
      </Box>
    );
  }

  const isRoot = !currentPath;

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      <Box sx={{ px: 2, py: 1, borderBottom: '1px solid', borderColor: 'divider', display: 'flex', alignItems: 'center', gap: 1 }}>
        <IconButton size="small" onClick={() => setCurrentPath('')} disabled={isRoot || loading} title="Up">
          <ArrowBackIcon fontSize="small" />
        </IconButton>
        <Typography variant="caption" color="text.secondary" sx={{ flexGrow: 1, fontFamily: 'monospace', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {fsroot?.root}
        </Typography>
        <IconButton size="small" onClick={onRefresh} title="Refresh" disabled={loading}>
          <RefreshIcon fontSize="small" />
        </IconButton>
      </Box>
      <Box sx={{ px: 2, py: 0.5, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Typography variant="caption" sx={{ fontFamily: 'monospace', color: 'primary.main' }}>
          /{currentPath}
        </Typography>
      </Box>
      {err && (
        <Typography variant="caption" color="error" sx={{ px: 2, py: 1 }}>
          {err}
        </Typography>
      )}
      <Box sx={{ flexGrow: 1, overflowY: 'auto' }}>
        <List dense disablePadding>
          {loading && (
            <Box sx={{ display: 'flex', justifyContent: 'center', py: 3 }}>
              <CircularProgress size={20} />
            </Box>
          )}
          {!loading &&
            (listing?.entries || []).map((e) => (
              <ListItemButton
                key={e.path}
                dense
                onClick={() => (e.type === 'dir' ? setCurrentPath(e.path) : onAttach(e.path))}
                sx={{ borderRadius: 1, mx: 0.5, mt: 0.25 }}
              >
                <ListItemIcon sx={{ minWidth: 32 }}>
                  {e.type === 'dir' ? (
                    <FolderIcon fontSize="small" color="primary" />
                  ) : (
                    <InsertDriveFileIcon fontSize="small" color="secondary" />
                  )}
                </ListItemIcon>
                <ListItemText
                  primary={e.name}
                  secondary={e.type === 'file' ? (e.size / 1024).toFixed(1) + ' KiB' : ''}
                  primaryTypographyProps={{ fontSize: '0.87rem' }}
                  secondaryTypographyProps={{ fontSize: '0.7rem' }}
                />
                {attached.has(e.path) && e.type === 'file' && (
                  <Chip label="attached" size="small" color="primary" variant="outlined" sx={{ height: 20, fontSize: '0.65rem' }} />
                )}
              </ListItemButton>
            ))}
          {!loading && (listing?.entries || []).length === 0 && (
            <Typography variant="body2" color="text.secondary" sx={{ px: 2, py: 2 }}>
              (empty)
            </Typography>
          )}
        </List>
      </Box>
      {listing?.truncated && (
        <Typography variant="caption" color="text.secondary" sx={{ px: 2, py: 0.5 }}>
          listing truncated (showing first {listing.entries.length})
        </Typography>
      )}
    </Box>
  );
}

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Link established. What are we working on?' },
  ]);
  const [input, setInput] = useState('');
  const [health, setHealth] = useState(null);
  const [fsroot, setFsroot] = useState(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [activeModel, setActiveModel] = useState(null);
  const [drawerOpen, setDrawerOpen] = useState(false);
  const [fsPath, setFsPath] = useState('');
  const [refreshTick, setRefreshTick] = useState(0);
  const endRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/health');
        setHealth(await res.json());
      } catch (e) {
        setHealth({ ok: false, status: 'network-error', message: e.message });
      }
      try {
        const res = await fetch('/api/fs/root');
        setFsroot(await res.json());
      } catch {
        setFsroot({ configured: false });
      }
    })();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

  const attached = useMemo(() => {
    const s = new Set();
    for (const m of messages) {
      for (const f of m.files || []) s.add(f.path);
    }
    return s;
  }, [messages]);

  function attachFile(path) {
    setInput((prev) => (prev.trim() ? prev + `\n@file(${path})` : `@file(${path})`));
    setDrawerOpen(false);
  }

  async function send() {
    const text = input.trim();
    if (!text || streaming) return;

    const userMsg = { role: 'user', content: text };
    const history = [...messages.filter((m) => m.content), userMsg];
    setMessages([...history, { role: 'assistant', content: '', streaming: true }]);
    setInput('');
    setError(null);
    setStreaming(true);

    try {
      const res = await fetch('/api/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages: history }),
      });

      if (!res.ok) {
        const body = await res.json().catch(() => ({}));
        throw new Error(body.error || `HTTP ${res.status}`);
      }

      const reader = res.body.getReader();
      const decoder = new TextDecoder();
      let buffer = '';
      let pendingFiles = [];

      for (;;) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });

        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          const trimmed = line.trim();
          if (!trimmed.startsWith('data:')) continue;
          const payload = trimmed.slice(5).trim();
          if (payload === '[DONE]') continue;

          let chunk;
          try {
            chunk = JSON.parse(payload);
          } catch {
            continue;
          }
          if (chunk.type === 'meta') {
            setActiveModel(chunk.model);
            continue;
          }
          if (chunk.type === 'files') {
            pendingFiles = chunk.files || [];
            // Mark the user's message with the attached-files chips.
            setMessages((prev) =>
              prev.map((m, i) =>
                i === prev.length - 2 && m.role === 'user' ? { ...m, files: pendingFiles } : m
              )
            );
            continue;
          }
          const delta = chunk.choices?.[0]?.delta || {};
          const text = delta.content;
          const reasoning = delta.reasoning || delta.reasoning_content;
          if (typeof text === 'string' && text.length > 0) {
            setMessages((prev) => {
              const next = prev.map((m) =>
                m.streaming ? { ...m, content: m.content + text } : m
              );
              return next;
            });
          }
          if (typeof reasoning === 'string' && reasoning.length > 0) {
            setMessages((prev) => {
              const next = prev.map((m) =>
                m.streaming ? { ...m, reasoning: (m.reasoning || '') + reasoning } : m
              );
              return next;
            });
          }
        }
      }
    } catch (err) {
      if (err.message) setError(err.message);
      else setError('Request failed');
      setMessages((prev) => {
        const next = prev.map((m) =>
          m.streaming && !m.content
            ? { ...m, content: `⚠ ${err.message}`, streaming: false }
            : m.streaming
              ? { ...m, streaming: false }
              : m
        );
        return next;
      });
    } finally {
      setStreaming(false);
      setMessages((prev) => prev.map((m) => (m.streaming ? { ...m, streaming: false } : m)));
    }
  }

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Box sx={{ height: '100vh', display: 'flex', flexDirection: 'column', bgcolor: 'background.default' }}>
        <AppBar position="static" elevation={1} sx={{ bgcolor: 'background.paper' }}>
          <Toolbar sx={{ gap: 1 }}>
            <Avatar sx={{ width: 32, height: 32, bgcolor: 'primary.main' }}>
              <SmartToyIcon fontSize="small" />
            </Avatar>
            <Typography variant="h6" component="div" sx={{ flexGrow: 1, letterSpacing: 1 }}>
              JARVIS&nbsp;{'//'}&nbsp;NIM&nbsp;BRIDGE
            </Typography>
            <Tooltip title={fsroot?.configured ? 'Workspace' : 'Filesystem not configured'}>
              <span>
                <IconButton
                  color={fsroot?.configured ? 'primary' : 'default'}
                  onClick={() => setDrawerOpen(true)}
                  disabled={!fsroot?.configured}
                  aria-label="open workspace"
                >
                  <FolderOpenIcon />
                </IconButton>
              </span>
            </Tooltip>
            <StatusChip health={health} fsroot={fsroot} />
          </Toolbar>
        </AppBar>

        <Drawer
          anchor="right"
          open={drawerOpen}
          onClose={() => setDrawerOpen(false)}
          PaperProps={{ sx: { width: 360, bgcolor: 'background.paper', borderLeft: '1px solid', borderColor: 'divider' } }}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', px: 2, py: 1, borderBottom: '1px solid', borderColor: 'divider' }}>
            <Typography variant="subtitle2" sx={{ flexGrow: 1 }}>
              Workspace
            </Typography>
            <IconButton size="small" onClick={() => setDrawerOpen(false)}>
              <CloseIcon fontSize="small" />
            </IconButton>
          </Box>
          <FileTree
            fsroot={fsroot}
            onAttach={attachFile}
            attached={attached}
            currentPath={fsPath}
            setCurrentPath={setFsPath}
            onRefresh={refreshTick}
          />
        </Drawer>

        <Box sx={{ flexGrow: 1, overflowY: 'auto', px: { xs: 2, md: 6 }, py: 2 }}>
          {messages.map((m, i) => (
            <MessageBubble key={i} message={m} />
          ))}
          {error && (
            <Typography variant="body2" color="error" sx={{ px: 1, py: 0.5 }}>
              {error}
            </Typography>
          )}
          <div ref={endRef} />
        </Box>

        <Paper
          elevation={0}
          sx={{
            p: 2,
            bgcolor: 'background.paper',
            borderTop: '1px solid',
            borderColor: 'divider',
          }}
        >
          <Box sx={{ display: 'flex', gap: 1, alignItems: 'flex-end' }}>
            <TextField
              fullWidth
              multiline
              maxRows={4}
              placeholder={
                health?.ok ? 'Message JARVIS…  (@file(path) attaches a file)' : 'Set your NIM key first — see server/.env'
              }
              value={input}
              disabled={streaming || !health?.ok}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  send();
                }
              }}
              size="small"
            />
            <Button
              variant="contained"
              color="primary"
              onClick={send}
              disabled={streaming || !input.trim() || !health?.ok}
              sx={{ height: 40, minWidth: 44, px: 2 }}
            >
              {streaming ? <CircularProgress size={18} color="inherit" /> : <SendIcon fontSize="small" />}
            </Button>
          </Box>
          <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mt: 1 }}>
            NVIDIA NIM · {health?.ok ? health.model : 'not linked'}
            {activeModel && activeModel !== health?.model
              ? `  ·  serving via ${activeModel}`
              : ''}
            {fsroot?.configured ? '  ·  workspace: on' : '  ·  workspace: off'}
            {'  ·  '}key stays server-side
          </Typography>
        </Paper>
      </Box>
    </ThemeProvider>
  );
}