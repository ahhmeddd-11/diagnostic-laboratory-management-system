import { fetchAPI, logActivity } from './api.js';

let currentUser = null;
let currentView = 'dashboard-view';
let currentPrintId = null;
let allPatients = [];
let allReports = [];
let allTests = [];

document.addEventListener('DOMContentLoaded', async () => {
    // 1. Authenticate & Setup
    try {
        const res = await fetchAPI('/auth/me');
        currentUser = res.user;
        setupUI();
        loadDashboardStats();
    } catch (err) {
        // Handled by api.js redirect
    }

    // 2. Navigation Logic
    const navLinksContainer = document.getElementById('nav-links');
    
    document.querySelectorAll('.nav-item').forEach(item => {
        item.addEventListener('click', (e) => {
            e.preventDefault();
            const targetViewId = item.getAttribute('data-view');
            switchView(targetViewId, item);
            if (window.innerWidth <= 768) {
                navLinksContainer.classList.remove('show');
            }
        });
    });

    // Mobile Menu Toggle
    document.getElementById('mobile-menu-btn')?.addEventListener('click', () => {
        navLinksContainer.classList.toggle('show');
    });

    window.logoutUser = async () => {
        await logActivity('LOGOUT', 'User logged out');
        await fetchAPI('/auth/logout', { method: 'POST' });
        window.location.href = '/';
    };

    // 3. Modal Close Logic
    document.querySelector('.close-modal').addEventListener('click', closeModal);
    document.querySelector('.close-print-modal').addEventListener('click', () => {
        document.getElementById('print-modal').classList.add('hidden');
    });

    // Close modal when clicking outside the card
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                if (modal.id === 'dynamic-modal') {
                    closeModal();
                } else {
                    modal.classList.add('hidden');
                }
            }
        });
    });

    // 4. Action Buttons (Role Check applied in setupUI)
    document.getElementById('btn-add-patient')?.addEventListener('click', openAddPatientModal);
    document.getElementById('btn-add-test')?.addEventListener('click', openAddTestModal);
    document.getElementById('btn-create-report')?.addEventListener('click', openCreateReportModal);
    document.getElementById('btn-add-user')?.addEventListener('click', openAddUserModal);

    // 5. Print Layout Logic
    document.getElementById('btn-print-with-header').addEventListener('click', async () => {
        const incPatho = document.getElementById('include-pathologist-sig').checked;
        window.open(`/print?id=${currentPrintId}&header=true&pathologist=${incPatho}`, '_blank');
        document.getElementById('print-modal').classList.add('hidden');
        await logActivity('PRINT_REPORT', `Printed Report ID: ${currentPrintId} (With Header)`);
    });
    document.getElementById('btn-print-no-header').addEventListener('click', async () => {
        const incPatho = document.getElementById('include-pathologist-sig').checked;
        window.open(`/print?id=${currentPrintId}&header=false&pathologist=${incPatho}`, '_blank');
        document.getElementById('print-modal').classList.add('hidden');
        await logActivity('PRINT_REPORT', `Printed Report ID: ${currentPrintId} (Without Header)`);
    });

    // 6. Theme Toggle Logic
    const themeBtn = document.getElementById('theme-toggle');
    if (themeBtn) {
        const savedTheme = localStorage.getItem('theme') || 'dark';
        themeBtn.textContent = savedTheme === 'dark' ? '☀️' : '🌙';

        themeBtn.addEventListener('click', () => {
            const currentTheme = document.documentElement.getAttribute('data-theme') || 'light';
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            document.documentElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeBtn.textContent = newTheme === 'dark' ? '☀️' : '🌙';
        });
    }

    // 7. Filter Event Listeners
    document.getElementById('search-patients')?.addEventListener('input', renderPatients);
    document.getElementById('filter-patients-date')?.addEventListener('change', renderPatients);
    
    document.getElementById('search-reports')?.addEventListener('input', renderReports);
    document.getElementById('filter-reports-date')?.addEventListener('change', renderReports);
    document.getElementById('report-filter')?.addEventListener('change', renderReports);

    document.getElementById('search-tests')?.addEventListener('input', renderTests);

    // Global Patient Search Header Bar
    const globalSearch = document.getElementById('global-patient-search');
    if (globalSearch) {
        globalSearch.addEventListener('keydown', (e) => {
            if (e.key === 'Enter') {
                e.preventDefault();
                const query = globalSearch.value;
                document.getElementById('nav-patients').click();
                setTimeout(() => {
                    document.getElementById('search-patients').value = query;
                    renderPatients();
                }, 100);
            }
        });
    }

    // 8. Scroll to Top Logic
    const scrollBtn = document.getElementById('scroll-to-top');
    
    if (scrollBtn) {
        // Track scroll position to show/hide button
        window.addEventListener('scroll', () => {
            if (window.scrollY > 300) {
                scrollBtn.classList.remove('hidden');
                // Tiny delay to allow display:block to apply before animating opacity
                setTimeout(() => scrollBtn.classList.add('visible'), 10);
            } else {
                scrollBtn.classList.remove('visible');
                setTimeout(() => scrollBtn.classList.add('hidden'), 300);
            }
        });

        // Click to scroll up smoothly
        scrollBtn.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
            // Add a little bounce animation when clicked
            scrollBtn.style.transform = 'scale(0.8)';
            setTimeout(() => {
                scrollBtn.style.transform = '';
            }, 150);
        });
    }
});

function setupUI() {
    document.getElementById('user-name').textContent = currentUser.name;
    document.getElementById('user-role').textContent = currentUser.role;
    
    const initials = currentUser.name.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase();
    const avatarEl = document.getElementById('user-avatar');
    
    if (currentUser.profile_photo) {
        avatarEl.innerHTML = `<img src="${currentUser.profile_photo}" style="width: 100%; height: 100%; object-fit: cover; border-radius: 50%;">`;
        avatarEl.style.background = 'transparent';
        avatarEl.style.color = 'transparent';
    } else {
        avatarEl.textContent = initials;
        avatarEl.style.background = 'var(--primary)';
        avatarEl.style.color = 'white';
    }

    // Role-based UI visibility adjustments
    if (currentUser.role === 'Admin') {
        document.getElementById('nav-users').classList.remove('hidden');
        document.getElementById('nav-logs')?.classList.remove('hidden');
    } else {
        // Non-admins cannot add tests
        if (document.getElementById('btn-add-test')) {
            document.getElementById('btn-add-test').style.display = 'none';
        }
        
        if (currentUser.role === 'Technician') {
            if (document.getElementById('btn-add-patient')) document.getElementById('btn-add-patient').style.display = 'none';
            if (document.getElementById('btn-create-report')) document.getElementById('btn-create-report').style.display = 'none';
        }
        
        if (currentUser.role === 'Operator') {
            if (document.getElementById('nav-billing')) document.getElementById('nav-billing').style.display = 'none';
        }
    }

    // Profile Click Logic
    const profileEl = document.querySelector('.user-profile');
    if (profileEl) {
        profileEl.style.cursor = 'pointer';
        profileEl.addEventListener('click', () => {
            const initials = currentUser.name.split(' ').map(n=>n[0]).join('').substring(0,2).toUpperCase();
            
            const avatarContent = currentUser.profile_photo 
                ? `<img src="${currentUser.profile_photo}" style="width: 80px; height: 80px; border-radius: 50%; object-fit: cover; margin: 0 auto 10px; border: 2px solid var(--primary); cursor: pointer; transition: transform 0.2s;" id="modal-avatar-img" title="Click to change photo">`
                : `<div id="modal-avatar-img" style="width: 80px; height: 80px; border-radius: 50%; background: var(--primary); color: white; display: flex; align-items: center; justify-content: center; font-size: 2rem; font-weight: bold; margin: 0 auto 10px; cursor: pointer; transition: transform 0.2s;" title="Click to add photo">${initials}</div>`;

            const removeBtn = currentUser.profile_photo 
                ? `<button id="btn-remove-photo" style="background: none; border: none; color: var(--danger); font-size: 0.85rem; cursor: pointer; margin-top: 5px; text-decoration: underline;">Remove Photo</button>`
                : '';

            setModal('My Profile', `
                <div style="margin-bottom: 20px; line-height: 1.6; text-align: center;">
                    <div style="position: relative; display: inline-block;">
                        ${avatarContent}
                        <input type="file" id="profile-photo-input" accept="image/*" style="display: none;">
                    </div>
                    <div>${removeBtn}</div>
                    <p style="font-size: 1.2rem; font-weight: 600; margin: 10px 0 0;">${currentUser.name}</p>
                    <p style="margin: 5px 0 0;"><span class="badge" style="background: var(--nav-active-bg); color: var(--primary); padding: 4px 10px; border-radius: 6px; font-size: 0.85rem;">${currentUser.role}</span></p>
                </div>
                <hr style="border: none; border-top: 1px solid var(--surface-border); margin: 20px 0;">
                <h4 style="margin-bottom: 15px; text-align: center;">Change Password</h4>
                <form id="form-change-password">
                    <div class="input-group">
                        <label>Current Password</label>
                        <input type="password" id="old-pw" required>
                    </div>
                    <div class="input-group">
                        <label>New Password</label>
                        <input type="password" id="new-pw" required minlength="6">
                    </div>
                    <div class="input-group">
                        <label>Confirm New Password</label>
                        <input type="password" id="confirm-pw" required minlength="6">
                    </div>
                    <div id="pw-error" class="error-text hidden"></div>
                    <div id="pw-success" style="color: var(--success); font-size: 0.85rem; margin-bottom: 16px; text-align: center;" class="hidden"></div>
                    <button type="submit" class="btn-primary" style="width: 100%;">Update Password</button>
                    <button type="button" class="btn-danger-outline" onclick="logoutUser()" style="width: 100%; margin-top: 12px;">Log Out</button>
                </form>
            `);

            // Photo Upload Listeners
            document.getElementById('modal-avatar-img').addEventListener('click', () => {
                document.getElementById('profile-photo-input').click();
            });

            document.getElementById('profile-photo-input').addEventListener('change', async (e) => {
                if (e.target.files && e.target.files[0]) {
                    const file = e.target.files[0];
                    const reader = new FileReader();
                    
                    reader.onload = (event) => {
                        // Open cropping modal on top of existing modal, or replace it
                        setModal('Crop Profile Photo', `
                            <div style="width: 100%; max-height: 400px; text-align: center; margin-bottom: 20px;">
                                <img id="crop-image-target" src="${event.target.result}" style="max-width: 100%; display: block;">
                            </div>
                            <div style="display: flex; gap: 10px;">
                                <button type="button" class="btn-primary" id="btn-crop-upload" style="flex: 1;">Crop & Upload</button>
                                <button type="button" class="btn-secondary" onclick="document.querySelector('.close-modal').click(); setTimeout(() => document.querySelector('.user-profile').click(), 100);" style="flex: 1;">Cancel</button>
                            </div>
                        `);
                        
                        const imgEl = document.getElementById('crop-image-target');
                        const cropper = new Cropper(imgEl, {
                            aspectRatio: 1,
                            viewMode: 1,
                            dragMode: 'move',
                            autoCropArea: 0.8,
                            restore: false,
                            guides: true,
                            center: true,
                            highlight: false,
                            cropBoxMovable: true,
                            cropBoxResizable: true,
                            toggleDragModeOnDblclick: false,
                        });
                        
                        document.getElementById('btn-crop-upload').addEventListener('click', async () => {
                            const btn = document.getElementById('btn-crop-upload');
                            btn.disabled = true;
                            btn.textContent = 'Uploading...';
                            
                            cropper.getCroppedCanvas({
                                width: 256,
                                height: 256,
                                imageSmoothingEnabled: true,
                                imageSmoothingQuality: 'high',
                            }).toBlob(async (blob) => {
                                const formData = new FormData();
                                formData.append('photo', blob, file.name);
                                
                                try {
                                    const res = await fetch('/api/auth/profile-photo', {
                                        method: 'POST',
                                        body: formData
                                    });
                                    const data = await res.json();
                                    if (!res.ok) throw new Error(data.error || 'Upload failed');
                                    
                                    currentUser.profile_photo = data.photo_url;
                                    setupUI();
                                    document.querySelector('.close-modal').click();
                                    setTimeout(() => profileEl.click(), 100); // Re-open profile modal
                                    await logActivity('PROFILE', 'User updated profile photo');
                                } catch (err) {
                                    alertDialog('Upload Error', err.message);
                                    btn.disabled = false;
                                    btn.textContent = 'Crop & Upload';
                                }
                            });
                        });
                    };
                    reader.readAsDataURL(file);
                }
            });

            const btnRemove = document.getElementById('btn-remove-photo');
            if (btnRemove) {
                btnRemove.addEventListener('click', async () => {
                    confirmDialog('Remove Photo', 'Are you sure you want to remove your photo?', async () => {
                        try {
                            const res = await fetch('/api/auth/profile-photo', { method: 'DELETE' });
                            const data = await res.json();
                            if (!res.ok) throw new Error(data.error || 'Removal failed');
                            
                            currentUser.profile_photo = null;
                            setupUI();
                            document.querySelector('.close-modal').click();
                            profileEl.click(); // Re-open
                            await logActivity('PROFILE', 'User removed profile photo');
                        } catch (err) {
                            alertDialog('Error', err.message);
                        }
                    });
                });
            }

            document.getElementById('form-change-password').addEventListener('submit', async (e) => {
                e.preventDefault();
                const oldPw = document.getElementById('old-pw').value;
                const newPw = document.getElementById('new-pw').value;
                const confirmPw = document.getElementById('confirm-pw').value;
                
                const errEl = document.getElementById('pw-error');
                const succEl = document.getElementById('pw-success');
                errEl.classList.add('hidden');
                succEl.classList.add('hidden');

                if (newPw !== confirmPw) {
                    errEl.textContent = 'New passwords do not match';
                    errEl.classList.remove('hidden');
                    return;
                }

                try {
                    const res = await fetch('/api/auth/change-password', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ old_password: oldPw, new_password: newPw })
                    });
                    const data = await res.json();
                    
                    if (!res.ok) throw new Error(data.error || 'Update failed');
                    
                    succEl.textContent = 'Password successfully updated!';
                    succEl.classList.remove('hidden');
                    document.getElementById('form-change-password').reset();
                    
                    await logActivity('SECURITY', 'User changed their password');
                } catch(err) {
                    errEl.textContent = err.message;
                    errEl.classList.remove('hidden');
                }
            });
        });
    }
}

function switchView(viewId, navElement) {
    document.querySelectorAll('.view-section').forEach(sec => sec.classList.add('hidden'));
    document.getElementById(viewId).classList.remove('hidden');
    
    document.querySelectorAll('.nav-item').forEach(nav => nav.classList.remove('active'));
    navElement.classList.add('active');

    document.getElementById('current-view-title').textContent = navElement.textContent.trim() + " Overview";
    currentView = viewId;

    if (viewId === 'patients-view') loadPatients();
    else if (viewId === 'tests-view') loadTests();
    else if (viewId === 'reports-view') loadReports();
    else if (viewId === 'users-view') loadUsers();
    else if (viewId === 'logs-view') loadLogs();
    else if (viewId === 'dashboard-view') loadDashboardStats();
    else if (viewId === 'billing-view') loadBilling();
    else if (viewId === 'packages-view') loadPackages();
}

/* =========================================
   BILLING & LEDGER
   ========================================= */
async function loadBilling() {
    try {
        const records = await fetchAPI('/reports/billing/daily-collection');
        const tbody = document.querySelector('#billing-table tbody');
        tbody.innerHTML = '';
        
        let grandTotalRevenue = 0;
        let grandTotalCollected = 0;
        let grandTotalPending = 0;

        records.forEach(r => {
            grandTotalRevenue += r.total_amount;
            grandTotalCollected += r.paid_amount;
            grandTotalPending += r.balance_due;

            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>#${r.report_id}</strong></td>
                <td><strong>${r.patient_name}</strong></td>
                <td>${r.report_date ? new Date(r.report_date).toLocaleDateString() : '-'}</td>
                <td>₹${r.total_amount.toFixed(2)}</td>
                <td>₹${r.discount.toFixed(2)}</td>
                <td style="color: var(--success); font-weight: 600;">₹${r.paid_amount.toFixed(2)}</td>
                <td style="color: var(--danger); font-weight: 600;">₹${r.balance_due.toFixed(2)}</td>
                <td><span class="badge" style="background: var(--nav-active-bg); color: var(--primary);">${r.payment_status}</span></td>
            `;
            tbody.appendChild(tr);
        });

        document.getElementById('billing-total-revenue').textContent = '₹' + grandTotalRevenue.toFixed(2);
        document.getElementById('billing-total-collected').textContent = '₹' + grandTotalCollected.toFixed(2);
        document.getElementById('billing-total-pending').textContent = '₹' + grandTotalPending.toFixed(2);
        
    } catch (err) {
        console.error('Error loading billing:', err);
    }
}


/* =========================================
   DASHBOARD / STATS
   ========================================= */
async function loadDashboardStats() {
    try {
        const [patients, tests, reports] = await Promise.all([
            fetchAPI('/patients/'),
            fetchAPI('/tests/'),
            fetchAPI('/reports/')
        ]);
        document.getElementById('stat-patients').textContent = patients.length || 0;
        document.getElementById('stat-tests').textContent = tests.length || 0;
        document.getElementById('stat-reports-pending').textContent = reports.filter(r => r.status === 'Pending').length || 0;

        // Populate Approved Reports table
        const approvedReports = reports.filter(r => r.status === 'Approved').slice(0, 5); // show latest 5
        const tbody = document.querySelector('#dashboard-reports-table tbody');
        tbody.innerHTML = '';
        approvedReports.forEach(r => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${r.id}</td>
                <td><strong>${r.patient_name}</strong></td>
                <td>${r.approved_by_name || '-'}</td>
                <td>${r.report_date ? new Date(r.report_date).toLocaleDateString() : new Date(r.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn-primary" onclick="openPrintOptions(${r.id})" style="padding: 4px 8px; font-size: 0.8rem;">🖨️ Print</button>
                </td>
            `;
            tbody.appendChild(tr);
        });

    } catch(e) { console.error('Error loading stats', e); }
}

/* =========================================
   PATIENTS
   ========================================= */
async function loadPatients() {
    try {
        allPatients = await fetchAPI('/patients/');
        renderPatients();
    } catch(e) { console.error('Failed to load patients', e); }
}

function renderPatients() {
    const searchText = (document.getElementById('search-patients').value || '').toLowerCase();
    const filterDate = document.getElementById('filter-patients-date').value;
    
    const filtered = allPatients.filter(p => {
        const matchesText = p.name.toLowerCase().includes(searchText) || 
                            String(p.id).includes(searchText) || 
                            (p.referred_doctor && p.referred_doctor.toLowerCase().includes(searchText));
        const matchesDate = filterDate ? p.date === filterDate : true;
        return matchesText && matchesDate;
    });

    const tbody = document.querySelector('#patients-table tbody');
    tbody.innerHTML = '';
    filtered.forEach(p => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td><strong>${p.name}</strong></td>
            <td>${p.age} / ${p.gender}</td>
            <td>${p.referred_doctor || 'Self'}</td>
            <td>${p.date}</td>
            <td>
                ${currentUser.role === 'Admin' ? 
                    `<button class="btn-danger-outline" onclick="deletePatient(${p.id})" style="padding: 4px 8px; font-size: 0.8rem;">Delete</button>` 
                    : '-'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.deletePatient = async (id) => {
    confirmDialog('Delete Patient', 'Are you sure you want to delete this patient?', async () => {
        await fetchAPI(`/patients/${id}`, { method: 'DELETE' });
        await logActivity('DELETE', `Deleted patient ID: ${id}`);
        loadPatients();
    });
};

function openAddPatientModal() {
    setModal('Add New Patient', `
        <form id="form-patient">
            <div class="input-group">
                <label>Name</label>
                <input type="text" id="p-name" required>
            </div>
            <div class="input-group">
                <label>Age</label>
                <input type="number" id="p-age" required>
            </div>
            <div class="input-group">
                <label>Gender</label>
                <select id="p-gender">
                    <option value="Male">Male</option>
                    <option value="Female">Female</option>
                    <option value="Other">Other</option>
                </select>
            </div>
            <div class="input-group">
                <label>Date</label>
                <input type="date" id="p-date" required>
            </div>
            <div class="input-group">
                <label>Referred Doctor</label>
                <input type="text" id="p-doc">
            </div>
            <button type="submit" class="btn-primary">Save Patient</button>
        </form>
    `);

    document.getElementById('form-patient').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById('p-name').value,
            age: parseInt(document.getElementById('p-age').value),
            gender: document.getElementById('p-gender').value,
            date: document.getElementById('p-date').value,
            referred_doctor: document.getElementById('p-doc').value
        };
        await fetchAPI('/patients/', { method: 'POST', body: JSON.stringify(data) });
        await logActivity('DATA_ENTRY', `Added new patient: ${data.name}`);
        closeModal();
        loadPatients();
    });
}

/* =========================================
   TESTS
   ========================================= */
async function loadTests() {
    try {
        allTests = await fetchAPI('/tests/');
        // Sort tests by ID ascending (1 to ...) by default
        allTests.sort((a, b) => a.id - b.id);
        renderTests();
    } catch(e) { console.error('Failed to load tests', e); }
}

function renderTests() {
    const searchText = (document.getElementById('search-tests').value || '').toLowerCase();
    
    const filtered = allTests.filter(t => {
        return String(t.id).includes(searchText) || t.test_name.toLowerCase().includes(searchText);
    });

    const tbody = document.querySelector('#tests-table tbody');
    tbody.innerHTML = '';
    filtered.forEach(t => {
        const paramCount = t.parameters ? t.parameters.length : 0;
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${t.id}</td>
            <td><strong>${t.test_name}</strong></td>
            <td>${paramCount} Parameters</td>
            <td>₹${t.price.toFixed(2)}</td>
            <td>
                ${currentUser.role === 'Admin' ? `
                <button class="btn-primary" onclick="editTest(${t.id}, '${t.test_name.replace(/'/g, "\\'")}', ${t.price})" style="padding: 4px 8px; font-size: 0.8rem; background: #f59e0b; border-color: #f59e0b; margin-right: 4px;">Edit</button>
                <button class="btn-secondary" onclick="configureParams(${t.id})" style="padding: 4px 8px; font-size: 0.8rem; margin-right: 4px;">Params</button>
                <button class="btn-danger-outline" onclick="deleteTest(${t.id})" style="padding: 4px 8px; font-size: 0.8rem;">Delete</button>
                ` : '-'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.deleteTest = async (id) => {
    confirmDialog('Delete Lab Test', 'Are you sure you want to delete this test?', async () => {
        await fetchAPI(`/tests/${id}`, { method: 'DELETE' });
        await logActivity('DELETE', `Deleted test ID: ${id}`);
        loadTests();
    });
};
window.configureParams = async (id) => {
    const tests = await fetchAPI('/tests/');
    const test = tests.find(t => t.id === id);
    if (!test) return;

    const renderParamRows = (params) => {
        return params.map((p, idx) => `
            <div class="param-config-row" style="background: rgba(255,255,255,0.05); padding: 12px; border-radius: 8px; margin-bottom: 10px; border: 1px solid var(--surface-border);">
                <div style="display: grid; grid-template-columns: 2fr 1fr 1.5fr; gap: 8px; margin-bottom: 8px;">
                    <div class="input-group">
                        <label>Parameter Name</label>
                        <input type="text" class="pc-name" value="${p.parameter_name}" required>
                    </div>
                    <div class="input-group">
                        <label>Unit</label>
                        <input type="text" class="pc-unit" value="${p.unit || ''}">
                    </div>
                    <div class="input-group">
                        <label>Normal Range</label>
                        <input type="text" class="pc-range" value="${p.normal_range || ''}">
                    </div>
                </div>
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 8px;">
                    <div class="input-group">
                        <label>Type</label>
                        <select class="pc-type" style="width: 100%;">
                            <option value="text" ${p.parameter_type === 'text' ? 'selected' : ''}>Text</option>
                            <option value="numeric" ${p.parameter_type === 'numeric' ? 'selected' : ''}>Numeric</option>
                            <option value="formula" ${p.parameter_type === 'formula' ? 'selected' : ''}>Formula (Calculated)</option>
                            <option value="widal" ${p.parameter_type === 'widal' ? 'selected' : ''}>Widal Grid</option>
                        </select>
                    </div>
                    <div class="input-group pc-formula-group ${p.parameter_type === 'formula' ? '' : 'hidden'}">
                        <label>Formula (e.g. [123] + [124])</label>
                        <input type="text" class="pc-formula" value="${p.formula || ''}" placeholder="Use [ParameterID] for references">
                    </div>
                </div>
                <div style="display: flex; justify-content: space-between; align-items: center; margin-top: 8px;">
                    <span style="font-size: 0.75rem; color: var(--text-secondary);">ID: <strong>${p.id || 'NEW'}</strong></span>
                    <button type="button" class="btn-danger-outline" onclick="this.parentElement.parentElement.remove()" style="padding: 2px 8px; font-size: 0.7rem;">Remove</button>
                </div>
            </div>
        `).join('');
    };

    setModal(`Configure Parameters: ${test.test_name}`, `
        <div id="params-config-container" style="max-height: 450px; overflow-y: auto; margin-bottom: 16px; padding-right: 8px;">
            ${renderParamRows(test.parameters)}
        </div>
        <div style="display: flex; gap: 10px;">
            <button type="button" class="btn-secondary" id="btn-add-param-row" style="flex: 1;">+ Add Parameter</button>
            <button type="button" class="btn-primary" id="btn-save-params" style="flex: 1;">Save Configuration</button>
        </div>
    `);

    document.getElementById('btn-add-param-row').addEventListener('click', () => {
        const container = document.getElementById('params-config-container');
        const div = document.createElement('div');
        div.innerHTML = renderParamRows([{ parameter_name: '', unit: '', normal_range: '', parameter_type: 'text', formula: '' }]);
        container.appendChild(div.firstElementChild);
        
        // Add listener for type change on new row
        const newRow = container.lastElementChild;
        newRow.querySelector('.pc-type').addEventListener('change', (e) => {
            const fGroup = newRow.querySelector('.pc-formula-group');
            if (e.target.value === 'formula') fGroup.classList.remove('hidden');
            else fGroup.classList.add('hidden');
        });
    });

    document.querySelectorAll('.pc-type').forEach(sel => {
        sel.addEventListener('change', (e) => {
            const row = e.target.closest('.param-config-row');
            const fGroup = row.querySelector('.pc-formula-group');
            if (e.target.value === 'formula') fGroup.classList.remove('hidden');
            else fGroup.classList.add('hidden');
        });
    });

    document.getElementById('btn-save-params').addEventListener('click', async () => {
        const paramRows = document.querySelectorAll('.param-config-row');
        const paramsData = Array.from(paramRows).map((row, idx) => ({
            parameter_name: row.querySelector('.pc-name').value,
            unit: row.querySelector('.pc-unit').value,
            normal_range: row.querySelector('.pc-range').value,
            parameter_type: row.querySelector('.pc-type').value,
            formula: row.querySelector('.pc-formula').value,
            display_order: idx + 1
        }));

        await fetchAPI(`/tests/${id}/parameters`, {
            method: 'PUT',
            body: JSON.stringify(paramsData)
        });
        await logActivity('CONFIG', `Updated parameters for test: ${test.test_name}`);
        closeModal();
        loadTests();
    });
};

function openAddTestModal() {
    setModal('Add New Test', `
        <form id="form-test">
            <div class="input-group">
                <label>Test Name</label>
                <input type="text" id="t-name" required>
            </div>
            <div class="input-group">
                <label>Price</label>
                <input type="number" step="0.01" id="t-price" required>
            </div>
            <button type="submit" class="btn-primary">Save Test</button>
        </form>
    `);

    document.getElementById('form-test').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            test_name: document.getElementById('t-name').value,
            normal_range: '',
            price: parseFloat(document.getElementById('t-price').value)
        };
        await fetchAPI('/tests/', { method: 'POST', body: JSON.stringify(data) });
        await logActivity('DATA_ENTRY', `Added new lab test: ${data.test_name}`);
        closeModal();
        loadTests();
    });
}

/* =========================================
   TEST PACKAGES
   ========================================= */
let allPackages = [];
async function loadPackages() {
    try {
        allPackages = await fetchAPI('/tests/packages');
        renderPackages();
    } catch(e) { console.error('Failed to load packages', e); }
}

function renderPackages() {
    const searchText = (document.getElementById('search-packages').value || '').toLowerCase();
    const filtered = allPackages.filter(p => p.package_name.toLowerCase().includes(searchText));

    const tbody = document.querySelector('#packages-table tbody');
    tbody.innerHTML = '';
    filtered.forEach(p => {
        const testsList = p.tests.map(t => t.test_name).join(', ');
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${p.id}</td>
            <td><strong>${p.package_name}</strong></td>
            <td style="font-size: 0.85rem; color: var(--text-secondary); max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis;" title="${testsList}">${testsList}</td>
            <td>₹${p.price.toFixed(2)}</td>
            <td>
                ${currentUser.role === 'Admin' ? `
                <button class="btn-danger-outline" onclick="deletePackage(${p.id})" style="padding: 4px 8px; font-size: 0.8rem;">Delete</button>
                ` : '-'}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.deletePackage = async (id) => {
    confirmDialog('Delete Package', 'Are you sure you want to delete this test package?', async () => {
        await fetchAPI(`/tests/packages/${id}`, { method: 'DELETE' });
        await logActivity('DELETE', `Deleted test package ID: ${id}`);
        loadPackages();
    });
};

async function openAddPackageModal() {
    const tests = await fetchAPI('/tests/');
    
    let testCheckboxes = tests.map(t => `
        <label style="display: flex; align-items: center; gap: 8px; background: rgba(0,0,0,0.2); padding: 8px; border-radius: 6px; cursor: pointer; margin-bottom: 4px;">
            <input type="checkbox" class="package-test-check" value="${t.id}" data-price="${t.price}">
            <span>${t.test_name} (₹${t.price})</span>
        </label>
    `).join('');

    setModal('Create Test Package', `
        <form id="form-package">
            <div class="input-group">
                <label>Package Name</label>
                <input type="text" id="pkg-name" required placeholder="e.g. Full Body Profile">
            </div>
            <div class="input-group">
                <label>Description</label>
                <textarea id="pkg-desc" style="width:100%; min-height:60px; background: var(--input-bg); border: 1px solid var(--surface-border); border-radius: 8px; color: white; padding: 10px;"></textarea>
            </div>
            <div class="input-group">
                <label>Select Tests to Include</label>
                <div style="max-height: 200px; overflow-y: auto; padding-right: 8px;" id="pkg-tests-container">
                    ${testCheckboxes}
                </div>
            </div>
            <div class="input-group">
                <label>Package Price (Total of tests: ₹<span id="pkg-tests-total">0.00</span>)</label>
                <input type="number" step="0.01" id="pkg-price" required placeholder="Custom package price">
            </div>
            <button type="submit" class="btn-primary" style="width:100%;">Save Package</button>
        </form>
    `);

    const priceInput = document.getElementById('pkg-price');
    const totalSpan = document.getElementById('pkg-tests-total');

    document.querySelectorAll('.package-test-check').forEach(chk => {
        chk.addEventListener('change', () => {
            let total = 0;
            document.querySelectorAll('.package-test-check:checked').forEach(c => {
                total += parseFloat(c.getAttribute('data-price'));
            });
            totalSpan.textContent = total.toFixed(2);
            if (!priceInput.value) priceInput.value = total.toFixed(2);
        });
    });

    document.getElementById('form-package').addEventListener('submit', async (e) => {
        e.preventDefault();
        const test_ids = Array.from(document.querySelectorAll('.package-test-check:checked')).map(c => parseInt(c.value));
        if (test_ids.length === 0) return alert('Please select at least one test.');

        const data = {
            package_name: document.getElementById('pkg-name').value,
            description: document.getElementById('pkg-desc').value,
            price: parseFloat(priceInput.value),
            test_ids: test_ids
        };
        await fetchAPI('/tests/packages', { method: 'POST', body: JSON.stringify(data) });
        await logActivity('DATA_ENTRY', `Created new test package: ${data.package_name}`);
        closeModal();
        loadPackages();
    });
}

// Global listeners for Packages View
document.addEventListener('click', e => {
    if (e.target.id === 'btn-add-package') openAddPackageModal();
});
if (document.getElementById('search-packages')) {
    document.getElementById('search-packages').addEventListener('input', renderPackages);
}


/* =========================================
   REPORTS
   ========================================= */
async function loadReports() {
    try {
        allReports = await fetchAPI('/reports/');
        renderReports();
    } catch(e) { console.error('Failed to load reports', e); }
}

function renderReports() {
    const searchText = (document.getElementById('search-reports').value || '').toLowerCase();
    const filterDate = document.getElementById('filter-reports-date').value;
    const filterStatus = document.getElementById('report-filter').value;
    
    const filtered = allReports.filter(r => {
        const matchesText = r.patient_name.toLowerCase().includes(searchText) || 
                            String(r.id).includes(searchText);
        
        // Report date formatting (handles both YYYY-MM-DD and timestamp formats)
        const rDateRaw = r.report_date || r.created_at;
        const rDate = rDateRaw ? rDateRaw.split('T')[0].split(' ')[0] : '';
        const matchesDate = filterDate ? rDate === filterDate : true;
        
        const matchesStatus = filterStatus === 'All' ? true : r.status === filterStatus;
        
        return matchesText && matchesDate && matchesStatus;
    });

    const tbody = document.querySelector('#reports-table tbody');
    tbody.innerHTML = '';
    filtered.forEach(r => {
        const tr = document.createElement('tr');
        const statusClass = r.status.toLowerCase();
        tr.innerHTML = `
            <td>${r.id}</td>
            <td><strong>${r.patient_name}</strong></td>
            <td><span class="status-badge ${statusClass}">${r.status}</span></td>
            <td>${r.approved_by_name || '-'}</td>
            <td>${new Date(r.created_at).toLocaleDateString()}</td>
            <td>
                <button class="btn-primary" onclick="viewReport(${r.id})" style="padding: 4px 8px; font-size: 0.8rem; margin-right: 4px;">View</button>
                ${currentUser.role === 'Admin' ? `
                <button class="btn-primary" onclick="editReport(${r.id})" style="padding: 4px 8px; font-size: 0.8rem; background: #f59e0b; border-color: #f59e0b; margin-right: 4px;">Edit</button>
                <button class="btn-danger-outline" onclick="deleteReport(${r.id})" style="padding: 4px 8px; font-size: 0.8rem;">Delete</button>
                ` : ''}
            </td>
        `;
        tbody.appendChild(tr);
    });
}

window.viewReport = async (id) => {
    try {
        const report = await fetchAPI(`/reports/${id}`);
        
        const groupedDetails = {};
        report.details.forEach(d => {
            if (!groupedDetails[d.test_name]) {
                groupedDetails[d.test_name] = { price: d.price, parameters: [] };
            }
            groupedDetails[d.test_name].parameters.push(d);
        });

        let totalCost = 0;
        let detailsHtml = `
            <div style="margin-bottom: 20px; line-height: 1.6;">
                <p><strong>Patient:</strong> ${report.patient_name} (${report.age} ${report.gender})</p>
                <p><strong>Status:</strong> ${report.status} ${report.approved_by_name ? `by ${report.approved_by_name}` : ''}</p>
                <p><strong>Date:</strong> ${new Date(report.created_at).toLocaleString()}</p>
            </div>
        `;

        Object.keys(groupedDetails).forEach(testName => {
            const group = groupedDetails[testName];
            totalCost += group.price;
            
            detailsHtml += `
            <div style="margin-bottom: 16px; background: rgba(0,0,0,0.15); border-radius: 8px; overflow: hidden; border: 1px solid var(--surface-border);">
                <div style="background: var(--surface-border); padding: 10px 14px; font-weight: bold; display: flex; justify-content: space-between;">
                    <span>${testName}</span>
                    <span>₹${group.price.toFixed(2)}</span>
                </div>
            `;
            
            group.parameters.forEach(p => {
                if (p.parameter_type === 'widal' && p.result_value) {
                    try {
                        const grid = JSON.parse(p.result_value);
                        detailsHtml += `
                        <div style="padding: 12px; border-bottom: 1px solid rgba(255,255,255,0.05);">
                            <p style="margin-bottom: 8px; color: var(--primary); font-weight: 600;">${p.parameter_name}</p>
                            <table style="width: 100%; border-collapse: collapse; font-size: 0.75rem; text-align: center;">
                                <thead>
                                    <tr><th style="text-align:left;">Antigen</th><th>1:20</th><th>1:40</th><th>1:80</th><th>1:160</th><th>1:320</th></tr>
                                </thead>
                                <tbody>
                                    ${Object.keys(grid).map(ant => `
                                        <tr>
                                            <td style="text-align:left; border:1px solid rgba(255,255,255,0.1); padding:4px;">${ant}</td>
                                            ${[20, 40, 80, 160, 320].map(dil => `<td style="border:1px solid rgba(255,255,255,0.1);">${grid[ant][dil] || '-'}</td>`).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>`;
                    } catch(e) { 
                        detailsHtml += `<div style="padding: 8px 14px;">Error rendering Widal data</div>`; 
                    }
                } else {
                    detailsHtml += `
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr 1fr; padding: 8px 14px; border-bottom: 1px solid rgba(255,255,255,0.02); font-size: 0.9rem;">
                        <span style="color: var(--text-secondary);">${p.parameter_name}</span>
                        <span style="font-weight: bold; color: var(--primary);">${p.result_value || '-'}</span>
                        <span style="color: var(--text-secondary);">${p.unit || '-'}</span>
                        <span style="font-size: 0.8rem; color: #888;">${p.normal_range || '-'}</span>
                    </div>`;
                }
            });
            
            detailsHtml += `</div>`;
        });
        
        detailsHtml += `
            <div style="text-align: right; padding: 12px; font-weight: bold; font-size: 1.1rem; color: var(--primary);">
                Total Charges: ₹${totalCost.toFixed(2)}
            </div>
        `;

        // Add Approval Button for Admin/Tech
        if (report.status === 'Pending' && ['Admin', 'Technician'].includes(currentUser.role)) {
            detailsHtml += `
                <button class="btn-primary btn-success" onclick="approveReport(${report.id})" style="width:100%; margin-bottom: 15px;">✓ Approve Report</button>
            `;
        }

        // Print Logic
        if (report.status === 'Pending' && currentUser.role === 'Operator') {
            detailsHtml += `
                <div style="text-align: center; padding: 12px; background: rgba(245,158,11,0.1); color: var(--warning); border-radius: 6px; font-size: 0.85rem; font-weight: 500; border: 1px solid rgba(245,158,11,0.2);">
                    ⚠️ This report is pending. You can print it once it is approved by an Admin or Technician.
                </div>
            `;
        } else {
            detailsHtml += `
                <button class="btn-primary" onclick="openPrintOptions(${report.id})" style="width:100%; background: #475569;">🖨️ Print Lab Report</button>
            `;
        }

        setModal(`Invoice / Report #${report.id}`, detailsHtml);
    } catch(e) { alert('Error loading report'); }
};

window.approveReport = async (id) => {
    try {
        await fetchAPI(`/reports/${id}/approve`, { method: 'PUT' });
        await logActivity('REPORT_APPROVAL', `Approved report ID: ${id}`);
        closeModal();
        loadReports();
        loadDashboardStats();
    } catch(err) { alert('Error approving report'); }
};

window.deleteReport = async (id) => {
    confirmDialog('Delete Report', 'Are you sure you want to delete this report?', async () => {
        await fetchAPI(`/reports/${id}`, { method: 'DELETE' });
        await logActivity('DELETE', `Deleted report ID: ${id}`);
        loadReports();
        loadDashboardStats();
    });
};

window.editReport = async (id) => {
    try {
        const report = await fetchAPI(`/reports/${id}`);
        const tests = await fetchAPI('/tests/');

        const existingParams = {};
        const includedTestIds = new Set();
        report.details.forEach(d => {
            existingParams[d.parameter_id] = d.result_value;
            includedTestIds.add(d.test_id);
        });

        let testCardsHtml = tests.map(t => {
            const isChecked = includedTestIds.has(t.id);
            
            let paramsHtml = t.parameters.map(p => {
                const val = existingParams[p.id] || '';
                
                if (p.parameter_type === 'widal') {
                    let grid = { 'S. Typhi O': {}, 'S. Typhi H': {}, 'S. Paratyphi AH': {}, 'S. Paratyphi BH': {} };
                    if (val) { try { grid = JSON.parse(val); } catch(e) {} }

                    return `
                    <div class="param-input edit-test-params-${t.id} ${isChecked ? '' : 'hidden'}" style="margin-top: 10px; margin-left: 24px;">
                        <label style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 8px; display: block;">${p.parameter_name} (Widal Grid)</label>
                        <div class="widal-grid-container" data-param-id="${p.id}" style="overflow-x: auto;">
                            <table class="widal-entry-table" style="width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: center;">
                                <thead>
                                    <tr><th>Antigen</th><th>1:20</th><th>1:40</th><th>1:80</th><th>1:160</th><th>1:320</th></tr>
                                </thead>
                                <tbody>
                                    ${Object.keys(grid).map(ant => `
                                        <tr>
                                            <td style="text-align: left; padding: 4px; border: 1px solid var(--surface-border);">${ant}</td>
                                            ${[20, 40, 80, 160, 320].map(dil => `
                                                <td style="border: 1px solid var(--surface-border);">
                                                    <select class="widal-select" data-antigen="${ant}" data-dilution="${dil}" style="width: 100%; background: transparent; border: none; color: white;">
                                                        <option value="-" ${grid[ant][dil] === '-' ? 'selected' : ''}>-</option>
                                                        <option value="+" ${grid[ant][dil] === '+' ? 'selected' : ''}>+</option>
                                                    </select>
                                                </td>
                                            `).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        <input type="hidden" class="edit-param-val" data-param-id="${p.id}" value='${val}'>
                    </div>
                    `;
                }

                const isFormula = p.parameter_type === 'formula';
                return `
                <div class="param-input edit-test-params-${t.id} ${isChecked ? '' : 'hidden'}" style="margin-top: 6px; margin-left: 24px; display: flex; flex-direction: column; gap: 4px;">
                    <label style="font-size: 0.85rem; color: var(--text-secondary);">${p.parameter_name} ${p.unit ? `(${p.unit})` : ''} <span style="font-size:0.75rem; color:#888;">[Normal: ${p.normal_range}]</span></label>
                    <input type="${p.parameter_type === 'numeric' ? 'number' : 'text'}" 
                           class="edit-param-val ${isFormula ? 'formula-field' : ''}" 
                           data-param-id="${p.id}" 
                           data-formula="${p.formula || ''}"
                           placeholder="${isFormula ? 'Auto-calculated' : 'Result'}"
                           ${isFormula ? 'readonly style="background: rgba(99, 102, 241, 0.1); border-color: var(--primary); font-weight: bold;"' : ''}
                           value="${val}">
                </div>
                `;
            }).join('');

            return `
            <div style="background: rgba(0,0,0,0.2); padding: 12px; margin-bottom: 8px; border-radius: 8px; display: flex; flex-direction: column; gap: 8px;">
                <label style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" class="edit-test-check" value="${t.id}" data-price="${t.price}" ${isChecked ? 'checked' : ''}>
                    <strong style="font-size: 1.05rem; color: var(--primary);">${t.test_name}</strong>
                </label>
                ${paramsHtml}
            </div>
            `;
        }).join('');

        setModal(`Edit Report #${id}`, `
            <form id="form-edit-report">
                <div class="input-group">
                    <label>Report Date</label>
                    <input type="date" id="e-date" required value="${report.report_date ? report.report_date.split('T')[0] : report.created_at.split(' ')[0]}">
                </div>
                <div class="input-group">
                    <label style="font-size: 1rem; color: var(--text-primary);">Patient: <strong>${report.patient_name}</strong></label>
                </div>
                <div style="margin-bottom: 16px;">
                    <label style="display:block; margin-bottom: 8px;">Update Tests & Results</label>
                    <div style="max-height: 350px; overflow-y: auto; padding-right: 8px;">
                        <input type="text" id="search-edit-tests" placeholder="Search Test Profiles..." class="input-group" style="margin-bottom: 10px; width: 100%;">
                        <div id="edit-tests-container">
                            ${testCardsHtml}
                        </div>
                    </div>
                </div>
                <div style="background: rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                    <h4 style="margin-top:0; margin-bottom: 10px;">Billing Details</h4>
                    <div style="display:flex; gap:10px;">
                        <div class="input-group" style="flex:1;">
                            <label>Total Amount</label>
                            <input type="number" id="e-total" readonly value="${(report.total_amount || 0).toFixed(2)}">
                        </div>
                        <div class="input-group" style="flex:1;">
                            <label>Discount</label>
                            <input type="number" id="e-discount" value="${(report.discount || 0).toFixed(2)}" step="0.01" min="0">
                        </div>
                        <div class="input-group" style="flex:1;">
                            <label>Paid Amount</label>
                            <input type="number" id="e-paid" value="${(report.paid_amount || 0).toFixed(2)}" step="0.01" min="0">
                        </div>
                        <div class="input-group" style="flex:1;">
                            <label>Balance</label>
                            <input type="number" id="e-balance" readonly value="${(report.balance_due || 0).toFixed(2)}">
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button type="submit" class="btn-secondary" id="btn-edit-draft" style="flex: 1;">Save as Draft</button>
                    <button type="submit" class="btn-primary" id="btn-edit-submit" style="flex: 1;">Update Report</button>
                </div>
            </form>
        `);

        // Re-use Logic from Create Modal
        const calculateBilling = () => {
            let total = 0;
            document.querySelectorAll('.edit-test-check:checked').forEach(chk => {
                total += parseFloat(chk.getAttribute('data-price') || 0);
            });
            document.getElementById('e-total').value = total.toFixed(2);
            const discount = parseFloat(document.getElementById('e-discount').value) || 0;
            const paid = parseFloat(document.getElementById('e-paid').value) || 0;
            document.getElementById('e-balance').value = (total - discount - paid).toFixed(2);
        };

        const runFormulaEngine = () => {
            const allValues = {};
            document.querySelectorAll('.edit-param-val:not(.formula-field)').forEach(inp => {
                const id = inp.getAttribute('data-param-id');
                const val = parseFloat(inp.value);
                if (!isNaN(val)) allValues[id] = val;
            });
            document.querySelectorAll('.formula-field').forEach(fld => {
                let formula = fld.getAttribute('data-formula');
                if (!formula) return;
                let canCalculate = true;
                const replaced = formula.replace(/\[(\d+)\]/g, (match, id) => {
                    if (allValues[id] !== undefined) return allValues[id];
                    canCalculate = false; return 0;
                });
                if (canCalculate) { try { const result = eval(replaced); fld.value = isFinite(result) ? result.toFixed(2) : ''; } catch(e) { fld.value = 'Error'; } }
                else fld.value = '';
            });
        };

        document.getElementById('search-edit-tests').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('#edit-tests-container > div').forEach(div => {
                const testName = div.querySelector('strong').innerText.toLowerCase();
                div.style.display = testName.includes(query) ? 'flex' : 'none';
            });
        });

        document.querySelectorAll('.edit-test-check').forEach(chk => {
            chk.addEventListener('change', (e) => {
                const paramInputs = document.querySelectorAll(`.edit-test-params-${e.target.value}`);
                paramInputs.forEach(inp => {
                    if (e.target.checked) inp.classList.remove('hidden');
                    else inp.classList.add('hidden');
                });
                calculateBilling();
                runFormulaEngine();
            });
        });

        document.getElementById('e-discount').addEventListener('input', calculateBilling);
        document.getElementById('e-paid').addEventListener('input', calculateBilling);
        
        // Use a persistent listener for formula/widal updates in edit modal
        const editModal = document.getElementById('dynamic-modal');
        editModal.addEventListener('input', e => { if (e.target.classList.contains('edit-param-val')) runFormulaEngine(); });
        editModal.addEventListener('change', e => {
            if (e.target.classList.contains('widal-select')) {
                const container = e.target.closest('.widal-grid-container');
                const hiddenInput = container.parentElement.querySelector('.edit-param-val');
                const gridData = {};
                container.querySelectorAll('.widal-select').forEach(sel => {
                    const ant = sel.getAttribute('data-antigen');
                    const dil = sel.getAttribute('data-dilution');
                    if (!gridData[ant]) gridData[ant] = {};
                    gridData[ant][dil] = sel.value;
                });
                hiddenInput.value = JSON.stringify(gridData);
            }
        });

        document.getElementById('form-edit-report').addEventListener('submit', async (e) => {
            e.preventDefault();
            const report_date = document.getElementById('e-date').value;
            
            const parametersData = [];
            const checkedTests = document.querySelectorAll('.edit-test-check:checked');
            if (checkedTests.length === 0) return alert('Select at least one test.');

            checkedTests.forEach(chk => {
                const paramInputs = document.querySelectorAll(`.edit-test-params-${chk.value} .edit-param-val`);
                paramInputs.forEach(inp => {
                    parametersData.push({
                        parameter_id: inp.getAttribute('data-param-id'),
                        result_value: inp.value || ''
                    });
                });
            });

            const total_amount = parseFloat(document.getElementById('e-total').value) || 0;
            const discount = parseFloat(document.getElementById('e-discount').value) || 0;
            const paid_amount = parseFloat(document.getElementById('e-paid').value) || 0;
            const balance_due = parseFloat(document.getElementById('e-balance').value) || 0;
            const payment_status = balance_due <= 0 ? (total_amount === 0 ? 'Pending' : 'Paid') : (paid_amount > 0 ? 'Partial' : 'Pending');

            const status = e.submitter && e.submitter.id === 'btn-edit-draft' ? 'Draft' : 'Pending';

            await fetchAPI(`/reports/${id}`, { 
                method: 'PUT', 
                body: JSON.stringify({ 
                    report_date, 
                    parameters: parametersData,
                    total_amount, discount, paid_amount, balance_due, payment_status,
                    status
                }) 
            });
            await logActivity('REPORT_EDIT', `Updated report ID: ${id} with Phase 2 results`);
            closeModal();
            loadReports();
            loadDashboardStats();
        });
    } catch(e) { console.error('Error loading report for edit', e); }
};

window.editTest = (id, currentName, currentPrice) => {
    setModal('Edit Lab Test', `
        <form id="form-edit-test">
            <div class="input-group">
                <label>Test Name</label>
                <input type="text" id="et-name" required value="${currentName}">
            </div>
            <div class="input-group">
                <label>Price (₹)</label>
                <input type="number" step="0.01" id="et-price" required value="${currentPrice}">
            </div>
            <button type="submit" class="btn-primary" style="width: 100%;">Update Test</button>
        </form>
    `);

    document.getElementById('form-edit-test').addEventListener('submit', async (e) => {
        e.preventDefault();
        const test_name = document.getElementById('et-name').value;
        const normal_range = '';
        const price = document.getElementById('et-price').value;

        try {
            await fetchAPI(`/tests/${id}`, {
                method: 'PUT',
                body: JSON.stringify({ test_name, normal_range, price })
            });
            await logActivity('EDIT', `Updated test details for test ID: ${id}`);
            closeModal();
            loadTests();
        } catch(err) { alert('Failed to update test'); }
    });
};

async function openCreateReportModal() {
    try {
        const [patients, tests, packages] = await Promise.all([
            fetchAPI('/patients/'),
            fetchAPI('/tests/'),
            fetchAPI('/tests/packages')
        ]);

        let patientOptions = patients.map(p => `<option value="${p.id}">${p.name} (ID: ${p.id})</option>`).join('');
        
        let testCardsHtml = tests.map(t => {
            let paramsHtml = t.parameters.map(p => {
                if (p.parameter_type === 'widal') {
                    return `
                    <div class="param-input hidden test-params-${t.id}" style="margin-top: 10px; margin-left: 24px;">
                        <label style="font-size: 0.85rem; color: var(--text-secondary); margin-bottom: 8px; display: block;">${p.parameter_name} (Widal Grid)</label>
                        <div class="widal-grid-container" data-param-id="${p.id}" style="overflow-x: auto;">
                            <table class="widal-entry-table" style="width: 100%; border-collapse: collapse; font-size: 0.8rem; text-align: center;">
                                <thead>
                                    <tr>
                                        <th>Antigen</th><th>1:20</th><th>1:40</th><th>1:80</th><th>1:160</th><th>1:320</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    ${['S. Typhi O', 'S. Typhi H', 'S. Paratyphi AH', 'S. Paratyphi BH'].map(ant => `
                                        <tr>
                                            <td style="text-align: left; padding: 4px; border: 1px solid var(--surface-border);">${ant}</td>
                                            ${[20, 40, 80, 160, 320].map(dil => `
                                                <td style="border: 1px solid var(--surface-border);">
                                                    <select class="widal-select" data-antigen="${ant}" data-dilution="${dil}" style="width: 100%; background: transparent; border: none; color: white;">
                                                        <option value="-">-</option>
                                                        <option value="+">+</option>
                                                    </select>
                                                </td>
                                            `).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                        <input type="hidden" class="param-val" data-param-id="${p.id}" value="">
                    </div>
                    `;
                }

                const isFormula = p.parameter_type === 'formula';
                return `
                <div class="param-input hidden test-params-${t.id}" style="margin-top: 6px; margin-left: 24px; display: flex; flex-direction: column; gap: 4px;">
                    <label style="font-size: 0.85rem; color: var(--text-secondary);">${p.parameter_name} ${p.unit ? `(${p.unit})` : ''} <span style="font-size:0.75rem; color:#888;">[Normal: ${p.normal_range}]</span></label>
                    <input type="${p.parameter_type === 'numeric' ? 'number' : 'text'}" 
                           class="param-val ${isFormula ? 'formula-field' : ''}" 
                           data-param-id="${p.id}" 
                           data-formula="${p.formula || ''}"
                           placeholder="${isFormula ? 'Auto-calculated' : 'Result'}"
                           ${isFormula ? 'readonly style="background: rgba(99, 102, 241, 0.1); border-color: var(--primary); font-weight: bold;"' : ''}>
                </div>
                `;
            }).join('');

            return `
            <div class="test-item-card" data-test-id="${t.id}" style="background: rgba(0,0,0,0.2); padding: 12px; margin-bottom: 8px; border-radius: 8px; display: flex; flex-direction: column; gap: 8px;">
                <label style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" class="test-check" value="${t.id}" data-price="${t.price}">
                    <strong style="font-size: 1.05rem; color: var(--primary);">${t.test_name}</strong>
                </label>
                ${paramsHtml}
            </div>
            `;
        }).join('');

        let packageCardsHtml = packages.map(pkg => {
            const testIds = pkg.tests.map(t => t.id).join(',');
            return `
            <div class="package-item-card" style="background: linear-gradient(135deg, rgba(99, 102, 241, 0.1), rgba(0,0,0,0.2)); padding: 12px; margin-bottom: 8px; border-radius: 8px; border: 1px solid rgba(99, 102, 241, 0.2);">
                <label style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
                    <input type="checkbox" class="package-check" value="${pkg.id}" data-price="${pkg.price}" data-tests="${testIds}">
                    <strong style="font-size: 1.05rem; color: var(--primary);">📦 ${pkg.package_name}</strong>
                    <span style="margin-left: auto; font-weight: bold;">₹${pkg.price.toFixed(2)}</span>
                </label>
                <div style="font-size: 0.8rem; color: var(--text-secondary); margin-left: 24px; margin-top: 4px;">
                    Includes: ${pkg.tests.map(t => t.test_name).join(', ')}
                </div>
            </div>
            `;
        }).join('');

        setModal('Create Lab Report', `
            <form id="form-report">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 16px;">
                    <div class="input-group">
                        <label>Report Date</label>
                        <input type="date" id="r-date" required value="${new Date().toISOString().split('T')[0]}">
                    </div>
                    <div class="input-group">
                        <label>Select Patient</label>
                        <select id="r-patient" required>
                            <option value="">-- Choose Patient --</option>
                            ${patientOptions}
                        </select>
                    </div>
                </div>

                <div style="margin-bottom: 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                        <label>Select Tests & Packages</label>
                        <div style="display: flex; gap: 10px;">
                            <button type="button" class="btn-secondary" id="tab-btn-tests" style="padding: 4px 10px; font-size: 0.8rem;">Individual Tests</button>
                            <button type="button" class="btn-secondary" id="tab-btn-packages" style="padding: 4px 10px; font-size: 0.8rem;">Packages</button>
                        </div>
                    </div>

                    <input type="text" id="search-report-items" placeholder="Search tests & packages..." style="margin-bottom: 10px; width: 100%; padding: 10px 14px; border-radius: 6px; border: 1px solid var(--surface-border); background: var(--input-bg); color: var(--text-primary);" onkeydown="if(event.key==='Enter'){event.preventDefault();}">
                    
                    <div id="tests-tab-content" style="max-height: 350px; overflow-y: auto; padding-right: 8px;">
                        ${testCardsHtml}
                    <div id="packages-tab-content" class="hidden" style="max-height: 350px; overflow-y: auto; padding-right: 8px;">
                        ${packageCardsHtml}
                    </div>
                </div>

                <div style="background: rgba(0,0,0,0.1); padding: 12px; border-radius: 8px; margin-bottom: 16px;">
                    <h4 style="margin-top:0; margin-bottom: 10px;">Billing Details</h4>
                    <div style="display:flex; gap:10px;">
                        <div class="input-group" style="flex:1;">
                            <label>Total Amount</label>
                            <input type="number" id="r-total" readonly value="0.00">
                        </div>
                        <div class="input-group" style="flex:1;">
                            <label>Discount</label>
                            <input type="number" id="r-discount" value="0.00" step="0.01" min="0">
                        </div>
                        <div class="input-group" style="flex:1;">
                            <label>Paid Amount</label>
                            <input type="number" id="r-paid" value="0.00" step="0.01" min="0">
                        </div>
                        <div class="input-group" style="flex:1;">
                            <label>Balance</label>
                            <input type="number" id="r-balance" readonly value="0.00">
                        </div>
                    </div>
                </div>
                <div style="display: flex; gap: 10px;">
                    <button type="submit" class="btn-secondary" id="btn-save-draft" style="flex: 1;">Save as Draft</button>
                    <button type="submit" class="btn-primary" id="btn-save-submit" style="flex: 1;">Generate Report</button>
                </div>
            </form>
        `);

        // Tabs Logic
        document.getElementById('tab-btn-tests').addEventListener('click', () => {
            document.getElementById('tests-tab-content').classList.remove('hidden');
            document.getElementById('packages-tab-content').classList.add('hidden');
        });
        document.getElementById('tab-btn-packages').addEventListener('click', () => {
            document.getElementById('tests-tab-content').classList.add('hidden');
            document.getElementById('packages-tab-content').classList.remove('hidden');
        });

        // Search Logic
        document.getElementById('search-report-items').addEventListener('input', (e) => {
            const query = e.target.value.toLowerCase();
            document.querySelectorAll('.test-item-card, .package-item-card').forEach(card => {
                const text = card.textContent.toLowerCase();
                card.style.display = text.includes(query) ? 'flex' : 'none';
            });
        });

        // Formula Calculation Engine
        const runFormulaEngine = () => {
            const allValues = {};
            document.querySelectorAll('.param-val:not(.formula-field)').forEach(inp => {
                const id = inp.getAttribute('data-param-id');
                const val = parseFloat(inp.value);
                if (!isNaN(val)) allValues[id] = val;
            });

            document.querySelectorAll('.formula-field').forEach(fld => {
                let formula = fld.getAttribute('data-formula');
                if (!formula) return;

                // Replace [ID] with actual values
                let canCalculate = true;
                const replaced = formula.replace(/\[(\d+)\]/g, (match, id) => {
                    if (allValues[id] !== undefined) return allValues[id];
                    canCalculate = false;
                    return 0;
                });

                if (canCalculate) {
                    try {
                        // eslint-disable-next-line no-eval
                        const result = eval(replaced);
                        fld.value = isFinite(result) ? result.toFixed(2) : '';
                    } catch(e) { fld.value = 'Error'; }
                } else {
                    fld.value = '';
                }
            });
        };

        // Billing & Toggle Logic
        const calculateBilling = () => {
            let total = 0;
            let packagedTestIds = new Set();
            
            // Sum packages and track their inner test IDs
            document.querySelectorAll('.package-check:checked').forEach(chk => {
                total += parseFloat(chk.getAttribute('data-price') || 0);
                const testIds = chk.getAttribute('data-tests');
                if (testIds) {
                    testIds.split(',').forEach(id => {
                        if (id) packagedTestIds.add(id);
                    });
                }
            });

            // Sum individual tests ONLY if they aren't part of a checked package
            document.querySelectorAll('.test-check:checked').forEach(chk => {
                if (!packagedTestIds.has(chk.value)) {
                    total += parseFloat(chk.getAttribute('data-price') || 0);
                }
            });

            document.getElementById('r-total').value = total.toFixed(2);
            const discount = parseFloat(document.getElementById('r-discount').value) || 0;
            const paid = parseFloat(document.getElementById('r-paid').value) || 0;
            document.getElementById('r-balance').value = (total - discount - paid).toFixed(2);
        };

        // Handle Test Selection
        document.querySelectorAll('.test-check').forEach(chk => {
            chk.addEventListener('change', (e) => {
                const paramInputs = document.querySelectorAll(`.test-params-${e.target.value}`);
                paramInputs.forEach(inp => {
                    if (e.target.checked) inp.classList.remove('hidden');
                    else inp.classList.add('hidden');
                });
                calculateBilling();
                runFormulaEngine();
            });
        });

        // Handle Package Selection (Expand tests)
        document.querySelectorAll('.package-check').forEach(chk => {
            chk.addEventListener('change', (e) => {
                const testIds = e.target.getAttribute('data-tests').split(',');
                testIds.forEach(tid => {
                    const testChk = document.querySelector(`.test-check[value="${tid}"]`);
                    if (testChk) {
                        testChk.checked = e.target.checked;
                        testChk.dispatchEvent(new Event('change'));
                    }
                });
                calculateBilling();
            });
        });

        // Real-time formula triggers
        document.addEventListener('input', e => {
            if (e.target.classList.contains('param-val')) runFormulaEngine();
        });

        // Widal Grid Serializer
        document.addEventListener('change', e => {
            if (e.target.classList.contains('widal-select')) {
                const container = e.target.closest('.widal-grid-container');
                const hiddenInput = container.parentElement.querySelector('.param-val');
                const gridData = {};
                container.querySelectorAll('.widal-select').forEach(sel => {
                    const ant = sel.getAttribute('data-antigen');
                    const dil = sel.getAttribute('data-dilution');
                    if (!gridData[ant]) gridData[ant] = {};
                    gridData[ant][dil] = sel.value;
                });
                hiddenInput.value = JSON.stringify(gridData);
            }
        });

        document.getElementById('r-discount').addEventListener('input', calculateBilling);
        document.getElementById('r-paid').addEventListener('input', calculateBilling);

        // Form Submit
        document.getElementById('form-report').addEventListener('submit', async (e) => {
            e.preventDefault();
            const patient_id = document.getElementById('r-patient').value;
            const report_date = document.getElementById('r-date').value;
            
            const parametersData = [];
            const checkedTests = document.querySelectorAll('.test-check:checked');
            if (checkedTests.length === 0) return alert('Select at least one test or package.');

            checkedTests.forEach(chk => {
                const paramInputs = document.querySelectorAll(`.test-params-${chk.value} .param-val`);
                paramInputs.forEach(inp => {
                    parametersData.push({
                        parameter_id: inp.getAttribute('data-param-id'),
                        result_value: inp.value || ''
                    });
                });
            });

            const total_amount = parseFloat(document.getElementById('r-total').value) || 0;
            const discount = parseFloat(document.getElementById('r-discount').value) || 0;
            const paid_amount = parseFloat(document.getElementById('r-paid').value) || 0;
            const balance_due = parseFloat(document.getElementById('r-balance').value) || 0;
            const payment_status = balance_due <= 0 ? (total_amount === 0 ? 'Pending' : 'Paid') : (paid_amount > 0 ? 'Partial' : 'Pending');

            const status = e.submitter && e.submitter.id === 'btn-save-draft' ? 'Draft' : 'Pending';

            await fetchAPI('/reports/', { 
                method: 'POST', 
                body: JSON.stringify({ 
                    patient_id, report_date, parameters: parametersData,
                    total_amount, discount, paid_amount, balance_due, payment_status,
                    status
                }) 
            });
            await logActivity('DATA_ENTRY', `Created report with Phase 2 features for patient ID: ${patient_id}`);
            closeModal();
            loadReports();
            loadDashboardStats();
        });

    } catch(e) { console.error('Error loading report modal', e); }
}

/* =========================================
   MODAL UTILS
   ========================================= */
/* =========================================
   USERS (Admin)
   ========================================= */
async function loadUsers() {
    try {
        const users = await fetchAPI('/users/');
        const tbody = document.querySelector('#users-table tbody');
        tbody.innerHTML = '';
        users.forEach(u => {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td>${u.id}</td>
                <td><strong>${u.name}</strong></td>
                <td>${u.email}</td>
                <td><span class="status-badge" style="background: rgba(99, 102, 241, 0.2); color: var(--primary);">${u.role}</span></td>
                <td>${new Date(u.created_at).toLocaleDateString()}</td>
                <td>
                    <button class="btn-danger-outline" onclick="deleteUser(${u.id})" style="padding: 4px 8px; font-size: 0.8rem;">Delete</button>
                </td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) { console.error('Failed to load users', e); }
}

window.deleteUser = async (id) => {
    confirmDialog('Delete User', 'Are you sure you want to delete this user?', async () => {
        await fetchAPI(`/users/${id}`, { method: 'DELETE' });
        await logActivity('DELETE', `Deleted user ID: ${id}`);
        loadUsers();
    });
};

function openAddUserModal() {
    setModal('Create New User', `
        <form id="form-user">
            <div class="input-group">
                <label>Name</label>
                <input type="text" id="u-name" required>
            </div>
            <div class="input-group">
                <label>Email</label>
                <input type="email" id="u-email" required>
            </div>
            <div class="input-group">
                <label>Password</label>
                <input type="password" id="u-password" required>
            </div>
            <div class="input-group">
                <label>Role</label>
                <select id="u-role">
                    <option value="Admin">Admin</option>
                    <option value="Technician">Technician</option>
                    <option value="Operator">Operator</option>
                </select>
            </div>
            <button type="submit" class="btn-primary">Create User</button>
        </form>
    `);

    document.getElementById('form-user').addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            name: document.getElementById('u-name').value,
            email: document.getElementById('u-email').value,
            password: document.getElementById('u-password').value,
            role: document.getElementById('u-role').value
        };
        await fetchAPI('/users/', { method: 'POST', body: JSON.stringify(data) });
        await logActivity('ADMIN', `Created new user: ${data.name} (${data.role})`);
        closeModal();
        loadUsers();
    });
}

/* =========================================
   ACTIVITY LOGS (Admin)
   ========================================= */
async function loadLogs() {
    try {
        const logs = await fetchAPI('/logs/');
        const tbody = document.querySelector('#logs-table tbody');
        tbody.innerHTML = '';
        logs.forEach(l => {
            const tr = document.createElement('tr');
            let color = 'var(--text-secondary)';
            if (l.action_type === 'ERROR' || l.action_type === 'LOGIN_FAILED') color = 'var(--danger)';
            else if (l.action_type === 'DELETE') color = 'var(--warning)';
            else if (l.action_type === 'DATA_ENTRY') color = 'var(--primary)';
            else if (l.action_type === 'LOGIN') color = 'var(--success)';

            tr.innerHTML = `
                <td style="font-size: 0.8rem; color: var(--text-secondary);">${new Date(l.created_at).toLocaleString()}</td>
                <td><strong>${l.user_name || 'System / Anonymous'}</strong></td>
                <td><span class="status-badge" style="background: rgba(0,0,0,0.05); color: ${color}; border: 1px solid ${color};">${l.action_type}</span></td>
                <td style="color: var(--text-secondary);">${l.description}</td>
            `;
            tbody.appendChild(tr);
        });
    } catch(e) { console.error('Failed to load logs', e); }
}

function setModal(title, htmlContent) {
    document.getElementById('modal-title').textContent = title;
    document.getElementById('modal-body').innerHTML = htmlContent;
    document.getElementById('dynamic-modal').classList.remove('hidden');
}

window.closeModal = function() {
    document.getElementById('dynamic-modal').classList.add('hidden');
    document.getElementById('modal-body').innerHTML = '';
};
// Make it accessible for internal module bindings as well
const closeModal = window.closeModal;

// Close modals on Escape key press
document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') {
        const dynamicModal = document.getElementById('dynamic-modal');
        const printModal = document.getElementById('print-modal');
        if (dynamicModal && !dynamicModal.classList.contains('hidden')) {
            closeModal();
        }
        if (printModal && !printModal.classList.contains('hidden')) {
            printModal.classList.add('hidden');
        }
    }
});

window.confirmDialog = (title, message, onConfirm) => {
    setModal(title, `
        <div style="margin-bottom: 20px;">
            <p style="font-size: 1rem; color: var(--text-primary); margin: 0;">${message}</p>
        </div>
        <div style="display: flex; gap: 10px; justify-content: flex-end;">
            <button class="btn-primary" onclick="closeModal()" style="background: transparent; color: var(--text-primary); border: 1px solid var(--surface-border);">Cancel</button>
            <button class="btn-danger-outline" id="confirm-btn-yes" style="background: var(--danger); color: white; border: none;">Yes, Proceed</button>
        </div>
    `);
    
    document.getElementById('confirm-btn-yes').addEventListener('click', () => {
        closeModal();
        onConfirm();
    });
};

window.alertDialog = (title, message) => {
    setModal(title, `
        <div style="margin-bottom: 20px;">
            <p style="font-size: 1rem; color: var(--text-primary); margin: 0;">${message}</p>
        </div>
        <div style="display: flex; justify-content: flex-end;">
            <button class="btn-primary" onclick="closeModal()">OK</button>
        </div>
    `);
};

window.openPrintOptions = (id) => {
    currentPrintId = id;
    document.getElementById('print-modal').classList.remove('hidden');
};
