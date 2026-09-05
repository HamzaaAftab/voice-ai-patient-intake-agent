// ==============================================================================
// Voice AI Patient Registration System — Dashboard Client Application
// ==============================================================================

let currentPatients = [];
let currentCallLogs = [];

document.addEventListener('DOMContentLoaded', () => {
    loadAllData();
    setupEventListeners();
});

function setupEventListeners() {
    // Search input filtering
    const searchInput = document.getElementById('searchInput');
    if (searchInput) {
        searchInput.addEventListener('input', (e) => filterPatients(e.target.value));
    }

    // State & Status filters
    const filterStatus = document.getElementById('filterStatus');
    if (filterStatus) {
        filterStatus.addEventListener('change', () => loadPatients());
    }

    // Tab buttons
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            const targetTab = btn.dataset.tab;
            if (targetTab === 'patients') {
                document.getElementById('patientsSection').style.display = 'block';
                document.getElementById('callsSection').style.display = 'none';
            } else {
                document.getElementById('patientsSection').style.display = 'none';
                document.getElementById('callsSection').style.display = 'block';
                loadCallLogs();
            }
        });
    });
}

async function loadAllData() {
    await Promise.all([loadMetrics(), loadPatients(), loadCallLogs()]);
}

async function loadMetrics() {
    try {
        const res = await fetch('/patients/metrics/summary');
        const json = await res.json();
        if (json.data) {
            document.getElementById('metricTotal').textContent = json.data.total_patients ?? 0;
            document.getElementById('metricActive').textContent = json.data.active_patients ?? 0;
            document.getElementById('metricDeleted').textContent = json.data.deleted_patients ?? 0;
        }
    } catch (err) {
        console.error('Failed to load metrics:', err);
    }
}

async function loadPatients() {
    const filterStatus = document.getElementById('filterStatus')?.value || 'active';
    const includeDeleted = filterStatus === 'all' || filterStatus === 'deleted';

    try {
        const res = await fetch(`/patients?include_deleted=${includeDeleted}&limit=100`);
        const json = await res.json();
        if (json.data) {
            currentPatients = json.data;
            if (filterStatus === 'deleted') {
                renderPatientsTable(currentPatients.filter(p => p.deleted_at !== null));
            } else if (filterStatus === 'active') {
                renderPatientsTable(currentPatients.filter(p => p.deleted_at === null));
            } else {
                renderPatientsTable(currentPatients);
            }
        }
    } catch (err) {
        console.error('Failed to load patients:', err);
    }
}

function renderPatientsTable(patients) {
    const tbody = document.getElementById('patientsTableBody');
    if (!tbody) return;

    if (patients.length === 0) {
        tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 32px;">No patient records found.</td></tr>`;
        return;
    }

    tbody.innerHTML = patients.map(p => {
        const isDeleted = p.deleted_at !== null;
        const statusBadge = isDeleted 
            ? `<span class="badge badge-deleted">Soft-Deleted</span>` 
            : `<span class="badge badge-active">Active</span>`;
        
        const formattedPhone = p.phone_number ? `(${p.phone_number.slice(0,3)}) ${p.phone_number.slice(3,6)}-${p.phone_number.slice(6)}` : 'N/A';
        const formattedDate = new Date(p.created_at).toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });

        return `
            <tr>
                <td>
                    <div style="font-weight: 600;">${p.first_name} ${p.last_name}</div>
                    <div class="mono" style="font-size: 11px;">${p.patient_id.slice(0, 8)}...</div>
                </td>
                <td>${p.date_of_birth}</td>
                <td><span class="badge badge-sex">${p.sex}</span></td>
                <td class="mono">${formattedPhone}</td>
                <td>${p.city}, <span class="badge badge-state">${p.state}</span> ${p.zip_code}</td>
                <td>${statusBadge}</td>
                <td>
                    <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px;" onclick="viewPatientDetail('${p.patient_id}')">Details</button>
                    ${!isDeleted ? `<button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px; color: var(--accent-rose); border-color: rgba(251, 113, 133, 0.3);" onclick="softDeletePatient('${p.patient_id}')">Delete</button>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function filterPatients(searchTerm) {
    const term = searchTerm.toLowerCase();
    const filtered = currentPatients.filter(p => 
        p.first_name.toLowerCase().includes(term) ||
        p.last_name.toLowerCase().includes(term) ||
        p.phone_number.includes(term) ||
        p.city.toLowerCase().includes(term) ||
        p.state.toLowerCase().includes(term) ||
        p.zip_code.includes(term)
    );
    renderPatientsTable(filtered);
}

function viewPatientDetail(patientId) {
    const p = currentPatients.find(item => item.patient_id === patientId);
    if (!p) return;

    const modalBody = document.getElementById('modalBody');
    const formattedPhone = p.phone_number ? `(${p.phone_number.slice(0,3)}) ${p.phone_number.slice(3,6)}-${p.phone_number.slice(6)}` : 'N/A';
    const emergencyPhone = p.emergency_contact_phone ? `(${p.emergency_contact_phone.slice(0,3)}) ${p.emergency_contact_phone.slice(3,6)}-${p.emergency_contact_phone.slice(6)}` : 'None';

    modalBody.innerHTML = `
        <div class="detail-grid">
            <div class="detail-item"><label>Full Legal Name</label><span>${p.first_name} ${p.last_name}</span></div>
            <div class="detail-item"><label>Date of Birth</label><span>${p.date_of_birth}</span></div>
            <div class="detail-item"><label>Biological Sex</label><span>${p.sex}</span></div>
            <div class="detail-item"><label>Phone Number</label><span>${formattedPhone}</span></div>
            <div class="detail-item" style="grid-column: span 2;"><label>Street Address</label><span>${p.address_line_1}${p.address_line_2 ? ', ' + p.address_line_2 : ''}, ${p.city}, ${p.state} ${p.zip_code}</span></div>
            <div class="detail-item"><label>Email Address</label><span>${p.email || 'Not provided'}</span></div>
            <div class="detail-item"><label>Preferred Language</label><span>${p.preferred_language || 'English'}</span></div>
            <div class="detail-item"><label>Insurance Carrier</label><span>${p.insurance_provider || 'Self-Pay / None'}</span></div>
            <div class="detail-item"><label>Insurance Member ID</label><span>${p.insurance_member_id || 'N/A'}</span></div>
            <div class="detail-item"><label>Emergency Contact</label><span>${p.emergency_contact_name || 'Not provided'}</span></div>
            <div class="detail-item"><label>Emergency Phone</label><span>${emergencyPhone}</span></div>
            <div class="detail-item" style="grid-column: span 2;"><label>Patient UUID</label><span class="mono" style="font-size: 11px;">${p.patient_id}</span></div>
        </div>
    `;

    document.getElementById('detailModal').style.display = 'flex';
}

function closeModal() {
    document.getElementById('detailModal').style.display = 'none';
}

async function softDeletePatient(patientId) {
    if (!confirm('Are you sure you want to soft-delete this patient record?')) return;

    try {
        const res = await fetch(`/patients/${patientId}`, { method: 'DELETE' });
        const json = await res.json();
        if (json.data) {
            showToast('Patient record marked as soft-deleted.');
            await loadAllData();
        }
    } catch (err) {
        console.error('Failed to delete patient:', err);
    }
}

async function loadCallLogs() {
    try {
        const res = await fetch('/webhooks/call-logs');
        const json = await res.json();
        if (json.data) {
            currentCallLogs = json.data;
            document.getElementById('metricCalls').textContent = currentCallLogs.length;
            renderCallLogsTable(currentCallLogs);
        }
    } catch (err) {
        console.error('Failed to load call logs:', err);
    }
}

function renderCallLogsTable(logs) {
    const tbody = document.getElementById('callsTableBody');
    if (!tbody) return;

    if (logs.length === 0) {
        tbody.innerHTML = `<tr><td colspan="6" style="text-align: center; color: var(--text-muted); padding: 32px;">No telephone intake calls logged yet. Call the live number to test!</td></tr>`;
        return;
    }

    tbody.innerHTML = logs.map(l => {
        const formattedDate = l.created_at ? new Date(l.created_at).toLocaleString() : 'N/A';
        const patientBadge = l.patient_id 
            ? `<span class="badge badge-active" style="cursor: pointer;" onclick="viewPatientDetail('${l.patient_id}')">${l.patient_name}</span>`
            : `<span class="badge badge-sex">${l.patient_name || 'Unregistered Caller'}</span>`;

        return `
            <tr>
                <td class="mono">${l.call_id.slice(0, 16)}...</td>
                <td class="mono">${l.caller_phone}</td>
                <td>${patientBadge}</td>
                <td>${l.duration_seconds}s</td>
                <td>${formattedDate}</td>
                <td>
                    <button class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px;" onclick="viewTranscript('${l.log_id}')">View Transcript</button>
                    ${l.recording_url ? `<a href="${l.recording_url}" target="_blank" class="btn btn-ghost" style="padding: 4px 10px; font-size: 12px; color: var(--primary);">Play Audio</a>` : ''}
                </td>
            </tr>
        `;
    }).join('');
}

function viewTranscript(logId) {
    const log = currentCallLogs.find(l => l.log_id === logId);
    if (!log) return;

    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 16px;">
            <div class="detail-item">
                <label>Call Session</label>
                <span class="mono">${log.call_id} | Caller: ${log.caller_phone} (${log.duration_seconds}s)</span>
            </div>
            <div class="detail-item">
                <label>Transcript</label>
                <div style="background: rgba(0,0,0,0.4); padding: 14px; border-radius: 8px; font-family: monospace; font-size: 12px; white-space: pre-wrap; line-height: 1.6; max-height: 350px; overflow-y: auto;">
                    ${log.transcript || 'No transcript recorded for this session.'}
                </div>
            </div>
        </div>
    `;
    document.getElementById('detailModal').style.display = 'flex';
}

function exportDataJSON() {
    const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(currentPatients, null, 2));
    const downloadAnchor = document.createElement('a');
    downloadAnchor.setAttribute("href", dataStr);
    downloadAnchor.setAttribute("download", `patients_export_${new Date().toISOString().slice(0,10)}.json`);
    document.body.appendChild(downloadAnchor);
    downloadAnchor.click();
    downloadAnchor.remove();
    showToast('Exported patient directory to JSON.');
}

function showToast(message) {
    const toast = document.getElementById('toast');
    toast.textContent = message;
    toast.style.display = 'block';
    setTimeout(() => { toast.style.display = 'none'; }, 3500);
}
