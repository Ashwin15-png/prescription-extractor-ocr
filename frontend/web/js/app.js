const API_BASE = "http://localhost:8000";

// Upload Logic - Triggered when file is selected
const imageInput = document.getElementById('imageInput');
const loading = document.getElementById('loading');
const resultSection = document.getElementById('resultSection');
const uploadZone = document.getElementById('uploadZone');

if (imageInput) {
    imageInput.addEventListener('change', async () => {
        if (!imageInput.files[0]) return;

        const formData = new FormData();
        formData.append('file', imageInput.files[0]);

        // UI state: hide upload zone and show loading
        uploadZone.classList.add('hidden');
        loading.classList.remove('hidden');
        resultSection.classList.add('hidden');

        try {
            const response = await fetch(`${API_BASE}/upload`, {
                method: 'POST',
                body: formData
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "Failed to process image");
            }
            
            // Populate fields
            document.getElementById('rawText').value = data.raw_text;
            document.getElementById('patientName').value = data.extracted_fields.patient_name;
            document.getElementById('medicine').value = data.extracted_fields.medicine;
            document.getElementById('dosage').value = data.extracted_fields.dosage;
            document.getElementById('date').value = data.extracted_fields.date;

            loading.classList.add('hidden');
            resultSection.classList.remove('hidden');
        } catch (error) {
            console.error(error);
            alert(error.message || "Error processing prescription.");
            loading.classList.add('hidden');
            uploadZone.classList.remove('hidden');
        }
    });
}

// Save Logic
const saveBtn = document.getElementById('saveBtn');
if (saveBtn) {
    saveBtn.addEventListener('click', async () => {
        const payload = {
            patient_name: document.getElementById('patientName').value,
            medicine: document.getElementById('medicine').value,
            dosage: document.getElementById('dosage').value,
            date: document.getElementById('date').value,
            raw_text: document.getElementById('rawText').value
        };

        try {
            const response = await fetch(`${API_BASE}/save`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify(payload)
            });

            const data = await response.json();

            if (response.ok) {
                alert("Prescription saved successfully!");
                window.location.href = 'dashboard.html';
            } else {
                alert(data.error || "Error saving to database.");
            }
        } catch (error) {
            console.error(error);
            alert("Error communicating with server.");
        }
    });
}

// Dashboard Logic
const fetchRecordsBtn = document.getElementById('fetchRecordsBtn');
const recordsBody = document.getElementById('recordsBody');

const fetchPrescriptions = async () => {
    if (!recordsBody) return;
    
    try {
        const response = await fetch(`${API_BASE}/prescriptions`);
        const records = await response.json();
        
        recordsBody.innerHTML = '';
        records.forEach(record => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${record.id}</td>
                <td>${record.patient_name}</td>
                <td>${record.date}</td>
                <td>${record.medicine}</td>
                <td>${record.dosage}</td>
            `;
            recordsBody.appendChild(row);
        });
    } catch (error) {
        console.error("Error fetching records:", error);
    }
};

if (fetchRecordsBtn) {
    fetchRecordsBtn.addEventListener('click', fetchPrescriptions);
    // Fetch on initial load
    fetchPrescriptions();
}
