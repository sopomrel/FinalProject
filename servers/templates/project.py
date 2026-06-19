"""HTML template for the project navigation dashboard."""

from .base import render_template

_EXTRA_CSS = '''
/* ── Tabs ─────────────────────────────────────────────────────────────────── */
.tab-bar {
    display: flex;
    gap: 4px;
    margin-bottom: 12px;
    border-bottom: 1px solid var(--border-color);
    padding-bottom: 0;
}
.tab-btn {
    padding: 7px 18px;
    border: none;
    border-bottom: 2px solid transparent;
    background: transparent;
    color: var(--text-secondary);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    border-radius: 4px 4px 0 0;
    transition: color 0.15s, border-color 0.15s;
    font-family: inherit;
    margin-bottom: -1px;
}
.tab-btn:hover { color: var(--text-primary); }
.tab-btn.active { color: var(--accent-blue); border-bottom-color: var(--accent-blue); }
.tab-panel { display: none; flex-direction: column; gap: 12px; }
.tab-panel.active { display: flex; }

/* ── Status badge ─────────────────────────────────────────────────────────── */
.status-badge {
    display: inline-block;
    padding: 2px 8px;
    border-radius: 10px;
    font-size: 11px;
    font-weight: 600;
}
.status-badge.running { background: rgba(63,185,80,0.15); color: #3fb950; border: 1px solid #3fb950; }
.status-badge.stopped { background: rgba(248,81,73,0.15);  color: #f85149; border: 1px solid #f85149; }
.status-badge.manual  { background: rgba(163,113,247,0.15); color: #a371f7; border: 1px solid #a371f7; }

/* ── Route picker ─────────────────────────────────────────────────────────── */
.route-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 8px;
    margin-bottom: 8px;
}
.route-btn {
    padding: 8px 4px;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background: var(--bg-sidebar);
    color: var(--text-primary);
    font-size: 13px;
    font-weight: 600;
    cursor: pointer;
    transition: background 0.15s, border-color 0.15s;
}
.route-btn:hover { background: var(--accent-blue); border-color: var(--accent-blue); color: #fff; }
.route-btn.active { background: var(--accent-blue); border-color: var(--accent-blue); color: #fff; }
.route-display {
    font-size: 22px;
    font-weight: 700;
    color: var(--accent-blue);
    text-align: center;
    margin: 4px 0 4px;
    letter-spacing: 1px;
}
.heading-hint {
    text-align: center;
    font-size: 12px;
    color: var(--text-secondary);
    margin-bottom: 10px;
}
.heading-hint strong { color: var(--accent-orange); font-size: 14px; }
.approach-grid {
    display: grid;
    grid-template-columns: repeat(5, 1fr);
    gap: 6px;
    margin: 8px 0 10px;
}
.approach-btn {
    padding: 6px 2px;
    border-radius: 6px;
    border: 1px solid var(--border-color);
    background: var(--bg-sidebar);
    color: var(--text-primary);
    font-size: 11px;
    font-weight: 600;
    cursor: pointer;
}
.approach-btn:hover { background: var(--accent-orange); border-color: var(--accent-orange); color: #fff; }
.approach-btn.active { background: var(--accent-orange); border-color: var(--accent-orange); color: #fff; }
.approach-label {
    text-align: center;
    font-size: 11px;
    color: var(--text-muted);
    margin-bottom: 4px;
}

/* ── HSV section titles ───────────────────────────────────────────────────── */
.hsv-section-title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-secondary);
    margin: 12px 0 8px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.hsv-section-title.red1 { color: #ff6b6b; }
.hsv-section-title.red2 { color: #ff4444; }
.hsv-section-title.yellow { color: #f1c40f; }
.hsv-section-title.white  { color: #ecf0f1; }
.control-group { margin-bottom: 16px; }
.control-group label { display: block; margin-bottom: 6px; font-size: 13px; font-weight: 600; }
.control-row { display: flex; align-items: center; gap: 10px; }
.value-display { min-width: 48px; text-align: right; font-family: monospace; font-size: 12px; color: var(--text-secondary); }

/* ── Manual key display ───────────────────────────────────────────────────── */
.key-display {
    display: grid;
    grid-template-areas: ". up ." "left down right";
    gap: 6px;
    justify-content: center;
    margin: 12px 0 8px;
}
.key-box {
    width: 44px; height: 44px;
    display: flex; align-items: center; justify-content: center;
    border: 1px solid var(--border-color);
    border-radius: 6px;
    font-size: 16px; font-weight: 700;
    color: var(--text-muted);
    background: var(--bg-sidebar);
    transition: background 0.1s, border-color 0.1s, color 0.1s;
    user-select: none;
}
.key-box.active { background: rgba(63,185,80,0.2); border-color: var(--accent-green); color: var(--accent-green); }
.key-up    { grid-area: up; }
.key-down  { grid-area: down; }
.key-left  { grid-area: left; }
.key-right { grid-area: right; }
.key-hint  { text-align: center; font-size: 11px; color: var(--text-muted); margin-top: 2px; }
'''

_CONTENT = '''
    <div class="container">
        <div class="video-section">
            <img src="{{ url_for('video') }}" class="stream" alt="Navigation Stream">
        </div>

        <div class="controls-section">

            <!-- Tab bar -->
            <div class="tab-bar">
                <button class="tab-btn active" onclick="switchTab('auto',this)">Auto Navigation</button>
                <button class="tab-btn"        onclick="switchTab('manual',this)">Manual Control</button>
                <button class="tab-btn"        onclick="switchTab('lane',this)">Lane Calibration</button>
            </div>

            <!-- ══ AUTO TAB ══════════════════════════════════════════════════ -->
            <div id="tab-auto" class="tab-panel active">

                <!-- Route picker -->
                <div class="card">
                    <div class="card-header">Select Route</div>
                    <div class="route-display" id="route-display">A → C</div>
                    <div class="heading-hint">
                        Place the robot on the road facing
                        <strong id="hint-approach">North ↑</strong>,
                        lane-follow to red line at <strong id="hint-start">A</strong>,
                        then to <strong id="hint-goal">C</strong>
                        (<strong id="hint-red-count">3</strong> red lines total)
                    </div>
                    <div class="approach-label">Robot heading when crossing the start red line</div>
                    <div class="approach-grid">
                        <button class="approach-btn active" id="appr-N" onclick="setApproach('N')">N ↑</button>
                        <button class="approach-btn" id="appr-S" onclick="setApproach('S')">S ↓</button>
                        <button class="approach-btn" id="appr-E" onclick="setApproach('E')">E →</button>
                        <button class="approach-btn" id="appr-W" onclick="setApproach('W')">W ←</button>
                        <button class="approach-btn" id="appr-auto" onclick="setApproach('auto')">Auto</button>
                    </div>
                    <div id="route-plan" class="heading-hint" style="margin-top:6px;font-size:11px"></div>
                    <div class="route-grid">
                        <button class="route-btn" onclick="setRoute(\'A\',\'B\')">A → B</button>
                        <button class="route-btn active" onclick="setRoute(\'A\',\'C\')">A → C</button>
                        <button class="route-btn" onclick="setRoute(\'B\',\'A\')">B → A</button>
                        <button class="route-btn" onclick="setRoute(\'B\',\'C\')">B → C</button>
                        <button class="route-btn" onclick="setRoute(\'C\',\'A\')">C → A</button>
                        <button class="route-btn" onclick="setRoute(\'C\',\'B\')">C → B</button>
                    </div>
                    <div id="route-status" class="status"></div>
                </div>

                <!-- Navigation status -->
                <div class="card">
                    <div class="card-header">
                        Navigation Status
                        <span id="run-badge" class="status-badge stopped">STOPPED</span>
                    </div>
                    <div class="stats-grid">
                        <div class="stat-box">
                            <div class="stat-value" id="stat-state">—</div>
                            <div class="stat-label">State</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value" id="stat-redline">1/3</div>
                            <div class="stat-label">Red Line</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value" id="stat-turn">—</div>
                            <div class="stat-label">At Line</div>
                        </div>
                        <div class="stat-box">
                            <div class="stat-value" id="stat-red">0.000</div>
                            <div class="stat-label">Red Ratio</div>
                        </div>
                    </div>
                    <div style="display:flex;gap:10px;margin-top:4px">
                        <button onclick="driveStart()" class="button success" style="flex:1">Start</button>
                        <button onclick="driveStop()"  class="button danger"  style="flex:1">Stop</button>
                    </div>
                    <div style="display:flex;gap:10px;margin-top:8px">
                        <button onclick="resetRoute()"    class="button" style="flex:1;background:#2d6a6a">Reset Route</button>
                        <button onclick="resetPosition()" class="button" style="flex:1;background:var(--accent-orange)">Reset Position</button>
                    </div>
                    <div id="nav-status" class="status"></div>
                </div>

                <!-- Intersection crossing timing -->
                <div class="card">
                    <div class="card-header">Intersection Crossing Timing</div>
                    <p style="font-size:12px;color:var(--text-muted);margin:0 0 10px">
                        <strong>Crossing duration</strong> = total seconds driving through the intersection.
                        <strong>Forward bias</strong> = straight creep before the turn fully engages.
                        Saved to <code>navigation_config.yaml</code>.
                    </p>

                    <div class="hsv-section-title">Stop at red line</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Wait before crossing (s)</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navStopWait" min="0" max="15" step="0.5" value="5" class="slider">
                            <input type="number" id="navStopWait-input" min="0" max="15" step="0.5" value="5" class="input-box">
                        </div>
                    </div>

                    <div class="hsv-section-title" style="margin-top:14px">Crossing duration (s)</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Straight through</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navCrossStraight" min="0.5" max="6" step="0.05" value="2.8" class="slider">
                            <input type="number" id="navCrossStraight-input" min="0.5" max="6" step="0.05" value="2.8" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Left turn</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navCrossLeft" min="0.5" max="6" step="0.05" value="3.4" class="slider">
                            <input type="number" id="navCrossLeft-input" min="0.5" max="6" step="0.05" value="3.4" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Right turn</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navCrossRight" min="0.5" max="6" step="0.05" value="2.6" class="slider">
                            <input type="number" id="navCrossRight-input" min="0.5" max="6" step="0.05" value="2.6" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Goal line (creep)</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navCrossGoal" min="0.1" max="3" step="0.05" value="0.5" class="slider">
                            <input type="number" id="navCrossGoal-input" min="0.1" max="3" step="0.05" value="0.5" class="input-box">
                        </div>
                    </div>

                    <div class="hsv-section-title" style="margin-top:14px">Forward bias before turn (s)</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Left turn</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navBiasLeft" min="0" max="2" step="0.05" value="0.55" class="slider">
                            <input type="number" id="navBiasLeft-input" min="0" max="2" step="0.05" value="0.55" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Right turn</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navBiasRight" min="0" max="2" step="0.05" value="0.2" class="slider">
                            <input type="number" id="navBiasRight-input" min="0" max="2" step="0.05" value="0.2" class="input-box">
                        </div>
                    </div>

                    <div class="hsv-section-title" style="margin-top:14px">Victory dance (after mission)</div>
                    <p style="font-size:12px;color:var(--text-muted);margin:0 0 10px">
                        After the goal line: drive forward into the intersection, then spin in place.
                        All LEDs flash blue every 0.5 s during the celebration.
                    </p>
                    <div class="slider-group">
                        <div class="slider-label"><span>Drive forward after victory (s)</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navVictoryForward" min="0" max="5" step="0.1" value="1.5" class="slider">
                            <input type="number" id="navVictoryForward-input" min="0" max="5" step="0.1" value="1.5" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Spin celebration (s)</span></div>
                        <div class="slider-controls">
                            <input type="range" id="navVictorySpin" min="0" max="10" step="0.1" value="3" class="slider">
                            <input type="number" id="navVictorySpin-input" min="0" max="10" step="0.1" value="3" class="input-box">
                        </div>
                    </div>
                    <div id="nav-timing-status" class="status"></div>
                </div>

                <!-- HSV calibration -->
                <div class="card">
                    <div class="card-header">Red Stop-Line HSV Calibration</div>

                    <div class="hsv-section-title red1">Range 1 (hue near 0°)</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Hue High</span><span style="color:var(--text-muted)">0–30</span></div>
                        <div class="slider-controls">
                            <input type="range" id="r1HighH" min="0" max="30" value="10" class="slider">
                            <input type="number" id="r1HighH-input" min="0" max="30" value="10" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Saturation Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="r1LowS" min="0" max="255" value="80" class="slider">
                            <input type="number" id="r1LowS-input" min="0" max="255" value="80" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Value Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="r1LowV" min="0" max="255" value="80" class="slider">
                            <input type="number" id="r1LowV-input" min="0" max="255" value="80" class="input-box">
                        </div>
                    </div>

                    <div class="hsv-section-title red2" style="margin-top:16px">Range 2 (hue near 180°)</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Hue Low</span><span style="color:var(--text-muted)">150–179</span></div>
                        <div class="slider-controls">
                            <input type="range" id="r2LowH" min="150" max="179" value="160" class="slider">
                            <input type="number" id="r2LowH-input" min="150" max="179" value="160" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Saturation Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="r2LowS" min="0" max="255" value="80" class="slider">
                            <input type="number" id="r2LowS-input" min="0" max="255" value="80" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Value Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="r2LowV" min="0" max="255" value="80" class="slider">
                            <input type="number" id="r2LowV-input" min="0" max="255" value="80" class="input-box">
                        </div>
                    </div>

                    <div class="hsv-section-title" style="margin-top:16px">ROI &amp; Threshold</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>ROI top (% from top)</span><span style="color:var(--text-muted)">0–100</span></div>
                        <div class="slider-controls">
                            <input type="range" id="roiY" min="0" max="100" value="45" class="slider">
                            <input type="number" id="roiY-input" min="0" max="100" value="45" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>ROI side margin (% from edge)</span><span style="color:var(--text-muted)">0–100</span></div>
                        <div class="slider-controls">
                            <input type="range" id="roiX" min="0" max="100" value="15" class="slider">
                            <input type="number" id="roiX-input" min="0" max="100" value="15" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Min red ratio ×1000</span><span style="color:var(--text-muted)">1–100</span></div>
                        <div class="slider-controls">
                            <input type="range" id="minRed" min="1" max="100" value="12" class="slider">
                            <input type="number" id="minRed-input" min="1" max="100" value="12" class="input-box">
                        </div>
                    </div>
                    <div id="hsv-status" class="status"></div>
                </div>

            </div><!-- /tab-auto -->

            <!-- ══ MANUAL TAB ═════════════════════════════════════════════════ -->
            <div id="tab-manual" class="tab-panel">

                <div class="card">
                    <div class="card-header">
                        Manual Drive
                        <span id="manual-badge" class="status-badge stopped">OFF</span>
                    </div>
                    <div style="display:flex;gap:10px;margin-bottom:8px">
                        <button id="manual-toggle" onclick="toggleManual()" class="button" style="flex:1;background:#6e40c9">Enable Manual</button>
                        <button onclick="resetPosition()" class="button" style="flex:1;background:var(--accent-orange)">Reset</button>
                    </div>
                    <p style="font-size:12px;color:var(--text-muted);margin-bottom:4px;text-align:center">
                        Enabling manual stops auto-navigation.
                    </p>

                    <!-- Arrow key pad -->
                    <div class="key-display">
                        <div class="key-box key-up"    id="key-up">&#9650;</div>
                        <div class="key-box key-left"  id="key-left">&#9664;</div>
                        <div class="key-box key-down"  id="key-down">&#9660;</div>
                        <div class="key-box key-right" id="key-right">&#9654;</div>
                    </div>
                    <p class="key-hint">Arrow keys or WASD &nbsp;·&nbsp; click here first to capture keyboard</p>

                    <!-- On-screen touch buttons -->
                    <div style="display:grid;grid-template-areas:\'. u .\' \'l d r\';gap:6px;justify-content:center;margin-top:10px">
                        <button style="grid-area:u" class="button" style="width:44px;height:44px;padding:0;margin:0"
                            onpointerdown="onScreenKey(\'up\',true)"   onpointerup="onScreenKey(\'up\',false)"   onpointerleave="onScreenKey(\'up\',false)">&#9650;</button>
                        <button style="grid-area:l" class="button" style="width:44px;height:44px;padding:0;margin:0"
                            onpointerdown="onScreenKey(\'left\',true)" onpointerup="onScreenKey(\'left\',false)" onpointerleave="onScreenKey(\'left\',false)">&#9664;</button>
                        <button style="grid-area:d" class="button" style="width:44px;height:44px;padding:0;margin:0"
                            onpointerdown="onScreenKey(\'down\',true)" onpointerup="onScreenKey(\'down\',false)" onpointerleave="onScreenKey(\'down\',false)">&#9660;</button>
                        <button style="grid-area:r" class="button" style="width:44px;height:44px;padding:0;margin:0"
                            onpointerdown="onScreenKey(\'right\',true)" onpointerup="onScreenKey(\'right\',false)" onpointerleave="onScreenKey(\'right\',false)">&#9654;</button>
                    </div>

                    <div style="margin-top:12px">
                        <button onclick="backToAuto()" class="button success">Switch to Auto Navigation</button>
                    </div>
                    <div id="manual-status" class="status"></div>
                </div>

            </div><!-- /tab-manual -->

            <!-- ══ LANE CALIBRATION TAB ══════════════════════════════════════ -->
            <div id="tab-lane" class="tab-panel">

                <div class="card">
                    <div class="card-header">Lane Mask Preview</div>
                    <p style="font-size:12px;color:var(--text-muted);margin-bottom:8px">
                        Video shows camera + lane / white / yellow masks (same as visual lane servoing).
                        Adjust HSV below — changes save to <code>lane_servoing_hsv_config.yaml</code>.
                    </p>
                </div>

                <div class="card">
                    <div class="card-header">Lane HSV Calibration</div>

                    <div class="hsv-section-title yellow">Yellow Line (left / dashed)</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Hue Low</span><span style="color:var(--text-muted)">0–179</span></div>
                        <div class="slider-controls">
                            <input type="range" id="yLowH" min="0" max="179" value="20" class="slider">
                            <input type="number" id="yLowH-input" min="0" max="179" value="20" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Hue High</span><span style="color:var(--text-muted)">0–179</span></div>
                        <div class="slider-controls">
                            <input type="range" id="yHighH" min="0" max="179" value="40" class="slider">
                            <input type="number" id="yHighH-input" min="0" max="179" value="40" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Saturation Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="yLowS" min="0" max="255" value="80" class="slider">
                            <input type="number" id="yLowS-input" min="0" max="255" value="80" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Saturation High</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="yHighS" min="0" max="255" value="255" class="slider">
                            <input type="number" id="yHighS-input" min="0" max="255" value="255" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Value Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="yLowV" min="0" max="255" value="100" class="slider">
                            <input type="number" id="yLowV-input" min="0" max="255" value="100" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Value High</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="yHighV" min="0" max="255" value="255" class="slider">
                            <input type="number" id="yHighV-input" min="0" max="255" value="255" class="input-box">
                        </div>
                    </div>

                    <div class="hsv-section-title white" style="margin-top:16px">White Line (right / solid)</div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Hue Low</span><span style="color:var(--text-muted)">0–179</span></div>
                        <div class="slider-controls">
                            <input type="range" id="wLowH" min="0" max="179" value="0" class="slider">
                            <input type="number" id="wLowH-input" min="0" max="179" value="0" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Hue High</span><span style="color:var(--text-muted)">0–179</span></div>
                        <div class="slider-controls">
                            <input type="range" id="wHighH" min="0" max="179" value="179" class="slider">
                            <input type="number" id="wHighH-input" min="0" max="179" value="179" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Saturation Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="wLowS" min="0" max="255" value="0" class="slider">
                            <input type="number" id="wLowS-input" min="0" max="255" value="0" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Saturation High</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="wHighS" min="0" max="255" value="40" class="slider">
                            <input type="number" id="wHighS-input" min="0" max="255" value="40" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Value Low</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="wLowV" min="0" max="255" value="180" class="slider">
                            <input type="number" id="wLowV-input" min="0" max="255" value="180" class="input-box">
                        </div>
                    </div>
                    <div class="slider-group">
                        <div class="slider-label"><span>Value High</span><span style="color:var(--text-muted)">0–255</span></div>
                        <div class="slider-controls">
                            <input type="range" id="wHighV" min="0" max="255" value="255" class="slider">
                            <input type="number" id="wHighV-input" min="0" max="255" value="255" class="input-box">
                        </div>
                    </div>
                    <div id="lane-hsv-status" class="status"></div>
                </div>

                <div class="card">
                    <div class="card-header">Lane Control Parameters</div>
                    <div class="control-group">
                        <label for="k_d">Lateral Gain (k_d)</label>
                        <div class="control-row">
                            <input type="range" id="k_d" class="slider" min="0" max="1" step="0.01" value="0.1">
                            <span class="value-display" id="k_d_value">0.1</span>
                        </div>
                    </div>
                    <div class="control-group">
                        <label for="k_phi">Heading Gain (k_phi)</label>
                        <div class="control-row">
                            <input type="range" id="k_phi" class="slider" min="0" max="2" step="0.01" value="0.35">
                            <span class="value-display" id="k_phi_value">0.35</span>
                        </div>
                    </div>
                    <div class="control-group">
                        <label for="laneSpeed">Base Speed <span style="color:var(--text-muted);font-weight:400;font-size:11px">(PWM 0–1)</span></label>
                        <div class="control-row">
                            <input type="range" id="laneSpeed" class="slider" min="0" max="1" step="0.01" value="0.2">
                            <span class="value-display" id="laneSpeed_value">0.2</span>
                        </div>
                    </div>
                    <button onclick="updateLaneConfig()" class="button success">Apply Lane Config</button>
                    <div id="lane-config-status" class="status"></div>
                </div>

            </div><!-- /tab-lane -->

        </div>
    </div>
'''

_JS = '''
    // ── Tab switching ─────────────────────────────────────────────────────────
    const TAB_VIEWS = { auto: 'nav', manual: 'nav', lane: 'lane' };

    function switchTab(name, btn) {
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('tab-' + name).classList.add('active');
        btn.classList.add('active');
        postJSON('/set_view', { view: TAB_VIEWS[name] || 'nav' }).catch(() => {});
    }

    // ── Route selection ───────────────────────────────────────────────────────
    const HEADING_LABEL = { N: 'North ↑', S: 'South ↓', E: 'East →', W: 'West ←' };
    let selectedApproach = 'N';

    function setApproach(dir) {
        selectedApproach = dir;
        document.querySelectorAll('.approach-btn').forEach(btn => btn.classList.remove('active'));
        const btn = document.getElementById('appr-' + dir.toLowerCase());
        if (btn) btn.classList.add('active');
        const start = document.getElementById('hint-start').textContent;
        const goal  = document.getElementById('route-display').textContent.split('→').map(s => s.trim());
        if (goal.length === 2) setRoute(goal[0], goal[1]);
    }

    function formatStopPlan(stops) {
        if (!stops || !stops.length) return '';
        return stops.map((s, i) => {
            const turn = s.turn === 'done' ? 'finish' : s.turn;
            return `${i + 1}. ${s.intersection} → ${turn}`;
        }).join(' · ');
    }

    function setRoute(start, goal) {
        postJSON('/set_route', { start, goal, approach: selectedApproach })
            .then(d => {
                if (d.status === 'ok') {
                    updateRouteUI(d);
                    showStatus('route-status', `Route set: ${d.start} → ${d.goal}`, 'success');
                } else {
                    showStatus('route-status', d.message || 'Error', 'error');
                }
            })
            .catch(() => showStatus('route-status', 'Request failed', 'error'));
    }

    function updateRouteUI(d) {
        const start = d.start || d.route_start;
        const goal  = d.goal  || d.route_goal;
        if (!start || !goal) return;

        document.getElementById('route-display').textContent = `${start} → ${goal}`;
        document.getElementById('hint-start').textContent = start;
        document.getElementById('hint-goal').textContent = goal;

        const n = d.num_red_lines || (d.stops ? d.stops.length : 0);
        document.getElementById('hint-red-count').textContent = n || '—';

        const approach = d.approach_heading;
        if (approach) {
            document.getElementById('hint-approach').textContent = HEADING_LABEL[approach] || approach;
            selectedApproach = approach;
            document.querySelectorAll('.approach-btn').forEach(btn => btn.classList.remove('active'));
            const btn = document.getElementById('appr-' + approach.toLowerCase());
            if (btn) btn.classList.add('active');
        } else {
            document.getElementById('hint-approach').textContent = 'route lane';
            selectedApproach = 'auto';
            document.querySelectorAll('.approach-btn').forEach(btn => btn.classList.remove('active'));
            document.getElementById('appr-auto').classList.add('active');
        }

        const plan = formatStopPlan(d.stops);
        document.getElementById('route-plan').textContent = plan || d.route_summary || '';

        document.querySelectorAll('.route-btn').forEach(btn => {
            const label = btn.textContent.trim().replace(/\\s/g, '');
            btn.classList.toggle('active', label === `${start}→${goal}`);
        });
    }

    // ── Status polling ────────────────────────────────────────────────────────
    function pollStatus() {
        fetch('/status').then(r => r.json()).then(d => {
            document.getElementById('stat-state').textContent = d.state  || '—';
            document.getElementById('stat-turn').textContent  = d.next_stop || d.turn || '—';
            document.getElementById('stat-red').textContent   = (d.red_ratio || 0).toFixed(4);
            const ri = d.red_line_index || 1;
            const rn = d.red_line_total || d.num_red_lines || 0;
            document.getElementById('stat-redline').textContent = rn ? `${ri}/${rn}` : '—';

            const badge = document.getElementById('run-badge');
            if (d.manual_mode) {
                badge.textContent = 'MANUAL'; badge.className = 'status-badge manual';
            } else if (d.running) {
                badge.textContent = 'RUNNING'; badge.className = 'status-badge running';
            } else {
                badge.textContent = 'STOPPED'; badge.className = 'status-badge stopped';
            }

            // Sync manual badge + button label
            const mb = document.getElementById('manual-badge');
            const mt = document.getElementById('manual-toggle');
            if (d.manual_mode) {
                mb.textContent = 'ON';  mb.className = 'status-badge running';
                mt.textContent = 'Disable Manual'; mt.style.background = '#c0392b';
            } else {
                mb.textContent = 'OFF'; mb.className = 'status-badge stopped';
                mt.textContent = 'Enable Manual';  mt.style.background = '#6e40c9';
            }
            _manualMode = !!d.manual_mode;

            if (d.route_start && d.route_goal)
                updateRouteUI(d);
            if (d.nav_config) loadNavConfig(d.nav_config);
        }).catch(() => {});
    }
    setInterval(pollStatus, 500);
    pollStatus();

    // ── Auto drive controls ───────────────────────────────────────────────────
    function driveStart() {
        postJSON('/start', {})
            .then(() => showStatus('nav-status', 'Started!', 'success'))
            .catch(() => showStatus('nav-status', 'Start failed', 'error'));
    }
    function driveStop() {
        postJSON('/stop', {})
            .then(() => showStatus('nav-status', 'Stopped.', 'success'))
            .catch(() => showStatus('nav-status', 'Stop failed', 'error'));
    }
    function resetRoute() {
        postJSON('/reset_route', {})
            .then(() => showStatus('nav-status', 'Route reset — ready to re-run!', 'success'))
            .catch(() => showStatus('nav-status', 'Reset failed', 'error'));
    }
    function resetPosition() {
        postJSON('/reset', {})
            .then(() => showStatus('nav-status', 'Position + route reset!', 'success'))
            .catch(() => showStatus('nav-status', 'Reset failed', 'error'));
    }

    // ── Manual control ────────────────────────────────────────────────────────
    let _manualMode = false;
    const keyState = {up: false, down: false, left: false, right: false};
    const keyMap = {
        'ArrowUp':'up','w':'up','W':'up',
        'ArrowDown':'down','s':'down','S':'down',
        'ArrowLeft':'left','a':'left','A':'left',
        'ArrowRight':'right','d':'right','D':'right',
    };

    function updateKeyDisplay() {
        ['up','down','left','right'].forEach(k => {
            const el = document.getElementById('key-' + k);
            if (el) el.classList.toggle('active', keyState[k]);
        });
    }

    function sendKeys() {
        fetch('/keys', {method:'POST', headers:{'Content-Type':'application/json'},
            body: JSON.stringify(keyState)}).catch(() => {});
    }

    function toggleManual() {
        _manualMode = !_manualMode;
        postJSON('/set_mode', {mode: _manualMode ? 'manual' : 'auto'})
            .then(() => showStatus('manual-status',
                _manualMode ? 'Manual enabled — use arrow keys / WASD' : 'Auto mode restored', 'success'));
    }

    function backToAuto() {
        if (_manualMode) {
            _manualMode = false;
            postJSON('/set_mode', {mode: 'auto'});
        }
        document.querySelectorAll('.tab-panel').forEach(p => p.classList.remove('active'));
        document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
        document.getElementById('tab-auto').classList.add('active');
        document.querySelectorAll('.tab-btn')[0].classList.add('active');
        postJSON('/set_view', { view: 'nav' }).catch(() => {});
    }

    function onScreenKey(dir, down) {
        if (!_manualMode) return;
        keyState[dir] = down;
        updateKeyDisplay();
        sendKeys();
    }

    document.addEventListener('keydown', e => {
        const dir = keyMap[e.key];
        if (dir && !keyState[dir]) {
            e.preventDefault();
            keyState[dir] = true;
            updateKeyDisplay();
            if (_manualMode) sendKeys();
        }
    });
    document.addEventListener('keyup', e => {
        const dir = keyMap[e.key];
        if (dir) {
            e.preventDefault();
            keyState[dir] = false;
            updateKeyDisplay();
            if (_manualMode) sendKeys();
        }
    });
    window.addEventListener('blur', () => {
        Object.keys(keyState).forEach(k => keyState[k] = false);
        updateKeyDisplay();
        if (_manualMode) sendKeys();
    });
    // Heartbeat while keys are held
    setInterval(() => {
        if (_manualMode && Object.values(keyState).some(Boolean)) sendKeys();
    }, 150);

    // ── Navigation crossing timing (float sliders) ───────────────────────────
    function setNavSlider(id, value) {
        const v = parseFloat(value);
        document.getElementById(id).value = v;
        document.getElementById(id + '-input').value = Number(v).toFixed(2);
    }

    function syncNavSlider(sliderId, onChange) {
        const slider = document.getElementById(sliderId);
        const input  = document.getElementById(sliderId + '-input');
        let timeout  = null;
        const clamp = (raw) => {
            let v = parseFloat(raw);
            if (isNaN(v)) return parseFloat(slider.value);
            return Math.max(parseFloat(slider.min), Math.min(parseFloat(slider.max), v));
        };
        const apply = (v) => {
            setNavSlider(sliderId, v);
            clearTimeout(timeout);
            timeout = setTimeout(onChange, 250);
        };
        slider.addEventListener('input', function() { apply(this.value); });
        input.addEventListener('input', function() { apply(clamp(this.value)); });
    }

    function loadNavConfig(cfg) {
        if (!cfg) return;
        setNavSlider('navStopWait', cfg.stop_wait_s ?? 5);
        const cf = cfg.cross_forward_s || {};
        setNavSlider('navCrossStraight', cf.straight ?? 2.8);
        setNavSlider('navCrossLeft',     cf.left     ?? 3.4);
        setNavSlider('navCrossRight',    cf.right    ?? 2.6);
        setNavSlider('navCrossGoal',     cf.goal     ?? 0.5);
        const fb = cfg.forward_bias_s || {};
        setNavSlider('navBiasLeft',  fb.left  ?? 0.55);
        setNavSlider('navBiasRight', fb.right ?? 0.2);
        setNavSlider('navVictoryForward', cfg.victory_forward_s ?? 1.5);
        setNavSlider('navVictorySpin',    cfg.victory_spin_s    ?? 3.0);
    }

    function pushNavConfig() {
        const payload = {
            stop_wait_s: parseFloat(document.getElementById('navStopWait').value),
            cross_forward_s: {
                straight: parseFloat(document.getElementById('navCrossStraight').value),
                left:     parseFloat(document.getElementById('navCrossLeft').value),
                right:    parseFloat(document.getElementById('navCrossRight').value),
                goal:     parseFloat(document.getElementById('navCrossGoal').value),
            },
            forward_bias_s: {
                straight: 0,
                left:  parseFloat(document.getElementById('navBiasLeft').value),
                right: parseFloat(document.getElementById('navBiasRight').value),
            },
            victory_forward_s: parseFloat(document.getElementById('navVictoryForward').value),
            victory_spin_s:    parseFloat(document.getElementById('navVictorySpin').value),
        };
        postJSON('/update_nav_config', payload)
            .then(() => showStatus('nav-timing-status', 'Timing saved!', 'success'))
            .catch(() => showStatus('nav-timing-status', 'Save failed', 'error'));
    }

    fetch('/get_nav_config').then(r => r.json()).then(loadNavConfig);

    ['navStopWait', 'navCrossStraight', 'navCrossLeft', 'navCrossRight',
     'navCrossGoal', 'navBiasLeft', 'navBiasRight',
     'navVictoryForward', 'navVictorySpin'].forEach(id => {
        syncNavSlider(id, pushNavConfig);
    });

    // ── HSV sliders ───────────────────────────────────────────────────────────
    fetch('/get_hsv').then(r => r.json()).then(d => {
        setSliderValue('r1HighH', d.red_upper_h_1 || 10);
        setSliderValue('r1LowS',  d.red_lower_s_1 || 80);
        setSliderValue('r1LowV',  d.red_lower_v_1 || 80);
        setSliderValue('r2LowH',  d.red_lower_h_2 || 160);
        setSliderValue('r2LowS',  d.red_lower_s_2 || 80);
        setSliderValue('r2LowV',  d.red_lower_v_2 || 80);
        setSliderValue('roiY',    Math.round((d.roi_y_start   || 0.45)  * 100));
        setSliderValue('roiX',    Math.round((d.roi_x_margin  || 0.15)  * 100));
        setSliderValue('minRed',  Math.round((d.min_red_ratio || 0.012) * 1000));
    });

    const hsvKeys = {
        'r1HighH': 'red_upper_h_1', 'r1LowS': 'red_lower_s_1', 'r1LowV': 'red_lower_v_1',
        'r2LowH':  'red_lower_h_2', 'r2LowS': 'red_lower_s_2', 'r2LowV': 'red_lower_v_2',
    };
    Object.entries(hsvKeys).forEach(([sliderId, key]) => {
        syncSliderInput(sliderId, () => {
            const payload = {};
            payload[key] = parseInt(document.getElementById(sliderId).value);
            postJSON('/update_hsv', payload)
                .then(() => showStatus('hsv-status', 'HSV Updated!', 'success'));
        });
    });
    syncSliderInput('roiY', () => {
        postJSON('/update_roi', {roi_y_start: parseInt(document.getElementById('roiY').value) / 100})
            .then(() => showStatus('hsv-status', 'ROI Updated!', 'success'));
    });
    syncSliderInput('roiX', () => {
        postJSON('/update_roi', {roi_x_margin: parseInt(document.getElementById('roiX').value) / 100})
            .then(() => showStatus('hsv-status', 'ROI margin Updated!', 'success'));
    });
    syncSliderInput('minRed', () => {
        postJSON('/update_roi', {min_red_ratio: parseInt(document.getElementById('minRed').value) / 1000})
            .then(() => showStatus('hsv-status', 'Threshold Updated!', 'success'));
    });

    // ── Lane HSV + config ─────────────────────────────────────────────────────
    fetch('/get_lane_hsv').then(r => r.json()).then(d => {
        setSliderValue('yLowH',  d.yellow_lower_h);
        setSliderValue('yHighH', d.yellow_upper_h);
        setSliderValue('yLowS',  d.yellow_lower_s);
        setSliderValue('yHighS', d.yellow_upper_s);
        setSliderValue('yLowV',  d.yellow_lower_v);
        setSliderValue('yHighV', d.yellow_upper_v);
        setSliderValue('wLowH',  d.white_lower_h);
        setSliderValue('wHighH', d.white_upper_h);
        setSliderValue('wLowS',  d.white_lower_s);
        setSliderValue('wHighS', d.white_upper_s);
        setSliderValue('wLowV',  d.white_lower_v);
        setSliderValue('wHighV', d.white_upper_v);
    });

    const laneHsvKeys = {
        'yLowH': 'yellow_lower_h', 'yHighH': 'yellow_upper_h',
        'yLowS': 'yellow_lower_s', 'yHighS': 'yellow_upper_s',
        'yLowV': 'yellow_lower_v', 'yHighV': 'yellow_upper_v',
        'wLowH': 'white_lower_h',  'wHighH': 'white_upper_h',
        'wLowS': 'white_lower_s',  'wHighS': 'white_upper_s',
        'wLowV': 'white_lower_v',  'wHighV': 'white_upper_v',
    };
    Object.entries(laneHsvKeys).forEach(([sliderId, key]) => {
        syncSliderInput(sliderId, () => {
            const payload = {};
            payload[key] = parseInt(document.getElementById(sliderId).value);
            postJSON('/update_lane_hsv', payload)
                .then(() => showStatus('lane-hsv-status', 'Lane HSV Updated!', 'success'));
        });
    });

    function loadLaneConfig(cfg) {
        if (!cfg) return;
        document.getElementById('k_d').value = cfg.p_gain;
        document.getElementById('k_d_value').textContent = cfg.p_gain;
        document.getElementById('k_phi').value = cfg.d_gain;
        document.getElementById('k_phi_value').textContent = cfg.d_gain;
        document.getElementById('laneSpeed').value = cfg.base_speed;
        document.getElementById('laneSpeed_value').textContent = cfg.base_speed;
    }

    document.getElementById('k_d').oninput = function() {
        document.getElementById('k_d_value').textContent = this.value;
    };
    document.getElementById('k_phi').oninput = function() {
        document.getElementById('k_phi_value').textContent = this.value;
    };
    document.getElementById('laneSpeed').oninput = function() {
        document.getElementById('laneSpeed_value').textContent = this.value;
    };

    function updateLaneConfig() {
        postJSON('/update_lane_config', {
            k_d:   parseFloat(document.getElementById('k_d').value),
            k_phi: parseFloat(document.getElementById('k_phi').value),
            const: parseFloat(document.getElementById('laneSpeed').value),
        })
        .then(() => showStatus('lane-config-status', 'Lane config saved!', 'success'))
        .catch(() => showStatus('lane-config-status', 'Save failed', 'error'));
    }

    fetch('/status').then(r => r.json()).then(d => loadLaneConfig(d.lane_config));
'''

PROJECT_TEMPLATE = render_template(
    'Navigation — {{ hostname }}',
    '{{ hostname }} — Dijkstra Navigation',
    _CONTENT,
    extra_css=_EXTRA_CSS,
    extra_js=_JS,
)
