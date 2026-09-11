import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
    Leaf, Droplets, Thermometer, CloudRain, Activity,
    BarChart3, TrendingUp, X, Sparkles, Loader2,
    ShieldCheck, AlertTriangle, Calendar, Target, ChevronRight,
    Wifi, WifiOff, SlidersHorizontal, RefreshCw
} from 'lucide-react';
import axios from 'axios';
import {
    BarChart, Bar, XAxis, YAxis, CartesianGrid,
    Tooltip, ResponsiveContainer, Cell
} from 'recharts';
import { getApiUrl } from '../config/api';

const inputStats = {
    ndvi: { min: 0, max: 1, unit: "", label: "NDVI Index", icon: Leaf },
    moisture: { min: 0, max: 100, unit: "%", label: "Soil Moisture", icon: Droplets },
    nitrogen: { min: 0, max: 500, unit: "mg/kg", label: "Nitrogen (N)", icon: Activity },
    temp: { min: 0, max: 50, unit: "°C", label: "Temperature", icon: Thermometer },
    rainfall: { min: 0, max: 1000, unit: "mm", label: "Rainfall", icon: CloudRain }
};

const CropYieldPrediction = () => {
    const [formData, setFormData] = useState({
        ndvi: 0.65, moisture: 45, nitrogen: 140, temp: 28, rainfall: 450,
        soil_type: "Alluvial"
    });

    const [result, setResult] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('top3');
    const [predictionCount, setPredictionCount] = useState(0);
    const [selectedCrop, setSelectedCrop] = useState(null);
    const [insights, setInsights] = useState(null);
    const [insightsLoading, setInsightsLoading] = useState(false);

    // IoT toggle state
    const [inputMode, setInputMode] = useState('manual'); // 'manual' | 'iot'
    const [iotLoading, setIotLoading] = useState(false);
    const [iotStatus, setIotStatus] = useState(null); // null | 'success' | 'error'
    const [iotRaw, setIotRaw] = useState(null);

    const handleChange = (e) => {
        let val = parseFloat(e.target.value);
        setFormData({ ...formData, [e.target.name]: val });
    };

    const handleSelectChange = (e) => {
        setFormData({ ...formData, [e.target.name]: e.target.value });
    };

    const fetchIoTData = async () => {
        setIotLoading(true);
        setIotStatus(null);
        try {
            const res = await axios.get(getApiUrl('api/crop-yield/iot-telemetry'));
            if (res.data?.success) {
                const t = res.data.telemetry;
                setFormData(prev => ({ ...prev, ...t }));
                setIotRaw(res.data.raw);
                setIotStatus('success');
            } else {
                setIotStatus('error');
                alert(res.data?.error || 'No IoT data available');
            }
        } catch (err) {
            console.error("IoT fetch error:", err);
            setIotStatus('error');
            alert('Failed to fetch IoT data. Is your hardware connected?');
        }
        setIotLoading(false);
    };

    const handleModeSwitch = (mode) => {
        setInputMode(mode);
        if (mode === 'iot') {
            fetchIoTData();
        } else {
            setIotStatus(null);
            setIotRaw(null);
        }
    };

    const handlePredict = async () => {
        setLoading(true);
        setResult(null);       // clear old results so UI resets cleanly
        setSelectedCrop(null);
        setInsights(null);
        setPredictionCount(c => c + 1);

        // NORMALIZE values for the model (0-1)
        const normalizedData = {
            ndvi: Math.min(1, Math.max(0, formData.ndvi)),
            moisture: Math.min(1, Math.max(0, formData.moisture / 100)),
            nitrogen: Math.min(1, Math.max(0, formData.nitrogen / 500)), // Based on router.py scale
            temp: Math.min(1, Math.max(0, formData.temp / 60)),          // Based on router.py scale
            rainfall: Math.min(1, Math.max(0, formData.rainfall / 1200)), // Based on router.py scale
            soil_type: formData.soil_type
        };

        try {
            const res = await axios.post(getApiUrl('api/crop-yield/predict'), normalizedData);
            setResult(res.data);
            setActiveTab('top3');
        } catch (error) {
            console.error("Prediction error:", error);
            alert("Prediction engine busy. Try again in 10s.");
        }
        setLoading(false);
    };

    const handleCropClick = async (crop) => {
        setSelectedCrop(crop);
        setInsights(null);
        setInsightsLoading(true);

        // Normalized values for Explain call (Gemini expects 0-1 codes as per router logic)
        const normalizedInputs = {
            ndvi: Math.min(1, Math.max(0, formData.ndvi)),
            moisture: Math.min(1, Math.max(0, formData.moisture / 100)),
            nitrogen: Math.min(1, Math.max(0, formData.nitrogen / 500)),
            temp: Math.min(1, Math.max(0, formData.temp / 60)),
            rainfall: Math.min(1, Math.max(0, formData.rainfall / 1200))
        };

        try {
            const res = await axios.post(getApiUrl('api/crop-yield/explain'), {
                crop_name: crop.crop, yield_tons_ha: crop.yield_tons_ha,
                mandi_price_quintal: crop.mandi_price_quintal, profit_margin_pct: crop.profit_margin_pct,
                revenue_ha: crop.revenue_ha, cost_ha: crop.cost_ha, profit_ha: crop.profit_ha,
                soil_type: formData.soil_type, ...normalizedInputs
            });
            if (res.data?.success) setInsights(res.data.insights);
        } catch (err) {
            console.error("Explain error:", err);
            setInsights({
                roi_explanation: "Unable to fetch AI insights at the moment.",
                market_conditions: "Please try again later.",
                maximize_tips: [], risks: [], best_season: "N/A",
                confidence_note: "Analysis unavailable right now."
            });
        }
        setInsightsLoading(false);
    };

    const soilTypes = ["Alluvial", "Black", "Red", "Laterite", "Desert", "Montane"];

    const chartData = result?.raw_analysis?.map(item => ({
        name: item.crop, roi: item.profit_margin_pct,
    })).sort((a, b) => b.roi - a.roi).slice(0, 10) || [];

    return (
        <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-6 pt-24 font-sans text-slate-900 dark:text-white">
            <div className="max-w-7xl mx-auto">
                {/* Tabs */}
                <div className="flex justify-end mb-8">
                    <div className="flex items-center gap-2 bg-white dark:bg-slate-900 p-2 rounded-xl border border-slate-200 dark:border-slate-800">
                        <button onClick={() => setActiveTab('top3')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'top3' ? 'bg-organic-green-600 text-white' : 'text-slate-500'}`}>Recommendations</button>
                        <button onClick={() => setActiveTab('analysis')} className={`px-4 py-2 rounded-lg text-sm font-bold transition-all ${activeTab === 'analysis' ? 'bg-organic-green-600 text-white' : 'text-slate-500'}`}>Analysis</button>
                    </div>
                </div>

                <div className="grid grid-cols-1 xl:grid-cols-12 gap-10">
                    {/* Input Panel */}
                    <div className="xl:col-span-4">
                        <div className="bg-white dark:bg-slate-900 rounded-3xl p-8 border border-slate-200 dark:border-slate-800 shadow-sm">
                            {/* Manual / IoT Toggle */}
                            <div className="flex items-center justify-between mb-6">
                                <h2 className="text-2xl font-black flex items-center gap-2">
                                    <span className="underline decoration-organic-green-500/30">Telemetry</span>
                                </h2>
                                <div className="flex items-center bg-slate-100 dark:bg-slate-800 rounded-xl p-1">
                                    <button
                                        onClick={() => handleModeSwitch('manual')}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${inputMode === 'manual' ? 'bg-organic-green-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'
                                            }`}
                                    >
                                        <SlidersHorizontal size={12} /> Manual
                                    </button>
                                    <button
                                        onClick={() => handleModeSwitch('iot')}
                                        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold transition-all ${inputMode === 'iot' ? 'bg-organic-green-600 text-white shadow-sm' : 'text-slate-500 hover:text-slate-700'
                                            }`}
                                    >
                                        <Wifi size={12} /> IoT
                                    </button>
                                </div>
                            </div>

                            {/* IoT Status Banner */}
                            {inputMode === 'iot' && (
                                <div className={`mb-4 p-3 rounded-xl text-xs font-bold flex items-center justify-between ${iotLoading ? 'bg-amber-50 dark:bg-amber-500/10 text-amber-600 border border-amber-200 dark:border-amber-500/20' :
                                        iotStatus === 'success' ? 'bg-green-50 dark:bg-green-500/10 text-green-700 border border-green-200 dark:border-green-500/20' :
                                            iotStatus === 'error' ? 'bg-red-50 dark:bg-red-500/10 text-red-600 border border-red-200 dark:border-red-500/20' :
                                                'bg-slate-50 dark:bg-slate-800 text-slate-500 border border-slate-200 dark:border-slate-700'
                                    }`}>
                                    <span className="flex items-center gap-2">
                                        {iotLoading ? (
                                            <><Loader2 size={12} className="animate-spin" /> Fetching sensor data...</>
                                        ) : iotStatus === 'success' ? (
                                            <><Wifi size={12} /> Live sensor data loaded</>
                                        ) : iotStatus === 'error' ? (
                                            <><WifiOff size={12} /> Sensor offline — using last values</>
                                        ) : (
                                            <><Wifi size={12} /> Connecting to sensors...</>
                                        )}
                                    </span>
                                    {inputMode === 'iot' && !iotLoading && (
                                        <button onClick={fetchIoTData} className="p-1 hover:bg-white/50 dark:hover:bg-slate-700 rounded transition-colors" title="Refresh IoT data">
                                            <RefreshCw size={12} />
                                        </button>
                                    )}
                                </div>
                            )}

                            {/* IoT Raw Data Display */}
                            {inputMode === 'iot' && iotRaw && iotStatus === 'success' && (
                                <div className="mb-4 bg-green-50 dark:bg-green-500/5 rounded-xl p-3 border border-green-100 dark:border-green-500/10">
                                    <p className="text-[10px] font-black uppercase text-green-600 dark:text-green-400 mb-2">Raw Readings</p>
                                    <div className="grid grid-cols-2 gap-x-4 gap-y-2 text-[11px]">
                                        <div className="flex justify-between border-b border-green-500/10 pb-1"><span className="text-slate-500">Moist:</span> <span className="font-bold">{iotRaw.soil_moisture}%</span></div>
                                        <div className="flex justify-between border-b border-green-500/10 pb-1"><span className="text-slate-500">N:</span> <span className="font-bold">{iotRaw.nitrogen_mg_kg}</span></div>
                                        <div className="flex justify-between border-b border-green-500/10 pb-1"><span className="text-slate-500">Temp:</span> <span className="font-bold">{iotRaw.temperature_c}°</span></div>
                                        <div className="flex justify-between border-b border-green-500/10 pb-1"><span className="text-slate-500">pH:</span> <span className="font-bold">{iotRaw.ph}</span></div>
                                    </div>
                                </div>
                            )}

                            <div className="space-y-6">
                                <div className="space-y-2">
                                    <label className="text-xs font-black uppercase text-slate-500 tracking-wider">Soil Profile</label>
                                    <select name="soil_type" value={formData.soil_type} onChange={handleSelectChange} className="w-full bg-slate-100 dark:bg-slate-800 p-4 rounded-xl font-bold outline-none border border-transparent focus:border-organic-green-500 transition-all">
                                        {soilTypes.map(soil => <option key={soil} value={soil}>{soil}</option>)}
                                    </select>
                                </div>
                                {Object.entries(inputStats).map(([name, config]) => (
                                    <div key={name}>
                                        <div className="flex justify-between mb-2 text-xs font-black uppercase text-slate-500 tracking-wider">
                                            <label className="flex items-center gap-2"><config.icon size={14} className="text-organic-green-500" />{config.label}</label>
                                            <span className="text-organic-green-600 dark:text-organic-green-400 font-mono">{formData[name].toFixed(name === 'ndvi' ? 2 : 0)}{config.unit}</span>
                                        </div>
                                        <input
                                            type="range" name={name} min={config.min} max={config.max} step={name === 'ndvi' ? 0.01 : 1}
                                            value={formData[name]} onChange={handleChange}
                                            disabled={inputMode === 'iot'}
                                            className={`w-full h-2 rounded-lg appearance-none bg-slate-100 dark:bg-slate-800 cursor-pointer accent-organic-green-600 ${inputMode === 'iot' ? 'opacity-40' : ''}`}
                                        />
                                    </div>
                                ))}
                            </div>
                            <button onClick={handlePredict} disabled={loading} className="mt-10 w-full py-4 bg-organic-green-600 hover:bg-organic-green-700 text-white rounded-2xl font-black shadow-lg shadow-organic-green-600/20 active:scale-[0.98] transition-all disabled:opacity-50">
                                {loading ? "Analyzing Environment..." : "Predict Harvest Outcomes"}
                            </button>
                        </div>
                    </div>

                    {/* Results Panel */}
                    <div className="xl:col-span-8">
                        <AnimatePresence mode="wait">
                            {!result ? (
                                <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }} className="h-full min-h-[500px] flex flex-col items-center justify-center p-12 bg-white dark:bg-slate-900 rounded-[3rem] border-2 border-dashed border-slate-200 dark:border-slate-800">
                                    <Leaf size={48} className="text-organic-green-500 mb-6 animate-bounce" />
                                    <h3 className="text-2xl font-black mb-2">Ready to Predict</h3>
                                    <p className="text-slate-500 text-center">
                                        {inputMode === 'iot'
                                            ? 'IoT sensors loaded. Click predict to get AI recommendations.'
                                            : 'Adjust telemetry sliders and click predict to see crop recommendations.'
                                        }
                                    </p>
                                </motion.div>
                            ) : activeTab === 'top3' ? (
                                <motion.div key={`top3-${predictionCount}`} initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }} className="space-y-6">
                                    {result.top_3_crops.map((crop, idx) => (
                                        <motion.div
                                            key={idx}
                                            initial={{ x: 20, opacity: 0 }}
                                            animate={{ x: 0, opacity: 1 }}
                                            transition={{ delay: idx * 0.08 }}
                                            onClick={() => handleCropClick(crop)}
                                            className={`p-8 rounded-[2.5rem] border transition-all cursor-pointer group
                                                ${selectedCrop?.crop === crop.crop
                                                    ? 'ring-2 ring-organic-green-500 bg-organic-green-700 text-white shadow-2xl shadow-organic-green-600/20'
                                                    : idx === 0
                                                        ? 'bg-organic-green-600 text-white shadow-2xl shadow-organic-green-600/20 hover:shadow-organic-green-600/30'
                                                        : 'bg-white dark:bg-slate-900 border-slate-100 dark:border-slate-800 hover:border-organic-green-300 dark:hover:border-organic-green-500/30'
                                                }`}
                                        >
                                            <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4">
                                                <div className="flex items-center gap-6">
                                                    <div className="text-5xl font-black opacity-20 italic select-none">#0{idx + 1}</div>
                                                    <div>
                                                        <div className="flex items-center gap-2">
                                                            <h4 className="text-3xl font-black tracking-tight">{crop.crop}</h4>
                                                            <Sparkles size={16} className={`opacity-0 group-hover:opacity-100 transition-opacity ${selectedCrop?.crop === crop.crop || idx === 0 ? 'text-yellow-300' : 'text-organic-green-400'}`} />
                                                        </div>
                                                        <div className={`text-sm font-bold mt-1 ${selectedCrop?.crop === crop.crop || idx === 0 ? 'opacity-70' : 'text-slate-500'}`}>
                                                            Est: {crop.yield_tons_ha} Tons/Ha &nbsp;|&nbsp; Mandi: ₹{crop.mandi_price_quintal}/Qtl
                                                        </div>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-4">
                                                    <div className="text-right">
                                                        <div className={`text-4xl font-black ${(selectedCrop?.crop !== crop.crop && idx !== 0)
                                                                ? (crop.profit_margin_pct < 0 ? 'text-red-500' : 'text-organic-green-600 dark:text-organic-green-400')
                                                                : ''
                                                            }`}>
                                                            {crop.profit_margin_pct > 0 ? '+' : ''}{crop.profit_margin_pct}%
                                                        </div>
                                                        <div className={`text-sm font-bold ${selectedCrop?.crop === crop.crop || idx === 0 ? 'opacity-60' : 'text-slate-400'}`}>ROI</div>
                                                    </div>
                                                    <ChevronRight size={20} className={`opacity-40 group-hover:opacity-100 transition-opacity ${selectedCrop?.crop === crop.crop || idx === 0 ? 'text-white' : 'text-organic-green-400'}`} />
                                                </div>
                                            </div>
                                            {idx === 0 && !selectedCrop && (
                                                <div className="mt-5 pt-5 border-t border-white/20 flex flex-wrap gap-6 text-sm font-semibold opacity-80">
                                                    <span>Revenue: ₹{crop.revenue_ha?.toLocaleString('en-IN')}/ha</span>
                                                    <span>Cost: ₹{crop.cost_ha?.toLocaleString('en-IN')}/ha</span>
                                                    <span>Profit: ₹{crop.profit_ha?.toLocaleString('en-IN')}/ha</span>
                                                </div>
                                            )}
                                        </motion.div>
                                    ))}

                                    <p className="text-center text-xs text-slate-400 font-medium">Click any crop for AI-powered insights</p>

                                    {/* Gemini Insights Panel */}
                                    <AnimatePresence>
                                        {selectedCrop && (
                                            <motion.div
                                                initial={{ opacity: 0, y: 20, height: 0 }}
                                                animate={{ opacity: 1, y: 0, height: 'auto' }}
                                                exit={{ opacity: 0, y: 20, height: 0 }}
                                                className="bg-white dark:bg-slate-900 rounded-3xl border border-organic-green-200 dark:border-organic-green-500/30 overflow-hidden shadow-lg"
                                            >
                                                <div className="p-8">
                                                    <div className="flex justify-between items-start mb-6">
                                                        <div className="flex items-center gap-3">
                                                            <div className="p-2 bg-organic-green-100 dark:bg-organic-green-500/20 rounded-xl">
                                                                <Sparkles size={20} className="text-organic-green-600" />
                                                            </div>
                                                            <div>
                                                                <h3 className="text-xl font-black">{selectedCrop.crop} — AI Insights</h3>

                                                            </div>
                                                        </div>
                                                        <button onClick={() => { setSelectedCrop(null); setInsights(null); }} className="p-2 hover:bg-slate-100 dark:hover:bg-slate-800 rounded-lg transition-colors">
                                                            <X size={18} className="text-slate-400" />
                                                        </button>
                                                    </div>

                                                    {insightsLoading ? (
                                                        <div className="flex flex-col items-center justify-center py-12 gap-3">
                                                            <Loader2 size={32} className="text-organic-green-500 animate-spin" />
                                                            <p className="text-slate-400 text-sm font-medium">Generating insights...</p>
                                                        </div>
                                                    ) : insights ? (
                                                        <div className="space-y-6">
                                                            <div className="bg-green-50 dark:bg-green-500/10 p-5 rounded-2xl border border-green-100 dark:border-green-500/20">
                                                                <div className="flex items-center gap-2 mb-2">
                                                                    <TrendingUp size={16} className="text-organic-green-600" />
                                                                    <h4 className="font-black text-sm uppercase text-organic-green-700 dark:text-organic-green-400">ROI Explanation</h4>
                                                                </div>
                                                                <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">{insights.roi_explanation}</p>
                                                            </div>

                                                            <div className="bg-amber-50 dark:bg-amber-500/10 p-5 rounded-2xl border border-amber-100 dark:border-amber-500/20">
                                                                <div className="flex items-center gap-2 mb-2">
                                                                    <BarChart3 size={16} className="text-amber-500" />
                                                                    <h4 className="font-black text-sm uppercase text-amber-600 dark:text-amber-400">Market Conditions</h4>
                                                                </div>
                                                                <p className="text-slate-700 dark:text-slate-300 text-sm leading-relaxed">{insights.market_conditions}</p>
                                                            </div>

                                                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                                                                {insights.maximize_tips?.length > 0 && (
                                                                    <div className="bg-emerald-50 dark:bg-emerald-500/10 p-5 rounded-2xl border border-emerald-100 dark:border-emerald-500/20">
                                                                        <div className="flex items-center gap-2 mb-3">
                                                                            <Target size={16} className="text-emerald-500" />
                                                                            <h4 className="font-black text-sm uppercase text-emerald-600 dark:text-emerald-400">How to Maximize</h4>
                                                                        </div>
                                                                        <ul className="space-y-2">
                                                                            {insights.maximize_tips.map((tip, i) => (
                                                                                <li key={i} className="text-sm text-slate-700 dark:text-slate-300 flex items-start gap-2">
                                                                                    <span className="text-emerald-500 font-bold mt-0.5">•</span> {tip}
                                                                                </li>
                                                                            ))}
                                                                        </ul>
                                                                    </div>
                                                                )}
                                                                {insights.risks?.length > 0 && (
                                                                    <div className="bg-rose-50 dark:bg-rose-500/10 p-5 rounded-2xl border border-rose-100 dark:border-rose-500/20">
                                                                        <div className="flex items-center gap-2 mb-3">
                                                                            <AlertTriangle size={16} className="text-rose-500" />
                                                                            <h4 className="font-black text-sm uppercase text-rose-600 dark:text-rose-400">Risks to Watch</h4>
                                                                        </div>
                                                                        <ul className="space-y-2">
                                                                            {insights.risks.map((risk, i) => (
                                                                                <li key={i} className="text-sm text-slate-700 dark:text-slate-300 flex items-start gap-2">
                                                                                    <span className="text-rose-500 font-bold mt-0.5">•</span> {risk}
                                                                                </li>
                                                                            ))}
                                                                        </ul>
                                                                    </div>
                                                                )}
                                                            </div>

                                                            <div className="flex flex-wrap gap-4">
                                                                {insights.best_season && (
                                                                    <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded-xl">
                                                                        <Calendar size={14} className="text-organic-green-600" />
                                                                        <span className="text-xs font-bold text-slate-600 dark:text-slate-300">{insights.best_season}</span>
                                                                    </div>
                                                                )}
                                                                {insights.confidence_note && (
                                                                    <div className="flex items-center gap-2 bg-slate-100 dark:bg-slate-800 px-4 py-2 rounded-xl">
                                                                        <ShieldCheck size={14} className="text-emerald-500" />
                                                                        <span className="text-xs font-bold text-slate-600 dark:text-slate-300">{insights.confidence_note}</span>
                                                                    </div>
                                                                )}
                                                            </div>
                                                        </div>
                                                    ) : null}
                                                </div>
                                            </motion.div>
                                        )}
                                    </AnimatePresence>
                                </motion.div>
                            ) : (
                                <motion.div key="analysis" initial={{ opacity: 0, y: 30 }} animate={{ opacity: 1, y: 0 }} className="bg-white dark:bg-slate-900 rounded-[3rem] p-8 border border-slate-200 dark:border-slate-800 h-full">
                                    <h3 className="text-2xl font-black mb-8">ROI Comparison</h3>
                                    {chartData.length > 0 ? (
                                        <div className="h-[400px]">
                                            <ResponsiveContainer width="100%" height="100%">
                                                <BarChart data={chartData} layout="vertical">
                                                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" opacity={0.3} horizontal={false} />
                                                    <XAxis type="number" axisLine={false} tickLine={false} tick={{ fontSize: 10 }} tickFormatter={(v) => `${v}%`} />
                                                    <YAxis dataKey="name" type="category" axisLine={false} tickLine={false} tick={{ fontSize: 11, fontWeight: 900 }} width={100} />
                                                    <Tooltip
                                                        contentStyle={{ borderRadius: '12px', border: 'none', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                                                        formatter={(value) => [`${value}%`, 'ROI']}
                                                    />
                                                    <Bar dataKey="roi" radius={[0, 10, 10, 0]} barSize={28}>
                                                        {chartData.map((entry, i) => (
                                                            <Cell key={i} fill={entry.roi < 0 ? '#f87171' : (i === 0 ? '#16a34a' : i < 3 ? '#86efac' : '#e2e8f0')} />
                                                        ))}
                                                    </Bar>
                                                </BarChart>
                                            </ResponsiveContainer>
                                        </div>
                                    ) : (
                                        <div className="h-full flex flex-col items-center justify-center text-slate-400">
                                            <Activity className="animate-pulse mb-4" />
                                            <p>Run a prediction first to see analysis.</p>
                                        </div>
                                    )}
                                    {result && (
                                        <div className="mt-8 bg-green-50 dark:bg-green-500/5 p-6 rounded-2xl border border-green-100 dark:border-green-500/10 text-slate-600 dark:text-slate-400 font-medium text-sm">
                                            Top {chartData.length} crops sorted by ROI for <strong>{formData.soil_type}</strong> soil.
                                            Best ROI: <strong className="text-organic-green-600">{result.top_3_crops[0]?.crop}</strong> at {result.top_3_crops[0]?.profit_margin_pct}%.
                                        </div>
                                    )}
                                </motion.div>
                            )}
                        </AnimatePresence>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default CropYieldPrediction;
