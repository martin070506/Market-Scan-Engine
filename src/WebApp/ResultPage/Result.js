const API_BASE = "https://market-scan-engine.onrender.com";
//const API_BASE = "http://127.0.0.1:8000";
let sma150Slow = []
let sma150Fast = []
let sma200Slow = []
let sma200Fast = []
let sma20Below = []
let sma20Above = []

// ── Helpers ──────────────────────────────────────────────────────────────────

function renderStocks(bodyId, badgeId, stocks, showToolbar = false) {
    const body = document.getElementById(bodyId);
    const badge = document.getElementById(badgeId);

    if (!Array.isArray(stocks) || stocks.length === 0) {
        body.innerHTML = '<span class="state-empty">No stocks found</span>';
        badge.textContent = '0';
        return;
    }

    badge.textContent = stocks.length;

    const stocksHtml = stocks.map((s, idx) => {
        let ticker = '';
        let subText = '';
        let dates = [];
        const uid = `${bodyId}-stock-${idx}`;

        if (Array.isArray(s) && s.length === 2) {
            ticker = s[0];
            subText = s[1];
        }
        else if (typeof s === 'object' && s !== null) {
            ticker = s.Stock ?? '—';
            dates = Array.isArray(s.Data) ? s.Data : [];
        }
        else {
            ticker = s;
        }

        // --- Complex Format: Cup & Handle (Vertical/Collapsible) ---
        if (dates.length > 0) {
            const datesHtml = dates.map(d => `<div class="pivot-set-label" style="margin: 4px 0; font-size: 0.85em; opacity: 0.8;">• ${d}</div>`).join('');

            return `
                <div class="pivot-stock" id="${uid}" style="width: 100%; margin-bottom: 8px;">
                    <button class="pivot-stock-header" onclick="togglePivot('${uid}')">
                        <span class="pivot-ticker">${ticker}</span>
                        <span class="pivot-meta">
                            <span class="pivot-count">${dates.length} points</span>
                            <span class="pivot-chevron">▸</span>
                        </span>
                    </button>
                    <div class="pivot-sets-grid" style="display:none; padding: 12px;">
                        <div class="pivot-set">
                            <div class="pivot-set-label" style="color: var(--accent); font-weight: 800;">Pattern Dates</div>
                            ${datesHtml}
                        </div>
                    </div>
                </div>`;
        }

        // --- Simple Format: MA Pairs (Horizontal/Pills) ---
        const isAbove = subText.toLowerCase() === 'above';
        const statusColor = isAbove ? '#fcbf18' : '#fcbf18'; // Green for Above, Red for Below
        const labelMarkup = subText ? `<span style="margin-left: 6px; font-size: 0.7em; color: ${statusColor}; font-weight: 800;">${subText}</span>` : '';

        return `
            <div class="stock-pill" style="display: flex; align-items: center; padding: 8px 12px; border: 1px solid var(--border); border-radius: 6px; background: rgba(255,255,255,0.03); white-space: nowrap;">
                <span style="font-weight: 700; font-size: 0.9em; letter-spacing: 0.5px;">${ticker}</span>
                ${labelMarkup}
            </div>`;
    }).join('');

    const toolbarHtml = showToolbar ? `
        <div class="pivot-toolbar" style="display: flex; gap: 8px; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 4px; width: 100%;">
            <button class="pivot-collapse-btn" onclick="collapseAllPivots('${bodyId}')">Collapse all</button>
            <button class="pivot-collapse-btn" onclick="expandAllPivots('${bodyId}')">Expand all</button>
        </div>` : '';

    // The "flex-wrap: wrap" on the container is what makes them sit next to each other
    body.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 12px; width: 100%;">
            ${toolbarHtml}
            <div class="stock-list-container" style="display: flex; flex-wrap: wrap; gap: 8px; align-items: flex-start;">
                ${stocksHtml}
            </div>
        </div>`;
}

// Renders pivot data: array of { Stock, Data } objects
// Each stock row is collapsed by default; click to expand. A top button collapses all.
function renderPivots(bodyId, badgeId, items) {
    const body = document.getElementById(bodyId);
    const badge = document.getElementById(badgeId);

    if (!Array.isArray(items) || items.length === 0) {
        body.innerHTML = '<span class="state-empty">No stocks found</span>';
        badge.textContent = '0';
        return;
    }

    badge.textContent = items.length;

    const stocksHtml = items.map((item, idx) => {
        const stock = item.Stock ?? '—';
        const pivotSets = item.Data ?? [];
        const uid = `${bodyId}-stock-${idx}`;

        const setsHtml = pivotSets.map((pivotSet, setIdx) => {
            const rowsHtml = pivotSet.map(([price, date, bar]) => `
                <tr>
                    <td>${date}</td>
                    <td>$${Number(price).toFixed(2)}</td>
                    <td>${bar}</td>
                </tr>`).join('');

            return `
                <div class="pivot-set">
                    <div class="pivot-set-label">Set ${setIdx + 1} <span>(${pivotSet.length} pivot${pivotSet.length !== 1 ? 's' : ''})</span></div>
                    <table class="pivot-table">
                        <thead><tr><th>Date</th><th>Price</th><th>Bar</th></tr></thead>
                        <tbody>${rowsHtml}</tbody>
                    </table>
                </div>`;
        }).join('');

        return `
            <div class="pivot-stock" id="${uid}">
                <button class="pivot-stock-header" onclick="togglePivot('${uid}')">
                    <span class="pivot-ticker">${stock}</span>
                    <span class="pivot-meta">
                        <span class="pivot-count">${pivotSets.length} set${pivotSets.length !== 1 ? 's' : ''}</span>
                        <span class="pivot-chevron">▸</span>
                    </span>
                </button>
                <div class="pivot-sets-grid" style="display:none;">${setsHtml}</div>
            </div>`;
    }).join('');

    body.innerHTML = `
        <div style="display: flex; flex-direction: column; gap: 16px;">
            <div class="pivot-toolbar" style="display: flex; gap: 8px; order: 1; border-bottom: 1px solid var(--border); padding-bottom: 12px; margin-bottom: 4px;">
                <button class="pivot-collapse-btn" onclick="collapseAllPivots('${bodyId}')">Collapse all</button>
                <button class="pivot-collapse-btn" onclick="expandAllPivots('${bodyId}')">Expand all</button>
            </div>
            <div class="pivot-list" style="order: 2;">
                ${stocksHtml}
            </div>
        </div>`;
}

function togglePivot(uid) {
    const stock = document.getElementById(uid);
    const grid = stock.querySelector('.pivot-sets-grid');
    const chev = stock.querySelector('.pivot-chevron');
    const open = grid.style.display !== 'none';
    grid.style.display = open ? 'none' : 'block';
    chev.textContent = open ? '▸' : '▾';
    stock.classList.toggle('pivot-open', !open);
}

function collapseAllPivots(bodyId) {
    document.querySelectorAll(`#${bodyId} .pivot-stock`).forEach(stock => {
        stock.querySelector('.pivot-sets-grid').style.display = 'none';
        stock.querySelector('.pivot-chevron').textContent = '▸';
        stock.classList.remove('pivot-open');
    });
}

function expandAllPivots(bodyId) {
    document.querySelectorAll(`#${bodyId} .pivot-stock`).forEach(stock => {
        stock.querySelector('.pivot-sets-grid').style.display = 'block';
        stock.querySelector('.pivot-chevron').textContent = '▾';
        stock.classList.add('pivot-open');
    });
}

// Toggle the entire card body (the whole pivot list) open/closed
function toggleCardBody(cardId) {
    const card = document.getElementById(cardId);
    const body = card.querySelector('.card-body');
    const btn = card.querySelector('.card-toggle-btn');
    const collapsed = body.classList.toggle('card-body--collapsed');
    btn.textContent = collapsed ? '▸' : '▾';
}

function renderError(bodyId, badgeId) {
    const body = document.getElementById(bodyId);
    const badge = document.getElementById(badgeId);
    body.innerHTML = '<span class="state-error">Failed to load</span>';
    badge.textContent = '!';
}

function setStatus(state, text) {
    const el = document.getElementById('global-status');
    el.className = state;
    document.getElementById('status-text').textContent = text;
}




// ── Main fetch ────────────────────────────────────────────────────────────────

async function fetchResults() {
    const urlParams = new URLSearchParams(window.location.search);
    const resultId = urlParams.get('id');

    document.getElementById('scan-id-display').textContent =
        resultId ? `ID: ${resultId}` : 'No ID';

    setStatus('loading', 'Fetching data…');

    const get = async (path) => {
        const r = await fetch(`${API_BASE}/results/${resultId}/${path}`);
        return r.json().catch(() => null);
    };

    try {
        const [
            cupHandle,
            doubleBottom,
            close150Slow,
            close150_3atr,
            close200Slow,
            close200_3atr,
            minPivots,
            maxPivots,
            above20,
            below20,
        ] = await Promise.all([
            get('cup-handle'),
            get('double-bottom'),
            get('close-to-150-slow-atr'),
            get('close-to-150-3-atr'),
            get('close-to-200-slow-atr'),
            get('close-to-200-3-atr'),
            get('min-pivots-ready-for-entry'),
            get('max-pivots-ready-for-entry'),
            get('above-from-20-above-2x-atr'),
            get('below-from-20-above-2x-atr'),
        ]);
        sma20Above = above20.stocks
        sma20Below = below20.stocks
        sma150Slow = filterPairsStockStatus(close150Slow.stocks)
        sma150Fast = filterPairsStockStatus(close150_3atr.stocks)
        sma200Slow = filterPairsStockStatus(close200Slow.stocks)
        sma200Fast = filterPairsStockStatus(close200_3atr.stocks)

        // Add 'true' to show buttons for Cup & Handle
        renderStocks('body-cup-handle', 'badge-cup-handle', cupHandle?.stocks, true);

        // Keep 'false' (or omit) for MA sections to hide buttons
        renderStocks('body-double-bottom', 'badge-double-bottom', doubleBottom?.stocks, false);
        renderStocks('body-150-slow', 'badge-150-slow', close150Slow?.stocks, false);
        renderStocks('body-150-3atr', 'badge-150-3atr', close150_3atr?.stocks, false);
        renderStocks('body-200-slow', 'badge-200-slow', close200Slow?.stocks, false);
        renderStocks('body-200-3atr', 'badge-200-3atr', close200_3atr?.stocks, false);
        renderStocks('body-above-20', 'badge-above-20', above20?.stocks, false);
        renderStocks('body-below-20', 'badge-below-20', below20?.stocks, false);

        // Min/Max pivots — unwrap if needed, then render
        // API may return the array directly, or wrapped as { stocks: [...] } or { data: [...] }
        const unwrapPivots = (raw) => {
            if (Array.isArray(raw)) return raw;
            if (raw && Array.isArray(raw.stocks)) return raw.stocks;
            if (raw && Array.isArray(raw.data)) return raw.data;
            return [];
        };
        renderPivots('body-min-pivots', 'badge-min-pivots', unwrapPivots(minPivots));
        renderPivots('body-max-pivots', 'badge-max-pivots', unwrapPivots(maxPivots));

        setStatus('done', 'All results loaded');

    } catch (err) {
        console.error(err);
        setStatus('error', 'Error loading results');

        ['cup-handle', 'double-bottom', '150-slow', '150-3atr',
            '200-slow', '200-3atr', 'min-pivots', 'max-pivots',
            'above-20', 'below-20'].forEach(id => {
                renderError(`body-${id}`, `badge-${id}`);
            });
    }
}

function filterPairsStockStatus(listOfPairs) {
    let resultList = []
    for (pair of listOfPairs) {
        resultList.push(pair[0])
    }
    return resultList

}

function copyToClipboard(list) {
    if (list.length === 0) {
        console.warn("List is empty, nothing to copy.");
        return;
    }

    // .join(",") turns ['A', 'B'] into "A,B"
    const textToCopy = list.join(",");

    navigator.clipboard.writeText(textToCopy).then(() => {
        console.log("Copied to clipboard: " + textToCopy);
    }).catch(err => {
        console.error("Failed to copy: ", err);
    });
}

document.addEventListener('DOMContentLoaded', () => {
    const mlBtn = document.getElementById('run-ml-model');
    const tickerInput = document.getElementById('ticker-input');
    const mlContainer = document.querySelector('.ml-container');

    mlBtn.addEventListener('click', async () => {
        const rawValue = tickerInput.value.trim();
        if (!rawValue) return alert("Please enter tickers.");

        const tickerList = rawValue.split(',').map(t => t.trim().toUpperCase()).filter(t => t);

        // 1. Enter Loading State
        mlBtn.innerHTML = `Computing... <span class="state-loading"></span>`;
        mlBtn.style.pointerEvents = "none";

        try {
            const response = await fetch(`${API_BASE}/run-ml-analysis`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ tickers: tickerList })
            });

            const data = await response.json();

            if (data.success) {
                // 2. Minimize the Input Area
                const inputGroup = document.querySelector('.ml-input-group');
                const description = document.querySelector('.ml-description');

                // Smoothly hide the elements
                inputGroup.style.display = 'none';
                description.style.display = 'none';

                // 3. Render the Results
                renderMLResults(data.results);
            }
        } catch (err) {
            console.error(err);
            alert("Connection error to ML Engine.");
        } finally {
            mlBtn.innerHTML = `Execute Model`;
            mlBtn.style.pointerEvents = "auto";
        }
    });
});

function renderMLResults(results) {
    const footer = document.querySelector('.ml-footer');

    // Create results container if it doesn't exist
    let resultsDiv = document.getElementById('ml-results-list');
    if (!resultsDiv) {
        resultsDiv = document.createElement('div');
        resultsDiv.id = 'ml-results-list';
        resultsDiv.className = 'ml-results-grid';
        // Insert before the footer
        footer.parentNode.insertBefore(resultsDiv, footer);
    }

    resultsDiv.innerHTML = results.map(res => {
        const color = res.probability > 70 ? 'var(--accent2)' : (res.probability > 40 ? 'var(--accent)' : 'var(--muted)');
        return `
            <div class="ml-result-item" style="border-left: 3px solid ${color}">
                <span class="ml-ticker">${res.ticker}</span>
                <div class="ml-prob-container">
                    <span class="ml-prob-val">${res.probability}%</span>
                    <div class="ml-prob-bar"><div class="ml-prob-fill" style="width: ${res.probability}%; background: ${color}"></div></div>
                </div>
            </div>
        `;
    }).join('');
}

// Your 6 functions calling the helper
function copy150Slow() { copyToClipboard(sma150Slow); }
function copy150Fast() { copyToClipboard(sma150Fast); }
function copy200Slow() { copyToClipboard(sma200Slow); }
function copy200Fast() { copyToClipboard(sma200Fast); }
function copy20Below() { copyToClipboard(sma20Below); }
function copy20Above() { copyToClipboard(sma20Above); }

fetchResults();