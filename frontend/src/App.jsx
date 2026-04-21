// frontend/src/App.jsx
import React, { useState, useEffect, useRef } from 'react';
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
import PlayArrowIcon from '@mui/icons-material/PlayArrow';
import FileUploadIcon from '@mui/icons-material/FileUpload';
import StopIcon from '@mui/icons-material/Stop';
import SpeedIcon from '@mui/icons-material/Speed';

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
// 1. LEFT COLUMN: Unified Configurator
// ============================================================================
const Configurator = ({ isSimMode, setIsSimMode, configState, setConfigState, activeNode }) => {
  const [file, setFile] = useState(null);
  const [modelChoice, setModelChoice] = useState('YOLOv8_Nano');
  const [uploadStatus, setUploadStatus] = useState('');
  const [confidence, setConfidence] = useState(0.15); 
  const [stopLine, setStopLine] = useState(1600); // 👈 NEW: Stop Line UI Tracker
  const fileInputRef = useRef();

  const handleFileChange = (e) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
      setUploadStatus('');
    }
  };

  const handleStartSimulation = async () => {
    if (!file) {
      alert("Please upload a video file first.");
      return;
    }
    try {
      setUploadStatus('Uploading video...');
      const uploadData = new FormData();
      uploadData.append('file', file);
      const uploadRes = await axios.post('http://localhost:8000/api/upload_video', uploadData);
      
      const serverVideoPath = uploadRes.data.video_path;

      setUploadStatus('Initializing AI Engine...');
      const simData = new FormData();
      simData.append('video_path', serverVideoPath);
      simData.append('model_choice', modelChoice);
      simData.append('node_id', activeNode);
      
      await axios.post('http://localhost:8000/api/run_simulation', simData);
      
      // Resend the custom UI configurations immediately after boot
      setTimeout(() => {
        handleConfidenceSubmit(null, confidence);
        handleStopLineSubmit(null, stopLine);
      }, 2000);

      setUploadStatus('Simulation Running!');
      setIsSimMode(true); 
      setTimeout(() => setUploadStatus(''), 5000);
    } catch (error) {
      setUploadStatus('Error starting simulation.');
      alert("Failed to start simulation. Check backend console.");
    }
  };

  const handleStopSimulation = async () => {
    try {
      setUploadStatus('Stopping simulation...');
      await axios.post('http://localhost:8000/api/stop_simulation');
      setIsSimMode(false); 
      setUploadStatus('Simulation Stopped.');
      setTimeout(() => setUploadStatus(''), 3000);
    } catch (error) {
      console.error(error);
    }
  };

  const forceGreen = async () => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "FORCE_GREEN", node_id: activeNode });
      alert(`EMERGENCY SIGNAL BROADCASTED: ${activeNode} Forced to GREEN for 15s.`);
    } catch (e) { alert("Connection Error: Backend Command API Offline."); }
  };

  const restartVideo = async () => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "RESTART_VIDEO", node_id: activeNode });
    } catch (e) { alert("Connection Error."); }
  };

  const handleConfidenceSubmit = async (event, newValue) => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "SET_CONFIDENCE", node_id: activeNode, value: newValue });
    } catch (e) { console.error("Failed to update confidence"); }
  };

  // 👇 NEW: Send dynamic stop line updates to the backend
  const handleStopLineSubmit = async (event, newValue) => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "SET_STOP_LINE", node_id: activeNode, value: newValue });
    } catch (e) { console.error("Failed to update stop line"); }
  };

  return (
    <Paper sx={{ p: 3, gap: 2.5 }}>
      
      <Typography variant="subtitle1" color="primary" sx={{ borderBottom: '2px solid #002b5c', pb: 1 }}>
        Model Benchmarking
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0' }}>
          <Typography variant="caption" color="textSecondary" fontWeight="bold">VIDEO SOURCE</Typography>
          <input type="file" accept="video/mp4,video/x-m4v,video/*" style={{ display: 'none' }} ref={fileInputRef} onChange={handleFileChange} />
          <Button variant="outlined" fullWidth startIcon={<FileUploadIcon />} onClick={() => fileInputRef.current.click()} sx={{ mt: 1, justifyContent: 'flex-start', color: '#475569', borderColor: '#cbd5e1' }}>
            {file ? file.name : "Select Video (.mp4)"}
          </Button>
        </Box>

        <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0' }}>
          <Typography variant="caption" color="textSecondary" fontWeight="bold" sx={{ display: 'block', mb: 1 }}>AI MODEL</Typography>
          <FormControl fullWidth size="small">
            <Select value={modelChoice} onChange={(e) => setModelChoice(e.target.value)} sx={{ bgcolor: 'white' }}>
              <MenuItem value="YOLOv8_Nano">YOLOv8 Nano (Highest FPS)</MenuItem>
              <MenuItem value="YOLOv8_Small">YOLOv8 Small (Balanced)</MenuItem>
              <MenuItem value="YOLOv8_Custom">Custom PFE Model (High Accuracy)</MenuItem>
            </Select>
          </FormControl>
        </Box>

        <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0', mt: 0.5 }}>
          <Typography variant="caption" color="textSecondary" fontWeight="bold" sx={{ display: 'flex', justifyContent: 'space-between' }}>
            <span>LIVE AI CONFIDENCE</span>
            <span style={{ color: '#00a0d1' }}>{(confidence * 100).toFixed(0)}%</span>
          </Typography>
          <Slider value={confidence} min={0.05} max={0.95} step={0.05} onChange={(e, val) => setConfidence(val)} onChangeCommitted={handleConfidenceSubmit} color="secondary" />
        </Box>

        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button variant="contained" color="secondary" startIcon={<PlayArrowIcon />} onClick={handleStartSimulation} fullWidth sx={{ py: 1.5 }}>
            LAUNCH
          </Button>
          <Button variant="outlined" color="error" startIcon={<StopIcon />} onClick={handleStopSimulation} sx={{ minWidth: '100px' }}>
            STOP
          </Button>
        </Box>
        
        {uploadStatus && <Typography variant="body2" sx={{ color: '#16a34a', fontWeight: 'bold', textAlign: 'center' }}>{uploadStatus}</Typography>}
      </Box>

      <Typography variant="subtitle1" color="primary" sx={{ borderBottom: '2px solid #002b5c', pb: 1, mt: 1 }}>
        Visual Configurator
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0' }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <DarkModeIcon sx={{ fontSize: 16, color: '#64748b' }} />
            <Typography variant="body2" fontWeight="bold" color="#334155">Night Mode (UI Filter)</Typography>
          </Box>
          <Switch checked={configState.nightMode} onChange={(e) => setConfigState({...configState, nightMode: e.target.checked})} color="primary" />
        </Box>

        <Box sx={{ px: 1, mt: 1 }}>
          <Typography variant="caption" color="textSecondary" fontWeight="bold">BRIGHTNESS</Typography>
          <Slider value={configState.brightness} min={50} max={200} onChange={(e, val) => setConfigState({...configState, brightness: val})} color="secondary" />
          
          <Typography variant="caption" color="textSecondary" fontWeight="bold">CONTRAST</Typography>
          <Slider value={configState.contrast} min={50} max={200} onChange={(e, val) => setConfigState({...configState, contrast: val})} color="secondary" />

          <Typography variant="caption" color="textSecondary" fontWeight="bold">SATURATION</Typography>
          <Slider value={configState.saturation} min={0} max={300} onChange={(e, val) => setConfigState({...configState, saturation: val})} color="secondary" />

          {/* 👇 NEW: Dynamic Stop-Line Calibration */}
          <Typography variant="caption" color="textSecondary" fontWeight="bold" sx={{ display: 'flex', justifyContent: 'space-between', mt: 1 }}>
            <span>RED LIGHT STOP-LINE (Y-AXIS)</span>
            <span style={{ color: '#00a0d1' }}>{stopLine}px</span>
          </Typography>
          <Slider value={stopLine} min={100} max={2000} step={10} onChange={(e, val) => setStopLine(val)} onChangeCommitted={handleStopLineSubmit} color="error" />
        </Box>
      </Box>

      <Typography variant="subtitle1" color="primary" sx={{ borderBottom: '2px solid #002b5c', pb: 1, mt: 1 }}>
        Edge Controls
      </Typography>
      
      <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1.5 }}>
        <Button variant="contained" color="error" startIcon={<WarningIcon />} onClick={forceGreen} fullWidth sx={{ py: 1.5 }}>FORCE EMERGENCY GREEN</Button>
        <Button variant="outlined" color="primary" startIcon={<RestartAltIcon />} onClick={restartVideo} fullWidth sx={{ py: 1 }}>RESTART CURRENT VIDEO</Button>
      </Box>
    </Paper>
  );
};

// ============================================================================
// 2. MIDDLE COLUMN: Video & Table
// ============================================================================
const CameraView = ({ isSimMode, activeNode, configState }) => {
  const videoFilters = `
    brightness(${configState.brightness}%) 
    contrast(${configState.contrast}%) 
    saturate(${configState.saturation}%)
    ${configState.nightMode ? 'invert(1) hue-rotate(180deg) grayscale(20%)' : ''}
  `;

  return (
    <Paper sx={{ width: '100%', height: { xs: 300, md: 420 }, backgroundColor: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden', borderRadius: 2, border: 'none' }}>
      {isSimMode ? (
        <img 
          src={`http://localhost:8000/api/video_feed/${activeNode}`} 
          alt="Live Stream" 
          style={{ width: '100%', height: '100%', objectFit: 'contain', filter: videoFilters, transition: 'filter 0.3s ease' }} 
        />
      ) : (
        <Box sx={{ textAlign: 'center', color: '#64748b' }}>
          <VideocamOffIcon sx={{ fontSize: 64, color: '#d13239', mb: 2, opacity: 0.8 }} />
          <Typography variant="button" display="block" sx={{ letterSpacing: 2 }}>Awaiting Simulation Upload</Typography>
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
    <Paper sx={{ width: '100%', minHeight: '300px', display: 'flex', flexDirection: 'column' }}>
      <Typography variant="subtitle1" color="primary" sx={{ p: 2, borderBottom: '1px solid #e2e8f0', bgcolor: '#f8fafc' }}>
        ALPR Scan Logs
      </Typography>
      <TableContainer sx={{ flexGrow: 1 }}>
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
const RightColumnPanel = ({ refreshRate, activeNode }) => { 
  const [timeframe, setTimeframe] = useState('all');
  const [weatherData, setWeatherData] = useState("Fetching API...");
  const [totalViolations, setTotalViolations] = useState(0);
  const [telemetry, setTelemetry] = useState({ fps: 0, inference_ms: 0, cpu: 0, ram: 0 }); 

  useEffect(() => {
    axios.get("https://api.open-meteo.com/v1/forecast?latitude=36.4561&longitude=10.7376&current_weather=true")
      .then(res => setWeatherData(`${res.data.current_weather.temperature}°C | Wind: ${res.data.current_weather.windspeed} km/h`))
      .catch(() => setWeatherData("API Offline"));
  }, []);

  useEffect(() => {
    const fetchStatsAndTelemetry = async () => {
      try {
        const resStats = await axios.get('http://localhost:8000/api/stats');
        setTotalViolations(resStats.data.total_violations);
        
        const resTele = await axios.get(`http://localhost:8000/api/telemetry/${activeNode}`);
        setTelemetry(resTele.data);
      } catch (e) { }
    };
    fetchStatsAndTelemetry();
    const interval = setInterval(fetchStatsAndTelemetry, refreshRate);
    return () => clearInterval(interval);
  }, [refreshRate, activeNode]);

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
    <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
      <Paper sx={{ p: 4, textAlign: 'center', bgcolor: '#ffffff', borderTop: '4px solid #00a0d1' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 2 }}>
          <AssessmentIcon color="secondary" />
          <Typography variant="subtitle1" color="primary">Analytics</Typography>
        </Box>
        <Typography variant="h2" sx={{ fontWeight: 900, color: '#002b5c', my: 1 }}>{totalViolations}</Typography>
        <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700, letterSpacing: 1.5 }}>TOTAL VIOLATIONS</Typography>
      </Paper>

      <Paper sx={{ p: 3, display: 'flex', flexDirection: 'column' }}>
        <Box sx={{ display: 'flex', justifyContent: 'space-between', borderBottom: '2px solid #002b5c', pb: 1.5, mb: 2 }}>
          <Typography variant="subtitle1" color="primary">Live Telemetry</Typography>
          <SpeedIcon color="secondary" />
        </Box>
        
        <Box sx={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 1.5 }}>
          <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700 }}>INFERENCE</Typography>
            <Typography variant="h6" sx={{ color: '#0f172a' }}>{telemetry.inference_ms || 0} ms</Typography>
          </Box>
          <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700 }}>PROCESSING</Typography>
            <Typography variant="h6" sx={{ color: '#0f172a' }}>{telemetry.fps || 0} FPS</Typography>
          </Box>
          <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700 }}>NODE CPU</Typography>
            <Typography variant="h6" sx={{ color: telemetry.cpu > 80 ? '#d13239' : '#0f172a' }}>{telemetry.cpu || 0}%</Typography>
          </Box>
          <Box sx={{ bgcolor: '#f8fafc', p: 1.5, borderRadius: 1.5, border: '1px solid #e2e8f0', textAlign: 'center' }}>
            <Typography variant="caption" sx={{ color: '#64748b', fontWeight: 700 }}>NODE RAM</Typography>
            <Typography variant="h6" sx={{ color: telemetry.ram > 80 ? '#d13239' : '#0f172a' }}>{telemetry.ram || 0}%</Typography>
          </Box>
        </Box>
      </Paper>

      <Paper sx={{ p: 3, display: 'flex', flexDirection: 'column', gap: 3 }}>
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
    <Box sx={{ display: 'grid', gridTemplateColumns: { xs: '1fr', md: 'repeat(2, 1fr)', lg: 'repeat(3, 1fr)' }, gap: 3 }}>
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
  
  const activeNode = 'NODE_A';

  if (!isAuthenticated) {
    return (
      <ThemeProvider theme={capgeminiTheme}>
        <CssBaseline />
        <GlobalStyles styles={{ 
          '*, *::before, *::after': { boxSizing: 'border-box' },
          '#root': { width: '100vw', height: '100vh', margin: 0, padding: 0 }, 
          body: { margin: 0, padding: 0 } 
        }} />
        <LoginScreen onLogin={() => setIsAuthenticated(true)} />
      </ThemeProvider>
    );
  }

  return (
    <ThemeProvider theme={capgeminiTheme}>
      <CssBaseline />
      
      <GlobalStyles styles={{ 
        '*, *::before, *::after': { boxSizing: 'border-box' },
        '#root': { minHeight: '100vh', display: 'flex', flexDirection: 'column' }, 
        body: { margin: 0, padding: 0, minHeight: '100vh', backgroundColor: '#eef2f6', overflowX: 'hidden' },
        '*::-webkit-scrollbar': { width: '8px' },
        '*::-webkit-scrollbar-track': { background: '#f1f5f9' },
        '*::-webkit-scrollbar-thumb': { background: '#cbd5e1', borderRadius: '4px' },
        '*::-webkit-scrollbar-thumb:hover': { background: '#94a3b8' }
      }} />

      <AppBar position="static" elevation={0} sx={{ bgcolor: '#002b5c', width: '100%' }}>
        <Toolbar sx={{ minHeight: '80px', px: 3, display: 'flex', justifyContent: 'space-between' }}>
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <img src="/capgemini-logo.png" alt="Capgemini Engineering" style={{ height: '65px', objectFit: 'contain' }} />
          </Box>
          
          <Box sx={{ display: 'flex', alignItems: 'center' }}>
            <Typography variant="body2" sx={{ color: '#a0b2c6', fontWeight: 600, mr: 2, display: { xs: 'none', sm: 'block' } }}>
              v1.3.44 <span style={{ margin: '0 10px' }}>|</span> SYS_ADMIN
            </Typography>
            <IconButton color="inherit" onClick={() => setIsAuthenticated(false)} title="Logout" sx={{ bgcolor: 'rgba(255,255,255,0.1)', '&:hover': { bgcolor: 'rgba(255,255,255,0.2)' } }}>
              <LogoutIcon fontSize="small" />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ bgcolor: '#001c3d', px: { xs: 2, md: 4 }, borderBottom: '1px solid #e2e8f0', width: '100%', display: 'flex', alignItems: 'center', flexWrap: 'wrap' }}>
        <Typography variant="h6" sx={{ color: '#ffffff', fontSize: '1.25rem', mr: 4, fontWeight: 900, letterSpacing: '1px', display: { xs: 'none', md: 'block' } }}>
          SMART CITY ADAS
        </Typography>
        <Tabs 
          value={currentTab} 
          onChange={(e, val) => setCurrentTab(val)} 
          textColor="inherit" 
          indicatorColor="secondary"
          variant="scrollable"
          scrollButtons="auto"
          sx={{ minHeight: '56px', '& .MuiTab-root': { minHeight: '56px' } }}
        >
          <Tab label="DASHBOARD" />
          <Tab label="EDGE NODES" />
          <Tab label="REPORTS" />
          <Tab label="SETTINGS" />
        </Tabs>
      </Box>

      <Box sx={{ flexGrow: 1, p: 3, width: '100%' }}>
        {currentTab === 0 && (
          <Box sx={{ 
            display: 'grid', 
            gridTemplateColumns: { xs: '1fr', lg: '3fr 6fr 3fr' }, 
            gap: '24px', 
            alignItems: 'start'
          }}>
            <Box>
              <Configurator 
                isSimMode={isSimulationMode}
                setIsSimMode={setIsSimulationMode}
                configState={config}
                setConfigState={setConfig}
                activeNode={activeNode}
              />
            </Box>
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
              <CameraView isSimMode={isSimulationMode} activeNode={activeNode} configState={config} />
              <ScanLogsTable refreshRate={config.refreshRate} />
            </Box>
            <Box>
              <RightColumnPanel refreshRate={config.refreshRate} activeNode={activeNode} />
            </Box>
          </Box>
        )}
        {currentTab === 1 && <EdgeNodesTab />}
        {currentTab === 2 && <ReportsTab />}
        {currentTab === 3 && <SettingsTab />}
      </Box>
    </ThemeProvider>
  );
}