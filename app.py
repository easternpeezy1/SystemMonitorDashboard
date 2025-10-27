"""
System Monitor Dashboard - Single File Version
Requirements: pip install flask psutil flask-cors
Optional: pip install gputil (for GPU monitoring)

Run: python app.py
Then open: http://localhost:5000
"""

from flask import Flask, jsonify
from flask_cors import CORS
import psutil
import platform
import socket
from datetime import datetime

app = Flask(__name__)
CORS(app)

# Store historical data for graphs
cpu_history = []
ram_history = []
MAX_HISTORY = 60

def get_size(bytes):
    """Convert bytes to human readable format"""
    for unit in ['', 'K', 'M', 'G', 'T', 'P']:
        if bytes < 1024:
            return f"{bytes:.2f}{unit}B"
        bytes /= 1024

def get_system_info():
    """Get static system information"""
    try:
        # Basic system info
        info = {
            'platform': platform.system(),
            'platform_release': platform.release(),
            'platform_version': platform.version(),
            'architecture': platform.machine(),
            'hostname': socket.gethostname(),
            'processor': platform.processor(),
            'cpu_cores': psutil.cpu_count(logical=False),
            'cpu_threads': psutil.cpu_count(logical=True),
        }
        
        # Get RAM total
        mem = psutil.virtual_memory()
        info['ram_total'] = get_size(mem.total)
        
        # Get GPU info
        try:
            import GPUtil
            gpus = GPUtil.getGPUs()
            info['gpu_list'] = []
            for gpu in gpus:
                info['gpu_list'].append({
                    'name': gpu.name,
                    'memory': f"{gpu.memoryTotal:.0f}MB",
                    'driver': getattr(gpu, 'driver', 'Unknown')
                })
        except:
            info['gpu_list'] = []
        
        # Get display info (Windows)
        try:
            if platform.system() == 'Windows':
                import ctypes
                user32 = ctypes.windll.user32
                info['displays'] = [{
                    'resolution': f"{user32.GetSystemMetrics(0)}x{user32.GetSystemMetrics(1)}",
                    'primary': True
                }]
            else:
                info['displays'] = []
        except:
            info['displays'] = []
        
        # Get boot time
        boot_time = datetime.fromtimestamp(psutil.boot_time())
        info['boot_time'] = boot_time.strftime('%Y-%m-%d %H:%M:%S')
        
        return info
    except Exception as e:
        return {'error': str(e)}

def get_cpu_info():
    """Get CPU usage information"""
    try:
        cpu_percent = psutil.cpu_percent(interval=1, percpu=False)
        cpu_freq = psutil.cpu_freq()
        
        info = {
            'usage': cpu_percent,
            'freq_current': cpu_freq.current if cpu_freq else 0,
            'freq_max': cpu_freq.max if cpu_freq else 0,
            'per_core': psutil.cpu_percent(interval=1, percpu=True)
        }
        return info
    except Exception as e:
        return {'error': str(e)}

def get_memory_info():
    """Get RAM usage information"""
    try:
        mem = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        info = {
            'total': get_size(mem.total),
            'available': get_size(mem.available),
            'used': get_size(mem.used),
            'percent': mem.percent,
            'swap_total': get_size(swap.total),
            'swap_used': get_size(swap.used),
            'swap_percent': swap.percent
        }
        return info
    except Exception as e:
        return {'error': str(e)}

def get_disk_info():
    """Get disk usage information"""
    try:
        partitions = []
        for partition in psutil.disk_partitions():
            try:
                usage = psutil.disk_usage(partition.mountpoint)
                partitions.append({
                    'device': partition.device,
                    'mountpoint': partition.mountpoint,
                    'fstype': partition.fstype,
                    'total': get_size(usage.total),
                    'used': get_size(usage.used),
                    'free': get_size(usage.free),
                    'percent': usage.percent
                })
            except PermissionError:
                continue
        return partitions
    except Exception as e:
        return {'error': str(e)}

def get_network_info():
    """Get network information"""
    try:
        net_io = psutil.net_io_counters()
        info = {
            'bytes_sent': get_size(net_io.bytes_sent),
            'bytes_recv': get_size(net_io.bytes_recv),
            'packets_sent': net_io.packets_sent,
            'packets_recv': net_io.packets_recv,
        }
        return info
    except Exception as e:
        return {'error': str(e)}

def get_gpu_info():
    """Get GPU information (requires gputil)"""
    try:
        import GPUtil
        gpus = GPUtil.getGPUs()
        gpu_list = []
        for gpu in gpus:
            gpu_list.append({
                'id': gpu.id,
                'name': gpu.name,
                'load': f"{gpu.load * 100:.1f}",
                'temp': f"{gpu.temperature:.1f}",
                'memory_used': f"{gpu.memoryUsed:.0f}",
                'memory_total': f"{gpu.memoryTotal:.0f}",
                'memory_percent': f"{(gpu.memoryUsed / gpu.memoryTotal * 100):.1f}"
            })
        return gpu_list
    except Exception:
        return []

def get_temperature_info():
    """Get system temperature (if available)"""
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            temp_info = {}
            for name, entries in temps.items():
                temp_info[name] = [{'label': entry.label, 'current': entry.current} for entry in entries]
            return temp_info
        return {}
    except Exception:
        return {}

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>System Monitor Dashboard</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/3.9.1/chart.min.js"></script>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }

        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
            color: #333;
        }

        .container {
            max-width: 1400px;
            margin: 0 auto;
        }

        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }

        header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }

        .timestamp {
            font-size: 1em;
            opacity: 0.9;
        }

        .grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }

        .card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
            transition: transform 0.3s ease;
        }

        .card:hover {
            transform: translateY(-5px);
        }

        .card-header {
            display: flex;
            align-items: center;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #f0f0f0;
        }

        .card-icon {
            font-size: 2em;
            margin-right: 10px;
        }

        .card-title {
            font-size: 1.3em;
            font-weight: bold;
            color: #667eea;
        }

        .metric {
            margin: 10px 0;
        }

        .metric-label {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 5px;
        }

        .metric-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #333;
        }

        .progress-bar {
            width: 100%;
            height: 25px;
            background: #f0f0f0;
            border-radius: 12px;
            overflow: hidden;
            margin-top: 8px;
            position: relative;
        }

        .progress-fill {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 12px;
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.85em;
        }

        .progress-fill.warning {
            background: linear-gradient(90deg, #f093fb, #f5576c);
        }

        .progress-fill.critical {
            background: linear-gradient(90deg, #fa709a, #fee140);
        }

        .stat-grid {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-top: 10px;
        }

        .stat-item {
            background: #f8f9fa;
            padding: 10px;
            border-radius: 8px;
        }

        .stat-item-label {
            font-size: 0.8em;
            color: #666;
        }

        .stat-item-value {
            font-size: 1.2em;
            font-weight: bold;
            color: #333;
        }

        .chart-container {
            grid-column: 1 / -1;
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 10px 30px rgba(0,0,0,0.2);
        }

        canvas {
            max-height: 300px;
        }

        .core-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(80px, 1fr));
            gap: 8px;
            margin-top: 10px;
        }

        .core-item {
            background: #f8f9fa;
            padding: 8px;
            border-radius: 8px;
            text-align: center;
        }

        .disk-list {
            margin-top: 10px;
        }

        .disk-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .gpu-list {
            margin-top: 10px;
        }

        .gpu-item {
            background: #f8f9fa;
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 10px;
        }

        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #4caf50;
            margin-right: 5px;
            animation: pulse 2s infinite;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.5; }
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>⚡ System Monitor Dashboard</h1>
            <div class="timestamp">
                <span class="status-indicator"></span>
                <span id="timestamp">Loading...</span>
            </div>
        </header>

        <div class="grid">
            <div class="card">
                <div class="card-header">
                    <div class="card-icon">💻</div>
                    <div class="card-title">CPU Usage</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="cpu-usage">--</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="cpu-progress">0%</div>
                    </div>
                </div>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-item-label">Frequency</div>
                        <div class="stat-item-value" id="cpu-freq">-- MHz</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">Cores</div>
                        <div class="stat-item-value" id="cpu-cores">--</div>
                    </div>
                </div>
                <div class="core-grid" id="core-grid"></div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-icon">🧠</div>
                    <div class="card-title">Memory (RAM)</div>
                </div>
                <div class="metric">
                    <div class="metric-value" id="ram-usage">--</div>
                    <div class="progress-bar">
                        <div class="progress-fill" id="ram-progress">0%</div>
                    </div>
                </div>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-item-label">Used</div>
                        <div class="stat-item-value" id="ram-used">-- GB</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">Total</div>
                        <div class="stat-item-value" id="ram-total">-- GB</div>
                    </div>
                </div>
            </div>

            <div class="card">
                <div class="card-header">
                    <div class="card-icon">🌐</div>
                    <div class="card-title">Network</div>
                </div>
                <div class="stat-grid">
                    <div class="stat-item">
                        <div class="stat-item-label">↑ Sent</div>
                        <div class="stat-item-value" id="net-sent">-- MB</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-item-label">↓ Received</div>
                        <div class="stat-item-value" id="net-recv">-- MB</div>
                    </div>
                </div>
            </div>

            <div class="card" id="gpu-card" style="display: none;">
                <div class="card-header">
                    <div class="card-icon">🎮</div>
                    <div class="card-title">GPU</div>
                </div>
                <div class="gpu-list" id="gpu-list"></div>
            </div>
        </div>

        <div class="chart-container">
            <div class="card-header">
                <div class="card-icon">💾</div>
                <div class="card-title">Disk Storage</div>
            </div>
            <div class="disk-list" id="disk-list"></div>
        </div>

        <div class="grid">
            <div class="chart-container">
                <h3>CPU Usage History</h3>
                <canvas id="cpu-chart"></canvas>
            </div>
            <div class="chart-container">
                <h3>RAM Usage History</h3>
                <canvas id="ram-chart"></canvas>
            </div>
        </div>
    </div>

    <script>
        const cpuChart = new Chart(document.getElementById('cpu-chart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'CPU %',
                    data: [],
                    borderColor: '#667eea',
                    backgroundColor: 'rgba(102, 126, 234, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

        const ramChart = new Chart(document.getElementById('ram-chart'), {
            type: 'line',
            data: {
                labels: [],
                datasets: [{
                    label: 'RAM %',
                    data: [],
                    borderColor: '#764ba2',
                    backgroundColor: 'rgba(118, 75, 162, 0.1)',
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });

        function updateProgress(elementId, value) {
            const element = document.getElementById(elementId);
            element.style.width = value + '%';
            element.textContent = value + '%';
            
            element.className = 'progress-fill';
            if (value > 80) {
                element.classList.add('critical');
            } else if (value > 60) {
                element.classList.add('warning');
            }
        }

        async function fetchStats() {
            try {
                const response = await fetch('/api/stats');
                const data = await response.json();
                
                document.getElementById('timestamp').textContent = data.timestamp;
                
                const cpuUsage = data.cpu.usage.toFixed(1);
                document.getElementById('cpu-usage').textContent = cpuUsage + '%';
                updateProgress('cpu-progress', cpuUsage);
                document.getElementById('cpu-freq').textContent = data.cpu.freq_current.toFixed(0) + ' MHz';
                
                const coreGrid = document.getElementById('core-grid');
                coreGrid.innerHTML = '';
                data.cpu.per_core.forEach((core, index) => {
                    const coreDiv = document.createElement('div');
                    coreDiv.className = 'core-item';
                    coreDiv.innerHTML = `<div style="font-size: 0.8em; color: #666;">Core ${index}</div><div style="font-weight: bold;">${core.toFixed(0)}%</div>`;
                    coreGrid.appendChild(coreDiv);
                });
                
                const ramUsage = data.memory.percent.toFixed(1);
                document.getElementById('ram-usage').textContent = ramUsage + '%';
                updateProgress('ram-progress', ramUsage);
                document.getElementById('ram-used').textContent = data.memory.used;
                document.getElementById('ram-total').textContent = data.memory.total;
                
                document.getElementById('net-sent').textContent = data.network.bytes_sent;
                document.getElementById('net-recv').textContent = data.network.bytes_recv;
                
                if (data.gpu && data.gpu.length > 0) {
                    document.getElementById('gpu-card').style.display = 'block';
                    const gpuList = document.getElementById('gpu-list');
                    gpuList.innerHTML = '';
                    data.gpu.forEach(gpu => {
                        const gpuDiv = document.createElement('div');
                        gpuDiv.className = 'gpu-item';
                        gpuDiv.innerHTML = `
                            <div style="font-weight: bold; margin-bottom: 5px;">${gpu.name}</div>
                            <div style="font-size: 0.9em;">Load: ${gpu.load}% | Temp: ${gpu.temp}°C</div>
                            <div style="font-size: 0.9em;">Memory: ${gpu.memory_used}MB / ${gpu.memory_total}MB (${gpu.memory_percent}%)</div>
                        `;
                        gpuList.appendChild(gpuDiv);
                    });
                }
                
                const diskList = document.getElementById('disk-list');
                diskList.innerHTML = '';
                data.disk.forEach(disk => {
                    const diskDiv = document.createElement('div');
                    diskDiv.className = 'disk-item';
                    diskDiv.innerHTML = `
                        <div style="font-weight: bold; margin-bottom: 5px;">${disk.device} - ${disk.mountpoint}</div>
                        <div class="progress-bar">
                            <div class="progress-fill ${disk.percent > 80 ? 'critical' : disk.percent > 60 ? 'warning' : ''}" style="width: ${disk.percent}%">${disk.percent}%</div>
                        </div>
                        <div style="font-size: 0.9em; margin-top: 5px; color: #666;">Used: ${disk.used} / Total: ${disk.total} (Free: ${disk.free})</div>
                    `;
                    diskList.appendChild(diskDiv);
                });
                
                const now = new Date().toLocaleTimeString();
                
                if (cpuChart.data.labels.length > 60) {
                    cpuChart.data.labels.shift();
                    cpuChart.data.datasets[0].data.shift();
                }
                cpuChart.data.labels.push(now);
                cpuChart.data.datasets[0].data.push(data.cpu.usage);
                cpuChart.update('none');
                
                if (ramChart.data.labels.length > 60) {
                    ramChart.data.labels.shift();
                    ramChart.data.datasets[0].data.shift();
                }
                ramChart.data.labels.push(now);
                ramChart.data.datasets[0].data.push(data.memory.percent);
                ramChart.update('none');
                
            } catch (error) {
                console.error('Error fetching stats:', error);
            }
        }

        fetchStats();
        
        fetch('/api/system')
            .then(response => response.json())
            .then(data => {
                document.getElementById('cpu-cores').textContent = `${data.cpu_cores}/${data.cpu_threads}`;
            });
        
        setInterval(fetchStats, 2000);
    </script>
</body>
</html>
"""

@app.route('/')
def index():
    """Serve the dashboard HTML"""
    return HTML_TEMPLATE

@app.route('/api/system')
def api_system():
    """API endpoint for system information"""
    return jsonify(get_system_info())

@app.route('/api/stats')
def api_stats():
    """API endpoint for all system stats"""
    global cpu_history, ram_history
    
    cpu_info = get_cpu_info()
    ram_info = get_memory_info()
    
    cpu_history.append(cpu_info.get('usage', 0))
    ram_history.append(ram_info.get('percent', 0))
    
    if len(cpu_history) > MAX_HISTORY:
        cpu_history.pop(0)
    if len(ram_history) > MAX_HISTORY:
        ram_history.pop(0)
    
    stats = {
        'cpu': cpu_info,
        'memory': ram_info,
        'disk': get_disk_info(),
        'network': get_network_info(),
        'gpu': get_gpu_info(),
        'temperature': get_temperature_info(),
        'history': {
            'cpu': cpu_history,
            'ram': ram_history
        },
        'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    }
    return jsonify(stats)

if __name__ == '__main__':
    import webbrowser
    import threading
    
    def open_browser():
        webbrowser.open('http://localhost:5000')  # Match your port
    
    timer = threading.Timer(1.5, open_browser)
    timer.daemon = True
    timer.start()
    
    print("=" * 60)
    print("          SYSTEM MONITOR DASHBOARD v1.3")
    print("=" * 60)
    print()
    print("  ✅ Server running successfully")
    print("  🌐 Dashboard opened in your browser")
    print("  🔄 Monitoring in real-time...")
    print()
    print("  ⚠️  DO NOT CLOSE THIS WINDOW")
    print("      (Closing stops the monitoring)")
    print()
    print("=" * 60)
    
    app.run(debug=False, host='127.0.0.1', port=5000, use_reloader=False)
