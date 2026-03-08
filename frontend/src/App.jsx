import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import { Activity, VideoOff, Maximize, ShieldAlert, Moon, RefreshCw, Download } from 'lucide-react';
import jsPDF from 'jspdf';
import autoTable from 'jspdf-autotable';
import * as XLSX from 'xlsx';

// --- Reusable Enterprise Card Component (ICONS REMOVED AS REQUESTED) ---
const DashboardCard = ({ title, accentColor, headerBg, textColor, children, extraHeader }) => (
  <div className="bg-white rounded-xl shadow-md flex flex-col overflow-hidden h-full border border-gray-200/60 min-h-0">
    <div className={`px-5 py-4 ${headerBg} ${textColor} flex items-center justify-between border-b-4 ${accentColor} shrink-0`}>
      <h2 className="text-lg font-bold tracking-wide uppercase">{title}</h2>
      {extraHeader && <div>{extraHeader}</div>}
    </div>
    <div className="p-5 flex-1 flex flex-col overflow-hidden text-capgemini-darkBlue bg-white min-h-0">
      {children}
    </div>
  </div>
);

// --- 1. Left Column: Configurator ---
const Configurator = ({ isSimMode, toggleSimMode, configState, setConfigState }) => {
  const forceGreen = async () => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "FORCE_GREEN", node_id: "NODE_A" });
      alert("EMERGENCY SIGNAL BROADCASTED: Node A Forced to GREEN for 15s.");
    } catch (e) {
      alert("Connection Error: Backend Command API Offline.");
    }
  };

  const restartVideo = async () => {
    try {
      await axios.post('http://localhost:8000/api/command', { action: "RESTART_VIDEO", node_id: "NODE_A" });
    } catch (e) { alert("Connection Error: Backend Command API Offline."); }
  };

  return (
    <DashboardCard title="Configurator" headerBg="bg-capgemini-darkBlue" textColor="text-white" accentColor="border-capgemini-blue">
      <div className="space-y-4 flex-1 flex flex-col overflow-y-auto pr-2 custom-scrollbar">
        
        {/* 🎚️ TOGGLES */}
        <div className="space-y-2 shrink-0">
          <div className="flex justify-between items-center bg-capgemini-gray bg-opacity-50 p-3 rounded-lg border border-gray-100 shadow-sm">
            <span className="font-semibold text-sm text-gray-700">Simulation Mode</span>
            <div onClick={toggleSimMode} className={`w-12 h-6 rounded-full relative cursor-pointer shadow-inner transition-colors duration-300 ${isSimMode ? 'bg-capgemini-lightBlue' : 'bg-gray-300'}`}>
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 shadow transition-all duration-300 ${isSimMode ? 'left-6' : 'left-0.5'}`}></div>
            </div>
          </div>
          
          <div className="flex justify-between items-center bg-capgemini-gray bg-opacity-50 p-3 rounded-lg border border-gray-100 shadow-sm">
            <span className="font-semibold text-sm text-gray-700 flex items-center gap-2"><Moon size={16} className="text-capgemini-blue"/> Night Mode</span>
            <div onClick={() => setConfigState({...configState, nightMode: !configState.nightMode})} className={`w-12 h-6 rounded-full relative cursor-pointer shadow-inner transition-colors duration-300 ${configState.nightMode ? 'bg-capgemini-darkBlue' : 'bg-gray-300'}`}>
              <div className={`w-5 h-5 bg-white rounded-full absolute top-0.5 shadow transition-all duration-300 ${configState.nightMode ? 'left-6' : 'left-0.5'}`}></div>
            </div>
          </div>
        </div>

        {/* 🚨 EMERGENCY TRAFFIC CONTROL */}
        <div className="space-y-2 shrink-0">
          <button 
            onClick={forceGreen}
            className="w-full bg-red-600 hover:bg-red-700 text-white font-black py-3 rounded-xl flex items-center justify-center gap-2 shadow-lg transition-all active:scale-95 group border-2 border-red-500 hover:border-red-400"
          >
            <ShieldAlert size={20} className="group-hover:animate-pulse" />
            FORCE EMERGENCY GREEN
          </button>
          
          <button 
            onClick={restartVideo}
            className="w-full bg-capgemini-darkBlue hover:bg-capgemini-blue text-white font-bold py-2.5 rounded-xl flex items-center justify-center gap-2 shadow transition-all active:scale-95"
          >
            <RefreshCw size={16} />
            RESTART SIMULATION
          </button>
        </div>
        
        {/* 🎛️ SLIDERS */}
        <div className="space-y-3 shrink-0 bg-gray-50 p-3 rounded-xl border border-gray-200 shadow-inner">
          <div>
            <div className="flex justify-between text-[10px] font-bold text-gray-500 mb-1 uppercase tracking-wider"><span>Polling Rate</span><span className="text-capgemini-blue">{configState.refreshRate} ms</span></div>
            <input type="range" min="100" max="5000" step="100" value={configState.refreshRate} onChange={(e) => setConfigState({...configState, refreshRate: e.target.value})} className="w-full accent-capgemini-blue cursor-pointer h-1.5 bg-gray-200 rounded-lg appearance-none" />
          </div>
          <div>
            <div className="flex justify-between text-[10px] font-bold text-gray-500 mb-1 uppercase tracking-wider"><span>Brightness</span><span className="text-capgemini-blue">{configState.brightness}%</span></div>
            <input type="range" min="50" max="200" value={configState.brightness} onChange={(e) => setConfigState({...configState, brightness: e.target.value})} className="w-full accent-capgemini-turquoise cursor-pointer h-1.5 bg-gray-200 rounded-lg appearance-none" />
          </div>
          <div>
            <div className="flex justify-between text-[10px] font-bold text-gray-500 mb-1 uppercase tracking-wider"><span>Contrast</span><span className="text-capgemini-blue">{configState.contrast}%</span></div>
            <input type="range" min="50" max="200" value={configState.contrast} onChange={(e) => setConfigState({...configState, contrast: e.target.value})} className="w-full accent-capgemini-lightBlue cursor-pointer h-1.5 bg-gray-200 rounded-lg appearance-none" />
          </div>
          <div>
            <div className="flex justify-between text-[10px] font-bold text-gray-500 mb-1 uppercase tracking-wider"><span>Saturation</span><span className="text-capgemini-blue">{configState.saturation}%</span></div>
            <input type="range" min="0" max="300" value={configState.saturation} onChange={(e) => setConfigState({...configState, saturation: e.target.value})} className="w-full accent-capgemini-blue cursor-pointer h-1.5 bg-gray-200 rounded-lg appearance-none" />
          </div>
        </div>
      </div>
    </DashboardCard>
  );
};

// --- 2. Middle Column: Camera & Control Center ---
const CameraView = ({ isSimMode, configState }) => {
  const [isPlaying, setIsPlaying] = useState(true);
  const videoContainerRef = useRef(null);

  const toggleFullScreen = () => {
    if (videoContainerRef.current && videoContainerRef.current.requestFullscreen) {
      videoContainerRef.current.requestFullscreen();
    }
  };

  const videoFilters = `
    brightness(${configState.brightness}%) 
    contrast(${configState.contrast}%) 
    saturate(${configState.saturation}%) 
    ${configState.nightMode ? 'invert(1) hue-rotate(180deg) grayscale(20%)' : ''}
  `;

  return (
    <div ref={videoContainerRef} className="flex-1 min-h-0 relative rounded-xl shadow-lg border-4 border-capgemini-darkBlue overflow-hidden bg-black flex items-center justify-center group">
      <div className="absolute top-0 left-0 w-full bg-gradient-to-b from-black/80 to-transparent p-4 flex justify-between items-start z-20">
        <div className="text-white">
          <span className="font-bold tracking-widest uppercase text-xs drop-shadow-md">Node A - Live Feed</span>
        </div>
        <div className="flex gap-3 items-center">
          <button onClick={toggleFullScreen} className="bg-white/20 hover:bg-white/40 p-1.5 rounded text-white transition-colors shadow-md backdrop-blur-sm" title="Full Screen">
            <Maximize size={16} />
          </button>
          <div className={`flex items-center gap-2 text-[10px] font-black text-white px-3 py-1.5 rounded-full shadow-lg transition-colors ${isSimMode ? 'bg-capgemini-turquoise/90' : 'bg-red-600/90'}`}>
            <div className={`w-1.5 h-1.5 rounded-full bg-white ${isSimMode && isPlaying ? 'animate-pulse' : ''}`}></div>
            {isSimMode ? (isPlaying ? 'LIVE' : 'PAUSED') : 'OFFLINE'}
          </div>
        </div>
      </div>
      
      {isSimMode ? (
        <div className="relative w-full h-full flex items-center justify-center bg-black">
          {isPlaying ? (
            <img 
              src="http://localhost:8000/api/video_feed/NODE_A" 
              alt="Live Stream"
              className="w-full h-full object-contain transition-opacity duration-500"
              style={{ filter: videoFilters }} 
              onError={(e) => { e.target.style.display = 'none'; e.target.nextSibling.style.display = 'flex'; }}
            />
          ) : (
            <div className="flex flex-col items-center text-capgemini-lightBlue animate-pulse">
              <Activity size={48} className="mb-2" />
              <span className="text-xs font-mono tracking-widest uppercase">[ Stream Paused ]</span>
            </div>
          )}

          <div className="absolute bottom-6 left-1/2 -translate-x-1/2 flex items-center gap-6 bg-black/60 backdrop-blur-md px-6 py-2 rounded-full border border-white/20 opacity-0 group-hover:opacity-100 transition-opacity duration-300 z-30 shadow-2xl">
            <button onClick={() => setIsPlaying(!isPlaying)} className="text-white hover:text-capgemini-lightBlue transition-colors font-bold text-xs tracking-wider">
              {isPlaying ? "PAUSE FEED" : "RESUME FEED"}
            </button>
          </div>
        </div>
      ) : (
        <div className="flex flex-col items-center justify-center text-gray-400 font-mono text-sm tracking-widest p-8 text-center">
          <VideoOff size={48} className="mb-4 opacity-50 text-red-400" />
          <span className="text-lg font-bold text-white mb-2 uppercase tracking-widest">[ Hardware Offline ]</span>
        </div>
      )}
    </div>
  );
};

const ScanLogs = ({ refreshRate }) => {
  const [logs, setLogs] = useState([]);

  useEffect(() => {
    const fetchLogs = async () => {
      try {
        const response = await axios.get('http://localhost:8000/api/violations?limit=5');
        setLogs(response.data);
      } catch (error) { console.error("API error", error); }
    };
    fetchLogs();
    const interval = setInterval(fetchLogs, refreshRate); 
    return () => clearInterval(interval);
  }, [refreshRate]);

  return (
    <div className="h-[280px] shrink-0 flex flex-col">
      <DashboardCard title="ALPR Scan Logs" headerBg="bg-capgemini-blue" textColor="text-white" accentColor="border-capgemini-lightBlue">
        <div className="flex-1 overflow-y-auto text-sm pr-2">
          <table className="w-full text-left border-collapse">
            <thead className="sticky top-0 bg-white z-10 shadow-sm">
              <tr className="bg-gray-50 text-[10px] uppercase tracking-widest text-gray-500">
                <th className="p-3 font-bold rounded-tl-lg">Timestamp</th>
                <th className="p-3 font-bold">Plate / ID</th>
                <th className="p-3 font-bold">Type</th>
                <th className="p-3 font-bold text-right rounded-tr-lg">Fine</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log, index) => (
                <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                  <td className="p-3 text-gray-600 font-mono text-xs">{log.timestamp.split(' ')[1]}</td>
                  <td className="p-3 font-bold text-capgemini-darkBlue uppercase text-xs">{log.plate_number || log.vehicle_id}</td>
                  <td className="p-3">
                    <span className={`px-2 py-1 rounded text-[9px] font-black uppercase whitespace-nowrap ${log.violation_type === 'RED_LIGHT' ? 'bg-red-100 text-red-700' : 'bg-orange-100 text-orange-700'}`}>
                      {log.violation_type.replace('_', ' ')}
                    </span>
                  </td>
                  <td className="p-3 text-right font-black text-capgemini-blue whitespace-nowrap text-xs">{log.fine_amount} TND</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </DashboardCard>
    </div>
  );
};

// --- 3. Right Column: Env Data & Export ---
const EnvData = () => {
  const [weatherData, setWeatherData] = useState("Fetching API...");

  useEffect(() => {
    axios.get("https://api.open-meteo.com/v1/forecast?latitude=36.4561&longitude=10.7376&current_weather=true")
      .then(res => {
        const temp = res.data.current_weather.temperature;
        const wind = res.data.current_weather.windspeed;
        setWeatherData(`${temp}°C | Wind: ${wind} km/h`);
      })
      .catch(() => setWeatherData("API Offline"));
  }, []);

  // ADVANCED DYNAMIC EXPORT LOGIC (WITH TIMEFRAME FILTERS)
  const handleExport = async (format) => {
    try {
      // 1. Grab the currently selected timeframe from the dropdown
      const selectedTimeframe = document.getElementById('timeframe').value;
      
      // 2. Fetch the filtered data from the backend
      const response = await axios.get(`http://localhost:8000/api/violations?limit=999999&timeframe=${selectedTimeframe}`);
      const allLogs = response.data;
      const totalViolationsReached = allLogs.length; 

      if (format === 'pdf') {
        const doc = new jsPDF();
        
        doc.setFontSize(16);
        // Dynamically change the PDF Title!
        const reportTitle = `Capgemini Smart City - ${selectedTimeframe.toUpperCase()} Report`;
        doc.text(reportTitle, 14, 15);
        
        doc.setFontSize(11);
        doc.setTextColor(0, 112, 173); 
        doc.text(`Total Violations Reached: ${totalViolationsReached}`, 14, 23);
        
        const tableData = allLogs.map(log => [
          log.id || log.vehicle_id, 
          log.plate_number, 
          log.timestamp, 
          log.image_path 
        ]);

        autoTable(doc, {
          head: [['ID (Inc)', 'Car Number', 'Time', 'Image Link']],
          body: tableData,
          startY: 28, 
          styles: { fontSize: 8, cellPadding: 2 },
          headStyles: { fillColor: [0, 112, 173] } 
        });

        doc.save(`Capgemini_${selectedTimeframe}_Report.pdf`);
      } 
      else if (format === 'excel') {
        const excelData = allLogs.map(log => ({
          "ID (Inc)": log.id || log.vehicle_id,
          "Car Number": log.plate_number,
          "Time": log.timestamp,
          "Image Link": log.image_path
        }));

        const worksheet = XLSX.utils.json_to_sheet(excelData);
        const workbook = XLSX.utils.book_new();
        XLSX.utils.book_append_sheet(workbook, worksheet, `${selectedTimeframe}_violations`);
        XLSX.writeFile(workbook, `Capgemini_${selectedTimeframe}_Report.xlsx`);
      }
    } catch (error) {
      alert("Export failed: " + error.message);
    }
  };

  return (
    <div className="flex-1 min-h-0 flex flex-col mb-4">
      <DashboardCard title="Environment & Export" headerBg="bg-white" textColor="text-capgemini-darkBlue" accentColor="border-capgemini-turquoise" extraHeader={<div className="text-xs font-bold text-capgemini-turquoise bg-capgemini-turquoise/10 px-2 py-1 rounded shrink-0">SYNCED</div>}>
        <div className="space-y-4 flex-1 flex flex-col justify-between overflow-y-auto">
          {/* Environment Stats */}
          <div className="space-y-3">
            <div className="flex justify-between items-center border-b border-gray-100 pb-2 shrink-0">
              <span className="text-gray-500 font-semibold text-xs uppercase">Weather (Nabeul)</span>
              <span className="font-bold text-xs text-capgemini-blue">{weatherData}</span>
            </div>
            <div className="flex justify-between items-center shrink-0">
              <span className="text-gray-500 font-semibold text-xs uppercase">Active Node</span>
              <span className="font-bold bg-capgemini-darkBlue text-white px-3 py-1 rounded-md text-[10px] uppercase shadow-sm">Nabeul, TN</span>
            </div>
          </div>

          {/* Report Generator Control WITH DROPDOWN */}
          <div className="bg-gray-50 p-4 rounded-xl border border-gray-200 shadow-inner">
            <h3 className="text-[10px] font-bold text-gray-500 uppercase tracking-widest mb-3 flex items-center gap-2">
              <Download size={14} /> Generate Report
            </h3>
            
            {/* 👇 TIMEFRAME DROPDOWN ADDED HERE */}
            <select id="timeframe" className="w-full text-xs p-2 rounded-lg border border-gray-300 font-semibold text-capgemini-darkBlue mb-3 outline-none focus:ring-2 focus:ring-capgemini-lightBlue">
              <option value="all">All-Time History</option>
              <option value="daily">Daily Summary (Last 24h)</option>
              <option value="weekly">Weekly Overview (Last 7 Days)</option>
              <option value="monthly">Monthly Audit (Last 30 Days)</option>
            </select>

            <div className="flex gap-3">
              <button onClick={() => handleExport('pdf')} className="flex-1 bg-red-500 hover:bg-red-600 text-white text-xs font-bold py-2 rounded-lg transition-colors shadow-md">PDF</button>
              <button onClick={() => handleExport('excel')} className="flex-1 bg-green-600 hover:bg-green-700 text-white text-xs font-bold py-2 rounded-lg transition-colors shadow-md">EXCEL</button>
            </div>
          </div>
        </div>
      </DashboardCard>
    </div>
  );
};

const ResultsView = ({ refreshRate }) => {
  const [total, setTotal] = useState(0);
  useEffect(() => {
    const fetchStats = async () => {
      try {
        const res = await axios.get('http://localhost:8000/api/stats');
        setTotal(res.data.total_violations);
      } catch (e) { }
    };
    fetchStats();
    const interval = setInterval(fetchStats, refreshRate);
    return () => clearInterval(interval);
  }, [refreshRate]);

  return (
    <div className="flex-1 min-h-0 flex flex-col">
      <DashboardCard title="Analytics" headerBg="bg-white" textColor="text-capgemini-darkBlue" accentColor="border-capgemini-blue">
        <div className="flex-1 flex flex-col justify-center items-center shrink-0">
          <div className="text-8xl font-black text-capgemini-darkBlue mb-4 tracking-tighter transition-all duration-300 drop-shadow-sm">
            {total}
          </div>
          <div className="text-xs font-bold text-capgemini-blue uppercase tracking-widest bg-capgemini-blue/10 px-6 py-2 rounded-full shadow-sm">
            Total Violations
          </div>
        </div>
      </DashboardCard>
    </div>
  );
};

// --- Master Layout Assembly ---
export default function App() {
  const [isSimulationMode, setIsSimulationMode] = useState(false);
  
  const [config, setConfig] = useState({ 
    refreshRate: 500, 
    brightness: 100,
    contrast: 100,
    saturation: 100,
    nightMode: false
  });

  return (
    <div className="h-screen w-screen bg-[#E5E7EB] flex flex-col font-sans overflow-hidden">
      
      {/* Global Header */}
      <header className="bg-capgemini-darkBlue text-white px-8 py-4 flex justify-between items-center shadow-lg z-50 shrink-0">
        <div className="flex items-center gap-6">
          <h1 className="text-3xl font-black tracking-widest border-r-2 border-white/20 pr-6 uppercase italic">Capgemini</h1>
          <p className="text-capgemini-lightBlue text-[10px] font-black uppercase tracking-[0.4em]">Smart City ADAS Platform</p>
        </div>
        <div className="bg-capgemini-blue px-6 py-1.5 rounded-full text-xs font-black shadow-inner uppercase tracking-wider">
          Sys_Admin
        </div>
      </header>

      {/* Main Grid Layout */}
      <main className="flex-1 p-6 grid grid-cols-12 gap-6 overflow-hidden min-h-0">
        
        {/* LEFT COLUMN */}
        <div className="col-span-3 h-full flex flex-col min-h-0">
          <Configurator 
            isSimMode={isSimulationMode} 
            toggleSimMode={() => setIsSimulationMode(!isSimulationMode)} 
            configState={config} 
            setConfigState={setConfig} 
          />
        </div>

        {/* MIDDLE COLUMN */}
        <div className="col-span-6 h-full flex flex-col gap-6 min-h-0">
          <CameraView isSimMode={isSimulationMode} configState={config} />
          <ScanLogs refreshRate={config.refreshRate} />
        </div>

        {/* RIGHT COLUMN */}
        <div className="col-span-3 h-full flex flex-col gap-6 min-h-0">
          <EnvData />
          <ResultsView refreshRate={config.refreshRate} />
        </div>

      </main>
    </div>
  );
}