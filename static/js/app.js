// Personal Finance Manager - Application Engine

document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initShortcuts();
    
    // If we are on the dashboard, load dynamic data
    if (document.getElementById('dashboard-view')) {
        loadDashboardData();
    }
});

// ----------------- THEME MANAGER -----------------

function initTheme() {
    const themeToggle = document.getElementById('theme-toggle');
    if (!themeToggle) return;
    
    themeToggle.addEventListener('click', () => {
        const isDark = !document.body.classList.contains('dark-mode');
        document.body.classList.toggle('dark-mode', isDark);
        
        // Change icon
        themeToggle.innerHTML = isDark ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon"></i>';
        
        // Save preferences via AJAX
        const csrfToken = getCookie('csrftoken');
        fetch('/profile/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
                'X-CSRFToken': csrfToken
            },
            body: `action=toggle_theme&dark_mode=${isDark}`
        })
        .then(response => response.json())
        .then(data => {
            if (data.status === 'success') {
                showToast(isDark ? 'Dark Mode Activated' : 'Light Mode Activated', 'success');
            }
        });
    });
}

// ----------------- DYNAMIC DASHBOARD DATA (AJAX) -----------------

let balanceChart, categoryChart, monthlyChart;

function loadDashboardData() {
    fetch('/api/analytics/dashboard-data/')
    .then(response => {
        if (response.status === 403) {
            // Not authenticated or session expired
            window.location.href = '/login/';
            return;
        }
        return response.json();
    })
    .then(data => {
        if (!data) return;
        
        // Hide skeletons and show cards
        document.querySelectorAll('.skeleton').forEach(el => el.classList.remove('skeleton'));
        
        // Update KPIs safely
        const balanceEl = document.getElementById('balance-val');
        if (balanceEl) balanceEl.innerText = formatCurrency(data.kpis.balance);
        
        const incomeEl = document.getElementById('income-val');
        if (incomeEl) incomeEl.innerText = formatCurrency(data.kpis.income);
        
        const expenseEl = document.getElementById('expense-val');
        if (expenseEl) expenseEl.innerText = formatCurrency(data.kpis.expense);
        
        const savingsRatioEl = document.getElementById('savings-ratio-val');
        if (savingsRatioEl) savingsRatioEl.innerText = data.kpis.savings_ratio + '%';
        
        const netWorthEl = document.getElementById('net-worth-val');
        if (netWorthEl) netWorthEl.innerText = formatCurrency(data.kpis.net_worth);
        
        const monthSpentEl = document.getElementById('month-spent-val');
        if (monthSpentEl) monthSpentEl.innerText = formatCurrency(data.kpis.month_expense);
        
        const healthScoreEl = document.getElementById('health-score-val');
        if (healthScoreEl) healthScoreEl.innerText = data.kpis.health_score + '/100';
        
        // Progress health score circle
        const circle = document.getElementById('health-circle');
        if (circle) {
            const val = data.kpis.health_score;
            circle.style.strokeDashoffset = 251.2 - (251.2 * val) / 100;
        }

        // Render AI Insights list
        const insightsList = document.getElementById('ai-insights-list');
        if (insightsList) {
            insightsList.innerHTML = '';
            data.ai_insights.forEach(ins => {
                let alertClass = 'alert-info';
                if (ins.type === 'warning') alertClass = 'alert-warning';
                if (ins.type === 'success') alertClass = 'alert-success';
                
                insightsList.innerHTML += `
                    <div class="alert ${alertClass} d-flex align-items-start gap-2 mb-3 border-0 rounded-4" style="background: rgba(255,255,255,0.05); color: var(--text-primary);">
                        <i class="bi bi-robot fs-5 text-primary"></i>
                        <div>
                            <h6 class="alert-heading fw-bold mb-1">${ins.title}</h6>
                            <small class="text-secondary">${ins.message}</small>
                        </div>
                    </div>
                `;
            });
        }

        // Render Recent Transactions
        const recentList = document.getElementById('recent-tx-list');
        if (recentList) {
            recentList.innerHTML = '';
            if (data.recent_transactions.length === 0) {
                recentList.innerHTML = '<div class="text-center py-4 text-secondary">No transactions logged yet.</div>';
            } else {
                data.recent_transactions.forEach(t => {
                    const badgeClass = t.type === 'Income' ? 'text-success bg-success-subtle' : 'text-danger bg-danger-subtle';
                    const amountSign = t.type === 'Income' ? '+' : '-';
                    recentList.innerHTML += `
                        <div class="d-flex align-items-center justify-content-between py-2 border-bottom border-light-subtle">
                            <div class="d-flex align-items-center gap-3">
                                <div class="bg-body-secondary p-2 rounded-3 text-center" style="width: 40px;">
                                    <i class="bi ${t.category_icon || 'bi-tag'} fs-5" style="color: ${t.category_color}"></i>
                                </div>
                                <div>
                                    <h6 class="mb-0 fw-semibold">${t.title}</h6>
                                    <small class="text-secondary">${t.category} &bull; ${t.date}</small>
                                </div>
                            </div>
                            <span class="badge ${badgeClass} fs-6 fw-semibold">${amountSign} ${t.currency_symbol}${t.amount}</span>
                        </div>
                    `;
                });
            }
        }

        // Render Upcoming Bills
        const billsList = document.getElementById('upcoming-bills-list');
        if (billsList) {
            billsList.innerHTML = '';
            if (data.upcoming_bills.length === 0) {
                billsList.innerHTML = '<div class="text-center py-3 text-secondary">All caught up! No bills due.</div>';
            } else {
                data.upcoming_bills.forEach(b => {
                    billsList.innerHTML += `
                        <div class="d-flex align-items-center justify-content-between py-2">
                            <div>
                                <h6 class="mb-0 fw-semibold">${b.name}</h6>
                                <small class="text-secondary">Due in ${b.days_left} days (${b.due_date})</small>
                            </div>
                            <span class="fw-bold text-danger">$${b.amount}</span>
                        </div>
                    `;
                });
            }
        }

        // Render Goals Progress
        const goalsList = document.getElementById('dashboard-goals-list');
        if (goalsList) {
            goalsList.innerHTML = '';
            if (data.goals.length === 0) {
                goalsList.innerHTML = '<div class="text-center py-3 text-secondary">No financial goals set.</div>';
            } else {
                data.goals.forEach(g => {
                    goalsList.innerHTML += `
                        <div class="mb-3">
                            <div class="d-flex justify-content-between mb-1">
                                <small class="fw-semibold">${g.name}</small>
                                <small class="text-secondary">$${g.current_amount} / $${g.target_amount} (${g.percent}%)</small>
                            </div>
                            <div class="progress rounded-pill" style="height: 6px; background: rgba(0,0,0,0.1);">
                                <div class="progress-bar bg-primary rounded-pill" style="width: ${g.percent}%"></div>
                            </div>
                        </div>
                    `;
                });
            }
        }

        // ----------------- RENDER CHART.JS CHARTS -----------------
        renderCharts(data);
    });
}

function renderCharts(data) {
    const isDark = document.body.classList.contains('dark-mode');
    const labelColor = isDark ? '#94a3b8' : '#64748b';
    const gridColor = isDark ? 'rgba(255,255,255,0.05)' : 'rgba(0,0,0,0.05)';

    // 1. Donut Chart - Expense Categories
    const ctxCategory = document.getElementById('categoryChart').getContext('2d');
    if (categoryChart) categoryChart.destroy();
    categoryChart = new Chart(ctxCategory, {
        type: 'doughnut',
        data: {
            labels: data.category_pie.categories,
            datasets: [{
                data: data.category_pie.amounts,
                backgroundColor: [
                    '#38bdf8', '#818cf8', '#fb923c', '#f87171', '#34d399', '#a78bfa',
                    '#fbbf24', '#2dd4bf', '#f472b6', '#94a3b8', '#ec4899', '#f43f5e'
                ],
                borderWidth: 0
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: { color: labelColor, boxWidth: 12, font: { family: 'Plus Jakarta Sans' } }
                }
            },
            cutout: '70%'
        }
    });

    // 2. Bar Chart - Income vs Expenses
    const ctxMonthly = document.getElementById('monthlyChart').getContext('2d');
    if (monthlyChart) monthlyChart.destroy();
    monthlyChart = new Chart(ctxMonthly, {
        type: 'bar',
        data: {
            labels: data.monthly_trend.map(d => d.month),
            datasets: [
                {
                    label: 'Income',
                    data: data.monthly_trend.map(d => d.income),
                    backgroundColor: '#10b981',
                    borderRadius: 6
                },
                {
                    label: 'Expense',
                    data: data.monthly_trend.map(d => d.expense),
                    backgroundColor: '#ef4444',
                    borderRadius: 6
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { labels: { color: labelColor, font: { family: 'Plus Jakarta Sans' } } }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: labelColor } },
                y: { grid: { color: gridColor }, ticks: { color: labelColor } }
            }
        }
    });

    // 3. Area Chart - Weekly Trend
    const ctxBalance = document.getElementById('balanceChart').getContext('2d');
    if (balanceChart) balanceChart.destroy();
    balanceChart = new Chart(ctxBalance, {
        type: 'line',
        data: {
            labels: Object.keys(data.weekly_trend),
            datasets: [{
                label: 'Expenses',
                data: Object.values(data.weekly_trend),
                borderColor: '#0ea5e9',
                backgroundColor: 'rgba(14, 165, 233, 0.1)',
                fill: true,
                tension: 0.4,
                borderWidth: 3
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: { display: false }
            },
            scales: {
                x: { grid: { display: false }, ticks: { color: labelColor } },
                y: { grid: { color: gridColor }, ticks: { color: labelColor } }
            }
        }
    });
}

// ----------------- TOAST NOTIFICATIONS -----------------

function showToast(message, type = 'info') {
    const container = document.getElementById('toast-container') || createToastContainer();
    const toast = document.createElement('div');
    toast.className = `toast align-items-center show border-0 rounded-4 glass-card p-2 text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : 'primary'}`;
    toast.style.minWidth = '250px';
    toast.role = 'alert';
    
    toast.innerHTML = `
        <div class="d-flex">
            <div class="toast-body fw-semibold">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
        </div>
    `;
    
    container.appendChild(toast);
    setTimeout(() => {
        toast.classList.remove('show');
        setTimeout(() => toast.remove(), 300);
    }, 4000);
}

function createToastContainer() {
    const el = document.createElement('div');
    el.id = 'toast-container';
    el.className = 'toast-container position-fixed top-0 end-0 p-3';
    document.body.appendChild(el);
    return el;
}

// ----------------- KEYBOARD SHORTCUTS -----------------

function initShortcuts() {
    let keysPressed = {};
    
    window.addEventListener('keydown', (e) => {
        keysPressed[e.key.toLowerCase()] = true;
        
        // Shortcut combo g + <key>
        if (keysPressed['g']) {
            if (e.key.toLowerCase() === 'd') {
                e.preventDefault();
                window.location.href = '/';
            } else if (e.key.toLowerCase() === 't') {
                e.preventDefault();
                window.location.href = '/transactions/';
            } else if (e.key.toLowerCase() === 'b') {
                e.preventDefault();
                window.location.href = '/budgets/';
            } else if (e.key.toLowerCase() === 'g') {
                e.preventDefault();
                window.location.href = '/goals/';
            } else if (e.key.toLowerCase() === 'i') {
                e.preventDefault();
                window.location.href = '/bills/';
            }
        }
        
        // Single key shortcuts
        if (e.key.toLowerCase() === 'n' && !['input', 'textarea'].includes(document.activeElement.tagName.toLowerCase())) {
            e.preventDefault();
            // Open Add Transaction modal if button exists
            const addBtn = document.getElementById('open-add-modal-btn');
            if (addBtn) addBtn.click();
        }
    });

    window.addEventListener('keyup', (e) => {
        delete keysPressed[e.key.toLowerCase()];
    });
}

// Helper: Format Currency
function formatCurrency(amount) {
    return new Intl.NumberFormat('en-US', {
        style: 'currency',
        currency: 'USD'
    }).format(amount);
}

// Helper: Get Cookie for CSRF
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
