import streamlit as st
from streamlit.components.v1 import html
import time
import base64
from pathlib import Path
import random  # Needed for particle positioning

# --- Helper function to encode image to Base64 ---
def img_to_base64(img_path):
    """Converts an image file to a Base64 encoded string."""
    path = Path(img_path)
    if not path.is_file():
        st.error(f"Error: Image file not found at {img_path}")
        return None
    with open(path, "rb") as img_file:
        return base64.b64encode(img_file.read()).decode()

# --- Configuration ---
st.set_page_config(
    page_title="EASTERN BEARING - Dashboard",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items=None
)
st.markdown("""
    <style>
        /* Hide header and footer */
        header, footer, [data-testid="stToolbar"] {
            display: none !important;
        }

        /* Remove padding and center content full screen */
        .block-container {
            padding: 0 !important;
            margin: 0 !important;
        }

        .main {
            padding: 0 !important;
        }

        /* Optional: make body 100% height and width */
        html, body, .main {
            height: 100%;
            width: 100%;
            overflow: hidden;
        }

        /* Optional: remove scrollbars */
        ::-webkit-scrollbar {
            display: none;
        }
    </style>
""", unsafe_allow_html=True)


# --- Image Encoding ---
image_file_name = "input_file_0.png"  # Make sure this file is accessible
b64_image = img_to_base64(image_file_name)

# --- Dimensions and Styling Variables ---
pbi_width = 1300
pbi_height = 750
nav_height = 75

content_width = pbi_width
content_height = nav_height + pbi_height

nav_bg_color = "#ffffff"
pbi_shadow = "0 4px 12px rgba(0, 0, 0, 0.1)"
nav_border_radius = "6px 6px 0 0"
pbi_border_radius = "5 5 6px 6px"  # For effects layer and container

# --- Effects Configuration ---
particle_count_pbi = 12  # Number of particles
particle_size = 3
particle_color = "rgba(0, 123, 255, 0.7)"  # Increased opacity for more visibility
particle_blur = "1px"
pbi_glow_color = "rgba(0, 123, 255, 0.6)"  # Slightly stronger glow color

# --- Control Panel Position ---
control_panel_right = 120
control_panel_bottom = 85

# --- Watermark Configuration ---
watermark_text = "EASTERN BEARING"
watermark_color = "rgba(0, 86, 179, 0.15)"  # Noticeable blue
watermark_font_size = "8vw"
watermark_rotation = "-30deg"
watermark_opacity = 2.0  # Control visibility mainly via alpha

# --- Fallback if image fails ---
if not b64_image:
    nav_image_html = (
        '<div style="color: #dc3545; text-align: center; '
        'padding: 20px; font-weight: 500; background-color: #f8d7da; '
        'border-radius: 6px 6px 0 0; height: 100%; display: flex; '
        'align-items: center; justify-content: center;">Error: Header image not found.</div>'
    )
else:
    # Slide the image to left using margin-left: 20px
    nav_image_html = (
        f'<img src="data:image/png;base64,{b64_image}" alt="ARB Eastern Bearing Header Banner" '
        f'style="display: block; width: 100%; height: 100%; object-fit: contain; '
        f'border-radius: {nav_border_radius}; margin-right: 450px;">'
    )

# --- Particle Positioning along Boundaries ---
def generate_particle_positions(count):
    css_list = []
    for i in range(count):
        # Choose a random boundary: 0-top, 1-bottom, 2-left, 3-right
        edge = random.choice([0, 1, 2, 3])
        if edge == 0:  # top edge, small random offset from top
            top = random.uniform(0, 10)
            left = random.uniform(0, 100)
        elif edge == 1:  # bottom edge
            top = random.uniform(90, 100)
            left = random.uniform(0, 100)
        elif edge == 2:  # left edge
            top = random.uniform(0, 100)
            left = random.uniform(0, 10)
        else:  # right edge
            top = random.uniform(0, 100)
            left = random.uniform(90, 100)
        animation_delay = random.uniform(0, 7)
        css_list.append(
            f".pbi-scatter-particle:nth-child({i+1}) {{ top: {top:.2f}%; left: {left:.2f}%; animation-delay: {animation_delay:.2f}s; }}"
        )
    return " ".join(css_list)

particle_css = generate_particle_positions(particle_count_pbi)

# Add a loading state
with st.spinner("Loading Dashboard Interface..."):
    time.sleep(0.2)

# Generate iframe HTML with updated title and particle settings, with edge lightning removed and title moved to left 40px.
iframe_code = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Eastern Bearing Dashboard</title>
<style>
    /* Reset and base styles */
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    html {{ font-size: 16px; }}
    body {{
        width: var(--outer-width);
        min-height: var(--outer-height);
        margin: 0 auto;
        padding: 0;
        font-family: 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
        background-color: #f0f2f5;
        position: relative;
        display: flex;
        justify-content: center;
        align-items: flex-start;
    }}

    /* Watermark Style */
    body::before {{
        content: '{watermark_text}';
        position: fixed; top: 50%; left: 50%;
        transform: translate(-50%, -50%) rotate({watermark_rotation});
        font-size: {watermark_font_size}; font-weight: 700;
        color: {watermark_color};
        white-space: nowrap; z-index: 0;
        pointer-events: none; user-select: none;
        opacity: {watermark_opacity};
    }}

    /* Hide Streamlit elements */
    #MainMenu, header, footer, .css-1d391kg {{ visibility: hidden; height: 0; overflow: hidden; }}
    .block-container {{ padding: 0 !important; margin: 0 !important; max-width: none !important; }}
    .stApp {{ background: transparent !important; }}

    /* Wrapper for the fixed-width dashboard */
    .dashboard-wrapper {{
        width: 100%;
        margin: 0;
        position: relative;
        background-color: #ffffff;
        border-radius: 0px;
        box-shadow: {pbi_shadow};
        overflow: hidden;
    }}

    /* Dashboard Title - moved to left approx 40px */
    .dashboard-title {{
        position: absolute;
        top: 10px;
        right: 135px;
        color: #21137f;
        font-size: 2rem;
        font-weight: bold;
        letter-spacing: 1px;
        text-shadow: 1px 1px 2px rgba(0, 0, 0, 0.1);
        z-index: 101;
    }}

    /* Wrapper for Nav and PBI */
    .dashboard-container {{
        width: 100%;
        display: flex;
        flex-direction: column;
        align-items: center;
        position: relative;
    }}

    /* Navigation bar */
    .nav-tab-container {{
        width: 100%;
        height: {nav_height}px;
        position: relative;
        z-index: 100;
        border-bottom: 1px solid #e9ecef;
        background-color: {nav_bg_color};
        border-radius: {nav_border_radius};
        overflow: hidden;
    }}
    .nav-tab {{
        width: 100%; height: 100%;
        display: flex; align-items: center; justify-content: center;
    }}

    /* Power BI Section */
    .power-bi-container {{
        width: {pbi_width}px; height: {pbi_height}px;
        position: relative;
        z-index: 10;
        background-color: #ffffff;
        overflow: hidden;
        border-radius: {pbi_border_radius};
    }}

    /* Effects Layer */
    .pbi-effects-layer {{
        position: absolute;
        top: -5px; left: -5px;
        width: calc(100% + 10px); height: calc(100% + 10px);
        z-index: 1;
        pointer-events: none;
        border-radius: 8px;
        overflow: hidden;
    }}

    /* Glow Effect */
    .pbi-glow-effect {{
        position: absolute; top: 0; left: 0; right: 0; bottom: 0;
        border: 3px solid {pbi_glow_color};
        border-radius: inherit;
        box-shadow:
            0 0 18px 4px rgba(0, 123, 255, 0.25),
            inset 0 0 10px rgba(0, 123, 255, 0.2);
        animation: pbi-breathe 10s infinite ease-in-out;
        opacity: 0.8;
    }}
    @keyframes pbi-breathe {{
        0%   {{ opacity: 0.7; transform: scale(1); box-shadow: 0 0 18px 4px rgba(0, 123, 255, 0.25), inset 0 0 10px rgba(0, 123, 255, 0.2); }}
        50%  {{ opacity: 1.0; transform: scale(1.003); box-shadow: 0 0 25px 6px rgba(0, 123, 255, 0.35), inset 0 0 14px rgba(0, 123, 255, 0.25); }}
        100% {{ opacity: 0.7; transform: scale(1); box-shadow: 0 0 18px 4px rgba(0, 123, 255, 0.25), inset 0 0 10px rgba(0, 123, 255, 0.2); }}
    }}

    /* Particle Effect along Boundaries */
    .pbi-scatter-particle {{
        position: absolute;
        width: {particle_size}px; height: {particle_size}px;
        border-radius: 50%;
        background-color: {particle_color};
        filter: blur({particle_blur});
        animation: pbi-float 8s infinite ease-in-out alternate;
    }}
    {particle_css}
    @keyframes pbi-float {{
        0%   {{ opacity: 0.2; transform: translate(0px, 0px) scale(0.8); }}
        50%  {{ opacity: 0.8; transform: translate(4px, 4px) scale(1); }}
        100% {{ opacity: 0.2; transform: translate(8px, 8px) scale(0.8); }}
    }}

    /* Loading Overlay */
    .loading-container {{
        position: absolute; top: 0; left: 0; width: 100%; height: 100%;
        display: flex; flex-direction: column; justify-content: center; align-items: center;
        background-color: rgba(255, 255, 255, 0.95);
        z-index: 1001;
        transition: opacity 0.4s ease-out, visibility 0.4s ease-out;
        visibility: visible; opacity: 1;
    }}
    .loading-container.hidden {{ opacity: 0; visibility: hidden; }}
    .loading-spinner {{
        width: 45px; height: 45px; margin-bottom: 18px;
        border: 4px solid rgba(0, 123, 255, 0.2);
        border-radius: 50%; border-top-color: #007bff;
        animation: spin 1.2s linear infinite;
    }}
    .loading-text {{ color: #495057; font-size: 1rem; font-weight: 500; }}
    @keyframes spin {{ 100% {{ transform: rotate(360deg); }} }}

    /* Power BI Iframe */
    .power-bi-frame {{
        border: none;
        width: 100%; height: 100%;
        position: relative; z-index: 5;
        background: transparent;
    }}

    /* Error Message */
    .error-message {{
        position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%);
        background-color: #dc3545; color: white;
        padding: 15px 25px; border-radius: 5px; text-align: center;
        width: calc(100% - 40px); max-width: 500px;
        box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
        z-index: 1003;
        display: none; font-size: 0.95rem;
    }}

    /* Control Panel */
    .control-panel {{
        position: fixed;
        right: {control_panel_right}px; bottom: {control_panel_bottom}px;
        display: flex; gap: 10px; z-index: 1002;
        opacity: 0.75; transition: opacity 0.3s ease;
    }}
    .control-panel:hover {{ opacity: 1; }}
    .control-button {{
        background-color: rgba(255, 255, 255, 0.95); color: #0056b3;
        border: 1px solid #dee2e6; border-radius: 5px; padding: 8px 14px;
        font-size: 0.8rem; font-weight: 500; cursor: pointer;
        transition: all 0.2s ease; display: flex; align-items: center;
        gap: 6px; box-shadow: 0 2px 4px rgba(0,0,0,0.05); line-height: 1;
    }}
    .control-button:hover {{
        background-color: #0056b3; color: white; border-color: #0056b3;
        box-shadow: 0 3px 6px rgba(0,0,0,0.1);
    }}
    .control-button:hover .icon {{ border-color: white !important; }}
    .control-button:hover .refresh-icon::after {{ border-top-color: white !important; }}
    .control-button:hover .fullscreen-icon::before,
    .control-button:hover .fullscreen-icon::after {{ border-color: white !important; }}

    /* Icons */
    .icon {{ width: 14px; height: 14px; display: inline-block; vertical-align: middle; transition: border-color 0.2s ease; }}
    .refresh-icon {{ border: 2px solid #0056b3; border-radius: 50%; border-right-color: transparent; position: relative; animation: spin 1.5s linear infinite; animation-play-state: paused; }}
    .refresh-icon::after {{ content: ''; position: absolute; top: -3px; right: -1px; width: 0; height: 0; border-style: solid; border-width: 4px 4px 0 4px; border-color: #0056b3 transparent transparent transparent; transition: border-color 0.2s ease; }}
    .refreshing .refresh-icon {{ animation-play-state: running; }}
    .fullscreen-icon {{ border: 2px solid #0056b3; position: relative; }}
    .fullscreen-icon::before, .fullscreen-icon::after {{ content: ''; position: absolute; width: 4px; height: 4px; border-color: #0056b3; border-style: solid; transition: border-color 0.2s ease; }}
    .fullscreen-icon::before {{ top: -2px; left: -2px; border-width: 2px 0 0 2px; }}
    .fullscreen-icon::after {{ bottom: -2px; right: -2px; border-width: 0 2px 2px 0; }}
    .fullscreen-icon.is-fullscreen::before {{ top: auto; bottom: -2px; left: -2px; border-width: 0 0 2px 2px; }}
    .fullscreen-icon.is-fullscreen::after {{ top: -2px; bottom: auto; right: -2px; border-width: 2px 2px 0 0; }}

    /* Tooltip */
    .tooltip {{ position: relative; }}
    .tooltip .tooltip-text {{
        visibility: hidden; width: max-content; background-color: #343a40;
        color: white; text-align: center; border-radius: 4px; padding: 6px 10px;
        position: absolute; z-index: 1004; bottom: 140%; left: 50%;
        transform: translateX(-50%); opacity: 0; transition: opacity 0.3s, visibility 0.3s;
        font-size: 0.75rem; font-weight: 400; box-shadow: 0 2px 5px rgba(0,0,0,0.2);
        white-space: nowrap;
    }}
    .tooltip .tooltip-text::after {{ content: ""; position: absolute; top: 100%; left: 50%; margin-left: -5px; border-width: 5px; border-style: solid; border-color: #343a40 transparent transparent transparent; }}
    .tooltip:hover .tooltip-text {{ visibility: visible; opacity: 1; }}

</style>
</head>
<body>
    <!-- Dashboard Wrapper -->
    <div class="dashboard-wrapper" id="dashboardWrapper">
        <div class="dashboard-container" id="dashboardContainer">
            <div class="nav-tab-container">
                <div class="nav-tab">
                    {nav_image_html}
                </div>
                <!-- Dashboard Title now positioned to the left -->
                <div class="dashboard-title"> EASTERN BEARING DASHBOARD</div>
            </div>
            <div class="power-bi-container">
                <div class="pbi-effects-layer">
                    <div class="pbi-glow-effect"></div>
                    {' '.join(['<div class="pbi-scatter-particle"></div>' for _ in range(particle_count_pbi)])}
                </div>
                <div class="loading-container" id="loadingOverlay">
                    <div class="loading-spinner"></div>
                    <div class="loading-text">Loading Dashboard...</div>
                </div>
                <div class="error-message" id="errorMessage">
                    Failed to load dashboard. Please check connection or report setup and try refreshing.
                </div>
                <iframe
                    class="power-bi-frame"
                    id="powerBiFrame"
                    title="ARB Eastern Bearing Analysis Power BI Report"
                    aria-label="Embedded Power BI report for ARB Eastern Bearing Analysis"
                    width="{pbi_width}"
                    height="{pbi_height}"
                    src="https://app.powerbi.com/reportEmbed?reportId=edc2c5e4-eec4-46c1-bc44-cc39a5d10c97&autoAuth=true&ctid=c393e2ef-9c24-4bfc-bf28-c48ac7208f2e&navContentPaneEnabled=false&filterPaneEnabled=false&pageName=ReportSection"
                    frameborder="0"
                    allowFullScreen="true"
                    onload="iframeLoadSuccess()"
                    onerror="iframeLoadError(event)">
                </iframe>
            </div>
        </div>
    </div>
    <!-- Controls -->
    <div class="control-panel">
        <button class="control-button tooltip" id="refreshButton" onclick="refreshReport()" aria-label="Refresh dashboard data">
            <span class="icon refresh-icon"></span>
            <span>Refresh</span>
            <span class="tooltip-text">Reload latest data</span>
        </button>
        <button class="control-button tooltip" id="fullscreenButton" onclick="toggleFullscreen()" aria-label="Toggle fullscreen mode">
            <span class="icon fullscreen-icon" id="fullscreenIcon"></span>
            <span id="fullscreenText">Fullscreen</span>
            <span class="tooltip-text">Toggle fullscreen</span>
        </button>
    </div>
<script>
    const loadingOverlay = document.getElementById('loadingOverlay');
    const errorMessage = document.getElementById('errorMessage');
    const iframe = document.getElementById('powerBiFrame');
    const dashboardWrapper = document.getElementById('dashboardWrapper');
    const fullscreenButton = document.getElementById('fullscreenButton');
    const fullscreenIcon = document.getElementById('fullscreenIcon');
    const fullscreenText = document.getElementById('fullscreenText');
    const refreshButton = document.getElementById('refreshButton');

    function iframeLoadSuccess() {{
        console.log("Iframe loaded successfully.");
        loadingOverlay.classList.add('hidden');
        errorMessage.style.display = 'none';
        refreshButton.classList.remove('refreshing');
    }}

    function iframeLoadError(event) {{
        console.error("Iframe failed to load. Event:", event);
        errorMessage.textContent = 'Error loading dashboard. Please check the report link or your connection.';
        errorMessage.style.display = 'block';
        loadingOverlay.classList.add('hidden');
        refreshButton.classList.remove('refreshing');
    }}

    iframe.onload = iframeLoadSuccess;
    iframe.onerror = iframeLoadError;

    function refreshReport() {{
        console.log("Attempting to refresh iframe...");
        loadingOverlay.classList.remove('hidden');
        errorMessage.style.display = 'none';
        refreshButton.classList.add('refreshing');
        const currentSrc = iframe.src;
        iframe.src = 'about:blank';
        setTimeout(() => {{
            console.log("Resetting iframe src to:", currentSrc);
            iframe.onload = iframeLoadSuccess;
            iframe.onerror = iframeLoadError;
            iframe.src = currentSrc;
        }}, 60);
    }}

    function toggleFullscreen() {{
        const elementToFullscreen = dashboardWrapper;
        if (!document.fullscreenElement && !document.webkitFullscreenElement) {{
            console.log("Requesting fullscreen for wrapper element.");
            if (elementToFullscreen.requestFullscreen) {{
                elementToFullscreen.requestFullscreen().catch(err => {{
                    console.error(`Error attempting to enable full-screen mode: ${{err.message}} (${{err.name}})`);
                    alert(`Fullscreen request failed: ${{err.message}}`);
                }});
            }} else if (elementToFullscreen.webkitRequestFullscreen) {{
                elementToFullscreen.webkitRequestFullscreen().catch(err => {{
                    console.error(`Error attempting to enable full-screen mode: ${{err.message}} (${{err.name}})`);
                    alert(`Fullscreen request failed: ${{err.message}}`);
                }});
            }} else if (elementToFullscreen.msRequestFullscreen) {{
                elementToFullscreen.msRequestFullscreen();
            }}
        }} else {{
            console.log("Exiting fullscreen.");
            if (document.exitFullscreen) {{
                document.exitFullscreen().catch(err => {{
                    console.error(`Error attempting to disable full-screen mode: ${{err.message}} (${{err.name}})`);
                }});
            }} else if (document.webkitExitFullscreen) {{
                document.webkitExitFullscreen().catch(err => {{
                    console.error(`Error attempting to disable full-screen mode: ${{err.message}} (${{err.name}})`);
                }});
            }} else if (document.msExitFullscreen) {{
                document.msExitFullscreen();
            }}
        }}
    }}

    function handleFullscreenChange() {{
        const isFullscreen = !!(document.fullscreenElement || document.webkitFullscreenElement);
        console.log("Fullscreen state changed. Is fullscreen:", isFullscreen);
        if (isFullscreen) {{
            fullscreenIcon.classList.add('is-fullscreen');
            fullscreenText.textContent = 'Exit Fullscreen';
            document.body.classList.add('in-fullscreen-mode');
        }} else {{
            fullscreenIcon.classList.remove('is-fullscreen');
            fullscreenText.textContent = 'Fullscreen';
            document.body.classList.remove('in-fullscreen-mode');
        }}
    }}

    document.addEventListener('fullscreenchange', handleFullscreenChange);
    document.addEventListener('webkitfullscreenchange', handleFullscreenChange);
    document.addEventListener('mozfullscreenchange', handleFullscreenChange);
    document.addEventListener('MSFullscreenChange', handleFullscreenChange);

    let initialLoadComplete = false;
    function checkInitialLoad() {{
        if (!initialLoadComplete && iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
            initialLoadComplete = true;
            console.log("Iframe detected as complete on initial check/readystatechange.");
            iframeLoadSuccess();
            iframe.removeEventListener('readystatechange', checkInitialLoad);
        }}
    }}

    if (iframe.contentDocument && iframe.contentDocument.readyState === 'complete') {{
         checkInitialLoad();
    }} else {{
         iframe.addEventListener('readystatechange', checkInitialLoad);
         iframe.addEventListener('load', () => {{ checkInitialLoad(); }}, {{ once: true }});
    }}
</script>
</body>
</html>
"""

display_height = content_height + 100
st.components.v1.html(iframe_code, height=display_height, scrolling=True)
