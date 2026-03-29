import React, { useState, useEffect } from 'react';
import axios from 'axios';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';

// --- MUI IMPORTS ---
import { 
  ThemeProvider, createTheme, CssBaseline, GlobalStyles, Box, AppBar, Toolbar, Typography, Tabs, Tab, 
  Paper, Switch, Slider, Button, Table, TableBody, TableCell, TableContainer, 
  TableHead, TableRow, MenuItem, Select, FormControl, InputLabel, Divider, TextField, IconButton
} from '@mui/material';

// --- MUI ICONS ---
import VideocamOffIcon from '@mui/icons-material/VideocamOff';
import WarningIcon from '@mui/icons-material/Warning';
import RestartAltIcon from '@mui/icons-material/RestartAlt';
import DownloadIcon from '@mui/icons-material/Download';
import CloudSyncIcon from '@mui/icons-material/CloudSync';
import AssessmentIcon from '@mui/icons-material/Assessment';
import LogoutIcon from '@mui/icons-material/Logout';
import LockOutlinedIcon from '@mui/icons-material/LockOutlined';
import PersonIcon from '@mui/icons-material/Person';
import DarkModeIcon from '@mui/icons-material/DarkMode';

// ============================================================================
// 🎨 CAPGEMINI MUI DESIGN SYSTEM
// ============================================================================
const capgeminiTheme = createTheme({
  palette: {
    primary: { main: '#002b5c' },      
    secondary: { main: '#00a0d1' },    
    background: { default: '#eef2f6', paper: '#ffffff' }, 
    error: { main: '#d13239' },
  },
  typography: {
    fontFamily: '"Arial", "Roboto", "Helvetica", sans-serif',
    h6: { fontWeight: 800, letterSpacing: '0.5px' },
    subtitle1: { fontWeight: 800, fontSize: '0.8rem', textTransform: 'uppercase', letterSpacing: '0.5px' },
    body2: { fontSize: '0.8rem' }
  },
  components: {
    MuiPaper: {
      styleOverrides: {
        root: { borderRadius: 8, boxShadow: '0px 4px 20px rgba(0,0,0,0.04)', border: '1px solid #e2e8f0', display: 'flex', flexDirection: 'column' }
      }
    },
    MuiButton: {
      styleOverrides: {
        root: { textTransform: 'none', fontWeight: 700, borderRadius: 6, padding: '8px 16px', boxShadow: 'none' }
      }
    },
    MuiTableCell: {
      styleOverrides: {
        head: { fontWeight: 800, backgroundColor: '#f8fafc', borderBottom: '2px solid #e2e8f0', color: '#475569', fontSize: '0.7rem', textTransform: 'uppercase', letterSpacing: '0.5px' },
        root: { padding: '10px 16px', borderBottom: '1px solid #f1f5f9', fontSize: '0.8rem' }
      }
    },
    MuiTab: {
      styleOverrides: {
        root: { fontWeight: 700, color: '#a0b2c6', '&.Mui-selected': { color: '#ffffff' }, minHeight: '48px' }
      }
    }
  }
});

// ============================================================================
// 🔐 LOGIN INTERFACE
// ============================================================================
const LoginScreen = ({ onLogin }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');

  const handleLogin = (e) => {
    e.preventDefault();
    if (username && password) onLogin();
  };

  return (
    <Box sx={{ height: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center', bgcolor: '#002b5c', backgroundImage: 'linear-gradient(135deg, #002b5c 0%, #001229 100%)' }}>
      <Paper elevation={24} sx={{ p: 5, width: '100%', maxWidth: 420, borderRadius: 4, textAlign: 'center', border: 'none' }}>
        <img src="/capgemini-logo.png" alt="Capgemini Logo" style={{ height: '56px', marginBottom: '24px', objectFit: 'contain' }} />
        <Typography variant="h6" sx={{ color: '#002b5c', mb: 1 }}>SMART CITY ADAS PLATFORM</Typography>
        <Typography variant="body2" sx={{ color: '#64748b', mb: 4 }}>Please sign in to access the control panel.</Typography>

        <form onSubmit={handleLogin} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          <TextField fullWidth label="Username" variant="outlined" size="small" value={username} onChange={(e) => setUsername(e.target.value)} InputProps={{ startAdornment: <PersonIcon sx={{ color: '#94a3b8', mr: 1 }} /> }} />
          <TextField fullWidth label="Password" type="password" variant="outlined" size="small" value={password} onChange={(e) => setPassword(e.target.value)} InputProps={{ startAdornment: <LockOutlinedIcon sx={{ color: '#94a3b8', mr: 1 }} /> }} />
          <Button type="submit" variant="contained" color="secondary" size="large" fullWidth sx={{ mt: 2, py: 1.5, fontSize: '1rem' }}>SIGN IN</Button>
        </form>
      </Paper>
    </Box>
  );
};

// ============================================================================
// 1. LEFT COLUMN: Configurator
// ============================================================================
const Configurator = ({ isSimMode, toggleSimMode, configState, setConfigState }) => {
  const forceGreen = async () => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "FORCE_GREEN", node_id: "NODE_A" });
      alert("EMERGENCY SIGNAL BROADCASTED: Node A Forced to GREEN for 15s.");
    } catch (e) { alert("Connection Error: Backend Command API Offline."); }
  };

  const restartVideo = async () => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "RESTART_VIDEO", node_id: "NODE_A" });
    } catch (e) { alert("Connection Error."); }
  };

  return (
    <Paper sx={{ p: 3, height: '100%', gap: 3 }}>
      <Typography variant="subtitle1" color="primary" sx={{ borderBottom: '2px solid #002b5c', pb: 1.5 }}>
        Configurator
      </Typography>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5, bgcolor: '#f8fafc', p: 2, borderRadius: 1.5, border: '1px solid #e2e8f0' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Typography variant="body2" fontWeight="bold" color="#334155">Simulation Mode</Typography>
          <Switch checked={isSimMode} onChange={toggleSimMode} color="secondary" />
        </Box>
        <Divider />
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DarkModeIcon sx={{ fontSize: 16, color: '#64748b' }} />
            <Typography variant="body2" fontWeight="bold" color="#334155">Night Mode</Typography>
          </Box>
          <Switch checked={configState.nightMode} onChange={(e) => setConfigState({...configState, nightMode: e.target.checked})} color="primary" />
        </Box>
      </Box>

      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
        <Button variant="contained" color="error" startIcon={<WarningIcon />} onClick={forceGreen} fullWidth sx={{ py: 1.5 }}>FORCE EMERGENCY GREEN</Button>
        <Button variant="outlined" color="primary" startIcon={<RestartAltIcon />} onClick={restartVideo} fullWidth sx={{ py: 1.5 }}>RESTART SIMULATION</Button>
      </Box>

      <Box sx={{ flex: 1, mt: 1, px: 1, overflowY: 'auto' }}>
        <Typography variant="caption" color="textSecondary" fontWeight="bold">POLLING RATE (MS)</Typography>
        <Slider value={configState.refreshRate} min={100} max={5000} step={100} onChange={(e, val) => setConfigState({...configState, refreshRate: val})} color="secondary" valueLabelDisplay="auto" />
        
        <Box sx={{ mt: 1.5 }}>
          <Typography variant="caption" color="textSecondary" fontWeight="bold">BRIGHTNESS</Typography>
          <Slider value={configState.brightness} min={50} max={200} onChange={(e, val) => setConfigState({...configState, brightness: val})} color="secondary" />
        </Box>

        <Box sx={{ mt: 1.5 }}>
          <Typography variant="caption" color="textSecondary" fontWeight="bold">CONTRAST</Typography>
          <Slider value={configState.contrast} min={50} max={200} onChange={(e, val) => setConfigState({...configState, contrast: val})} color="secondary" />
        </Box>

        <Box sx={{ mt: 1.5 }}>
          <Typography variant="caption" color="textSecondary" fontWeight="bold">SATURATION</Typography>
          <Slider value={configState.saturation} min={0} max={300} onChange={(e, val) => setConfigState({...configState, saturation: val})} color="secondary" />
        </Box>
      </Box>
    </Paper>
  );
};

// ============================================================================
// 2. MIDDLE COLUMN: Video & Table
// ============================================================================
const CameraView = ({ isSimMode, configState, activeNode, setActiveNode }) => {
  const videoFilters = `
    brightness(${configState.brightness}%) 
    contrast(${configState.contrast}%) 
    saturate(${configState.saturation}%)
    ${configState.nightMode ? 'invert(1) hue-rotate(180deg) grayscale(20%)' : ''}
  `;

  return (
    <Paper sx={{ flexShrink: 0, height: 420, backgroundColor: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden', borderRadius: 2, border: 'none' }}>
      
      {/* 🟢 NEW CAMERA SWITCHER BUTTONS */}
      <Box sx={{ position: 'absolute', top: 12, left: 12, zIndex: 10, display: 'flex', gap: 1 }}>
        {['NODE_A', 'NODE_B', 'NODE_C'].map((node) => (
          <Button 
            key={node}
            size="small"
            onClick={() => setActiveNode(node)}
            sx={{ 
              bgcolor: activeNode === node ? '#00e676' : 'rgba(0,0,0,0.6)', 
              color: activeNode === node ? '#000000' : '#ffffff', 
              fontWeight: 900,
              fontSize: '0.7rem',
              letterSpacing: 1,
              '&:hover': { bgcolor: activeNode === node ? '#00c853' : 'rgba(0,0,0,0.8)' }
            }}
          >
            {activeNode === node ? 'LIVE: ' : ''} {node}
          </Button>
        ))}
      </Box>
      
      {isSimMode ? (
        <img 
          src={`http://localhost:8000/api/video_feed/${activeNode}`} 
          alt="Live Stream" 
          style={{ width: '100%', height: '100%', objectFit: 'contain', filter: videoFilters, transition: 'filter 0.3s ease' }} 
        />
      ) : (
        <Box sx={{ textAlign: 'center', color: '#64748b' }}>
          <VideocamOffIcon sx={{ fontSize: 64, color: '#d13239', mb: 2, opacity: 0.8 }} />
          <Typography variant="button" display="block" sx={{ letterSpacing: 2 }}>Hardware Offline</Typography>
        </Box>
      )}
    </Paper>
  );
};

const ScanLogsTable = ({ refreshRate }) => {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/violations?limit=5');
        setLogs(response.data);
      } catch (error) { console.error(error); }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, refreshRate); 
    return () => clearInterval(interval);
  }, [refreshRate]);

  return (
    <Paper sx={{ width: '100%', overflow: 'hidden', flex: 1, display: 'flex', flexDirection: 'column' }}>
      <Typography variant="subtitle1" color="primary" sx={{ p: 2, borderBottom: '1px solid #e2e8f0', bgcolor: '#f8fafc' }}>
        ALPR Scan Logs
      </Typography>
      <TableContainer sx={{ flex: 1, overflowY: 'auto' }}>
        <Table stickyHeader size="small">
          <TableHead>
            <TableRow>
              <TableCell>Time of Issue</TableCell>
              <TableCell>Vehicle / Plate</TableCell>
              <TableCell>Status</TableCell>
              <TableCell align="right">Fine</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {logs.map((log, idx) => (
              <TableRow key={idx} hover>
                <TableCell sx={{ color: '#475569' }}>{log.timestamp}</TableCell>
                <TableCell sx={{ fontFamily: 'monospace', fontWeight: 'bold', color: '#0f172a' }}>{log.plate_number || log.vehicle_id}</TableCell>
                <TableCell>
                   <span style={{ padding: '4px 8px', borderRadius: '4px', fontSize: '0.65rem', fontWeight: 'bold', backgroundColor: log.violation_type === 'RED_LIGHT' ? '#fee2e2' : '#ffedd5', color: log.violation_type === 'RED_LIGHT' ? '#dc2626' : '#ea580c' }}>
                      {log.violation_type.replace('_', ' ')}
                   </span>
                </TableCell>
                <TableCell align="right" sx={{ fontWeight: 'bold', color: '#00a0d1' }}>{log.fine_amount} TND</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>
    </Paper>
  );
};

// ============================================================================
// 3. RIGHT COLUMN: Env Data, Export & Analytics
// ============================================================================
const RightColumnPanel = ({ refreshRate }) => {
  const [timeframe, setTimeframe] = useState('all');
  const [weatherData, setWeatherData] = useState("Fetching API...");
  const [totalViolations, setTotalViolations] = useState(0);

  useEffect(() => {
    axios.get("https://api.open-meteo.com/v1/forecast?latitude=36.4561&longitude=10.7376&current_weather=true")
      .then(res => setWeatherData(`${res.data.current_weather.temperature}°C | Wind: ${res.data.current_weather.windspeed} km/h`))
      .catch(() => setWeatherData("API Offline"));
  }, []);

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/stats');
        setTotalViolations(res.data.total_violations);
      } catch (e) { }
    };
    fetchStats();
    const interval = setInterval(fetchStats, refreshRate);
    return () => clearInterval(interval);
  }, [refreshRate]);

  const handleExport = async (format) => {
    try {
      const response = await axios.get(`http://localhost:8000/api/violations?limit=999999&timeframe=${timeframe}`);
      const allLogs = response.data;

      if (format === 'pdf') {
        const doc = new jsPDF();
        doc.setFontSize(16);
        doc.text(`Capgemini Smart City - ${timeframe.toUpperCase()} Report`, 14, 15);
        doc.setFontSize(11);
        doc.setTextColor(0, 112, 173); 
        doc.text(`Total Violations Reached: ${allLogs.length}`, 14, 23);
        
        const tableData = allLogs.map(log => [log.id || log.vehicle_id, log.plate_number, log.timestamp, "View Evidence"]);
        autoTable(doc, {
          head: [['ID (Inc)', 'Car Number', 'Time', 'Image Link']],
          body: tableData,
          startY: 28, 
          styles: { fontSize: 8, cellPadding: 2 },
          headStyles: { fillColor: [0, 112, 173] },
          columnStyles: { 3: { textColor: [0, 112, 173], fontStyle: 'bold' } },
          didDrawCell: (data) => {
            if (data.column.index === 3 && data.cell.section === 'body' && allLogs[data.row.index].image_path) {
              doc.link(data.cell.x, data.cell.y, data.cell.width, data.cell.height, { url: allLogs[data.row.index].image_path });
            }
          }
        });
        doc.save(`Capgemini_${timeframe}_Report.pdf`);
      } 
      else if (format === 'excel') {
        const excelData = allLogs.map(log => ({
          "ID (Inc)": log.id || log.vehicle_id, "Car Number": log.plate_number, "Time": log.timestamp, "Image Link": log.image_path
        }));
        const worksheet = XLSX.utils.json_to_sheet(excelData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, `${timeframe}_violations`);
        XLSX.writeFile(workbook, `Capgemini_${timeframe}_Report.xlsx`);
      }
    } catch (error) { alert("Export failed: " + error.message); }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%', gap: 3 }}>
      <Paper sx={{ p: 4, textAlign: 'center', bgcolor: '#ffffff', borderTop: '4px solid #00a0d1' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <AssessmentIcon color="secondary" />
          <Typography variant="subtitle1" color="primary">Analytics</Typography>
        </Box>
        <Typography variant="h2" sx={{ fontWeight: 900, color: '#002b5c', my: 1 }}>{totalViolations}</Typography>
        <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700, letterSpacing: 1.5 }}>TOTAL VIOLATIONS</Typography>
      </Paper>

      <Paper sx={{ p: 3, flex: 1, display: 'flex', flexDirection: 'column', gap: 3 }}>
        <Box>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #002b5c', pb: 1.5, mb: 2 }}>
            <Typography variant="subtitle1" color="primary">Environment</Typography>
            <CloudSyncIcon color="secondary" />
          </Box>
          <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0' }}>
            <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700 }}>WEATHER (NABEUL)</Typography>
            <Typography variant="body2" sx={{ fontWeight: 800, color: '#0f172a', mt: 0.5 }}>{weatherData}</Typography>
          </Box>
        </Box>

        <Divider />
        
        <Box>
          <Typography variant="subtitle1" color="primary" sx={{ mb: 2 }}>Export Data</Typography>
          <FormControl fullWidth size="small" sx={{ mb: 2 }}>
            <InputLabel>Timeframe Filter</InputLabel>
            <Select value={timeframe} label="Timeframe Filter" onChange={(e) => setTimeframe(e.target.value)}>
              <MenuItem value="all">All-Time History</MenuItem>
              <MenuItem value="daily">Daily Summary</MenuItem>
              <MenuItem value="weekly">Weekly Overview</MenuItem>
              <MenuItem value="monthly">Monthly Audit</MenuItem>
            </Select>
          </FormControl>

          <Box sx={{ display: 'flex', gap: 1.5 }}>
            <Button variant="contained" color="error" fullWidth startIcon={<DownloadIcon />} onClick={() => handleExport('pdf')}>PDF</Button>
            <Button variant="contained" color="success" fullWidth startIcon={<DownloadIcon />} sx={{ bgcolor: '#16a34a', '&:hover': { bgcolor: '#15803d' } }} onClick={() => handleExport('excel')}>EXCEL</Button>
          </Box>
        </Box>
      </Paper>
    </Box>
  );
};
// ============================================================================
// 🧱 MOCKED TABS FOR JURY PRESENTATION (UI ONLY)
// ============================================================================

const EdgeNodesTab = () => (
  <Paper sx={{ p: 3, height: '100%', border: '1px solid #e2e8f0' }}>
    <Typography variant="h6" color="primary" sx={{ mb: 2, borderBottom: '2px solid #002b5c', pb: 1 }}>
      Network Topology & Edge Hardware
    </Typography>
    <TableContainer>
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>Node ID</TableCell>
            <TableCell>Location</TableCell>
            <TableCell>IP Address</TableCell>
            <TableCell>Status</TableCell>
            <TableCell>Last Ping</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          <TableRow hover>
            <TableCell sx={{ fontWeight: 'bold' }}>NODE_A_NABEUL</TableCell>
            <TableCell>Nabeul Center, Route 1</TableCell>
            <TableCell sx={{ fontFamily: 'monospace' }}>192.168.1.105</TableCell>
            <TableCell><span style={{ backgroundColor: '#dcfce7', color: '#16a34a', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold' }}>ONLINE</span></TableCell>
            <TableCell>2ms ago</TableCell>
          </TableRow>
          <TableRow hover>
            <TableCell sx={{ fontWeight: 'bold' }}>NODE_B_TUNIS</TableCell>
            <TableCell>Tunis, Avenue Habib Bourguiba</TableCell>
            <TableCell sx={{ fontFamily: 'monospace' }}>192.168.1.106</TableCell>
            <TableCell><span style={{ backgroundColor: '#fee2e2', color: '#dc2626', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold' }}>OFFLINE</span></TableCell>
            <TableCell>4 hrs ago</TableCell>
          </TableRow>
          <TableRow hover>
            <TableCell sx={{ fontWeight: 'bold' }}>NODE_C_SOUSSE</TableCell>
            <TableCell>Sousse, Corniche</TableCell>
            <TableCell sx={{ fontFamily: 'monospace' }}>192.168.1.107</TableCell>
            <TableCell><span style={{ backgroundColor: '#fef3c7', color: '#d97706', padding: '4px 8px', borderRadius: '4px', fontSize: '0.7rem', fontWeight: 'bold' }}>MAINTENANCE</span></TableCell>
            <TableCell>1 day ago</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </TableContainer>
  </Paper>
);

const ReportsTab = () => (
  <Paper sx={{ p: 3, height: '100%', border: '1px solid #e2e8f0' }}>
    <Typography variant="h6" color="primary" sx={{ mb: 2, borderBottom: '2px solid #002b5c', pb: 1 }}>
      Generated Compliance Audits
    </Typography>
    <Box sx={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 3 }}>
      {[1, 2, 3, 4, 5].map((item) => (
        <Paper key={item} sx={{ p: 2, border: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', gap: 2, bgcolor: '#f8fafc', cursor: 'pointer', '&:hover': { borderColor: '#00a0d1' } }}>
          <Box sx={{ bgcolor: '#fee2e2', color: '#dc2626', p: 1.5, borderRadius: 1, fontWeight: 'bold' }}>PDF</Box>
          <Box>
            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', color: '#002b5c' }}>Nabeul_Weekly_Audit_0{item}.pdf</Typography>
            <Typography variant="caption" sx={{ color: '#64748b' }}>Generated: March {10 + item}, 2026</Typography>
          </Box>
        </Paper>
      ))}
    </Box>
  </Paper>
);

const SettingsTab = () => (
  <Paper sx={{ p: 3, height: '100%', border: '1px solid #e2e8f0' }}>
    <Typography variant="h6" color="primary" sx={{ mb: 3, borderBottom: '2px solid #002b5c', pb: 1 }}>
      System Configuration
    </Typography>
    <Box sx={{ maxWidth: 600, display: 'flex', flexDirection: 'column', gap: 3 }}>
      <TextField disabled label="HiveMQ Broker URL" defaultValue="mqtt://broker.hivemq.com:1883" fullWidth size="small" />
      <TextField disabled label="Cloudinary Cloud Name" defaultValue="dh5f789pm" fullWidth size="small" />
      <TextField disabled label="SMTP Alert Email" defaultValue="hotline-dev@capgemini.com" fullWidth size="small" />
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', p: 2, border: '1px solid #e2e8f0', borderRadius: 1 }}>
        <Typography variant="body2" sx={{ fontWeight: 'bold', color: '#334155' }}>Enable Auto-Purge Database (30 Days)</Typography>
        <Switch disabled defaultChecked color="primary" />
      </Box>
      <Button disabled variant="contained" sx={{ alignSelf: 'flex-start', mt: 2 }}>SAVE CONFIGURATION</Button>
    </Box>
  </Paper>
);
// ============================================================================
// MASTER LAYOUT
// ============================================================================
export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isSimulationMode, setIsSimulationMode] = useState(false);
  const [currentTab, setCurrentTab] = useState(0);
  
  const [config, setConfig] = useState({ 
    refreshRate: 500, 
    brightness: 100, 
    contrast: 100, 
    saturation: 100, 
    nightMode: false 
  });
  const [activeNode, setActiveNode] = useState('NODE_A');
  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={capgeminiTheme}>
        <CssBaseline />
        <GlobalStyles styles={{ 
          '*, *::before, *::after': { boxSizing: 'border-box' },
          '#root': { width: '100vw', height: '100vh', margin: 0, padding: 0, maxWidth: 'none', overflow: 'hidden' }, 
          body: { margin: 0, padding: 0, overflow: 'hidden' } 
        }} />
        <LoginScreen onLogin={() => setIsAuthenticated(true)} />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={capgeminiTheme}>
      <CssBaseline />
      
      {/* 🚀 CSS NUKE: FORCES STRICT FULL-WIDTH BORDER-BOX SIZING 🚀 */}
      <GlobalStyles styles={{ 
        '*, *::before, *::after': { boxSizing: 'border-box' },
        '#root': { width: '100vw', height: '100vh', margin: 0, padding: 0, maxWidth: 'none', overflow: 'hidden' }, 
        body: { margin: 0, padding: 0, overflow: 'hidden', width: '100vw', height: '100vh' },
        '*::-webkit-scrollbar': { width: '6px' },
        '*::-webkit-scrollbar-track': { background: '#f1f5f9' },
        '*::-webkit-scrollbar-thumb': { background: '#cbd5e1', borderRadius: '4px' },
        '*::-webkit-scrollbar-thumb:hover': { background: '#94a3b8' }
      }} />

      <Box sx={{ width: '100vw', height: '100vh', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        
        {/* TOP NAVBAR */}
        <AppBar position="static" elevation={0} sx={{ bgcolor: '#002b5c', width: '100%', flexShrink: 0 }}>
          <Toolbar variant="dense" sx={{ minHeight: '64px', px: 3 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', flexGrow: 1 }}>
              <img src="/capgemini-logo.png" alt="Capgemini Engineering" style={{ height: '46px', objectFit: 'contain' }} />
              <Typography variant="h6" sx={{ color: '#ffffff', fontSize: '1.25rem', ml: 3, pl: 3, borderLeft: '1px solid #33557a' }}>
                SMART CITY ADAS
              </Typography>
            </Box>
            
            <Box sx={{ display: 'flex', alignItems: 'center' }}>
              <Typography variant="body2" sx={{ color: '#a0b2c6', fontWeight: 600, mr: 2 }}>
                v1.3.44 <span style={{ margin: '0 10px' }}>|</span> SYS_ADMIN
              </Typography>
              <IconButton color="inherit" onClick={() => setIsAuthenticated(false)} title="Logout" sx={{ bgcolor: 'rgba(255,255,255,0.1)', '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' } }}>
                <LogoutIcon fontSize="small" />
              </IconButton>
            </Box>
          </Toolbar>
        </AppBar>

        {/* REFINED TAB ROW */}
        <Box sx={{ bgcolor: '#001c3d', px: 4, flexShrink: 0, borderBottom: '1px solid #e2e8f0', width: '100%' }}>
          <Tabs value={currentTab} onChange={(e, val) => setCurrentTab(val)} textColor="inherit" indicatorColor="secondary">
            <Tab label="DASHBOARD" />
            <Tab label="EDGE NODES" />
            <Tab label="REPORTS" />
            <Tab label="SETTINGS" />
          </Tabs>
        </Box>

{/* 🎯 THE FIX: PURE CSS GRID INSTEAD OF MUI <Grid> 🎯 */}
<Box sx={{ flex: 1, p: 3, overflow: 'hidden', width: '100%' }}>
          
          {/* TAB 0: THE REAL DASHBOARD */}
          {currentTab === 0 && (
            <Box sx={{ 
              display: 'grid', 
              gridTemplateColumns: '3fr 6fr 3fr', // Forces 25% | 50% | 25% distribution mathematically
              gap: '24px', 
              height: '100%', 
              width: '100%' 
            }}>
              
              {/* LEFT COLUMN */}
              <Box sx={{ height: '100%', minWidth: 0 }}>
                {/* 👇 Pass activeNode so Emergency buttons apply to the correct intersection */}
                <Configurator isSimMode={isSimulationMode} toggleSimMode={() => setIsSimulationMode(!isSimulationMode)} configState={config} setConfigState={setConfig} activeNode={activeNode} />
              </Box>

              {/* MIDDLE COLUMN */}
              <Box sx={{ height: '100%', display: 'flex', flexDirection: 'column', gap: '24px', minWidth: 0 }}>
                {/* 👇 Pass activeNode and setActiveNode to the camera */}
                <CameraView isSimMode={isSimulationMode} configState={config} activeNode={activeNode} setActiveNode={setActiveNode} />
                <ScanLogsTable refreshRate={config.refreshRate} />
              </Box>

              {/* RIGHT COLUMN */}
              <Box sx={{ height: '100%', minWidth: 0 }}>
                <RightColumnPanel refreshRate={config.refreshRate} />
              </Box>

            </Box>
          )}

          {/* TAB 1: MOCKED EDGE NODES */}
          {currentTab === 1 && <EdgeNodesTab />}

          {/* TAB 2: MOCKED REPORTS */}
          {currentTab === 2 && <ReportsTab />}

          {/* TAB 3: MOCKED SETTINGS */}
          {currentTab === 3 && <SettingsTab />}

        </Box>

      </Box>
    </ThemeProvider>
  );
}