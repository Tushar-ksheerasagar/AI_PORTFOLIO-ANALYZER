// GrowwPro Portfolio Analyzer - Frontend Controller

// API Endpoints Base
const API_BASE = ""; // Serving same-origin

// Global State
let state = {
    user: null,
    portfolios: [],
    selectedPortfolioId: null,
    analytics: null,
    insights: null,
    allocationType: "ticker", // ticker or sector
    chatHistory: [],
    currentTheme: "dark"
};

// Treemap render state
let treemapRects = [];

// Chart.js Instances
let charts = {
    performance: null,
    allocation: null
};

// DOM Elements
const elements = {
    toast: document.getElementById("toast"),
    authSection: document.getElementById("auth-section"),
    appSection: document.getElementById("app-section"),
    authTitle: document.getElementById("auth-title"),
    authSubtitle: document.getElementById("auth-subtitle"),
    authForm: document.getElementById("auth-form"),
    authEmail: document.getElementById("auth-email"),
    authPassword: document.getElementById("auth-password"),
    authSubmitBtn: document.getElementById("auth-submit-btn"),
    authToggleLink: document.getElementById("auth-toggle-link"),
    authToggleText: document.getElementById("auth-toggle-text"),
    userEmail: document.getElementById("user-email"),
    portfolioSelect: document.getElementById("portfolio-select"),
    createPortfolioBtn: document.getElementById("create-portfolio-btn"),
    logoutBtn: document.getElementById("logout-btn"),
    currentPortfolioName: document.getElementById("current-portfolio-name"),
    portfolioActions: document.getElementById("portfolio-actions"),
    deletePortfolioBtn: document.getElementById("delete-portfolio-btn"),
    welcomeView: document.getElementById("welcome-view"),
    dashboardView: document.getElementById("dashboard-view"),
    
    // Summary Metrics
    totalValue: document.getElementById("metric-total-value"),
    costBasis: document.getElementById("metric-cost-basis"),
    absoluteReturn: document.getElementById("metric-absolute-return"),
    returnPct: document.getElementById("metric-return-pct"),
    returnArrow: document.getElementById("metric-return-arrow"),
    
    // Risk Metrics
    volatility: document.getElementById("metric-volatility"),
    sharpe: document.getElementById("metric-sharpe"),
    sharpeDesc: document.getElementById("metric-sharpe-desc"),
    beta: document.getElementById("metric-beta"),
    betaDesc: document.getElementById("metric-beta-desc"),
    drawdown: document.getElementById("metric-drawdown"),
    
    // Forms
    addHoldingForm: document.getElementById("add-holding-form"),
    holdingTicker: document.getElementById("holding-ticker"),
    holdingQty: document.getElementById("holding-qty"),
    holdingPrice: document.getElementById("holding-price"),
    holdingDate: document.getElementById("holding-date"),
    
    // Holdings table
    holdingsTbody: document.getElementById("holdings-tbody"),
    
    // AI Insights
    insightsSkeleton: document.getElementById("insights-skeleton"),
    insightsContent: document.getElementById("insights-content"),
    insightSummary: document.getElementById("insight-summary"),
    insightRisk: document.getElementById("insight-risk"),
    insightDiversification: document.getElementById("insight-diversification"),
    insightWatchList: document.getElementById("insight-watch-list"),
    insightDisclaimer: document.getElementById("insight-disclaimer"),
    regenerateInsightsBtn: document.getElementById("regenerate-insights-btn"),
    
    // Modal
    createPortfolioModal: document.getElementById("create-portfolio-modal"),
    createPortfolioForm: document.getElementById("create-portfolio-form"),
    portfolioNameInput: document.getElementById("portfolio-name-input"),
    closeModalBtn: document.getElementById("close-modal-btn"),
    cancelModalBtn: document.getElementById("cancel-modal-btn"),
    
    // Chart Toggles
    toggleTicker: document.getElementById("chart-toggle-ticker"),
    toggleSector: document.getElementById("chart-toggle-sector"),
    
    // Chatbot
    chatForm: document.getElementById("chat-form"),
    chatInput: document.getElementById("chat-input"),
    chatMessages: document.getElementById("chat-messages"),
    chatToggleFloating: document.getElementById("chat-toggle-floating"),
    chatFloatingWidget: document.getElementById("chat-floating-widget"),
    chatCloseFloating: document.getElementById("chat-close-floating"),
    
    // Sidebar home link
    sidebarLogoLink: document.getElementById("sidebar-logo-link"),
    
    // Smart Rebalancer Floating Widget
    runRebalancerBtn: document.getElementById("run-rebalancer-btn"),
    rebalancerToggleFloating: document.getElementById("rebalancer-toggle-floating"),
    rebalancerFloatingWidget: document.getElementById("rebalancer-floating-widget"),
    rebalancerCloseFloating: document.getElementById("rebalancer-close-floating"),
    rebalancerModalLoading: document.getElementById("rebalancer-modal-loading"),
    rebalancerModalOutput: document.getElementById("rebalancer-modal-output")
};

// --- TOAST SERVICE ---
function showToast(message, type = "success") {
    elements.toast.textContent = message;
    elements.toast.className = `toast ${type}`;
    elements.toast.classList.remove("hidden");
    
    setTimeout(() => {
        elements.toast.classList.add("hidden");
    }, 4000);
}

// --- API FETCH HELPER ---
async function apiRequest(endpoint, options = {}) {
    // Force sending credentials (cookies) on same-origin/CORS
    options.credentials = "include";
    
    if (options.body && typeof options.body === "object") {
        options.body = JSON.stringify(options.body);
        options.headers = {
            "Content-Type": "application/json",
            ...options.headers
        };
    }
    
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, options);
        if (response.status === 204) return null;
        
        const data = await response.json();
        if (!response.ok) {
            throw new Error(data.detail || "Request failed");
        }
        return data;
    } catch (err) {
        console.error(`API Error on ${endpoint}:`, err);
        throw err;
    }
}

// --- INIT APP ---
document.addEventListener("DOMContentLoaded", async () => {
    // Restore saved theme preference
    initTheme();
    
    // Initialize interactive wealth simulator
    initWealthSimulator();
    
    // Set default add position date to today
    elements.holdingDate.value = new Date().toISOString().split("T")[0];
    
    // Check if user is already logged in
    try {
        const user = await apiRequest("/api/auth/me");
        if (user) {
            loginSuccess(user);
        }
    } catch (err) {
        // Not logged in, show auth screen
        showAuthView();
    }
    
    setupEventListeners();
});

// --- STATE ACTIONS ---
function showAuthView() {
    state.user = null;
    elements.authSection.classList.remove("hidden");
    elements.appSection.classList.add("hidden");
    
    // Hide chat and rebalancer elements on logout
    if (elements.chatToggleFloating) elements.chatToggleFloating.classList.add("hidden");
    if (elements.chatFloatingWidget) elements.chatFloatingWidget.classList.add("hidden");
    if (elements.rebalancerToggleFloating) elements.rebalancerToggleFloating.classList.add("hidden");
    if (elements.rebalancerFloatingWidget) elements.rebalancerFloatingWidget.classList.add("hidden");
}

async function loginSuccess(user) {
    state.user = user;
    elements.userEmail.textContent = user.email;
    elements.authSection.classList.add("hidden");
    elements.appSection.classList.remove("hidden");
    
    await fetchPortfolios();
    fetchMarketIndices();
    fetchMarketNews();
    
    // Start continuous live price updates (every 15 seconds)
    startLivePriceFetching();
}

async function fetchPortfolios() {
    try {
        const list = await apiRequest("/api/portfolios");
        state.portfolios = list;
        renderPortfolioDropdown();
    } catch (err) {
        showToast("Error loading portfolios", "error");
    }
}

function renderPortfolioDropdown() {
    // Keep standard placeholder
    elements.portfolioSelect.innerHTML = `<option value="" disabled selected>Select a Portfolio</option>`;
    
    state.portfolios.forEach(p => {
        const opt = document.createElement("option");
        opt.value = p.id;
        opt.textContent = p.name;
        if (state.selectedPortfolioId === p.id) {
            opt.selected = true;
        }
        elements.portfolioSelect.appendChild(opt);
    });
}

// --- EVENT LISTENERS ---
function setupEventListeners() {
    // Toggle Login/Signup
    elements.authToggleLink.addEventListener("click", (e) => {
        e.preventDefault();
        const isLogin = elements.authSubmitBtn.textContent === "Log In";
        if (isLogin) {
            elements.authTitle.textContent = "Create Account";
            elements.authSubtitle.textContent = "Sign up to begin building your investment portfolio.";
            elements.authSubmitBtn.textContent = "Sign Up";
            elements.authToggleText.textContent = "Already have an account?";
            elements.authToggleLink.textContent = "Log In";
        } else {
            elements.authTitle.textContent = "Welcome Back";
            elements.authSubtitle.textContent = "Analyze your investments with advanced metrics and AI commentary.";
            elements.authSubmitBtn.textContent = "Log In";
            elements.authToggleText.textContent = "Don't have an account?";
            elements.authToggleLink.textContent = "Sign Up";
        }
    });

    // Auth Submission
    elements.authForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const email = elements.authEmail.value;
        const password = elements.authPassword.value;
        const isLogin = elements.authSubmitBtn.textContent === "Log In";
        
        try {
            if (isLogin) {
                await apiRequest("/api/auth/login", {
                    method: "POST",
                    body: { email, password }
                });
                showToast("Logged in successfully!");
                const user = await apiRequest("/api/auth/me");
                loginSuccess(user);
            } else {
                await apiRequest("/api/auth/register", {
                    method: "POST",
                    body: { email, password }
                });
                showToast("Registration successful! Logging you in...", "success");
                // Auto login after registration
                await apiRequest("/api/auth/login", {
                    method: "POST",
                    body: { email, password }
                });
                const user = await apiRequest("/api/auth/me");
                loginSuccess(user);
            }
            elements.authForm.reset();
        } catch (err) {
            showToast(err.message, "error");
        }
    });

    // Logout
    elements.logoutBtn.addEventListener("click", async (e) => {
        e.preventDefault();
        try {
            await apiRequest("/api/auth/logout", { method: "POST" });
            showToast("Logged out successfully");
            // Clear charts
            if (charts.performance) charts.performance.destroy();
            if (charts.allocation) charts.allocation.destroy();
            state.selectedPortfolioId = null;
            state.analytics = null;
            state.insights = null;
            showAuthView();
        } catch (err) {
            showToast("Logout failed", "error");
        }
    });

    // Modal Control
    elements.createPortfolioBtn.addEventListener("click", () => {
        elements.createPortfolioModal.classList.remove("hidden");
    });
    
    const closeModal = () => {
        elements.createPortfolioModal.classList.add("hidden");
        elements.createPortfolioForm.reset();
    };
    elements.closeModalBtn.addEventListener("click", closeModal);
    elements.cancelModalBtn.addEventListener("click", closeModal);
    
    // Create Portfolio Form Submit
    elements.createPortfolioForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        const name = elements.portfolioNameInput.value;
        try {
            const newPortfolio = await apiRequest("/api/portfolios", {
                method: "POST",
                body: { name }
            });
            showToast(`Portfolio '${name}' created!`);
            closeModal();
            state.selectedPortfolioId = newPortfolio.id;
            await fetchPortfolios();
            await selectPortfolio(newPortfolio.id);
        } catch (err) {
            showToast(err.message, "error");
        }
    });

    // Dropdown Switch Portfolio
    elements.portfolioSelect.addEventListener("change", async (e) => {
        const id = parseInt(e.target.value);
        if (id) {
            await selectPortfolio(id);
        }
    });

    elements.deletePortfolioBtn.addEventListener("click", async () => {
        if (!state.selectedPortfolioId) return;
        const pName = state.portfolios.find(p => p.id === state.selectedPortfolioId)?.name;
        if (!confirm(`Are you sure you want to delete the portfolio '${pName}' and all its holdings?`)) {
            return;
        }
        try {
            await apiRequest(`/api/portfolios/${state.selectedPortfolioId}`, { method: "DELETE" });
            showToast("Portfolio deleted successfully");
            state.selectedPortfolioId = null;
            state.analytics = null;
            state.insights = null;
            elements.welcomeView.classList.remove("hidden");
            elements.dashboardView.classList.add("hidden");
            elements.portfolioActions.classList.add("hidden");
            elements.currentPortfolioName.textContent = "Select or Create a Portfolio";
            
            // Hide floating chat elements
            if (elements.chatToggleFloating) elements.chatToggleFloating.classList.add("hidden");
            if (elements.chatFloatingWidget) elements.chatFloatingWidget.classList.add("hidden");
            
            await fetchPortfolios();
        } catch (err) {
            showToast(err.message, "error");
        }
    });

    // Add Holding Submission
    elements.addHoldingForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        if (!state.selectedPortfolioId) return;
        
        const ticker = elements.holdingTicker.value.trim().toUpperCase();
        const quantity = parseFloat(elements.holdingQty.value);
        const buy_price = parseFloat(elements.holdingPrice.value);
        const buy_date = elements.holdingDate.value;
        
        try {
            showToast(`Adding position '${ticker}'... Fetching live data...`, "success");
            await apiRequest(`/api/portfolios/${state.selectedPortfolioId}/holdings`, {
                method: "POST",
                body: { ticker, quantity, buy_price, buy_date }
            });
            showToast(`Added ${quantity} shares of ${ticker}`);
            elements.addHoldingForm.reset();
            elements.holdingDate.value = new Date().toISOString().split("T")[0];
            await refreshDashboard();
        } catch (err) {
            showToast(err.message, "error");
        }
    });

    // Chart Allocation Toggles
    elements.toggleTicker.addEventListener("click", () => {
        elements.toggleTicker.classList.add("active");
        elements.toggleSector.classList.remove("active");
        state.allocationType = "ticker";
        renderAllocationChart();
    });
    
    elements.toggleSector.addEventListener("click", () => {
        elements.toggleSector.classList.add("active");
        elements.toggleTicker.classList.remove("active");
        state.allocationType = "sector";
        renderAllocationChart();
    });

    // Regenerate Insights Button (On-Demand AI Diagnostics)
    elements.regenerateInsightsBtn.addEventListener("click", async () => {
        if (!state.selectedPortfolioId) return;
        // If insights are already loaded, force a fresh regeneration. Otherwise, check cache first.
        const force = !!state.insights;
        await fetchAIInsights(force);
    });

    // Theme Toggle Handler
    const themeCheckbox = document.getElementById("theme-toggle-checkbox");
    if (themeCheckbox) {
        themeCheckbox.addEventListener("change", () => {
            const newTheme = themeCheckbox.checked ? "light" : "dark";
            applyTheme(newTheme);
        });
    }

    // Sidebar Collapse/Expand Toggle
    const sidebarToggle = document.getElementById("sidebar-toggle");
    const sidebar = document.querySelector(".sidebar");
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener("click", () => {
            sidebar.classList.toggle("collapsed");
            const icon = sidebarToggle.querySelector("i");
            if (sidebar.classList.contains("collapsed")) {
                icon.className = "fa-solid fa-chevron-right";
                sidebarToggle.title = "Expand Sidebar";
            } else {
                icon.className = "fa-solid fa-chevron-left";
                sidebarToggle.title = "Collapse Sidebar";
            }
        });
    }

    // Popout Live Indices Ticker Window
    const popoutBtn = document.getElementById("popout-indices-btn");
    if (popoutBtn) {
        popoutBtn.addEventListener("click", () => {
            window.open(
                "indices.html",
                "GrowwProIndices",
                "width=650,height=165,menubar=no,toolbar=no,location=no,status=no,resizable=yes"
            );
        });
    }

    // Click Sidebar Logo Link to go back to Home/Welcome page
    if (elements.sidebarLogoLink) {
        elements.sidebarLogoLink.addEventListener("click", async (e) => {
            e.preventDefault();
            state.selectedPortfolioId = null;
            state.analytics = null;
            state.insights = null;
            
            elements.welcomeView.classList.remove("hidden");
            elements.dashboardView.classList.add("hidden");
            elements.portfolioActions.classList.add("hidden");
            elements.currentPortfolioName.textContent = "Select or Create a Portfolio";
            elements.portfolioSelect.value = ""; // Reset dropdown selection
            
            // Hide chatbot elements
            if (elements.chatToggleFloating) elements.chatToggleFloating.classList.add("hidden");
            if (elements.chatFloatingWidget) elements.chatFloatingWidget.classList.add("hidden");
            
            // Hide rebalancer elements
            if (elements.rebalancerToggleFloating) elements.rebalancerToggleFloating.classList.add("hidden");
            if (elements.rebalancerFloatingWidget) elements.rebalancerFloatingWidget.classList.add("hidden");
            
            // Force fetch indices on home page
            await fetchMarketIndices();
        });
    }

    // Chatbot Floating Window Toggle Controls
    if (elements.chatToggleFloating) {
        elements.chatToggleFloating.addEventListener("click", () => {
            if (elements.chatFloatingWidget) {
                elements.chatFloatingWidget.classList.toggle("hidden");
                if (!elements.chatFloatingWidget.classList.contains("hidden")) {
                    if (elements.chatInput) elements.chatInput.focus();
                    // Minimize rebalancer widget if open
                    if (elements.rebalancerFloatingWidget) elements.rebalancerFloatingWidget.classList.add("hidden");
                }
            }
        });
    }

    if (elements.chatCloseFloating) {
        elements.chatCloseFloating.addEventListener("click", () => {
            if (elements.chatFloatingWidget) {
                elements.chatFloatingWidget.classList.add("hidden");
            }
        });
    }

    // Rebalancer Floating Window Toggle Controls
    if (elements.rebalancerToggleFloating) {
        elements.rebalancerToggleFloating.addEventListener("click", () => {
            if (elements.rebalancerFloatingWidget) {
                elements.rebalancerFloatingWidget.classList.toggle("hidden");
                if (!elements.rebalancerFloatingWidget.classList.contains("hidden")) {
                    // Minimize chatbot widget if open
                    if (elements.chatFloatingWidget) elements.chatFloatingWidget.classList.add("hidden");
                }
            }
        });
    }

    if (elements.rebalancerCloseFloating) {
        elements.rebalancerCloseFloating.addEventListener("click", () => {
            if (elements.rebalancerFloatingWidget) {
                elements.rebalancerFloatingWidget.classList.add("hidden");
            }
        });
    }

    // Chatbot Advisor Submission Handler
    if (elements.chatForm) {
        elements.chatForm.addEventListener("submit", async (e) => {
            e.preventDefault();
            if (!state.selectedPortfolioId) return;
            
            const message = elements.chatInput.value.trim();
            if (!message) return;
            
            elements.chatInput.value = "";
            appendChatMessage("user", message);
            
            const loadingBubble = appendChatMessage("loading", '<i class="fa-solid fa-spinner fa-spin"></i> Thinking...');
            
            try {
                const chatData = await apiRequest(`/api/portfolios/${state.selectedPortfolioId}/insights/chat`, {
                    method: "POST",
                    body: {
                        message: message,
                        history: state.chatHistory
                    }
                });
                
                if (loadingBubble) loadingBubble.remove();
                appendChatMessage("assistant", chatData.response);
                
                state.chatHistory.push({ role: "user", content: message });
                state.chatHistory.push({ role: "assistant", content: chatData.response });
                
                if (state.chatHistory.length > 20) {
                    state.chatHistory = state.chatHistory.slice(-20);
                }
            } catch (err) {
                if (loadingBubble) loadingBubble.remove();
                appendChatMessage("system", `Error: ${err.message}`);
            }
        });
    }

    // Run Smart Rebalancer Click Event Listener
    if (elements.runRebalancerBtn) {
        elements.runRebalancerBtn.addEventListener("click", async () => {
            if (!state.selectedPortfolioId) return;
            
            // Show modal and loading state
            if (elements.rebalancerModal) elements.rebalancerModal.classList.remove("hidden");
            if (elements.rebalancerModalLoading) elements.rebalancerModalLoading.classList.remove("hidden");
            if (elements.rebalancerModalOutput) elements.rebalancerModalOutput.innerHTML = "";
            
            try {
                const data = await apiRequest(`/api/portfolios/${state.selectedPortfolioId}/insights/rebalance`, {
                    method: "POST"
                });
                
                if (elements.rebalancerModalLoading) elements.rebalancerModalLoading.classList.add("hidden");
                
                // Build recommendations layout
                let html = `
                    <div class="rebalance-weak-box">
                        <span class="weak-label"><i class="fa-solid fa-triangle-exclamation"></i> Weak Holding Identified:</span>
                        <strong>${data.weak_stock}</strong>. ${data.reason_weak}
                    </div>
                    <div style="font-size: 14px; font-weight: 600; color: var(--text-primary); margin-bottom: 12px; display: flex; align-items: center; gap: 8px;">
                        <i class="fa-solid fa-square-poll-vertical" style="color: var(--primary);"></i>
                        <span>Recommended Sector-Matched Alternatives:</span>
                    </div>
                    <div class="rebalance-grid">
                `;
                
                data.recommendations.forEach(rec => {
                    html += `
                        <div class="rebalance-card">
                            <div class="rebalance-card-header">
                                <span class="rebalance-card-ticker">${rec.ticker}</span>
                                <span class="rebalance-card-badge">RECOMMENDED</span>
                            </div>
                            <div class="rebalance-card-name">${rec.name}</div>
                            <p class="rebalance-card-rationale">${rec.rationale}</p>
                            <div class="rebalance-card-risk">
                                <span class="risk-label">Key Risk:</span> ${rec.risk}
                            </div>
                        </div>
                    `;
                });
                
                html += `</div>`;
                if (elements.rebalancerModalOutput) elements.rebalancerModalOutput.innerHTML = html;
                
            } catch (err) {
                if (elements.rebalancerModalLoading) elements.rebalancerModalLoading.classList.add("hidden");
                if (elements.rebalancerModalOutput) {
                    elements.rebalancerModalOutput.innerHTML = `
                        <div class="text-danger" style="font-size: 14px; color: var(--danger); text-align: center; padding: 30px 0;">
                            <i class="fa-solid fa-circle-exclamation fa-2xl" style="margin-bottom: 12px; display: block;"></i>
                            Failed to run rebalancer optimizer: ${err.message}
                        </div>
                    `;
                }
            }
        });
    }

    // Close Rebalancer Modal handlers
    const closeRebalancerModal = () => {
        if (elements.rebalancerModal) elements.rebalancerModal.classList.add("hidden");
    };

    if (elements.closeRebalancerModalBtn) {
        elements.closeRebalancerModalBtn.addEventListener("click", closeRebalancerModal);
    }
    if (elements.closeRebalancerModalFooterBtn) {
        elements.closeRebalancerModalFooterBtn.addEventListener("click", closeRebalancerModal);
    }
}

// --- MAIN DASHBOARD FLOWS ---
async function selectPortfolio(id) {
    state.selectedPortfolioId = id;
    const portfolio = state.portfolios.find(p => p.id === id);
    if (portfolio) {
        elements.currentPortfolioName.textContent = portfolio.name;
        elements.portfolioActions.classList.remove("hidden");
        elements.welcomeView.classList.add("hidden");
        elements.dashboardView.classList.remove("hidden");
        
        // Reset Chat Advisor session
        state.chatHistory = [];
        if (elements.chatMessages) {
            elements.chatMessages.innerHTML = `
                <div class="message assistant">
                    Hello! I am your GrowwPro AI Advisor. Ask me anything about your active portfolio's asset allocation, sector weights, risk metrics, or holdings.
                </div>
            `;
        }
        
        // Show floating chat & rebalancer bubble buttons
        if (elements.chatToggleFloating) elements.chatToggleFloating.classList.remove("hidden");
        if (elements.rebalancerToggleFloating) elements.rebalancerToggleFloating.classList.remove("hidden");
        
        // Reset Smart Rebalancer Output
        if (elements.rebalancerModalOutput) {
            elements.rebalancerModalOutput.innerHTML = `
                <div class="text-muted" style="font-size: 12.5px; text-align: center; padding: 30px 0;">
                    Click "Scan Underperforming Stock" to find weak assets and suggest alternatives.
                </div>
            `;
        }
        
        await refreshDashboard();
    }
}

async function refreshDashboard(isBackground = false) {
    if (!state.selectedPortfolioId) return;
    
    try {
        // 1. Fetch Analytics (returns, volatility, chart data)
        const analytics = await apiRequest(`/api/portfolios/${state.selectedPortfolioId}/analytics`);
        state.analytics = analytics;
        
        // 2. Render Metrics and Charts
        renderMetrics();
        renderHoldingsTable();
        renderAllocationChart();
        renderPerformanceChart();
        renderTreemap();
        
        // 3. Reset AI Insights UI (waiting for user click)
        if (!isBackground) {
            resetAIInsightsUI();
        }
        
    } catch (err) {
        console.error("Dashboard refresh error:", err);
        if (!isBackground) {
            showToast(`Failed to load portfolio metrics: ${err.message}`, "error");
        }
    }
}

// --- RENDER SERVICES ---
function renderMetrics() {
    const summary = state.analytics.summary;
    const risk = state.analytics.risk_metrics;
    
    // Summary
    elements.totalValue.textContent = `₹${summary.total_current_value.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    elements.costBasis.textContent = `₹${summary.total_cost_basis.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    const absReturn = summary.absolute_return;
    const pctReturn = summary.percentage_return;
    elements.absoluteReturn.textContent = `₹${absReturn.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    if (absReturn >= 0) {
        elements.returnPct.className = "card-badge positive";
        elements.returnPct.textContent = `+${pctReturn.toFixed(2)}%`;
        elements.absoluteReturn.className = "card-value text-positive";
        elements.returnArrow.innerHTML = `<span class="text-positive"><i class="fa-solid fa-arrow-trend-up"></i> Net Gain</span>`;
    } else {
        elements.returnPct.className = "card-badge negative";
        elements.returnPct.textContent = `${pctReturn.toFixed(2)}%`;
        elements.absoluteReturn.className = "card-value text-negative";
        elements.returnArrow.innerHTML = `<span class="text-negative"><i class="fa-solid fa-arrow-trend-down"></i> Net Loss</span>`;
    }
    
    // Risk
    elements.volatility.textContent = `${(risk.volatility * 100).toFixed(2)}%`;
    elements.sharpe.textContent = risk.sharpe_ratio.toFixed(2);
    
    const sr = risk.sharpe_ratio;
    if (sr > 1.5) {
        elements.sharpeDesc.textContent = "Excellent Risk-adjusted";
        elements.sharpe.className = "card-value text-positive";
    } else if (sr > 1) {
        elements.sharpeDesc.textContent = "Strong Risk-adjusted";
        elements.sharpe.className = "card-value text-positive";
    } else if (sr > 0) {
        elements.sharpeDesc.textContent = "Moderate Risk-adjusted";
        elements.sharpe.className = "card-value";
    } else {
        elements.sharpeDesc.textContent = "Weak Risk-adjusted";
        elements.sharpe.className = "card-value text-negative";
    }
    
    elements.beta.textContent = risk.beta.toFixed(2);
    const b = risk.beta;
    if (b > 1.2) {
        elements.betaDesc.textContent = "Aggressive (High volatility)";
    } else if (b >= 0.8) {
        elements.betaDesc.textContent = "Market-correlated";
    } else {
        elements.betaDesc.textContent = "Defensive (Low volatility)";
    }
    
    elements.drawdown.textContent = `${(risk.max_drawdown * 100).toFixed(2)}%`;
}

function renderHoldingsTable() {
    elements.holdingsTbody.innerHTML = "";
    
    if (state.analytics.holdings.length === 0) {
        elements.holdingsTbody.innerHTML = `
            <tr>
                <td colspan="9" style="text-align: center;" class="text-muted">No positions added yet. Use the form to add Indian shares.</td>
            </tr>
        `;
        return;
    }
    
    state.analytics.holdings.forEach(h => {
        const row = document.createElement("tr");
        
        const changeClass = h.absolute_return >= 0 ? "text-positive" : "text-negative";
        const sign = h.absolute_return >= 0 ? "+" : "";
        
        row.innerHTML = `
            <td><strong>${h.ticker}</strong></td>
            <td><span class="badge-sector">${h.sector}</span></td>
            <td>${h.quantity}</td>
            <td>₹${h.buy_price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
            <td>₹${h.current_price.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</td>
            <td><strong>₹${h.current_value.toLocaleString("en-IN", { minimumFractionDigits: 2 })}</strong></td>
            <td class="${changeClass}">${sign}₹${h.absolute_return.toLocaleString("en-IN", { minimumFractionDigits: 2 })} (${sign}${h.percentage_return.toFixed(1)}%)</td>
            <td>${(h.weight * 100).toFixed(1)}%</td>
            <td>
                <div class="table-row-actions">
                    <button class="btn-icon delete" title="Remove Position" onclick="deletePosition('${h.ticker}')">
                        <i class="fa-regular fa-trash-can"></i>
                    </button>
                </div>
            </td>
        `;
        elements.holdingsTbody.appendChild(row);
    });
}

// Global Delete Function (called from HTML inline click handler)
async function deletePosition(ticker) {
    if (!confirm(`Are you sure you want to remove all shares of '${ticker}' from this portfolio?`)) {
        return;
    }
    try {
        // Find holding ID first
        // In database, we query by portfolio/ticker
        // We will make a DELETE call to the specific holding endpoint.
        // Let's get the holding details from the portfolio detail endpoint or find it from analytics
        // Let's find holding by ticker from selected portfolio details
        const portfolioDetails = await apiRequest(`/api/portfolios/${state.selectedPortfolioId}`);
        const holding = portfolioDetails.holdings.find(h => h.ticker === ticker);
        if (holding) {
            await apiRequest(`/api/portfolios/${state.selectedPortfolioId}/holdings/${holding.id}`, {
                method: "DELETE"
            });
            showToast(`Removed position '${ticker}'`);
            await refreshDashboard();
        }
    } catch (err) {
        showToast(err.message, "error");
    }
}

// --- CHART GENERATION SERVICES ---
function renderAllocationChart() {
    if (charts.allocation) {
        charts.allocation.destroy();
    }
    
    const holdings = state.analytics.holdings;
    if (holdings.length === 0) return;
    
    let labels = [];
    let data = [];
    
    if (state.allocationType === "ticker") {
        labels = holdings.map(h => h.ticker);
        data = holdings.map(h => h.current_value);
    } else {
        const sectors = state.analytics.sector_allocations;
        labels = Object.keys(sectors);
        // Multiply total value to get sector values
        const totalVal = state.analytics.summary.total_current_value;
        data = Object.values(sectors).map(pct => (pct / 100) * totalVal);
    }
    
    const ctx = document.getElementById("allocation-chart").getContext("2d");
    
    // Curated rich design palette
    const colors = [
        "#06b6d4", "#3b82f6", "#10b981", "#8b5cf6", "#f59e0b",
        "#ec4899", "#14b8a6", "#f43f5e", "#6366f1", "#a855f7"
    ];
    
    charts.allocation = new Chart(ctx, {
        type: "doughnut",
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: "#0e1424",
                hoverOffset: 12
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: "right",
                    labels: {
                        color: "#94a3b8",
                        font: {
                            family: "Inter",
                            size: 11
                        },
                        padding: 15,
                        usePointStyle: true,
                        pointStyle: "circle"
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const val = context.raw;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const pct = ((val / total) * 100).toFixed(1);
                            return ` ₹${val.toLocaleString("en-IN", { maximumFractionDigits: 0 })} (${pct}%)`;
                        }
                    }
                }
            },
            cutout: "70%"
        }
    });
}

function renderPerformanceChart() {
    if (charts.performance) {
        charts.performance.destroy();
    }
    
    const history = state.analytics.historical_chart;
    if (history.length === 0) return;
    
    const labels = history.map(point => point.date);
    const data = history.map(point => point.value);
    
    const ctx = document.getElementById("performance-chart").getContext("2d");
    
    // Create gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 300);
    gradient.addColorStop(0, "rgba(6, 182, 212, 0.25)");
    gradient.addColorStop(1, "rgba(6, 182, 212, 0.00)");
    
    charts.performance = new Chart(ctx, {
        type: "line",
        data: {
            labels: labels,
            datasets: [{
                label: "Portfolio Value",
                data: data,
                borderColor: "#06b6d4",
                borderWidth: 2,
                fill: true,
                backgroundColor: gradient,
                tension: 0.15,
                pointRadius: 0,
                pointHoverRadius: 6,
                pointHoverBackgroundColor: "#06b6d4",
                pointHoverBorderColor: "#fff",
                pointHoverBorderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: "index",
                intersect: false
            },
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return ` Value: ₹${context.raw.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    grid: {
                        display: false,
                        color: "rgba(255, 255, 255, 0.05)"
                    },
                    ticks: {
                        color: "#64748b",
                        font: { size: 10 },
                        maxTicksLimit: 8
                    }
                },
                y: {
                    grid: {
                        color: "rgba(255, 255, 255, 0.05)"
                    },
                    ticks: {
                        color: "#64748b",
                        font: { size: 10 },
                        callback: function(value) {
                            return "₹" + value.toLocaleString("en-IN", { maximumFractionDigits: 0 });
                        }
                    }
                }
            }
        }
    });
}

// --- AI INSIGHT COMMENTARY SERVICES ---
async function fetchAIInsights(force = false) {
    if (!state.selectedPortfolioId) return;
    
    // Show loading skeleton, hide previous content
    elements.insightsSkeleton.classList.remove("hidden");
    elements.insightsContent.classList.add("hidden");
    elements.regenerateInsightsBtn.disabled = true;
    
    try {
        const endpoint = force 
            ? `/api/portfolios/${state.selectedPortfolioId}/insights/regenerate`
            : `/api/portfolios/${state.selectedPortfolioId}/insights`;
            
        const method = force ? "POST" : "GET";
        
        const insights = await apiRequest(endpoint, { method });
        state.insights = insights;
        renderAIInsights();
    } catch (err) {
        showToast(`AI Insights error: ${err.message}`, "error");
        elements.insightSummary.textContent = "Could not load AI commentary. Please ensure you have added holdings to compute analytics.";
    } finally {
        elements.insightsSkeleton.classList.add("hidden");
        elements.insightsContent.classList.remove("hidden");
        elements.regenerateInsightsBtn.disabled = false;
    }
}

function renderAIInsights() {
    if (!state.insights || !state.insights.content) return;
    
    const content = state.insights.content;
    
    elements.insightSummary.textContent = content.summary;
    elements.insightRisk.textContent = content.risk_commentary;
    elements.insightDiversification.textContent = content.diversification_note;
    
    // Render Watch list
    elements.insightWatchList.innerHTML = "";
    content.watch_items.forEach(item => {
        const li = document.createElement("li");
        li.textContent = item;
        elements.insightWatchList.appendChild(li);
    });
    
    elements.insightDisclaimer.textContent = content.disclaimer;
}

function resetAIInsightsUI() {
    state.insights = null;
    elements.insightSummary.textContent = "AI Analysis is currently pending. Click the 'Run AI Diagnostics' button above to analyze your portfolio metrics and generate insights.";
    elements.insightRisk.textContent = "Click 'Run AI Diagnostics' above to generate risk analysis.";
    elements.insightDiversification.textContent = "Click 'Run AI Diagnostics' above to generate diversification commentary.";
    elements.insightWatchList.innerHTML = "<li>Analysis pending. Click the button above to run diagnostics.</li>";
    elements.insightDisclaimer.textContent = "Disclaimer: Educational commentary only.";
}

async function fetchMarketIndices() {
    const grid = document.getElementById("market-ticker-grid");
    
    try {
        const data = await apiRequest("/api/market/indices");
        
        if (!state.homeIndices) {
            state.homeIndices = {};
        }
        
        data.forEach(idx => {
            // Save current baseline to state
            state.homeIndices[idx.symbol] = {
                price: idx.price,
                change: idx.change,
                pct_change: idx.pct_change,
                name: idx.name
            };
            
            // Update header ticker strip (always visible)
            updateStripItem(idx.symbol, idx.price, idx.change, idx.pct_change, false);
        });
        
        // Also render welcome-page grid if present
        if (grid) {
            grid.innerHTML = "";
            data.forEach(idx => {
                const isPositive = idx.change >= 0;
                const changeClass = isPositive ? "positive" : "negative";
                const sign = isPositive ? "+" : "";
                
                const card = document.createElement("div");
                card.className = "ticker-item";
                card.id = `home-card-${idx.symbol}`;
                card.innerHTML = `
                    <div class="ticker-name-area">
                        <div class="ticker-name">${idx.name}</div>
                        <div class="text-muted" style="font-size: 11px;">${idx.symbol}</div>
                    </div>
                    <div style="text-align: right;">
                        <div class="ticker-price">₹${idx.price.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</div>
                        <span class="ticker-change ${changeClass}">${sign}${idx.change.toFixed(2)} (${sign}${idx.pct_change.toFixed(2)}%)</span>
                    </div>
                `;
                grid.appendChild(card);
            });
        }
        
        // Start home page ticking loop if not already running
        if (!window.homeTickerInterval) {
            startHomeTickerTick();
        }
    } catch (err) {
        if (grid) {
            grid.innerHTML = `<div class="ticker-item error" style="grid-column: 1 / -1; justify-content: center; color: var(--danger);">Failed to load live indices.</div>`;
        }
    }
}

// Update header ticker strip item
function updateStripItem(symbol, price, change, pctChange, isTick = true) {
    const priceEl = document.getElementById(`strip-price-${symbol}`);
    const changeEl = document.getElementById(`strip-change-${symbol}`);
    const stripEl = document.getElementById(`strip-${symbol}`);
    
    if (!priceEl || !changeEl || !stripEl) return;
    
    priceEl.textContent = "₹" + price.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    
    const isPositive = change >= 0;
    const sign = isPositive ? "+" : "";
    changeEl.textContent = `${sign}${change.toFixed(2)} (${sign}${pctChange.toFixed(2)}%)`;
    changeEl.className = `strip-item-change ${isPositive ? "positive" : "negative"}`;
    
    if (isTick) {
        const tickClass = change >= 0 ? "tick-up" : "tick-down";
        stripEl.classList.add(tickClass);
        setTimeout(() => stripEl.classList.remove(tickClass), 400);
    }
}

function startHomeTickerTick() {
    if (window.homeTickerInterval) {
        clearInterval(window.homeTickerInterval);
    }
    
    window.homeTickerInterval = setInterval(() => {
        // Pause ticking if tab is hidden or data isn't loaded
        if (document.hidden || !state.homeIndices) return;
        
        Object.keys(state.homeIndices).forEach(symbol => {
            const idx = state.homeIndices[symbol];
            
            // Micro-fluctuation simulation of ±0.015% spreads
            const factor = 1 + (Math.random() - 0.5) * 0.0003; 
            const oldPrice = idx.price;
            const newPrice = oldPrice * factor;
            const priceDiff = newPrice - oldPrice;
            
            idx.price = newPrice;
            idx.change += priceDiff;
            
            const baseline = oldPrice / (1 + idx.pct_change / 100);
            idx.pct_change = ((newPrice - baseline) / baseline) * 100;
            
            // Always update header ticker strip
            updateStripItem(symbol, newPrice, idx.change, idx.pct_change, true);
            
            // Update welcome-page grid cards only when on welcome page
            if (!state.selectedPortfolioId) {
                const cardEl = document.getElementById(`home-card-${symbol}`);
                if (cardEl) {
                    const priceEl = cardEl.querySelector(".ticker-price");
                    const changeEl = cardEl.querySelector(".ticker-change");
                    
                    if (priceEl && changeEl) {
                        priceEl.textContent = "₹" + newPrice.toLocaleString("en-IN", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
                        
                        const isPositive = idx.change >= 0;
                        const sign = isPositive ? "+" : "";
                        changeEl.textContent = `${sign}${idx.change.toFixed(2)} (${sign}${idx.pct_change.toFixed(2)}%)`;
                        
                        if (isPositive) {
                            changeEl.className = "ticker-change positive";
                        } else {
                            changeEl.className = "ticker-change negative";
                        }
                        
                        const tickClass = idx.change >= 0 ? "tick-up" : "tick-down";
                        cardEl.classList.add(tickClass);
                        setTimeout(() => {
                            cardEl.classList.remove(tickClass);
                        }, 400);
                    }
                }
            }
        });
    }, 1000);
}

async function fetchMarketNews() {
    const grid = document.getElementById("market-news-grid");
    if (!grid) return;
    
    try {
        const data = await apiRequest("/api/market/news");
        grid.innerHTML = "";
        
        if (data.length === 0) {
            grid.innerHTML = `<div class="news-loading text-muted">No news updates available at this time.</div>`;
            return;
        }
        
        data.forEach(item => {
            const card = document.createElement("a");
            card.className = "news-card";
            card.href = item.link;
            card.target = "_blank";
            card.rel = "noopener noreferrer";
            
            card.innerHTML = `
                <div class="news-main-info">
                    <div class="news-source-meta">
                        <span class="news-source-badge">${item.source}</span>
                        <span class="news-date">${item.pub_date}</span>
                    </div>
                    <div class="news-title">${item.title}</div>
                </div>
                <div class="news-arrow">
                    <i class="fa-solid fa-arrow-right"></i>
                </div>
            `;
            grid.appendChild(card);
        });
    } catch (err) {
        grid.innerHTML = `<div class="news-loading text-muted" style="color: var(--danger);">Failed to load news feed.</div>`;
    }
}

function startLivePriceFetching() {
    if (window.livePriceInterval) {
        clearInterval(window.livePriceInterval);
    }
    
    window.livePriceInterval = setInterval(async () => {
        // Halt fetching if tab is hidden/minimized to avoid unnecessary yfinance calls
        if (!state.user || document.hidden) return;
        
        if (state.selectedPortfolioId) {
            // Update active portfolio (using background mode to preserve AI diagnostics)
            await refreshDashboard(true);
        } else {
            // Update key market indices on welcome landing page
            await fetchMarketIndices();
        }
    }, 15000);
}

function formatChatText(text) {
    if (!text) return "";
    // If text is raw HTML element like loading spinner, return as-is
    if (text.trim().startsWith("<i class=") || text.trim().startsWith("<span") || text.trim().startsWith("<div")) return text;
    
    // HTML escaping
    let formatted = text
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;");
        
    // Bold **text**
    formatted = formatted.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");
    // Italic *text*
    formatted = formatted.replace(/\*(.*?)\*/g, "<em>$1</em>");
    // Newlines
    formatted = formatted.replace(/\n/g, "<br>");
    
    return formatted;
}

function appendChatMessage(role, text) {
    if (!elements.chatMessages) return null;
    
    const bubble = document.createElement("div");
    bubble.className = `message ${role}`;
    bubble.innerHTML = formatChatText(text);
    
    elements.chatMessages.appendChild(bubble);
    elements.chatMessages.scrollTop = elements.chatMessages.scrollHeight;
    
    return bubble;
}

// ============================================================
// THEME MANAGEMENT
// ============================================================
function initTheme() {
    const saved = localStorage.getItem("growwpro-theme") || "dark";
    applyTheme(saved, false);
}

function applyTheme(theme, animate = true) {
    state.currentTheme = theme;
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("growwpro-theme", theme);
    
    // Update checkbox
    const checkbox = document.getElementById("theme-toggle-checkbox");
    if (checkbox) checkbox.checked = (theme === "light");
    
    // Update label text
    const label = document.getElementById("theme-toggle-label-text");
    if (label) label.textContent = theme === "light" ? "Dark Mode" : "Light Mode";
    
    // Update label icon
    const wrapper = document.getElementById("theme-toggle-wrapper");
    if (wrapper) {
        const icon = wrapper.querySelector(".theme-toggle-label i");
        if (icon) {
            icon.className = theme === "light"
                ? "fa-solid fa-moon"
                : "fa-solid fa-sun";
        }
    }
    
    // Refresh Chart.js colors if charts exist
    updateChartThemeColors();
}

function getThemeColors() {
    const isLight = state.currentTheme === "light";
    return {
        gridColor: isLight ? "rgba(0, 0, 0, 0.06)" : "rgba(255, 255, 255, 0.05)",
        tickColor: isLight ? "#64748b" : "#64748b",
        legendColor: isLight ? "#475569" : "#94a3b8"
    };
}

function updateChartThemeColors() {
    const colors = getThemeColors();
    
    if (charts.performance) {
        charts.performance.options.scales.x.ticks.color = colors.tickColor;
        charts.performance.options.scales.y.ticks.color = colors.tickColor;
        charts.performance.options.scales.y.grid.color = colors.gridColor;
        charts.performance.update("none");
    }
    
    if (charts.allocation) {
        if (charts.allocation.options.plugins.legend) {
            charts.allocation.options.plugins.legend.labels.color = colors.legendColor;
        }
        charts.allocation.update("none");
    }
    
    // Re-render treemap since it uses Canvas 2D directly
    if (state.analytics && state.analytics.holdings.length > 0) {
        renderTreemap();
    }
}

// ============================================================
// SQUARIFIED TREEMAP RENDERER
// ============================================================

// Sector color palette (matches allocation chart)
const TREEMAP_COLORS = [
    "#06b6d4", "#3b82f6", "#10b981", "#8b5cf6", "#f59e0b",
    "#ec4899", "#14b8a6", "#f43f5e", "#6366f1", "#a855f7"
];

function renderTreemap() {
    const canvas = document.getElementById("treemap-canvas");
    const container = document.getElementById("treemap-container");
    const legendEl = document.getElementById("treemap-legend");
    if (!canvas || !container || !state.analytics) return;
    
    const holdings = state.analytics.holdings;
    if (!holdings || holdings.length === 0) {
        const ctx = canvas.getContext("2d");
        canvas.width = container.clientWidth * (window.devicePixelRatio || 1);
        canvas.height = container.clientHeight * (window.devicePixelRatio || 1);
        ctx.scale(window.devicePixelRatio || 1, window.devicePixelRatio || 1);
        ctx.clearRect(0, 0, container.clientWidth, container.clientHeight);
        ctx.fillStyle = state.currentTheme === "light" ? "#94a3b8" : "#64748b";
        ctx.font = "14px Inter, sans-serif";
        ctx.textAlign = "center";
        ctx.fillText("Add holdings to see your asset treemap", container.clientWidth / 2, container.clientHeight / 2);
        if (legendEl) legendEl.innerHTML = "";
        treemapRects = [];
        return;
    }
    
    // Assign sector colors
    const sectorSet = [...new Set(holdings.map(h => h.sector))];
    const sectorColorMap = {};
    sectorSet.forEach((s, i) => {
        sectorColorMap[s] = TREEMAP_COLORS[i % TREEMAP_COLORS.length];
    });
    
    // Prepare data: sort by value descending
    const items = holdings.map(h => ({
        ticker: h.ticker,
        sector: h.sector,
        value: h.current_value,
        weight: h.weight,
        color: sectorColorMap[h.sector],
        returnPct: h.percentage_return
    })).sort((a, b) => b.value - a.value);
    
    // Setup canvas
    const dpr = window.devicePixelRatio || 1;
    const w = container.clientWidth;
    const h = container.clientHeight;
    canvas.width = w * dpr;
    canvas.height = h * dpr;
    const ctx = canvas.getContext("2d");
    ctx.scale(dpr, dpr);
    ctx.clearRect(0, 0, w, h);
    
    // Squarified treemap algorithm
    const totalValue = items.reduce((sum, item) => sum + item.value, 0);
    if (totalValue <= 0) return;
    
    treemapRects = [];
    squarify(items, { x: 0, y: 0, w: w, h: h }, totalValue);
    
    // Draw rectangles
    const gap = 2;
    const isLight = state.currentTheme === "light";
    
    treemapRects.forEach(rect => {
        const rx = rect.x + gap;
        const ry = rect.y + gap;
        const rw = rect.w - gap * 2;
        const rh = rect.h - gap * 2;
        
        if (rw <= 0 || rh <= 0) return;
        
        // Fill with sector color
        ctx.fillStyle = rect.color;
        ctx.globalAlpha = isLight ? 0.75 : 0.65;
        roundRect(ctx, rx, ry, rw, rh, 6);
        ctx.fill();
        ctx.globalAlpha = 1;
        
        // Border
        ctx.strokeStyle = isLight ? "rgba(255,255,255,0.6)" : "rgba(255,255,255,0.15)";
        ctx.lineWidth = 1;
        roundRect(ctx, rx, ry, rw, rh, 6);
        ctx.stroke();
        
        // Label text if rectangle is large enough
        if (rw > 50 && rh > 35) {
            ctx.fillStyle = "#fff";
            ctx.font = `bold ${Math.min(14, rw / 6)}px Outfit, sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            
            const label = rect.ticker.replace(".NS", "").replace(".BO", "");
            ctx.fillText(label, rx + rw / 2, ry + rh / 2 - 8);
            
            ctx.font = `600 ${Math.min(11, rw / 8)}px Inter, sans-serif`;
            ctx.fillStyle = "rgba(255,255,255,0.8)";
            ctx.fillText(`${(rect.weight * 100).toFixed(1)}%`, rx + rw / 2, ry + rh / 2 + 8);
        } else if (rw > 28 && rh > 20) {
            ctx.fillStyle = "#fff";
            ctx.font = `bold ${Math.min(10, rw / 5)}px Outfit, sans-serif`;
            ctx.textAlign = "center";
            ctx.textBaseline = "middle";
            const label = rect.ticker.replace(".NS", "").replace(".BO", "");
            ctx.fillText(label, rx + rw / 2, ry + rh / 2);
        }
    });
    
    // Render legend
    if (legendEl) {
        legendEl.innerHTML = "";
        sectorSet.forEach(sector => {
            const div = document.createElement("div");
            div.className = "treemap-legend-item";
            div.innerHTML = `<div class="treemap-legend-swatch" style="background: ${sectorColorMap[sector]}"></div>${sector}`;
            legendEl.appendChild(div);
        });
    }
    
    // Hover tooltip handler
    setupTreemapHover(canvas, container);
}

function squarify(items, rect, totalValue) {
    if (items.length === 0) return;
    if (items.length === 1) {
        treemapRects.push({ ...items[0], x: rect.x, y: rect.y, w: rect.w, h: rect.h });
        return;
    }
    
    const isHorizontal = rect.w >= rect.h;
    let row = [];
    let rowArea = 0;
    const side = isHorizontal ? rect.h : rect.w;
    
    for (let i = 0; i < items.length; i++) {
        const area = (items[i].value / totalValue) * rect.w * rect.h;
        const testRow = [...row, { ...items[i], area }];
        const testArea = rowArea + area;
        
        if (row.length === 0 || worstAspectRatio(testRow, testArea, side) <= worstAspectRatio(row, rowArea, side)) {
            row.push({ ...items[i], area });
            rowArea += area;
        } else {
            // Layout current row
            layoutRow(row, rect, isHorizontal, rowArea);
            
            // Compute remaining rectangle
            const rowSize = rowArea / side;
            let newRect;
            if (isHorizontal) {
                newRect = { x: rect.x + rowSize, y: rect.y, w: rect.w - rowSize, h: rect.h };
            } else {
                newRect = { x: rect.x, y: rect.y + rowSize, w: rect.w, h: rect.h - rowSize };
            }
            
            const remaining = items.slice(i);
            const remainingTotal = remaining.reduce((s, it) => s + it.value, 0);
            squarify(remaining, newRect, remainingTotal);
            return;
        }
    }
    
    // Layout final row
    if (row.length > 0) {
        layoutRow(row, rect, isHorizontal, rowArea);
    }
}

function worstAspectRatio(row, totalArea, side) {
    if (row.length === 0 || totalArea === 0 || side === 0) return Infinity;
    const rowLen = totalArea / side;
    let worst = 0;
    for (const item of row) {
        const itemSide = item.area / rowLen;
        const ratio = Math.max(rowLen / itemSide, itemSide / rowLen);
        if (ratio > worst) worst = ratio;
    }
    return worst;
}

function layoutRow(row, rect, isHorizontal, rowArea) {
    const side = isHorizontal ? rect.h : rect.w;
    const rowSize = side > 0 ? rowArea / side : 0;
    let offset = 0;
    
    for (const item of row) {
        const itemSize = rowSize > 0 ? item.area / rowSize : 0;
        
        let rx, ry, rw, rh;
        if (isHorizontal) {
            rx = rect.x;
            ry = rect.y + offset;
            rw = rowSize;
            rh = itemSize;
        } else {
            rx = rect.x + offset;
            ry = rect.y;
            rw = itemSize;
            rh = rowSize;
        }
        
        treemapRects.push({ ...item, x: rx, y: ry, w: rw, h: rh });
        offset += itemSize;
    }
}

function roundRect(ctx, x, y, w, h, r) {
    if (w < 2 * r) r = w / 2;
    if (h < 2 * r) r = h / 2;
    ctx.beginPath();
    ctx.moveTo(x + r, y);
    ctx.arcTo(x + w, y, x + w, y + h, r);
    ctx.arcTo(x + w, y + h, x, y + h, r);
    ctx.arcTo(x, y + h, x, y, r);
    ctx.arcTo(x, y, x + w, y, r);
    ctx.closePath();
}

function setupTreemapHover(canvas, container) {
    const tooltip = document.getElementById("treemap-tooltip");
    const tickerEl = document.getElementById("treemap-tooltip-ticker");
    const sectorEl = document.getElementById("treemap-tooltip-sector");
    const valueEl = document.getElementById("treemap-tooltip-value");
    
    if (!tooltip || !canvas) return;
    if (canvas._hoverAttached) return;
    canvas._hoverAttached = true;
    
    canvas.addEventListener("mousemove", (e) => {
        const rect = canvas.getBoundingClientRect();
        const mx = e.clientX - rect.left;
        const my = e.clientY - rect.top;
        
        const found = treemapRects.find(r =>
            mx >= r.x + 2 && mx <= r.x + r.w - 2 &&
            my >= r.y + 2 && my <= r.y + r.h - 2
        );
        
        if (found) {
            tickerEl.textContent = found.ticker;
            sectorEl.textContent = found.sector;
            const sign = found.returnPct >= 0 ? "+" : "";
            valueEl.innerHTML = `₹${found.value.toLocaleString("en-IN", { maximumFractionDigits: 0 })} · ${(found.weight * 100).toFixed(1)}% · <span style="color: ${found.returnPct >= 0 ? 'var(--success)' : 'var(--danger)'}">${sign}${found.returnPct.toFixed(1)}%</span>`;
            tooltip.classList.add("visible");
            
            // Position tooltip
            let tx = mx + 14;
            let ty = my - 10;
            if (tx + 200 > container.clientWidth) tx = mx - 180;
            if (ty < 0) ty = 10;
            tooltip.style.left = tx + "px";
            tooltip.style.top = ty + "px";
        } else {
            tooltip.classList.remove("visible");
        }
    });
    
    canvas.addEventListener("mouseleave", () => {
        tooltip.classList.remove("visible");
    });
}

// Window resize listener to keep canvas treemap sharp and properly sized
window.addEventListener("resize", () => {
    if (state.selectedPortfolioId && state.analytics) {
        renderTreemap();
    }
});

// ============================================================
// WEALTH COMPOUNDING SIMULATOR LOGIC
// ============================================================
function initWealthSimulator() {
    const monthlyInput = document.getElementById("sim-monthly");
    const yearsInput = document.getElementById("sim-years");
    const rateInput = document.getElementById("sim-rate");
    
    if (!monthlyInput || !yearsInput || !rateInput) return;
    
    const monthlyVal = document.getElementById("sim-monthly-val");
    const yearsVal = document.getElementById("sim-years-val");
    const rateVal = document.getElementById("sim-rate-val");
    
    const totalWealthEl = document.getElementById("sim-total-wealth");
    const totalInvestedEl = document.getElementById("sim-total-invested");
    const totalGainEl = document.getElementById("sim-total-gain");
    const wealthGrowthEl = document.getElementById("sim-wealth-growth");
    
    function updateCalculation() {
        const P = parseFloat(monthlyInput.value) || 10000;
        const years = parseInt(yearsInput.value) || 10;
        const annualRate = parseFloat(rateInput.value) || 12;
        
        const i = annualRate / 12 / 100;
        const n = years * 12;
        
        // Compound SIP Future Value Formula: FV = P * [((1 + i)^n - 1) / i] * (1 + i)
        const fv = P * (((Math.pow(1 + i, n) - 1) / i)) * (1 + i);
        const totalInvested = P * n;
        const totalGain = fv - totalInvested;
        const multiplier = totalInvested > 0 ? (totalGain / totalInvested) * 100 : 0;
        
        if (monthlyVal) monthlyVal.textContent = `₹${Math.round(P).toLocaleString("en-IN")}`;
        if (yearsVal) yearsVal.textContent = `${years} ${years === 1 ? "Year" : "Years"}`;
        if (rateVal) rateVal.textContent = `${annualRate.toFixed(1)}%`;
        
        if (totalWealthEl) totalWealthEl.textContent = `₹${Math.round(fv).toLocaleString("en-IN")}`;
        if (totalInvestedEl) totalInvestedEl.textContent = `₹${Math.round(totalInvested).toLocaleString("en-IN")}`;
        if (totalGainEl) totalGainEl.textContent = `₹${Math.round(totalGain).toLocaleString("en-IN")}`;
        if (wealthGrowthEl) wealthGrowthEl.textContent = `+${multiplier.toFixed(1)}% Wealth Multiplier`;
    }
    
    monthlyInput.addEventListener("input", updateCalculation);
    yearsInput.addEventListener("input", updateCalculation);
    rateInput.addEventListener("input", updateCalculation);
    
    const presetBtns = document.querySelectorAll(".btn-preset");
    presetBtns.forEach(btn => {
        btn.addEventListener("click", () => {
            presetBtns.forEach(b => b.classList.remove("active"));
            btn.classList.add("active");
            const rate = btn.getAttribute("data-rate");
            if (rate) {
                rateInput.value = rate;
                updateCalculation();
            }
        });
    });
    
    updateCalculation();
}
