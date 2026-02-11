import React, { useState } from 'react';

// ==========================================
// SINGLE BOREHOLE PROFILE VIEWER
// Black & White Theme
// Geotechnical Engineering Workflow Platform
// ==========================================

// Soil type configurations - Black & White theme with distinct patterns
const SOIL_TYPES = {
  fill: { name: 'Fill', color: '#666666', pattern: 'dots-bw', textColor: '#fff' },
  topsoil: { name: 'Topsoil', color: '#333333', pattern: 'organic-bw', textColor: '#fff' },
  soft_clay: { name: 'Soft Clay', color: '#CCCCCC', pattern: 'horizontal-bw', textColor: '#000' },
  medium_clay: { name: 'Medium Clay', color: '#999999', pattern: 'horizontal-dense-bw', textColor: '#fff' },
  stiff_clay: { name: 'Stiff Clay', color: '#555555', pattern: 'horizontal-thick-bw', textColor: '#fff' },
  loose_sand: { name: 'Loose Sand', color: '#F5F5F5', pattern: 'stipple-bw', textColor: '#000' },
  medium_sand: { name: 'Medium Sand', color: '#E0E0E0', pattern: 'stipple-dense-bw', textColor: '#000' },
  dense_sand: { name: 'Dense Sand', color: '#BDBDBD', pattern: 'stipple-heavy-bw', textColor: '#000' },
  gravel: { name: 'Gravel', color: '#888888', pattern: 'circles-bw', textColor: '#fff' },
  rock: { name: 'Rock', color: '#222222', pattern: 'diagonal-bw', textColor: '#fff' },
};

// Default sample data
const DEFAULT_LAYERS = [
  { id: 1, soilType: 'fill', depthFrom: 0, depthTo: 1.5, nValue: 5, description: 'Brown fill with brick fragments' },
  { id: 2, soilType: 'soft_clay', depthFrom: 1.5, depthTo: 6.0, nValue: 3, description: 'Grey soft clay, high plasticity' },
  { id: 3, soilType: 'medium_clay', depthFrom: 6.0, depthTo: 12.0, nValue: 12, description: 'Grey medium stiff clay' },
  { id: 4, soilType: 'dense_sand', depthFrom: 12.0, depthTo: 18.0, nValue: 35, description: 'Yellow-brown dense sand' },
  { id: 5, soilType: 'gravel', depthFrom: 18.0, depthTo: 22.0, nValue: 50, description: 'Sandy gravel, well graded' },
];

// SVG Pattern definitions for soil types - Black & White
const SoilPatterns = () => (
  <defs>
    {/* Dots pattern for Fill */}
    <pattern id="pattern-dots-bw" patternUnits="userSpaceOnUse" width="8" height="8">
      <rect width="8" height="8" fill="#666666" />
      <circle cx="4" cy="4" r="1.5" fill="#fff" />
    </pattern>
    
    {/* Horizontal lines for Soft Clay - sparse */}
    <pattern id="pattern-horizontal-bw" patternUnits="userSpaceOnUse" width="10" height="8">
      <rect width="10" height="8" fill="#CCCCCC" />
      <line x1="0" y1="4" x2="10" y2="4" stroke="#000" strokeWidth="1" />
    </pattern>
    
    {/* Horizontal lines for Medium Clay - dense */}
    <pattern id="pattern-horizontal-dense-bw" patternUnits="userSpaceOnUse" width="10" height="6">
      <rect width="10" height="6" fill="#999999" />
      <line x1="0" y1="3" x2="10" y2="3" stroke="#000" strokeWidth="1" />
    </pattern>
    
    {/* Horizontal lines for Stiff Clay - thick */}
    <pattern id="pattern-horizontal-thick-bw" patternUnits="userSpaceOnUse" width="10" height="5">
      <rect width="10" height="5" fill="#555555" />
      <line x1="0" y1="2.5" x2="10" y2="2.5" stroke="#fff" strokeWidth="1.5" />
    </pattern>
    
    {/* Stipple for Loose Sand */}
    <pattern id="pattern-stipple-bw" patternUnits="userSpaceOnUse" width="12" height="12">
      <rect width="12" height="12" fill="#F5F5F5" />
      <circle cx="2" cy="2" r="1" fill="#000" />
      <circle cx="8" cy="6" r="1" fill="#000" />
      <circle cx="4" cy="10" r="1" fill="#000" />
    </pattern>
    
    {/* Stipple for Medium Sand - denser */}
    <pattern id="pattern-stipple-dense-bw" patternUnits="userSpaceOnUse" width="10" height="10">
      <rect width="10" height="10" fill="#E0E0E0" />
      <circle cx="2" cy="2" r="1" fill="#000" />
      <circle cx="7" cy="3" r="1" fill="#000" />
      <circle cx="4" cy="6" r="1" fill="#000" />
      <circle cx="8" cy="8" r="1" fill="#000" />
    </pattern>
    
    {/* Stipple for Dense Sand - heavy */}
    <pattern id="pattern-stipple-heavy-bw" patternUnits="userSpaceOnUse" width="8" height="8">
      <rect width="8" height="8" fill="#BDBDBD" />
      <circle cx="2" cy="2" r="1.2" fill="#000" />
      <circle cx="6" cy="2" r="1.2" fill="#000" />
      <circle cx="4" cy="5" r="1.2" fill="#000" />
      <circle cx="2" cy="7" r="1.2" fill="#000" />
      <circle cx="6" cy="7" r="1.2" fill="#000" />
    </pattern>
    
    {/* Circles for Gravel */}
    <pattern id="pattern-circles-bw" patternUnits="userSpaceOnUse" width="16" height="16">
      <rect width="16" height="16" fill="#888888" />
      <circle cx="4" cy="4" r="3" fill="none" stroke="#000" strokeWidth="1.5" />
      <circle cx="12" cy="12" r="3" fill="none" stroke="#000" strokeWidth="1.5" />
      <circle cx="12" cy="4" r="2" fill="#000" />
      <circle cx="4" cy="12" r="2" fill="#000" />
    </pattern>
    
    {/* Diagonal lines for Rock */}
    <pattern id="pattern-diagonal-bw" patternUnits="userSpaceOnUse" width="8" height="8">
      <rect width="8" height="8" fill="#222222" />
      <path d="M0,8 L8,0" stroke="#fff" strokeWidth="1.5" />
      <path d="M-2,2 L2,-2" stroke="#fff" strokeWidth="1.5" />
      <path d="M6,10 L10,6" stroke="#fff" strokeWidth="1.5" />
    </pattern>
    
    {/* Organic pattern for Topsoil */}
    <pattern id="pattern-organic-bw" patternUnits="userSpaceOnUse" width="20" height="12">
      <rect width="20" height="12" fill="#333333" />
      <path d="M0,6 Q5,2 10,6 T20,6" fill="none" stroke="#fff" strokeWidth="1" />
      <circle cx="3" cy="9" r="1" fill="#fff" />
      <circle cx="15" cy="3" r="1" fill="#fff" />
    </pattern>
    
    {/* Water pattern */}
    <pattern id="pattern-water-bw" patternUnits="userSpaceOnUse" width="20" height="8">
      <path d="M0,4 Q5,1 10,4 T20,4" fill="none" stroke="#000" strokeWidth="1.5" />
    </pattern>
  </defs>
);

// Single soil layer component
const SoilLayer = ({ layer, yStart, height, width, scale, onHover, isHovered }) => {
  const soilConfig = SOIL_TYPES[layer.soilType];
  const patternId = `pattern-${soilConfig.pattern}`;
  
  return (
    <g 
      onMouseEnter={() => onHover(layer)}
      onMouseLeave={() => onHover(null)}
      style={{ cursor: 'pointer' }}
    >
      {/* Pattern fill */}
      <rect
        x={60}
        y={yStart}
        width={width}
        height={height}
        fill={`url(#${patternId})`}
        stroke={isHovered ? '#000' : '#333'}
        strokeWidth={isHovered ? 3 : 1}
        style={{ transition: 'all 0.2s ease' }}
      />
      
      {/* Depth labels */}
      <text x={52} y={yStart + 4} textAnchor="end" fontSize="11" fill="#333" fontFamily="'Courier New', monospace" fontWeight="600">
        {layer.depthFrom.toFixed(1)}m
      </text>
      <text x={52} y={yStart + height} textAnchor="end" fontSize="11" fill="#333" fontFamily="'Courier New', monospace" fontWeight="600">
        {layer.depthTo.toFixed(1)}m
      </text>
      
      {/* Soil type label (if layer is thick enough) */}
      {height > 30 && (
        <text 
          x={60 + width / 2} 
          y={yStart + height / 2 + 4} 
          textAnchor="middle" 
          fontSize="12" 
          fill={soilConfig.textColor}
          fontWeight="700"
          fontFamily="'Arial', sans-serif"
          style={{ textShadow: soilConfig.textColor === '#fff' ? '0 1px 2px rgba(0,0,0,0.8)' : '0 1px 2px rgba(255,255,255,0.8)' }}
        >
          {soilConfig.name}
        </text>
      )}
      
      {/* N-value on right side */}
      <text 
        x={60 + width + 8} 
        y={yStart + height / 2 + 4} 
        fontSize="11" 
        fill="#333"
        fontFamily="'Courier New', monospace"
        fontWeight="600"
      >
        N={layer.nValue}
      </text>
    </g>
  );
};

// Water table indicator
const WaterTable = ({ depth, scale, width }) => {
  const y = 60 + depth * scale;
  
  return (
    <g>
      <line 
        x1={40} 
        y1={y} 
        x2={60 + width + 40} 
        y2={y} 
        stroke="#000" 
        strokeWidth="2" 
        strokeDasharray="10,5"
      />
      <text x={60 + width + 45} y={y + 4} fontSize="11" fill="#000" fontFamily="'Arial', sans-serif" fontWeight="700">
        GWL
      </text>
      {/* Water symbol - inverted triangle */}
      <polygon 
        points={`${28},${y-12} ${22},${y+2} ${34},${y+2}`}
        fill="#000"
      />
    </g>
  );
};

// Tooltip component - B&W theme
const Tooltip = ({ layer, position }) => {
  if (!layer) return null;
  
  const soilConfig = SOIL_TYPES[layer.soilType];
  
  return (
    <div 
      style={{
        position: 'absolute',
        left: position.x + 20,
        top: position.y - 10,
        background: '#fff',
        border: '2px solid #000',
        borderRadius: '4px',
        padding: '12px 16px',
        boxShadow: '4px 4px 0 #000',
        zIndex: 100,
        minWidth: '220px',
        fontFamily: "'Arial', sans-serif",
      }}
    >
      <div style={{ 
        display: 'flex', 
        alignItems: 'center', 
        gap: '8px',
        marginBottom: '8px',
        paddingBottom: '8px',
        borderBottom: '1px solid #ccc'
      }}>
        <svg width="20" height="20">
          <defs>
            <pattern id={`tooltip-${soilConfig.pattern}`} patternUnits="userSpaceOnUse" width="8" height="8">
              <rect width="8" height="8" fill={soilConfig.color} />
            </pattern>
          </defs>
          <rect 
            width="20" 
            height="20" 
            fill={`url(#pattern-${soilConfig.pattern})`}
            stroke="#000"
            strokeWidth="1"
          />
        </svg>
        <span style={{ color: '#000', fontWeight: '700', fontSize: '14px' }}>
          {soilConfig.name}
        </span>
      </div>
      
      <div style={{ display: 'grid', gap: '6px', fontSize: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#666' }}>Depth:</span>
          <span style={{ color: '#000', fontFamily: "'Courier New', monospace", fontWeight: '600' }}>
            {layer.depthFrom.toFixed(1)} - {layer.depthTo.toFixed(1)} m
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#666' }}>Thickness:</span>
          <span style={{ color: '#000', fontFamily: "'Courier New', monospace", fontWeight: '600' }}>
            {(layer.depthTo - layer.depthFrom).toFixed(1)} m
          </span>
        </div>
        <div style={{ display: 'flex', justifyContent: 'space-between' }}>
          <span style={{ color: '#666' }}>SPT N-value:</span>
          <span style={{ color: '#000', fontWeight: '700', fontFamily: "'Courier New', monospace" }}>
            {layer.nValue}
          </span>
        </div>
        <div style={{ marginTop: '4px', color: '#555', fontStyle: 'italic', fontSize: '11px' }}>
          {layer.description}
        </div>
      </div>
    </div>
  );
};

// Layer input form row
const LayerInputRow = ({ layer, index, onUpdate, onDelete }) => (
  <div style={{
    display: 'grid',
    gridTemplateColumns: '40px 120px 70px 70px 60px 1fr 40px',
    gap: '8px',
    alignItems: 'center',
    padding: '8px 12px',
    background: index % 2 === 0 ? '#f5f5f5' : '#fff',
    borderRadius: '4px',
    border: '1px solid #ddd',
  }}>
    <span style={{ color: '#666', fontSize: '12px', fontFamily: "'Courier New', monospace", fontWeight: '600' }}>
      #{index + 1}
    </span>
    
    <select
      value={layer.soilType}
      onChange={(e) => onUpdate(layer.id, 'soilType', e.target.value)}
      style={{
        background: '#fff',
        border: '2px solid #333',
        borderRadius: '4px',
        color: '#000',
        padding: '6px 8px',
        fontSize: '12px',
        cursor: 'pointer',
        fontWeight: '600',
      }}
    >
      {Object.entries(SOIL_TYPES).map(([key, config]) => (
        <option key={key} value={key}>{config.name}</option>
      ))}
    </select>
    
    <input
      type="number"
      value={layer.depthFrom}
      onChange={(e) => onUpdate(layer.id, 'depthFrom', parseFloat(e.target.value) || 0)}
      step="0.5"
      style={{
        background: '#fff',
        border: '2px solid #333',
        borderRadius: '4px',
        color: '#000',
        padding: '6px 8px',
        fontSize: '12px',
        fontFamily: "'Courier New', monospace",
        width: '100%',
        fontWeight: '600',
      }}
    />
    
    <input
      type="number"
      value={layer.depthTo}
      onChange={(e) => onUpdate(layer.id, 'depthTo', parseFloat(e.target.value) || 0)}
      step="0.5"
      style={{
        background: '#fff',
        border: '2px solid #333',
        borderRadius: '4px',
        color: '#000',
        padding: '6px 8px',
        fontSize: '12px',
        fontFamily: "'Courier New', monospace",
        width: '100%',
        fontWeight: '600',
      }}
    />
    
    <input
      type="number"
      value={layer.nValue}
      onChange={(e) => onUpdate(layer.id, 'nValue', parseInt(e.target.value) || 0)}
      style={{
        background: '#fff',
        border: '2px solid #333',
        borderRadius: '4px',
        color: '#000',
        padding: '6px 8px',
        fontSize: '12px',
        fontFamily: "'Courier New', monospace",
        width: '100%',
        fontWeight: '700',
      }}
    />
    
    <input
      type="text"
      value={layer.description}
      onChange={(e) => onUpdate(layer.id, 'description', e.target.value)}
      placeholder="Description..."
      style={{
        background: '#fff',
        border: '2px solid #333',
        borderRadius: '4px',
        color: '#333',
        padding: '6px 8px',
        fontSize: '12px',
        width: '100%',
      }}
    />
    
    <button
      onClick={() => onDelete(layer.id)}
      style={{
        background: '#000',
        border: 'none',
        color: '#fff',
        cursor: 'pointer',
        padding: '6px 10px',
        borderRadius: '4px',
        fontWeight: '700',
        fontSize: '14px',
      }}
    >
      ✕
    </button>
  </div>
);

// Legend item with SVG pattern
const LegendItem = ({ soilKey, config }) => (
  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
    <svg width="24" height="24">
      <rect
        width="24"
        height="24"
        fill={`url(#pattern-${config.pattern})`}
        stroke="#000"
        strokeWidth="1"
      />
    </svg>
    <span style={{ fontSize: '11px', color: '#333', fontWeight: '500' }}>{config.name}</span>
  </div>
);

// Main component
export default function BoreholeProfileViewer() {
  const [layers, setLayers] = useState(DEFAULT_LAYERS);
  const [waterTableDepth, setWaterTableDepth] = useState(2.5);
  const [showWaterTable, setShowWaterTable] = useState(true);
  const [hoveredLayer, setHoveredLayer] = useState(null);
  const [mousePos, setMousePos] = useState({ x: 0, y: 0 });
  const [boreholeId, setBoreholeId] = useState('BH-01');
  const [scale, setScale] = useState(25); // pixels per meter
  
  // Calculate total depth and SVG dimensions
  const maxDepth = Math.max(...layers.map(l => l.depthTo), 0);
  const svgHeight = 60 + maxDepth * scale + 40;
  const profileWidth = 150;
  
  // Update layer property
  const updateLayer = (id, field, value) => {
    setLayers(prev => prev.map(layer => 
      layer.id === id ? { ...layer, [field]: value } : layer
    ));
  };
  
  // Add new layer
  const addLayer = () => {
    const lastLayer = layers[layers.length - 1];
    const newDepthFrom = lastLayer ? lastLayer.depthTo : 0;
    setLayers(prev => [...prev, {
      id: Date.now(),
      soilType: 'medium_clay',
      depthFrom: newDepthFrom,
      depthTo: newDepthFrom + 3,
      nValue: 10,
      description: 'New layer',
    }]);
  };
  
  // Delete layer
  const deleteLayer = (id) => {
    if (layers.length > 1) {
      setLayers(prev => prev.filter(layer => layer.id !== id));
    }
  };
  
  // Handle mouse move for tooltip
  const handleMouseMove = (e) => {
    const rect = e.currentTarget.getBoundingClientRect();
    setMousePos({
      x: e.clientX - rect.left,
      y: e.clientY - rect.top,
    });
  };
  
  return (
    <div style={{
      minHeight: '100vh',
      background: '#ffffff',
      padding: '24px',
      fontFamily: "'Arial', sans-serif",
      color: '#000',
    }}>
      {/* Header */}
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto 24px',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        borderBottom: '3px solid #000',
        paddingBottom: '16px',
      }}>
        <div>
          <h1 style={{
            fontSize: '28px',
            fontWeight: '900',
            margin: 0,
            color: '#000',
            letterSpacing: '-0.5px',
            textTransform: 'uppercase',
          }}>
            Borehole Profile Viewer
          </h1>
          <p style={{ color: '#666', margin: '4px 0 0', fontSize: '14px' }}>
            Interactive soil stratigraphy visualization
          </p>
        </div>
        
        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
          <div style={{
            background: '#fff',
            border: '2px solid #000',
            borderRadius: '4px',
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <span style={{ color: '#666', fontSize: '12px', fontWeight: '600' }}>ID:</span>
            <input
              type="text"
              value={boreholeId}
              onChange={(e) => setBoreholeId(e.target.value)}
              style={{
                background: 'transparent',
                border: 'none',
                color: '#000',
                fontSize: '14px',
                fontWeight: '900',
                fontFamily: "'Courier New', monospace",
                width: '80px',
              }}
            />
          </div>
          
          <div style={{
            background: '#fff',
            border: '2px solid #000',
            borderRadius: '4px',
            padding: '8px 16px',
            display: 'flex',
            alignItems: 'center',
            gap: '8px',
          }}>
            <span style={{ color: '#666', fontSize: '12px', fontWeight: '600' }}>Scale:</span>
            <input
              type="range"
              min="15"
              max="40"
              value={scale}
              onChange={(e) => setScale(parseInt(e.target.value))}
              style={{ width: '80px', accentColor: '#000' }}
            />
            <span style={{ color: '#000', fontSize: '12px', fontFamily: "'Courier New', monospace", fontWeight: '700' }}>
              1:{(100/scale).toFixed(0)}
            </span>
          </div>
        </div>
      </div>
      
      {/* Main content */}
      <div style={{
        maxWidth: '1400px',
        margin: '0 auto',
        display: 'grid',
        gridTemplateColumns: '320px 1fr',
        gap: '24px',
      }}>
        {/* Profile visualization */}
        <div 
          style={{
            background: '#fff',
            borderRadius: '4px',
            border: '2px solid #000',
            padding: '20px',
            position: 'relative',
          }}
          onMouseMove={handleMouseMove}
        >
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            marginBottom: '16px',
            padding: '8px 16px',
            background: '#000',
            borderRadius: '4px',
          }}>
            <span style={{ 
              color: '#fff', 
              fontWeight: '900', 
              fontSize: '16px',
              fontFamily: "'Courier New', monospace",
              letterSpacing: '2px',
            }}>
              {boreholeId}
            </span>
          </div>
          
          <svg width="100%" height={svgHeight} viewBox={`0 0 280 ${svgHeight}`}>
            <SoilPatterns />
            
            {/* Scale bar */}
            <g>
              <line x1="20" y1="60" x2="20" y2={60 + maxDepth * scale} stroke="#000" strokeWidth="2" />
              {Array.from({ length: Math.ceil(maxDepth) + 1 }, (_, i) => (
                <g key={i}>
                  <line x1="12" y1={60 + i * scale} x2="28" y2={60 + i * scale} stroke="#000" strokeWidth="2" />
                </g>
              ))}
            </g>
            
            {/* Borehole column outline */}
            <rect
              x={60}
              y={58}
              width={profileWidth}
              height={maxDepth * scale + 4}
              fill="none"
              stroke="#000"
              strokeWidth="2"
            />
            
            {/* Soil layers */}
            {layers.map((layer) => (
              <SoilLayer
                key={layer.id}
                layer={layer}
                yStart={60 + layer.depthFrom * scale}
                height={(layer.depthTo - layer.depthFrom) * scale}
                width={profileWidth}
                scale={scale}
                onHover={setHoveredLayer}
                isHovered={hoveredLayer?.id === layer.id}
              />
            ))}
            
            {/* Water table */}
            {showWaterTable && (
              <WaterTable depth={waterTableDepth} scale={scale} width={profileWidth} />
            )}
            
            {/* Ground surface symbol */}
            <g>
              <line x1={55} y1={60} x2={65} y2={52} stroke="#000" strokeWidth="2" />
              <line x1={65} y1={52} x2={75} y2={60} stroke="#000" strokeWidth="2" />
              <line x1={75} y1={60} x2={85} y2={52} stroke="#000" strokeWidth="2" />
              <line x1={85} y1={52} x2={95} y2={60} stroke="#000" strokeWidth="2" />
            </g>
            
            {/* Column headers */}
            <text x={60 + profileWidth / 2} y={45} textAnchor="middle" fontSize="10" fill="#333" fontWeight="700">
              SOIL PROFILE
            </text>
            <text x={60 + profileWidth + 30} y={45} textAnchor="middle" fontSize="10" fill="#333" fontWeight="700">
              SPT-N
            </text>
          </svg>
          
          {/* Tooltip */}
          <Tooltip layer={hoveredLayer} position={mousePos} />
          
          {/* Water table control */}
          <div style={{
            marginTop: '16px',
            padding: '12px',
            background: '#f5f5f5',
            borderRadius: '4px',
            border: '2px solid #000',
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
              <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
                <input
                  type="checkbox"
                  checked={showWaterTable}
                  onChange={(e) => setShowWaterTable(e.target.checked)}
                  style={{ accentColor: '#000', width: '16px', height: '16px' }}
                />
                <span style={{ fontSize: '13px', color: '#333', fontWeight: '600' }}>Show GWL</span>
              </label>
            </div>
            {showWaterTable && (
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <span style={{ fontSize: '12px', color: '#666', fontWeight: '600' }}>Depth:</span>
                <input
                  type="number"
                  value={waterTableDepth}
                  onChange={(e) => setWaterTableDepth(parseFloat(e.target.value) || 0)}
                  step="0.5"
                  style={{
                    background: '#fff',
                    border: '2px solid #000',
                    borderRadius: '4px',
                    color: '#000',
                    padding: '4px 8px',
                    fontSize: '12px',
                    fontFamily: "'Courier New', monospace",
                    width: '60px',
                    fontWeight: '700',
                  }}
                />
                <span style={{ fontSize: '12px', color: '#666', fontWeight: '600' }}>m</span>
              </div>
            )}
          </div>
        </div>
        
        {/* Data input panel */}
        <div style={{
          background: '#fff',
          borderRadius: '4px',
          border: '2px solid #000',
          padding: '20px',
        }}>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            marginBottom: '16px',
          }}>
            <h2 style={{ fontSize: '16px', fontWeight: '900', margin: 0, color: '#000', textTransform: 'uppercase' }}>
              Layer Data
            </h2>
            <button
              onClick={addLayer}
              style={{
                background: '#000',
                border: 'none',
                borderRadius: '4px',
                color: '#fff',
                padding: '10px 20px',
                fontSize: '13px',
                fontWeight: '700',
                cursor: 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '6px',
                textTransform: 'uppercase',
              }}
            >
              <span style={{ fontSize: '16px' }}>+</span> Add Layer
            </button>
          </div>
          
          {/* Column headers */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: '40px 120px 70px 70px 60px 1fr 40px',
            gap: '8px',
            padding: '8px 12px',
            borderBottom: '2px solid #000',
            marginBottom: '8px',
          }}>
            <span style={{ fontSize: '11px', color: '#666', fontWeight: '700' }}>#</span>
            <span style={{ fontSize: '11px', color: '#666', fontWeight: '700' }}>SOIL TYPE</span>
            <span style={{ fontSize: '11px', color: '#666', fontWeight: '700' }}>FROM (m)</span>
            <span style={{ fontSize: '11px', color: '#666', fontWeight: '700' }}>TO (m)</span>
            <span style={{ fontSize: '11px', color: '#666', fontWeight: '700' }}>N-VALUE</span>
            <span style={{ fontSize: '11px', color: '#666', fontWeight: '700' }}>DESCRIPTION</span>
            <span></span>
          </div>
          
          {/* Layer rows */}
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {layers.map((layer, index) => (
              <LayerInputRow
                key={layer.id}
                layer={layer}
                index={index}
                onUpdate={updateLayer}
                onDelete={deleteLayer}
              />
            ))}
          </div>
          
          {/* Legend - Black & White with patterns */}
          <div style={{
            marginTop: '24px',
            padding: '16px',
            background: '#f9f9f9',
            borderRadius: '4px',
            border: '2px solid #000',
          }}>
            <h3 style={{ fontSize: '13px', fontWeight: '900', margin: '0 0 12px', color: '#000', textTransform: 'uppercase' }}>
              Soil Types Legend
            </h3>
            <svg width="0" height="0" style={{ position: 'absolute' }}>
              <SoilPatterns />
            </svg>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '10px' }}>
              {Object.entries(SOIL_TYPES).map(([key, config]) => (
                <LegendItem key={key} soilKey={key} config={config} />
              ))}
            </div>
          </div>
          
          {/* Summary stats */}
          <div style={{
            marginTop: '16px',
            display: 'grid',
            gridTemplateColumns: 'repeat(3, 1fr)',
            gap: '12px',
          }}>
            <div style={{
              background: '#fff',
              borderRadius: '4px',
              padding: '12px',
              textAlign: 'center',
              border: '2px solid #000',
            }}>
              <div style={{ fontSize: '24px', fontWeight: '900', color: '#000', fontFamily: "'Courier New', monospace" }}>
                {maxDepth.toFixed(1)}m
              </div>
              <div style={{ fontSize: '11px', color: '#666', marginTop: '2px', fontWeight: '600', textTransform: 'uppercase' }}>Total Depth</div>
            </div>
            <div style={{
              background: '#fff',
              borderRadius: '4px',
              padding: '12px',
              textAlign: 'center',
              border: '2px solid #000',
            }}>
              <div style={{ fontSize: '24px', fontWeight: '900', color: '#000', fontFamily: "'Courier New', monospace" }}>
                {layers.length}
              </div>
              <div style={{ fontSize: '11px', color: '#666', marginTop: '2px', fontWeight: '600', textTransform: 'uppercase' }}>Layers</div>
            </div>
            <div style={{
              background: '#000',
              borderRadius: '4px',
              padding: '12px',
              textAlign: 'center',
            }}>
              <div style={{ fontSize: '24px', fontWeight: '900', color: '#fff', fontFamily: "'Courier New', monospace" }}>
                {Math.max(...layers.map(l => l.nValue))}
              </div>
              <div style={{ fontSize: '11px', color: '#ccc', marginTop: '2px', fontWeight: '600', textTransform: 'uppercase' }}>Max N-value</div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
