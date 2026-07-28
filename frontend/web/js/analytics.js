// analytics.js — Week 2 Analytics Page
// Fetches from GET /analytics and GET /prescriptions to build charts + table

(function () {
    const API_BASE = (function() {
        if (window.API_BASE_URL) return window.API_BASE_URL;
        if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
            return "http://127.0.0.1:8000";
        }
        return "https://prescription-extractor-api.onrender.com";
    })();



    // Chart colour palette matching the premium theme
    const PALETTE = [
        "#6366f1", "#0ea5e9", "#10b981", "#f59e0b",
        "#ef4444", "#c084fc", "#f97316", "#14b8a6",
        "#e879f9", "#84cc16"
    ];

    // ── Helpers ──────────────────────────────────────────────────────────────

    function setEl(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value;
    }

    function showLoader(visible) {
        const loader = document.getElementById("analyticsLoader");
        if (loader) loader.style.display = visible ? "flex" : "none";
    }

    // ── Fetch summary from /analytics ────────────────────────────────────────

    async function loadSummary() {
        try {
            const res = await fetch(`${API_BASE}/analytics`);
            if (!res.ok) throw new Error("Analytics endpoint error");
            const data = await res.json();

            setEl("statTotal",    data.total_prescriptions ?? "—");
            setEl("statRecent",   data.recent_uploads       ?? "—");
            setEl("statTopMed",   data.most_common_medicine ?? "—");
            setEl("statTopDosage",data.most_common_dosage   ?? "—");
        } catch (err) {
            console.error("Failed to load analytics summary:", err);
        }
    }

    // ── Fetch all records from /prescriptions for charts ─────────────────────

    async function loadCharts() {
        try {
            const res = await fetch(`${API_BASE}/prescriptions`);
            if (!res.ok) throw new Error("Prescriptions endpoint error");
            const records = await res.json();

            if (!records.length) {
                renderEmptyCharts();
                return;
            }

            // Build frequency maps
            const medMap  = {};
            const dosMap  = {};
            const dateMap = {};

            records.forEach(r => {
                if (r.medicine) medMap[r.medicine]  = (medMap[r.medicine]  || 0) + 1;
                if (r.dosage)   dosMap[r.dosage]    = (dosMap[r.dosage]    || 0) + 1;
                if (r.date)     dateMap[r.date]     = (dateMap[r.date]     || 0) + 1;
            });

            // Sort by count desc, take top 8
            const topMeds  = sortedEntries(medMap,  8);
            const topDoses = sortedEntries(dosMap,  6);
            const timeline = sortedEntries(dateMap, 20, true); // keep date order

            buildMedicineChart(topMeds);
            buildDosageChart(topDoses);
            buildTimelineChart(timeline);
            buildMedTable(topMeds, records.length);

        } catch (err) {
            console.error("Failed to load chart data:", err);
            showToast("Could not load chart data.", "error");
        }
    }

    function sortedEntries(map, limit, keepOrder = false) {
        let entries = Object.entries(map);
        if (!keepOrder) entries.sort((a, b) => b[1] - a[1]);
        return entries.slice(0, limit);
    }

    // ── Chart builders ───────────────────────────────────────────────────────

    function buildMedicineChart(entries) {
        const ctx = document.getElementById("medicineChart");
        if (!ctx) return;

        new Chart(ctx, {
            type: "bar",
            data: {
                labels: entries.map(e => e[0]),
                datasets: [{
                    label: "Prescriptions",
                    data: entries.map(e => e[1]),
                    backgroundColor: entries.map((_, i) => PALETTE[i % PALETTE.length] + "cc"),
                    borderColor:     entries.map((_, i) => PALETTE[i % PALETTE.length]),
                    borderWidth: 2,
                    borderRadius: 8,
                    borderSkipped: false,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} prescriptions` } }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: "Inter", size: 12 }, color: "#475569" }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: { family: "Inter", size: 12 }, color: "#475569" },
                        grid: { color: "#f1f5f9" }
                    }
                }
            }
        });
    }

    function buildDosageChart(entries) {
        const ctx = document.getElementById("dosageChart");
        if (!ctx) return;

        new Chart(ctx, {
            type: "doughnut",
            data: {
                labels: entries.map(e => e[0]),
                datasets: [{
                    data: entries.map(e => e[1]),
                    backgroundColor: entries.map((_, i) => PALETTE[i % PALETTE.length] + "dd"),
                    borderColor: "#ffffff",
                    borderWidth: 3,
                    hoverOffset: 8,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                cutout: "60%",
                plugins: {
                    legend: {
                        position: "bottom",
                        labels: {
                            font: { family: "Inter", size: 12 },
                            color: "#475569",
                            padding: 16,
                            usePointStyle: true,
                            pointStyleWidth: 10,
                        }
                    },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.label}: ${ctx.parsed} prescriptions` } }
                }
            }
        });
    }

    function buildTimelineChart(entries) {
        const ctx = document.getElementById("timelineChart");
        if (!ctx) return;

        new Chart(ctx, {
            type: "line",
            data: {
                labels: entries.map(e => e[0]),
                datasets: [{
                    label: "Prescriptions",
                    data: entries.map(e => e[1]),
                    borderColor: "#6366f1",
                    backgroundColor: "rgba(99,102,241,0.08)",
                    borderWidth: 2.5,
                    pointBackgroundColor: "#6366f1",
                    pointRadius: 5,
                    pointHoverRadius: 7,
                    fill: true,
                    tension: 0.4,
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: { callbacks: { label: ctx => ` ${ctx.parsed.y} prescriptions` } }
                },
                scales: {
                    x: {
                        grid: { display: false },
                        ticks: { font: { family: "Inter", size: 11 }, color: "#475569", maxRotation: 45 }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: { stepSize: 1, font: { family: "Inter", size: 12 }, color: "#475569" },
                        grid: { color: "#f1f5f9" }
                    }
                }
            }
        });
    }

    // ── Medicine frequency table ──────────────────────────────────────────────

    function buildMedTable(entries, total) {
        const tbody = document.getElementById("medTableBody");
        if (!tbody) return;

        tbody.innerHTML = "";

        if (!entries.length) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align:center; padding: 48px; color: var(--text-muted);">
                        <i class="fa-solid fa-folder-open" style="font-size:2rem; opacity:0.3; display:block; margin-bottom:12px;"></i>
                        No medicine data available yet.
                    </td>
                </tr>`;
            return;
        }

        entries.forEach(([medicine, count], idx) => {
            const share = total > 0 ? ((count / total) * 100).toFixed(1) : 0;
            const barColor = PALETTE[idx % PALETTE.length];
            const row = document.createElement("tr");
            row.innerHTML = `
                <td style="padding: 16px 32px; color: var(--text-muted); font-weight: 600;">${idx + 1}</td>
                <td style="padding: 16px 32px; font-weight: 600;">
                    <span class="medicine-tag">${medicine}</span>
                </td>
                <td style="padding: 16px 32px; font-weight: 700; color: var(--secondary);">${count}</td>
                <td style="padding: 16px 32px; min-width: 160px;">
                    <div style="display:flex; align-items:center; gap:10px;">
                        <div style="flex:1; height:8px; background:#f1f5f9; border-radius:10px; overflow:hidden;">
                            <div style="width:${share}%; height:100%; background:${barColor}; border-radius:10px; transition: width 0.6s ease;"></div>
                        </div>
                        <span style="font-size:0.8rem; font-weight:600; color:var(--text-secondary); min-width:40px;">${share}%</span>
                    </div>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    // ── Empty state for charts when no data ──────────────────────────────────

    function renderEmptyCharts() {
        ["medicineChart", "dosageChart", "timelineChart"].forEach(id => {
            const canvas = document.getElementById(id);
            if (!canvas) return;
            const parent = canvas.parentElement;
            parent.innerHTML = `
                <div style="height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; color:var(--text-muted); gap:12px;">
                    <i class="fa-solid fa-chart-bar" style="font-size:2.5rem; opacity:0.25;"></i>
                    <p style="font-size:0.9rem;">No data to display yet.</p>
                    <a href="upload.html" class="btn btn-primary" style="font-size:0.875rem; padding:8px 20px;">
                        <i class="fa-solid fa-plus"></i> Add Records
                    </a>
                </div>`;
        });

        const tbody = document.getElementById("medTableBody");
        if (tbody) {
            tbody.innerHTML = `
                <tr>
                    <td colspan="4" style="text-align:center; padding: 48px; color: var(--text-muted);">
                        <i class="fa-solid fa-folder-open" style="font-size:2rem; opacity:0.3; display:block; margin-bottom:12px;"></i>
                        No records found. <a href="upload.html" style="color:var(--primary); font-weight:600;">Upload a prescription</a> to get started.
                    </td>
                </tr>`;
        }
    }

    // ── Init ─────────────────────────────────────────────────────────────────

    async function init() {
        showLoader(true);
        await Promise.all([loadSummary(), loadCharts()]);
        showLoader(false);
    }

    init();
})();
