//const API_BASE = "https://market-scan-engine.onrender.com";
const API_BASE = "http://127.0.0.1:8000";

// ── Helpers ──────────────────────────────────────────────────────────────────

function renderStocks(bodyId, badgeId, stocks) {
    const body = document.getElementById(bodyId);
    const badge = document.getElementById(badgeId);

    if (!Array.isArray(stocks) || stocks.length === 0) {
        body.innerHTML = '<span class="state-empty">No stocks found</span>';
        badge.textContent = '0';
        return;
    }

    badge.textContent = stocks.length;

    const pillsHtml = stocks
        .map(s => `<span class="stock-pill">${s}</span>`)
        .join('');

    body.innerHTML = `<div class="stock-list">${pillsHtml}</div>`;
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

        renderStocks('body-cup-handle', 'badge-cup-handle', cupHandle?.stocks);
        renderStocks('body-double-bottom', 'badge-double-bottom', doubleBottom?.stocks);
        renderStocks('body-150-slow', 'badge-150-slow', close150Slow?.stocks);
        renderStocks('body-150-3atr', 'badge-150-3atr', close150_3atr?.stocks);
        renderStocks('body-200-slow', 'badge-200-slow', close200Slow?.stocks);
        renderStocks('body-200-3atr', 'badge-200-3atr', close200_3atr?.stocks);
        renderStocks('body-above-20', 'badge-above-20', above20?.stocks);
        renderStocks('body-below-20', 'badge-below-20', below20?.stocks);

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

fetchResults();