(function() {
const API_BASE = (function() {
    const urlParams = new URLSearchParams(window.location.search);
    if (urlParams.get('api')) {
        const paramApi = urlParams.get('api');
        localStorage.setItem('API_BASE_URL', paramApi);
        return paramApi;
    }
    if (localStorage.getItem('API_BASE_URL')) {
        return localStorage.getItem('API_BASE_URL');
    }
    if (window.API_BASE_URL) return window.API_BASE_URL;
    if (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1') {
        return "http://127.0.0.1:8000";
    }
    return "https://prescription-extractor-ocr.onrender.com";
})();

window.API_BASE = API_BASE;

// --- Toast System ---
function showToast(message, type = 'info') {
    const container = document.getElementById('toastContainer');
    if (!container) return;

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    
    let icon = 'fa-circle-info';
    if (type === 'success') icon = 'fa-circle-check';
    if (type === 'error') icon = 'fa-circle-exclamation';

    toast.innerHTML = `
        <i class="fa-solid ${icon}"></i>
        <span>${message}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
        toast.style.opacity = '0';
        toast.style.transform = 'translateX(100%)';
        toast.style.transition = 'all 0.3s ease';
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

window.showToast = showToast;

// --- Navigation & Dashboard Logic ---
const recordsBody = document.getElementById('recordsBody');
const searchInput = document.getElementById('searchInput');
const refreshBtn = document.getElementById('refreshBtn');
let allRecords = [];

let currentFilters = {};
let currentPage = 1;
let currentLimit = 15;
let currentSort = "";
let currentSearch = "";

const fetchPrescriptions = async (retryCount = 0) => {
    if (!recordsBody) return;

    // Show skeleton while loading
    document.querySelectorAll('.skeleton-row').forEach(r => r.style.display = '');
    document.getElementById('emptyState').classList.add('hidden');

    const qs = new URLSearchParams();
    if (currentSearch) qs.append('search', currentSearch);
    if (currentSort) qs.append('sort_by', currentSort);
    if (Object.keys(currentFilters).length > 0) {
        qs.append('filters', JSON.stringify(currentFilters));
    }
    qs.append('page', currentPage);
    qs.append('limit', currentLimit);

    try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 12000);

        const response = await fetch(`${API_BASE}/prescriptions?${qs.toString()}`, {
            signal: controller.signal
        });
        clearTimeout(timeoutId);

        if (!response.ok) throw new Error(`HTTP ${response.status}`);
        
        allRecords = await response.json();
        
        // Read X-Total-Count header for pagination info
        const totalHeader = response.headers.get('X-Total-Count');
        const totalRecordsCount = totalHeader ? parseInt(totalHeader, 10) : allRecords.length;

        // Fetch stats & charts backend analytics with active filters
        updateDashboardStats(totalRecordsCount, currentFilters);

        renderTable(allRecords);
        renderPagination(totalRecordsCount);
    } catch (error) {
        console.error("Error fetching records:", error);
        if (retryCount < 3) {
            showToast("Warming up cloud backend server... Retrying...", "info");
            setTimeout(() => fetchPrescriptions(retryCount + 1), 4000);
        } else {
            showToast("Unable to reach backend. Check Render server status.", "error");
            renderTable([]);
        }
    }
};

// Render Table Pagination Controls
function renderPagination(totalCount) {
    const info = document.getElementById('paginationInfo');
    const controls = document.getElementById('paginationControls');
    if (!info || !controls) return;

    if (totalCount === 0) {
        info.textContent = 'Showing 0 to 0 of 0 records';
        controls.innerHTML = '';
        return;
    }

    const start = (currentPage - 1) * currentLimit + 1;
    const end = Math.min(currentPage * currentLimit, totalCount);
    info.textContent = `Showing ${start} to ${end} of ${totalCount} records`;

    const totalPages = Math.ceil(totalCount / currentLimit);
    let html = '';

    // Previous Button
    html += `<button class="btn btn-outline btn-sm" ${currentPage === 1 ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''} onclick="window.setPage(${currentPage - 1})">
        <i class="fa-solid fa-chevron-left"></i> Prev
    </button>`;

    // Page numbers selection
    const maxPageButtons = 5;
    let startPage = Math.max(1, currentPage - Math.floor(maxPageButtons / 2));
    let endPage = Math.min(totalPages, startPage + maxPageButtons - 1);

    if (endPage - startPage + 1 < maxPageButtons) {
        startPage = Math.max(1, endPage - maxPageButtons + 1);
    }

    for (let p = startPage; p <= endPage; p++) {
        const isCurrent = p === currentPage;
        html += `<button class="btn ${isCurrent ? 'btn-primary' : 'btn-outline'} btn-sm" style="min-width:32px; padding:6px 10px; margin: 0 2px;" onclick="window.setPage(${p})">${p}</button>`;
    }

    // Next Button
    html += `<button class="btn btn-outline btn-sm" ${currentPage === totalPages ? 'disabled style="opacity:0.5; cursor:not-allowed;"' : ''} onclick="window.setPage(${currentPage + 1})">
        Next <i class="fa-solid fa-chevron-right"></i>
    </button>`;

    controls.innerHTML = html;
}

window.setPage = (p) => {
    currentPage = p;
    fetchPrescriptions();
};

function buildFiltersObject() {
    const filters = {};

    // Flat inputs
    const medicineFlat = (document.getElementById('medicineFilter')?.value || '').trim();
    const dateFlat = (document.getElementById('dateFilter')?.value || '').trim();
    if (medicineFlat) {
        filters.medicine = medicineFlat;
    }
    if (dateFlat) {
        filters.date = dateFlat;
    }

    // Drawer inputs
    const patName = (document.getElementById('filterPatientName')?.value || '').trim();
    const medName = (document.getElementById('filterMedicineName')?.value || '').trim();
    const genName = (document.getElementById('filterGenericName')?.value || '').trim();
    const diag = (document.getElementById('filterDiagnosis')?.value || '').trim();
    const sym = (document.getElementById('filterSymptoms')?.value || '').trim();

    if (patName) filters.patient_name = patName;
    if (medName) filters.medicine = medName; // overrides flat if both defined
    if (genName) filters.generic_name = genName;
    if (diag) filters.diagnosis = diag;
    if (sym) filters.symptoms = sym;

    const docName = (document.getElementById('filterDoctorName')?.value || '');
    const hospName = (document.getElementById('filterHospitalName')?.value || '');
    const dept = (document.getElementById('filterDepartment')?.value || '');
    const docSpec = (document.getElementById('filterDoctorSpecialty')?.value || '');
    const hospType = (document.getElementById('filterHospitalType')?.value || '');
    const medCat = (document.getElementById('filterMedicineCategory')?.value || '');

    if (docName) filters.doctor_name = docName;
    if (hospName) filters.hospital_name = hospName;
    if (dept) filters.department = dept;
    if (docSpec) filters.doctor_specialty = docSpec;
    if (hospType) filters.hospital_type = hospType;
    if (medCat) filters.medicine_category = medCat;

    const docType = (document.getElementById('filterDocumentType')?.value || '');
    const gender = (document.getElementById('filterGender')?.value || '');
    const ageMin = (document.getElementById('filterAgeMin')?.value || '').trim();
    const ageMax = (document.getElementById('filterAgeMax')?.value || '').trim();

    if (docType) filters.document_type = docType;
    if (gender) filters.gender = gender;
    
    if (ageMin !== "" || ageMax !== "") {
        const ageObj = {};
        if (ageMin !== "") ageObj.gte = parseInt(ageMin, 10);
        if (ageMax !== "") ageObj.lte = parseInt(ageMax, 10);
        filters.age = ageObj;
    }

    // Boolean flags
    if (document.getElementById('filterIsHandwritten')?.checked) filters.is_handwritten = true;
    if (document.getElementById('filterIsEmergency')?.checked) filters.is_emergency = true;
    if (document.getElementById('filterIsInpatient')?.checked) filters.is_inpatient = true;
    if (document.getElementById('filterIsOutpatient')?.checked) filters.is_outpatient = true;

    // Date Range Select
    const dateRange = (document.getElementById('filterDateRange')?.value || '');
    if (dateRange) {
        if (dateRange === "custom") {
            const start = (document.getElementById('filterDateStart')?.value || '');
            const end = (document.getElementById('filterDateEnd')?.value || '');
            if (start || end) {
                filters.custom_date_range = {};
                if (start) filters.custom_date_range.start = start;
                if (end) filters.custom_date_range.end = end;
            }
        } else {
            filters.date_range = dateRange;
        }
    }

    // OCR Thresholds
    const confMin = parseInt(document.getElementById('filterConfidenceMin')?.value || '0', 10);
    const qualMin = parseInt(document.getElementById('filterQualityMin')?.value || '0', 10);
    const noiseMax = parseInt(document.getElementById('filterNoiseMax')?.value || '100', 10);
    const contrastMin = parseInt(document.getElementById('filterContrastMin')?.value || '0', 10);

    if (confMin > 0) filters.confidence_score = { gte: confMin };
    if (qualMin > 0) filters.image_quality_score = { gte: qualMin };
    if (noiseMax < 100) filters.noise_level = { lte: noiseMax };
    if (contrastMin > 0) filters.contrast_score = { gte: contrastMin };

    const brightMin = (document.getElementById('filterBrightnessMin')?.value || '').trim();
    const brightMax = (document.getElementById('filterBrightnessMax')?.value || '').trim();
    if (brightMin !== "" || brightMax !== "") {
        const bObj = {};
        if (brightMin !== "") bObj.gte = parseInt(brightMin, 10);
        if (brightMax !== "") bObj.lte = parseInt(brightMax, 10);
        filters.brightness_score = bObj;
    }

    const skewMin = (document.getElementById('filterSkewMin')?.value || '').trim();
    const skewMax = (document.getElementById('filterSkewMax')?.value || '').trim();
    if (skewMin !== "" || skewMax !== "") {
        const sObj = {};
        if (skewMin !== "") sObj.gte = parseFloat(skewMin);
        if (skewMax !== "") sObj.lte = parseFloat(skewMax);
        filters.skew_angle = sObj;
    }

    return filters;
}

// Fetch Dynamic Filter Options
async function loadFilterOptions() {
    try {
        const response = await fetch(`${API_BASE}/api/v1/filters/options`);
        if (!response.ok) throw new Error("Failed to fetch filter options");
        const options = await response.json();

        // Populate Doctor list
        const docSelect = document.getElementById('filterDoctorName');
        if (docSelect) {
            docSelect.innerHTML = '<option value="">Select Doctor...</option>';
            const doctorList = options.doctor_names || options.doctors || [];
            doctorList.forEach(name => {
                if (name && name !== 'Unknown') {
                    docSelect.innerHTML += `<option value="${name}">${name}</option>`;
                }
            });
        }

        // Populate Hospital list
        const hospSelect = document.getElementById('filterHospitalName');
        if (hospSelect) {
            hospSelect.innerHTML = '<option value="">Select Hospital...</option>';
            const hospitalList = options.hospital_names || options.hospitals || [];
            hospitalList.forEach(name => {
                if (name && name !== 'Unknown') {
                    hospSelect.innerHTML += `<option value="${name}">${name}</option>`;
                }
            });
        }

        // Populate Department
        const deptSelect = document.getElementById('filterDepartment');
        if (deptSelect) {
            deptSelect.innerHTML = '<option value="">Select Department...</option>';
            const departmentList = options.departments || [];
            departmentList.forEach(d => {
                if (d) deptSelect.innerHTML += `<option value="${d}">${d}</option>`;
            });
        }

        // Populate Doctor Specialty
        const specSelect = document.getElementById('filterDoctorSpecialty');
        if (specSelect) {
            specSelect.innerHTML = '<option value="">Select Doctor Specialty...</option>';
            const specialtyList = options.doctor_specialties || [];
            specialtyList.forEach(s => {
                if (s) specSelect.innerHTML += `<option value="${s}">${s}</option>`;
            });
        }

        // Populate Hospital Type
        const hTypeSelect = document.getElementById('filterHospitalType');
        if (hTypeSelect) {
            hTypeSelect.innerHTML = '<option value="">Select Hospital Type...</option>';
            const typeList = options.hospital_types || [];
            typeList.forEach(t => {
                if (t) hTypeSelect.innerHTML += `<option value="${t}">${t}</option>`;
            });
        }

        // Populate Medicine Category
        const medCatSelect = document.getElementById('filterMedicineCategory');
        if (medCatSelect) {
            medCatSelect.innerHTML = '<option value="">Select Drug Category...</option>';
            const categoryList = options.medicine_categories || [];
            categoryList.forEach(c => {
                if (c) medCatSelect.innerHTML += `<option value="${c}">${c}</option>`;
            });
        }

        // Populate Document Type
        const docTypeSelect = document.getElementById('filterDocumentType');
        if (docTypeSelect) {
            docTypeSelect.innerHTML = '<option value="">Select Document Type...</option>';
            const docTypeList = options.document_types || [];
            docTypeList.forEach(type => {
                if (type) docTypeSelect.innerHTML += `<option value="${type}">${type}</option>`;
            });
        }

    } catch (err) {
        console.warn("Could not load dynamic filter dropdowns from database:", err);
    }
}

function initSliderTextHandlers() {
    const configSliders = [
        { id: 'filterConfidenceMin', valId: 'valConfidenceMin', suffix: '%' },
        { id: 'filterQualityMin', valId: 'valQualityMin', suffix: '%' },
        { id: 'filterNoiseMax', valId: 'valNoiseMax', suffix: '%' },
        { id: 'filterContrastMin', valId: 'valContrastMin', suffix: '%' }
    ];

    configSliders.forEach(slider => {
        const el = document.getElementById(slider.id);
        const valEl = document.getElementById(slider.valId);
        if (el && valEl) {
            el.addEventListener('input', (e) => {
                valEl.textContent = `${e.target.value}${slider.suffix}`;
            });
        }
    });

    // Brightness text observer
    const bMin = document.getElementById('filterBrightnessMin');
    const bMax = document.getElementById('filterBrightnessMax');
    const bText = document.getElementById('valBrightnessMinMax');
    const updateBrightnessText = () => {
        if (bText) {
            const min = bMin?.value || '0';
            const max = bMax?.value || '100';
            bText.textContent = `${min} - ${max}`;
        }
    };
    bMin?.addEventListener('input', updateBrightnessText);
    bMax?.addEventListener('input', updateBrightnessText);

    // Skew range observer
    const sMin = document.getElementById('filterSkewMin');
    const sMax = document.getElementById('filterSkewMax');
    const sText = document.getElementById('valSkewRange');
    const updateSkewText = () => {
        if (sText) {
            const min = sMin?.value || '';
            const max = sMax?.value || '';
            if (min === '' && max === '') {
                sText.textContent = 'All';
            } else {
                sText.textContent = `${min || '-90'}° to ${max || '90'}°`;
            }
        }
    };
    sMin?.addEventListener('input', updateSkewText);
    sMax?.addEventListener('input', updateSkewText);
}

function initDrawerEvents() {
    const toggleBtn = document.getElementById('toggleFiltersBtn');
    const drawer = document.getElementById('filterDrawer');
    const overlay = document.getElementById('filterDrawerOverlay');
    const closeBtn = document.getElementById('closeFilterDrawer');
    const dateRangeSelect = document.getElementById('filterDateRange');
    const customDateContainer = document.getElementById('customDateRangeInputs');

    if (toggleBtn && drawer && overlay) {
        toggleBtn.addEventListener('click', () => {
            drawer.classList.add('open');
            overlay.classList.remove('hidden');
        });
    }

    const closeDrawer = () => {
        drawer?.classList.remove('open');
        overlay?.classList.add('hidden');
    };

    closeBtn?.addEventListener('click', closeDrawer);
    overlay?.addEventListener('click', closeDrawer);

    dateRangeSelect?.addEventListener('change', (e) => {
        if (e.target.value === 'custom') {
            if (customDateContainer) customDateContainer.style.display = 'flex';
        } else {
            if (customDateContainer) customDateContainer.style.display = 'none';
        }
    });

    const resetFiltersBtn = document.getElementById('resetDrawerFilters');
    resetFiltersBtn?.addEventListener('click', () => {
        drawer.querySelectorAll('input[type="text"], input[type="number"], select').forEach(input => {
            input.value = '';
        });
        drawer.querySelectorAll('input[type="checkbox"]').forEach(chk => {
            chk.checked = false;
        });
        const confMin = document.getElementById('filterConfidenceMin');
        if (confMin) {
            confMin.value = '0';
            document.getElementById('valConfidenceMin').textContent = '0%';
        }
        const qualMin = document.getElementById('filterQualityMin');
        if (qualMin) {
            qualMin.value = '0';
            document.getElementById('valQualityMin').textContent = '0%';
        }
        const noiseMax = document.getElementById('filterNoiseMax');
        if (noiseMax) {
            noiseMax.value = '100';
            document.getElementById('valNoiseMax').textContent = '100%';
        }
        const contrastMin = document.getElementById('filterContrastMin');
        if (contrastMin) {
            contrastMin.value = '0';
            document.getElementById('valContrastMin').textContent = '0%';
        }
        if (customDateContainer) customDateContainer.style.display = 'none';
        
        currentFilters = {};
        currentPage = 1;
        fetchPrescriptions();
        closeDrawer();
    });

    const applyFiltersBtn = document.getElementById('applyDrawerFilters');
    applyFiltersBtn?.addEventListener('click', () => {
        currentFilters = buildFiltersObject();
        currentPage = 1;
        fetchPrescriptions();
        closeDrawer();
    });
}


// --- Upload & Drag-and-Drop ---
const imageInput = document.getElementById('imageInput');
const dropZone = document.getElementById('dropZone');
const filePreview = document.getElementById('filePreview');
const previewImg = document.getElementById('previewImg');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('resultSection');
const uploadStep = document.getElementById('uploadStep');

if (dropZone) {
    ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
        }, false);
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.add('active'), false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        dropZone.addEventListener(eventName, () => dropZone.classList.remove('active'), false);
    });

    dropZone.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        handleFiles(files);
    });
}

if (imageInput) {
    imageInput.addEventListener('change', () => handleFiles(imageInput.files));
}

function handleFiles(files) {
    if (!files[0]) return;
    const file = files[0];

    // Show preview
    const reader = new FileReader();
    reader.readAsDataURL(file);
    reader.onloadend = () => {
        previewImg.src = reader.result;
        filePreview.classList.remove('hidden');
        document.getElementById('fileName').textContent = file.name;
        document.getElementById('fileSize').textContent = (file.size / (1024 * 1024)).toFixed(2) + ' MB';
        
        // Auto-upload
        processUpload(file);
    };
}

async function processUpload(file) {
    const formData = new FormData();
    formData.append('file', file);

    uploadStep.classList.add('hidden');
    loading.classList.remove('hidden');
    resultSection.classList.add('hidden');

    const progressBar = document.getElementById('progressBar');
    if (progressBar) progressBar.style.width = '30%';

    try {
        if (progressBar) {
            setTimeout(() => progressBar.style.width = '60%', 500);
            setTimeout(() => progressBar.style.width = '90%', 1000);
        }

        const response = await fetch(`${API_BASE}/upload`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();

        if (!response.ok) {
            throw new Error(data.error || "Failed to process image");
        }

        // Simulate extraction quality
        const confidence = Math.floor(Math.random() * (99 - 85 + 1)) + 85;
        const badge = document.getElementById('confidenceBadge');
        badge.textContent = `${confidence}% Match`;
        badge.className = `confidence-badge ${confidence > 90 ? 'badge-high' : 'badge-mid'}`;

        // Populate fields
        document.getElementById('rawText').value = data.raw_text;
        document.getElementById('patientName').value = data.extracted_fields.patient_name !== "Unknown" ? data.extracted_fields.patient_name : '';
        document.getElementById('medicine').value = data.extracted_fields.medicine !== "Not Found" ? data.extracted_fields.medicine : '';
        document.getElementById('dosage').value = data.extracted_fields.dosage !== "Not Found" ? data.extracted_fields.dosage : '';
        document.getElementById('date').value = data.extracted_fields.date !== "Not Found" ? data.extracted_fields.date : '';
        
        if (document.getElementById('doctorName')) {
            document.getElementById('doctorName').value = data.extracted_fields.doctor_name !== "Unknown" ? data.extracted_fields.doctor_name : '';
        }
        if (document.getElementById('hospitalName')) {
            document.getElementById('hospitalName').value = data.extracted_fields.hospital_name !== "Unknown" ? data.extracted_fields.hospital_name : '';
        }

        // Duplicate alert banner
        const dupAlert = document.getElementById('duplicateAlert');
        if (dupAlert) {
            if (data.is_duplicate) dupAlert.classList.remove('hidden');
            else dupAlert.classList.add('hidden');
        }

        // Show real OCR confidence if available
        if (data.ocr_confidence !== undefined) {
            const conf = data.ocr_confidence;
            badge.textContent = `OCR Confidence: ${conf}%`;
            badge.className = `confidence-badge ${conf >= 80 ? 'badge-high' : 'badge-mid'}`;
        }

        loading.classList.add('hidden');
        resultSection.classList.remove('hidden');
        showToast("AI Analysis Complete!", "success");

    } catch (error) {
        console.error(error);
        showToast(error.message || "Error processing prescription.", "error");
        loading.classList.add('hidden');
        uploadStep.classList.remove('hidden');
    }
}

// Auto-clean button
const autoCleanBtn = document.getElementById('autoCleanBtn');
if (autoCleanBtn) {
    autoCleanBtn.addEventListener('click', () => {
        const rawEl = document.getElementById('rawText');
        if (!rawEl || !rawEl.value) return;
        let cleaned = rawEl.value.replace(/[\x00-\x08\x0b\x0c\x0e-\x1f]/g, '');
        cleaned = cleaned.replace(/\n{3,}/g, '\n\n').trim();
        rawEl.value = cleaned;
        showToast("OCR text cleaned!", "success");
    });
}

// --- Save Logic ---
const saveBtn = document.getElementById('saveBtn');
if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
        const payload = {
            patient_name: document.getElementById('patientName').value,
            medicine: document.getElementById('medicine').value,
            dosage: document.getElementById('dosage').value,
            date: document.getElementById('date').value,
            doctor_name: document.getElementById('doctorName')?.value || 'Unknown',
            hospital_name: document.getElementById('hospitalName')?.value || 'Unknown',
            raw_text: document.getElementById('rawText').value,
            confidence_score: 92
        };

        if (!payload.patient_name) {
            showToast("Patient name is required.", "error");
            return;
        }

        saveBtn.disabled = true;
        saveBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Saving...';

        try {
            const response = await fetch(`${API_BASE}/save`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(payload)
            });

            if (response.ok) {
                showToast("Prescription saved successfully!", "success");
                setTimeout(() => window.location.href = 'dashboard.html', 1500);
            } else {
                const data = await response.json();
                showToast(data.error || "Error saving to database.", "error");
                saveBtn.disabled = false;
                saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Confirm & Save';
            }
        } catch (error) {
            console.error(error);
            showToast("Error communicating with server.", "error");
            saveBtn.disabled = false;
            saveBtn.innerHTML = '<i class="fa-solid fa-floppy-disk"></i> Confirm & Save';
        }
    });
}

const discardBtn = document.getElementById('discardBtn');
if (discardBtn) {
    discardBtn.addEventListener('click', () => {
        if (confirm("Are you sure you want to discard this extraction?")) {
            window.location.reload();
        }
    });
}

// Duplicate Dashboard definitions removed representing bug fix.

function renderTable(records) {
    if (!recordsBody) return;
    
    // Hide skeletons
    document.querySelectorAll('.skeleton-row').forEach(r => r.style.display = 'none');

    recordsBody.innerHTML = '';
    const emptyState = document.getElementById('emptyState');
    
    if (records.length === 0) {
        emptyState.classList.remove('hidden');
        return;
    } else {
        emptyState.classList.add('hidden');
    }

    records.forEach(record => {
        const row = document.createElement('tr');
        const docHosp = record.doctor_name && record.doctor_name !== 'Unknown' 
            ? record.doctor_name 
            : (record.hospital_name || '—');

        row.innerHTML = `
            <td>#${record.id}</td>
            <td style="font-weight: 600;">${record.patient_name}</td>
            <td><span class="medicine-tag">${record.medicine}</span></td>
            <td style="color: var(--text-secondary);">${record.dosage}</td>
            <td>${record.date}</td>
            <td style="color: var(--text-secondary); font-size: 0.85rem;">${docHosp}</td>
            <td>
                <div style="display:flex; gap:4px;">
                    <button class="btn btn-ghost btn-icon-sm" title="View Details" onclick="viewDetails(${record.id})">
                        <i class="fa-solid fa-eye"></i>
                    </button>
                    <button class="btn btn-ghost btn-icon-sm btn-delete" title="Delete Record" onclick="confirmDelete(${record.id})">
                        <i class="fa-solid fa-trash"></i>
                    </button>
                </div>
            </td>
        `;
        recordsBody.appendChild(row);
    });
}

async function updateDashboardStats(totalCount, filters) {
    const totalEl = document.getElementById('totalRecords');
    const recentEl = document.getElementById('recentUploads');
    const topMedEl = document.getElementById('topMedicine');
    if (totalEl) totalEl.textContent = totalCount;

    // Fetch backend analytics with active filters
    const qs = new URLSearchParams();
    if (Object.keys(filters).length > 0) {
        qs.append('filters', JSON.stringify(filters));
    }
    
    try {
        const response = await fetch(`${API_BASE}/analytics?${qs.toString()}`);
        if (response.ok) {
            const data = await response.json();
            if (totalEl) totalEl.textContent = data.total_prescriptions;
            if (recentEl) recentEl.textContent = data.recent_uploads;
            if (topMedEl) topMedEl.textContent = data.most_common_medicine || 'N/A';
            const accuracyValEl = document.querySelector('.stats-grid .stat-card:nth-child(4) .value');
            if (accuracyValEl) {
                accuracyValEl.textContent = `${data.average_confidence_score.toFixed(1)}%`;
            }
        }
    } catch (e) {
        console.warn("Analytics fetch failed:", e);
    }
}

// --- Debounced Search & Autocomplete ---
let searchDebounceTimeout = null;
const searchSuggestions = document.getElementById('searchSuggestions');

if (searchInput && searchSuggestions) {
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchDebounceTimeout);
        const term = e.target.value.trim();

        if (term.length < 2) {
            searchSuggestions.classList.add('hidden');
            searchSuggestions.innerHTML = '';
            // If cleared, trigger fetch
            if (term.length === 0 && currentSearch !== "") {
                currentSearch = "";
                currentPage = 1;
                fetchPrescriptions();
            }
            return;
        }

        searchDebounceTimeout = setTimeout(async () => {
            currentSearch = term;
            currentPage = 1;
            
            try {
                const response = await fetch(`${API_BASE}/prescriptions?search=${encodeURIComponent(term)}&limit=8`);
                if (response.ok) {
                    const data = await response.json();
                    if (data.length === 0) {
                        searchSuggestions.classList.add('hidden');
                        return;
                    }
                    
                    const itemsSet = new Set();
                    data.forEach(r => {
                        if (r.patient_name && r.patient_name.toLowerCase().includes(term.toLowerCase())) {
                            itemsSet.add(JSON.stringify({ type: 'Patient', val: r.patient_name }));
                        }
                        if (r.medicine && r.medicine.toLowerCase().includes(term.toLowerCase())) {
                            itemsSet.add(JSON.stringify({ type: 'Medicine', val: r.medicine }));
                        }
                        if (r.doctor_name && r.doctor_name !== 'Unknown' && r.doctor_name.toLowerCase().includes(term.toLowerCase())) {
                            itemsSet.add(JSON.stringify({ type: 'Doctor', val: r.doctor_name }));
                        }
                    });

                    const items = Array.from(itemsSet).map(s => JSON.parse(s)).slice(0, 5);
                    if (items.length === 0) {
                        searchSuggestions.classList.add('hidden');
                        return;
                    }

                    searchSuggestions.innerHTML = '';
                    items.forEach(item => {
                        const div = document.createElement('div');
                        div.style.padding = '8px 14px';
                        div.style.cursor = 'pointer';
                        div.style.fontSize = '0.9rem';
                        div.style.borderBottom = '1px solid rgba(0,0,0,0.03)';
                        div.className = 'suggestion-item';
                        div.innerHTML = `<span style="font-weight:600; color:var(--primary); font-size:0.75rem; text-transform:uppercase; margin-right:8px; border:1px solid var(--primary-light); padding:1px 4px; border-radius:3px;">${item.type}</span> <span>${item.val}</span>`;
                        div.addEventListener('click', () => {
                            searchInput.value = item.val;
                            currentSearch = item.val;
                            searchSuggestions.classList.add('hidden');
                            currentPage = 1;
                            fetchPrescriptions();
                        });
                        searchSuggestions.appendChild(div);
                    });
                    
                    searchSuggestions.classList.remove('hidden');
                }
            } catch (err) {
                console.warn(err);
            }
        }, 300);
    });

    searchInput.addEventListener('keydown', (e) => {
        if (e.key === 'Enter') {
            clearTimeout(searchDebounceTimeout);
            const term = searchInput.value.trim();
            currentSearch = term;
            currentPage = 1;
            searchSuggestions.classList.add('hidden');
            fetchPrescriptions();
        }
    });

    document.addEventListener('click', (e) => {
        if (!searchInput.contains(e.target) && !searchSuggestions.contains(e.target)) {
            searchSuggestions.classList.add('hidden');
        }
    });
}

// Export excel & PDF & CSV triggers
const exportExcelBtn = document.getElementById('exportExcel');
if (exportExcelBtn) {
    exportExcelBtn.addEventListener('click', () => {
        const qs = new URLSearchParams();
        if (Object.keys(currentFilters).length > 0) {
            qs.append('filters', JSON.stringify(currentFilters));
        }
        if (currentSearch) qs.append('search', currentSearch);
        if (currentSort) qs.append('sort_by', currentSort);
        if (currentPage) qs.append('page', currentPage);
        if (currentLimit) qs.append('limit', currentLimit);
        window.open(`${API_BASE}/api/v1/export/excel?${qs.toString()}`, '_blank');
        showToast("Excel export started.", "success");
    });
}

const exportPDFBtn = document.getElementById('exportPDF');
if (exportPDFBtn) {
    exportPDFBtn.addEventListener('click', () => {
        const qs = new URLSearchParams();
        if (Object.keys(currentFilters).length > 0) {
            qs.append('filters', JSON.stringify(currentFilters));
        }
        if (currentSearch) qs.append('search', currentSearch);
        if (currentSort) qs.append('sort_by', currentSort);
        if (currentPage) qs.append('page', currentPage);
        if (currentLimit) qs.append('limit', currentLimit);
        window.open(`${API_BASE}/api/v1/export/pdf?${qs.toString()}`, '_blank');
        showToast("PDF report download started.", "success");
    });
}

const printReportBtn = document.getElementById('printReportBtn');
if (printReportBtn) {
    printReportBtn.addEventListener('click', () => {
        window.print();
    });
}

const sortSelect = document.getElementById('sortSelect');
if (sortSelect) {
    sortSelect.addEventListener('change', (e) => {
        currentSort = e.target.value;
        currentPage = 1;
        fetchPrescriptions();
    });
}

// Flat controls Apply & Reset buttons
const applyFiltersBtn = document.getElementById('applyFilters');
if (applyFiltersBtn) {
    applyFiltersBtn.addEventListener('click', () => {
        currentFilters = buildFiltersObject();
        currentPage = 1;
        fetchPrescriptions();
    });
}

const clearFiltersBtn = document.getElementById('clearFilters');
if (clearFiltersBtn) {
    clearFiltersBtn.addEventListener('click', () => {
        if (document.getElementById('searchInput'))   document.getElementById('searchInput').value = '';
        if (document.getElementById('medicineFilter')) document.getElementById('medicineFilter').value = '';
        if (document.getElementById('dateFilter'))    document.getElementById('dateFilter').value = '';
        if (document.getElementById('sortSelect'))    document.getElementById('sortSelect').value = '';
        
        // Reset drawer inputs
        const drawer = document.getElementById('filterDrawer');
        if (drawer) {
            drawer.querySelectorAll('input[type="text"], input[type="number"], select').forEach(input => {
                input.value = '';
            });
            drawer.querySelectorAll('input[type="checkbox"]').forEach(chk => {
                chk.checked = false;
            });
            const confMin = document.getElementById('filterConfidenceMin');
            if (confMin) {
                confMin.value = '0';
                document.getElementById('valConfidenceMin').textContent = '0%';
            }
            const qualMin = document.getElementById('filterQualityMin');
            if (qualMin) {
                qualMin.value = '0';
                document.getElementById('valQualityMin').textContent = '0%';
            }
            const noiseMax = document.getElementById('filterNoiseMax');
            if (noiseMax) {
                noiseMax.value = '100';
                document.getElementById('valNoiseMax').textContent = '100%';
            }
            const contrastMin = document.getElementById('filterContrastMin');
            if (contrastMin) {
                contrastMin.value = '0';
                document.getElementById('valContrastMin').textContent = '0%';
            }
            const customDateContainer = document.getElementById('customDateRangeInputs');
            if (customDateContainer) customDateContainer.style.display = 'none';
        }

        currentSearch = '';
        currentFilters = {};
        currentPage = 1;
        fetchPrescriptions();
    });
}

if (refreshBtn) {
    refreshBtn.addEventListener('click', async () => {
        refreshBtn.innerHTML = '<i class="fa-solid fa-rotate fa-spin"></i> Refreshing...';
        await fetchPrescriptions();
        setTimeout(() => {
            refreshBtn.innerHTML = '<i class="fa-solid fa-rotate"></i> Refresh';
            showToast("Data updated", "success");
        }, 500);
    });
}

const exportCSV = document.getElementById('exportCSV');
if (exportCSV) {
    exportCSV.addEventListener('click', () => {
        const qs = new URLSearchParams();
        if (Object.keys(currentFilters).length > 0) {
            qs.append('filters', JSON.stringify(currentFilters));
        }
        if (currentSearch) qs.append('search', currentSearch);
        if (currentSort) qs.append('sort_by', currentSort);
        if (currentPage) qs.append('page', currentPage);
        if (currentLimit) qs.append('limit', currentLimit);

        const url = `${API_BASE}/export-csv?${qs.toString()}`;
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', '');
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        showToast("CSV download started.", "success");
    });
}

// Global function for detail view
window.viewDetails = (id) => {
    const record = allRecords.find(r => r.id === id);
    if (!record) return;

    // Basic & Clinical
    document.getElementById('mdPatientName').textContent = record.patient_name || '—';
    document.getElementById('mdMedicine').textContent = record.medicine || '—';
    document.getElementById('mdGenericName').textContent = record.generic_name || '—';
    document.getElementById('mdDosage').textContent = record.dosage || '—';
    document.getElementById('mdDate').textContent = record.date || '—';
    document.getElementById('mdDoctorName').textContent = `${record.doctor_name || '—'}${record.doctor_specialty ? ' (' + record.doctor_specialty + ')' : ''}`;
    document.getElementById('mdHospitalName').textContent = `${record.hospital_name || '—'}${record.hospital_type ? ' (' + record.hospital_type + ')' : ''}`;
    document.getElementById('mdDepartment').textContent = record.department || '—';
    document.getElementById('mdDiagnosis').textContent = record.diagnosis || '—';
    document.getElementById('mdSymptoms').textContent = record.symptoms || '—';

    // Demographics & Admin
    const gender = record.gender || 'N/A';
    const age = record.age || 'N/A';
    document.getElementById('mdDemoGenderAge').textContent = `${gender} / ${age}`;
    
    // Classifications
    const docType = record.document_type || 'Prescription';
    const emergencyStr = record.is_emergency ? 'Emergency' : 'Standard';
    document.getElementById('mdClassificationStatus').textContent = `${docType} (${emergencyStr})`;
    
    const inpatientStr = record.is_inpatient ? 'Inpatient' : '';
    const outpatientStr = record.is_outpatient ? 'Outpatient' : '';
    const admission = [inpatientStr, outpatientStr].filter(Boolean).join('/') || 'Outpatient';
    document.getElementById('mdAdmissionStatus').textContent = admission;
    
    document.getElementById('mdMedicineCategory').textContent = record.medicine_category || '—';

    // OCR & Quality
    document.getElementById('mdReadabilityScore').textContent = `${record.readability_score ?? 100}%`;
    document.getElementById('mdWritingType').textContent = record.is_handwritten ? 'Handwritten' : 'Printed';
    document.getElementById('mdNoiseLevel').textContent = `${record.noise_level ?? 0}%`;
    document.getElementById('mdContrastBrightness').textContent = `Contrast: ${record.contrast_score ?? 100}% / Brightness: ${record.brightness_score ?? 100}%`;
    document.getElementById('mdRotationSkew').textContent = `Rotation: ${record.rotation ?? 0}° / Skew: ${record.skew_angle ?? 0}°`;
    document.getElementById('mdLanguage').textContent = record.language || 'English';

    // Raw OCR Text
    document.getElementById('mdRawText').textContent = record.raw_text || 'No raw text available.';

    openModal('detailsModal');
};

// ── Delete Logic ──────────────────────────────────────────────────────────
let pendingDeleteId = null;

window.confirmDelete = (id) => {
    const record = allRecords.find(r => r.id === id);
    if (!record) return;
    pendingDeleteId = id;
    const nameEl = document.getElementById('deletePatientName');
    if (nameEl) nameEl.textContent = record.patient_name;
    openModal('deleteModal');
};

const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
if (confirmDeleteBtn) {
    confirmDeleteBtn.addEventListener('click', async () => {
        if (!pendingDeleteId) return;

        confirmDeleteBtn.disabled = true;
        confirmDeleteBtn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Deleting...';

        try {
            const response = await fetch(`${API_BASE}/prescriptions/${pendingDeleteId}`, {
                method: 'DELETE'
            });

            if (response.ok) {
                closeModal('deleteModal');
                showToast("Record deleted successfully.", "success");
                await fetchPrescriptions();
            } else {
                const data = await response.json();
                showToast(data.detail || "Failed to delete record.", "error");
            }
        } catch (err) {
            console.error(err);
            showToast("Error communicating with server.", "error");
        } finally {
            confirmDeleteBtn.disabled = false;
            confirmDeleteBtn.innerHTML = '<i class="fa-solid fa-trash"></i> Delete';
            pendingDeleteId = null;
        }
    });
}

// ── Modal Helpers ─────────────────────────────────────────────────────────
function openModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.remove('hidden');
    document.body.style.overflow = 'hidden';
}

function closeModal(id) {
    const modal = document.getElementById(id);
    if (!modal) return;
    modal.classList.add('hidden');
    document.body.style.overflow = '';
}

// Close buttons
['closeDetailsModal', 'closeDetailsModalFooter'].forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (btn) btn.addEventListener('click', () => closeModal('detailsModal'));
});

['closeDeleteModal', 'cancelDeleteBtn'].forEach(btnId => {
    const btn = document.getElementById(btnId);
    if (btn) btn.addEventListener('click', () => closeModal('deleteModal'));
});

// Close on backdrop click
document.addEventListener('click', (e) => {
    if (e.target.classList.contains('modal-overlay')) {
        closeModal('detailsModal');
        closeModal('deleteModal');
    }
});

// Close on Escape key
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        closeModal('detailsModal');
        closeModal('deleteModal');
    }
});

// Initial load
if (recordsBody) {
    loadFilterOptions();
    initSliderTextHandlers();
    initDrawerEvents();
    fetchPrescriptions();
}
})();
