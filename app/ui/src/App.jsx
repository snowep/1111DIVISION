import { useEffect, useRef, useState } from 'react';
import {
  AppBar,
  Avatar,
  Box,
  Button,
  Chip,
  CircularProgress,
  CssBaseline,
  IconButton,
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

function StatusChip({ health }) {
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
    return (
      <Tooltip title={`${health.model} · ${health.modelCount} NIM models reachable`}>
        <Chip
          icon={<LinkIcon />}
          label={`linked · ${health.model}`}
          size="small"
          color="success"
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
          borderColor: isUser ? 'primary.main' : 'divider',
          whiteSpace: 'pre-wrap',
          wordBreak: 'break-word',
        }}
      >
        <Typography variant="body1" component="div" sx={{ fontSize: '0.95rem', lineHeight: 1.55 }}>
          {message.content || (message.streaming ? '\u200b' : '')}
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

export default function App() {
  const [messages, setMessages] = useState([
    { role: 'assistant', content: 'Link established. What are we working on?' },
  ]);
  const [input, setInput] = useState('');
  const [health, setHealth] = useState(null);
  const [streaming, setStreaming] = useState(false);
  const [error, setError] = useState(null);
  const endRef = useRef(null);

  useEffect(() => {
    (async () => {
      try {
        const res = await fetch('/api/health');
        setHealth(await res.json());
      } catch (e) {
        setHealth({ ok: false, status: 'network-error', message: e.message });
      }
    })();
  }, []);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, streaming]);

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
          const delta = chunk.choices?.[0]?.delta?.content;
          if (typeof delta === 'string' && delta.length > 0) {
            setMessages((prev) => {
              const next = prev.map((m) =>
                m.streaming ? { ...m, content: m.content + delta } : m
              );
              return next;
            });
          }
        }
      }
    } catch (err) {
      setError(err.message);
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
            <StatusChip health={health} />
          </Toolbar>
        </AppBar>

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
                health?.ok ? 'Message JARVIS…' : 'Set your NIM key first — see server/.env'
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
            {'  ·  '}key stays server-side
          </Typography>
        </Paper>
      </Box>
    </ThemeProvider>
  );
}