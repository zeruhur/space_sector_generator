import http.server
import json
import socketserver
import urllib.parse
from pathlib import Path
from .config import (DEFAULT_DENSITY, DEFAULT_PHONEMES, DEFAULT_REGION,
                     SUBSECTOR_LETTERS)
from .coordinates import derive_code, hexes_for_subsector
from .generator import generate_system
from .network import run_network_pass, resolve_pending_links
from .renderer import render_subsector_to_svg
from .viewer import translate_system_html
from .names import load_register

PORT = 8000

HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Space Sector Generator</title>
    <style>
        :root {
            --bg: #0f172a;
            --fg: #f1f5f9;
            --accent: #38bdf8;
            --card-bg: #1e293b;
            --border: #334155;
        }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background-color: var(--bg);
            color: var(--fg);
            margin: 0;
            display: flex;
            flex-direction: column;
            height: 100vh;
        }
        header {
            padding: 1rem 2rem;
            background: rgba(15, 23, 42, 0.8);
            border-bottom: 1px solid var(--border);
            backdrop-filter: blur(8px);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .nav-links {
            display: flex;
            gap: 1.5rem;
            margin-left: 2rem;
        }
        .nav-links a {
            color: var(--fg);
            text-decoration: none;
            font-size: 0.9rem;
            font-weight: 500;
            opacity: 0.7;
            transition: opacity 0.2s;
        }
        .nav-links a:hover, .nav-links a.active {
            opacity: 1;
            color: var(--accent);
        }
        main {
            display: flex;
            flex: 1;
            overflow: hidden;
        }
        #sidebar {
            width: 300px;
            padding: 2rem;
            border-right: 1px solid var(--border);
            display: flex;
            flex-direction: column;
            gap: 1.5rem;
            overflow-y: auto;
        }
        #content {
            flex: 1;
            padding: 2rem;
            overflow-y: auto;
            display: flex;
            flex-direction: column;
            gap: 2rem;
        }
        .form-group {
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
        }
        label { font-weight: 600; color: var(--accent); font-size: 0.875rem; }
        input, select {
            background: var(--card-bg);
            border: 1px solid var(--border);
            color: var(--fg);
            padding: 0.5rem;
            border-radius: 4px;
        }
        button {
            background: var(--accent);
            color: var(--bg);
            border: none;
            padding: 0.75rem;
            border-radius: 4px;
            font-weight: 700;
            cursor: pointer;
            transition: opacity 0.2s;
        }
        button:hover { opacity: 0.9; }
        .card {
            background: var(--card-bg);
            border: 1px solid var(--border);
            border-radius: 8px;
            padding: 1.5rem;
        }
        #map-card {
            position: relative;
        }
        #map-container {
            display: flex;
            justify-content: center;
            align-items: center;
            background: #000;
            border-radius: 8px;
            min-height: 500px;
            overflow: hidden;
            cursor: grab;
            position: relative;
        }
        #map-container:active { cursor: grabbing; }
        #map-container svg {
            transform-origin: 0 0;
            transition: transform 0.1s ease-out;
        }
        .map-hint {
            position: absolute;
            bottom: 1rem;
            left: 50%;
            transform: translateX(-50%);
            background: rgba(15, 23, 42, 0.8);
            padding: 0.5rem 1rem;
            border-radius: 20px;
            font-size: 0.8rem;
            color: var(--accent);
            border: 1px solid var(--accent);
            pointer-events: none;
            opacity: 0;
            transition: opacity 0.5s;
            z-index: 5;
        }
        #map-container:hover .map-hint {
            opacity: 1;
        }
        .controls {
            position: absolute;
            top: 1rem;
            right: 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            z-index: 10;
        }
        .control-btn {
            background: rgba(30, 41, 59, 0.8);
            color: var(--fg);
            border: 1px solid var(--border);
            width: 40px;
            height: 40px;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 1.25rem;
            cursor: pointer;
            border-radius: 4px;
        }
        .export-group {
            display: flex;
            gap: 0.5rem;
            margin-top: 1rem;
        }
        .export-btn {
            flex: 1;
            font-size: 0.75rem;
            padding: 0.5rem;
            background: #475569;
            color: white;
        }
        #system-details {
            display: none;
            border-top: 4px solid var(--accent);
        }
        #details-text {
            background: #000;
            padding: 2rem;
            border-radius: 4px;
            color: #e2e8f0;
            line-height: 1.6;
        }
        #details-text h3 { color: var(--accent); margin-top: 0; }
        #details-text h4 { color: #94a3b8; border-bottom: 1px solid var(--border); padding-bottom: 0.5rem; margin-top: 2rem; }
        #details-text ul { padding-left: 1.5rem; }
        #details-text li { margin-bottom: 0.5rem; }
        #details-text code { background: #1e293b; padding: 0.2rem 0.4rem; border-radius: 3px; }
        .loading {
            opacity: 0.5;
            pointer-events: none;
        }
        footer {
            padding: 1.5rem 2rem;
            background: rgba(15, 23, 42, 0.9);
            border-top: 1px solid var(--border);
            text-align: center;
            font-size: 0.85rem;
            color: #94a3b8;
        }
        footer a {
            color: var(--accent);
            text-decoration: none;
        }
        footer a:hover {
            text-decoration: underline;
        }
    </style>
</head>
<body>
    <header>
        <div style="display:flex; align-items:center;">
            <h1 style="margin:0; font-size: 1.5rem;">Space Sector Generator</h1>
            <nav class="nav-links">
                <a href="/" class="active">Generator</a>
                <a href="/system" target="_blank">System Rules ↗</a>
                <a href="/guide" target="_blank">User Guide ↗</a>
            </nav>
        </div>
        <div id="status">Ready</div>
    </header>
    <main>
        <div id="sidebar">
            <div class="form-group">
                <label>Region Name</label>
                <input type="text" id="region-name" value="Orion">
            </div>
            <div class="form-group">
                <label>Sector Name</label>
                <input type="text" id="sector-name" value="Cassian">
            </div>
            <div class="form-group">
                <label>Subsector</label>
                <select id="subsector">
                    <option value="A">A</option><option value="B">B</option>
                    <option value="C">C</option><option value="D">D</option>
                    <option value="E">E</option><option value="F">F</option>
                    <option value="G">G</option><option value="H">H</option>
                    <option value="I">I</option><option value="J">J</option>
                    <option value="K">K</option><option value="L">L</option>
                    <option value="M">M</option><option value="N">N</option>
                    <option value="O">O</option><option value="P">P</option>
                </select>
            </div>
            <div class="form-group">
                <label>Density</label>
                <select id="density">
                    <option value="sparse">Sparse</option>
                    <option value="standard" selected>Standard</option>
                    <option value="dense">Dense</option>
                    <option value="cluster">Cluster</option>
                </select>
            </div>
            <button id="generate-btn">Generate Subsector</button>
            
            <div class="export-group">
                <button class="export-btn" id="export-md">Export MD</button>
                <button class="export-btn" id="export-json">Export JSON</button>
                <button class="export-btn" id="export-tsv">Export TSV</button>
            </div>
            <div class="export-group">
                <button class="export-btn" id="export-svg" style="background: #0ea5e9">Export SVG</button>
                <button class="export-btn" id="export-png" style="background: #0ea5e9">Export PNG</button>
            </div>
        </div>
        <div id="content">
            <div class="card" id="map-card">
                <h2 style="margin-top:0">Subsector Map</h2>
                <div class="controls">
                    <div class="control-btn" id="zoom-in" title="Zoom In">+</div>
                    <div class="control-btn" id="zoom-out" title="Zoom Out">−</div>
                    <div class="control-btn" id="zoom-reset" title="Reset View">⟲</div>
                </div>
                <div id="map-container">
                    <div class="map-hint">Click a system for details</div>
                    <p style="color: #64748b">Generate a subsector to view the map.</p>
                </div>
            </div>
            <div class="card" id="system-details">
                <div id="details-text"></div>
            </div>
        </div>
    </main>
    <footer>
        <p>
            Created by <a href="https://github.com/zeruhur" target="_blank">zeruhur</a> | 
            Licensed under <a href="/license" target="_blank">MIT</a> | 
            Source: <a href="https://github.com/zeruhur/space_sector_generator" target="_blank">GitHub</a>
        </p>
    </footer>

    <script>
        const generateBtn = document.getElementById('generate-btn');
        const mapContainer = document.getElementById('map-container');
        const detailsCard = document.getElementById('system-details');
        const detailsText = document.getElementById('details-text');
        const status = document.getElementById('status');

        let scale = 1;
        let translateX = 0;
        let translateY = 0;
        let isDragging = false;
        let startX, startY;

        function updateTransform() {
            const svg = mapContainer.querySelector('svg');
            if (svg) {
                svg.style.transform = `translate(${translateX}px, ${translateY}px) scale(${scale})`;
            }
        }

        generateBtn.onclick = async () => {
            document.body.classList.add('loading');
            status.innerText = 'Generating...';
            
            const payload = {
                region: document.getElementById('region-name').value,
                sector: document.getElementById('sector-name').value,
                subsector: document.getElementById('subsector').value,
                density: document.getElementById('density').value
            };

            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify(payload)
                });
                const data = await response.json();
                
                if (data.error) {
                    alert(data.error);
                } else {
                    mapContainer.innerHTML = data.svg;
                    scale = 1; translateX = 0; translateY = 0;
                    updateTransform();
                    setTimeout(attachClickHandlers, 100);
                }
            } catch (err) {
                console.error(err);
                alert('Generation failed.');
            } finally {
                document.body.classList.remove('loading');
                status.innerText = 'Ready';
            }
        };

        // Export handlers
        document.getElementById('export-md').onclick = () => downloadExport('markdown');
        document.getElementById('export-json').onclick = () => downloadExport('json');
        document.getElementById('export-tsv').onclick = () => downloadExport('tsv');

        document.getElementById('export-svg').onclick = () => {
            const svg = mapContainer.querySelector('svg');
            if (!svg) { alert('No map generated yet.'); return; }
            
            // Clone to remove interactive styles for a clean export
            const clone = svg.cloneNode(true);
            clone.style.transform = '';
            
            const svgData = new XMLSerializer().serializeToString(clone);
            const blob = new Blob([svgData], {type: 'image/svg+xml;charset=utf-8'});
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = 'sector_map.svg';
            a.click();
            window.URL.revokeObjectURL(url);
        };

        document.getElementById('export-png').onclick = () => {
            const svg = mapContainer.querySelector('svg');
            if (!svg) { alert('No map generated yet.'); return; }
            
            status.innerText = 'Rendering High-Res PNG...';
            
            // Upscale factor for high-resolution (3x original)
            const resScale = 3;
            const originalWidth = svg.width.baseVal.value;
            const originalHeight = svg.height.baseVal.value;
            
            const clone = svg.cloneNode(true);
            clone.style.transform = '';
            clone.setAttribute('width', originalWidth * resScale);
            clone.setAttribute('height', originalHeight * resScale);
            
            const svgData = new XMLSerializer().serializeToString(clone);
            
            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');
            const img = new Image();
            
            canvas.width = originalWidth * resScale;
            canvas.height = originalHeight * resScale;
            
            img.onload = () => {
                // Clear with white background
                ctx.fillStyle = "white";
                ctx.fillRect(0, 0, canvas.width, canvas.height);
                ctx.drawImage(img, 0, 0);
                
                try {
                    const pngUrl = canvas.toDataURL("image/png");
                    const a = document.createElement('a');
                    a.href = pngUrl;
                    a.download = 'sector_map_highres.png';
                    a.click();
                } catch (err) {
                    console.error(err);
                    alert('PNG export failed: Check browser security settings for Canvas exports.');
                } finally {
                    status.innerText = 'Ready';
                }
            };
            
            img.onerror = () => {
                alert('Failed to render SVG to image.');
                status.innerText = 'Ready';
            };
            
            img.src = 'data:image/svg+xml;base64,' + btoa(unescape(encodeURIComponent(svgData)));
        };

        async function downloadExport(format) {
            status.innerText = `Exporting ${format}...`;
            try {
                const response = await fetch('/api/export', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ format })
                });
                
                if (!response.ok) {
                    const text = await response.text();
                    alert('Export failed: ' + response.statusText + '\\n' + (text.length < 200 ? text : 'No data generated yet.'));
                    return;
                }

                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement('a');
                a.href = url;
                const ext = format === 'markdown' ? 'md' : format;
                a.download = `sector_export.${ext}`;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
                a.remove();
            } catch (err) {
                console.error(err);
                alert('Export failed: ' + err.message);
            } finally {
                status.innerText = 'Ready';
            }
        }

        // Zoom controls
        document.getElementById('zoom-in').onclick = () => { scale *= 1.2; updateTransform(); };
        document.getElementById('zoom-out').onclick = () => { scale /= 1.2; updateTransform(); };
        document.getElementById('zoom-reset').onclick = () => { scale = 1; translateX = 0; translateY = 0; updateTransform(); };

        mapContainer.onwheel = (e) => {
            e.preventDefault();
            const delta = e.deltaY > 0 ? 0.9 : 1.1;
            scale *= delta;
            updateTransform();
        };

        // Pan controls
        mapContainer.onmousedown = (e) => {
            if (e.button !== 0) return;
            isDragging = true;
            startX = e.clientX - translateX;
            startY = e.clientY - translateY;
        };

        window.onmousemove = (e) => {
            if (!isDragging) return;
            translateX = e.clientX - startX;
            translateY = e.clientY - startY;
            updateTransform();
        };

        window.onmouseup = () => isDragging = false;

        function attachClickHandlers() {
            const systems = document.querySelectorAll('g[id]');
            systems.forEach(s => {
                s.style.cursor = 'pointer';
                s.onclick = async (e) => {
                    e.stopPropagation(); // Don't trigger pan
                    const sysId = s.id;
                    status.innerText = 'Fetching ' + sysId + '...';
                    
                    try {
                        const response = await fetch('/api/translate', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ id: sysId })
                        });
                        const data = await response.json();
                        
                        detailsCard.style.display = 'block';
                        detailsText.innerHTML = data.report;
                        detailsCard.scrollIntoView({ behavior: 'smooth' });
                    } catch (err) {
                        console.error(err);
                    } finally {
                        status.innerText = 'Ready';
                    }
                };
            });
        }
    </script>
</body>
</html>
"""

# Global storage for current session
WORKSPACE_PATH = Path("workspace.tsv")
current_systems = {}

def load_workspace():
    global current_systems
    if WORKSPACE_PATH.exists():
        from .io import load_tsv
        current_systems = load_tsv(WORKSPACE_PATH)
        print(f"Loaded {len(current_systems)} systems from {WORKSPACE_PATH}")
    else:
        current_systems = {}

def save_workspace():
    from .io import save_tsv
    save_tsv(WORKSPACE_PATH, current_systems)
    print(f"Auto-saved workspace to {WORKSPACE_PATH}")

class SGSHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode('utf-8'))
        elif self.path == '/system':
            self.handle_system_rules()
        elif self.path == '/guide':
            self.handle_user_guide()
        elif self.path == '/license':
            self.handle_license()
        else:
            self.send_error(404)

    def _render_markdown_page(self, title, file_path):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            import re
            html_lines = []
            in_code = False
            in_list = False
            in_table = False
            table_header_processed = False

            for line in lines:
                line = line.rstrip()
                
                # Code blocks
                if line.startswith('```'):
                    if not in_code:
                        html_lines.append('<pre><code>')
                        in_code = True
                    else:
                        html_lines.append('</code></pre>')
                        in_code = False
                    continue
                
                if in_code:
                    html_lines.append(line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;'))
                    continue

                # Escape HTML in normal text
                line = line.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
                
                # Horizontal rule
                if line == '---':
                    html_lines.append('<hr>')
                    continue

                # Headers
                if line.startswith('# '):
                    html_lines.append(f'<h1>{line[2:]}</h1>')
                    continue
                if line.startswith('## '):
                    html_lines.append(f'<h2>{line[3:]}</h2>')
                    continue
                if line.startswith('### '):
                    html_lines.append(f'<h3>{line[4:]}</h3>')
                    continue

                # Bold and Inline Code
                line = re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', line)
                line = re.sub(r'`(.*?)`', r'<code>\1</code>', line)

                # Tables (GFM style)
                if '|' in line:
                    # Filter out empty parts but keep internal structure
                    parts = [p.strip() for p in line.split('|')]
                    if len(parts) > 1 and parts[0] == '': parts = parts[1:]
                    if len(parts) > 1 and parts[-1] == '': parts = parts[:-1]
                    
                    if not parts: continue
                        
                    # Detect separator line
                    if all(re.match(r'^-+$', p) or re.match(r'^:?-+:?$', p) for p in parts):
                        if in_table and not table_header_processed:
                            table_header_processed = True
                            continue
                    
                    if not in_table:
                        html_lines.append('<table>')
                        in_table = True
                        table_header_processed = False
                        html_lines.append('<thead><tr>' + ''.join(f'<th>{p}</th>' for p in parts) + '</tr></thead><tbody>')
                    else:
                        html_lines.append('<tr>' + ''.join(f'<td>{p}</td>' for p in parts) + '</tr>')
                    continue
                elif in_table:
                    html_lines.append('</tbody></table>')
                    in_table = False

                # Lists
                if line.startswith('* ') or line.startswith('- '):
                    if not in_list:
                        html_lines.append('<ul>')
                        in_list = True
                    html_lines.append(f'<li>{line[2:]}</li>')
                    continue
                elif in_list:
                    html_lines.append('</ul>')
                    in_list = False

                # Paragraphs
                if line.strip():
                    html_lines.append(f'<p>{line}</p>')
                else:
                    html_lines.append('<br>')

            if in_table: html_lines.append('</tbody></table>')
            if in_list: html_lines.append('</ul>')
            
            html_content = '\n'.join(html_lines)
            
            page = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>{title} - Space Sector Generator</title>
                <style>
                    body {{ font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; max-width: 1000px; margin: 0 auto; padding: 3rem; background: #0f172a; color: #f1f5f9; }}
                    h1, h2, h3 {{ color: #38bdf8; margin-top: 2.5rem; border-bottom: 1px solid #334155; padding-bottom: 0.5rem; }}
                    pre {{ background: #000; padding: 1.5rem; border-radius: 8px; overflow-x: auto; border: 1px solid #334155; margin: 1.5rem 0; }}
                    code {{ font-family: 'Consolas', 'Monaco', monospace; color: #38bdf8; background: rgba(56, 189, 248, 0.1); padding: 0.2rem 0.4rem; border-radius: 4px; }}
                    pre code {{ background: none; padding: 0; color: #e2e8f0; }}
                    p, li {{ margin-bottom: 1rem; color: #cbd5e1; font-size: 1.05rem; }}
                    hr {{ border: 0; border-top: 1px solid #334155; margin: 4rem 0; }}
                    a.back {{ color: #38bdf8; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 2rem; border: 1px solid #38bdf8; padding: 0.5rem 1rem; border-radius: 4px; transition: all 0.2s; }}
                    a.back:hover {{ background: #38bdf8; color: #0f172a; }}
                    table {{ border-collapse: collapse; width: 100%; margin: 2rem 0; background: #1e293b; border-radius: 8px; overflow: hidden; border: 1px solid #334155; }}
                    th, td {{ padding: 1rem 1.25rem; text-align: left; border-bottom: 1px solid #334155; }}
                    th {{ background: #0f172a; color: #38bdf8; font-weight: 700; text-transform: uppercase; font-size: 0.85rem; letter-spacing: 0.05em; }}
                    tr:last-child td {{ border-bottom: none; }}
                    tr:hover td {{ background: rgba(56, 189, 248, 0.05); }}
                </style>
            </head>
            <body>
                <a href="/" class="back">&larr; Back to Generator</a>
                <div class="markdown-body">
                    {html_content}
                </div>
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(page.encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))

    def handle_license(self):
        try:
            license_path = Path(__file__).parent / 'LICENSE'
            content = license_path.read_text(encoding='utf-8')
            page = f"""
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <title>MIT License - Space Sector Generator</title>
                <style>
                    body {{ font-family: 'Segoe UI', system-ui, sans-serif; line-height: 1.6; max-width: 800px; margin: 0 auto; padding: 3rem; background: #0f172a; color: #f1f5f9; }}
                    pre {{ background: #000; padding: 2rem; border-radius: 8px; border: 1px solid #334155; white-space: pre-wrap; font-family: 'Consolas', monospace; color: #e2e8f0; }}
                    a.back {{ color: #38bdf8; text-decoration: none; font-weight: 600; display: inline-block; margin-bottom: 2rem; }}
                </style>
            </head>
            <body>
                <a href="/" class="back">&larr; Back to Generator</a>
                <h1>MIT License</h1>
                <pre>{content}</pre>
            </body>
            </html>
            """
            self.send_response(200)
            self.send_header('Content-Type', 'text/html')
            self.end_headers()
            self.wfile.write(page.encode('utf-8'))
        except Exception as e:
            self.send_error(500, str(e))

    def handle_system_rules(self):
        self._render_markdown_page("System Rules", 'sector_generation_system.md')

    def handle_user_guide(self):
        self._render_markdown_page("User Guide", 'USER_GUIDE.md')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        data = json.loads(post_data)

        if self.path == '/api/generate':
            self.handle_generate(data)
        elif self.path == '/api/translate':
            self.handle_translate(data)
        elif self.path == '/api/export':
            self.handle_export(data)
        else:
            self.send_error(404)

    def handle_generate(self, data):
        global current_systems
        region_name = data.get('region', 'Orion')
        sector_name = data.get('sector', 'Cassian')
        subsector_letter = data.get('subsector', 'A')
        density = data.get('density', 'standard')

        region_code = derive_code(region_name, set())
        sector_code = derive_code(sector_name, set())
        sector_id = f"{sector_code}-01"
        
        register = load_register('default')
        
        new_systems = {}
        for cid in hexes_for_subsector(region_code, sector_code, subsector_letter):
            s = generate_system(cid, sector_id, density=density, register=register)
            if s:
                new_systems[cid] = s
        
        # Additive logic: merge with current workspace (existing wins)
        from .io import merge
        current_systems = merge(current_systems, new_systems)
        
        # Run network pass and resolve links across the WHOLE workspace
        current_systems, _ = run_network_pass(current_systems)
        resolve_pending_links(current_systems)
        
        # Auto-save
        save_workspace()
        
        # Render ONLY the requested subsector for visual feedback
        # (Pass full dict so routes cross-subsector are rendered if they exist)
        svg = render_subsector_to_svg(current_systems, f"{region_code}-{sector_id}-{subsector_letter}")
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({'svg': svg}).encode('utf-8'))

    def handle_translate(self, data):
        sys_id = data.get('id')
        if not sys_id or sys_id not in current_systems:
            self.send_error(400, "System not found")
            return
        
        system = current_systems[sys_id]
        report = translate_system_html(system)
        
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({
            'name': system['name'],
            'report': report
        }).encode('utf-8'))

    def handle_export(self, data):
        global current_systems
        if not current_systems:
            self.send_error(400, "No data to export")
            return
        
        fmt = data.get('format', 'json')
        import tempfile
        from .io import export_markdown, export_json, save_tsv
        
        with tempfile.NamedTemporaryFile(delete=False) as tmp:
            tmp_path = Path(tmp.name)
        
        try:
            if fmt == 'markdown':
                export_markdown(tmp_path, current_systems)
                content_type = 'text/markdown'
            elif fmt == 'tsv':
                save_tsv(tmp_path, current_systems)
                content_type = 'text/tab-separated-values'
            else:
                export_json(tmp_path, current_systems)
                content_type = 'application/json'
            
            content = tmp_path.read_bytes()
            
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.send_header('Content-Length', len(content))
            self.end_headers()
            self.wfile.write(content)
        finally:
            if tmp_path.exists():
                tmp_path.unlink()

def run_server():
    load_workspace()
    with socketserver.TCPServer(("", PORT), SGSHandler) as httpd:
        print(f"Serving GUI at http://localhost:{PORT}")
        print("Press Ctrl+C to stop.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            pass
