
//const API_BASE = window.CONFIG.API_BASE;
const API_BASE = "https://market-scan-engine.onrender.com";



// 1. CONFIGURATION
// Switch this to your Back4App URL when deploying
//const API_BASE = "http://127.0.0.1:8000";

// 2. UI ELEMENTS
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-btn");
const statusEl = document.getElementById("upload-status");
const revealElements = document.querySelectorAll(".reveal");

// 3. REVEAL ANIMATION (Intersection Observer)
const revealObserver = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
        if (entry.isIntersecting) {
            entry.target.classList.add("visible");
            revealObserver.unobserve(entry.target);
        }
    });
}, { threshold: 0.18 });

revealElements.forEach((el) => revealObserver.observe(el));

// 4. HELPERS
function setStatus(message, type = "info") {
    if (!statusEl) return;
    statusEl.style.display = "block"; // Ensure it's visible

    let icon = "⚙️";
    let className = "status-loading";

    if (type === "error") {
        icon = "❌";
        className = "status-error";
    } else if (type === "success") {
        icon = "✅";
        className = "status-success";
    }

    statusEl.innerHTML = `
        <div class="status-wrapper ${className}">
            <span>${icon}</span> ${message}
        </div>
    `;
}

function isCsvFile(file) {
    if (!file) return false;
    const name = file.name.toLowerCase();
    const type = file.type.toLowerCase();
    return name.endsWith(".csv") || type === "text/csv" || type === "application/vnd.ms-excel";
}

// 5. UPLOAD & LOGIC EXECUTION
async function handleFileUpload(file) {
    if (!file) return;

    if (!isCsvFile(file)) {
        setStatus("Invalid file type. Please provide a .csv file.", "error");
        return;
    }

    setStatus(`Uploading ${file.name}...`, "loading");

    const formData = new FormData();
    formData.append("file", file);

    try {
        // --- STEP 1: UPLOAD ---
        const uploadResponse = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData
        });

        if (!uploadResponse.ok) {
            const errorData = await uploadResponse.json().catch(() => ({}));
            throw new Error(errorData.error || `Upload failed (${uploadResponse.status})`);
        }

        setStatus("Analyzing market data...", "loading");

        // --- STEP 2: RUN LOGIC ---
        const runResponse = await fetch(`${API_BASE}/run_logic`, {
            method: "POST",
            body: formData
        });

        if (!runResponse.ok) {
            throw new Error("Pattern recognition failed.");
        }

        const data = await runResponse.json();

        if (data.result_id) {
            setStatus("Success! Redirecting to Terminal...", "success");
            localStorage.setItem("resultId", JSON.stringify(data.result_id));

            // Short delay so user sees the success message
            setTimeout(() => {
                window.location.href = `../ResultPage/Result.html?id=${data.result_id}`;
            }, 1000);
        } else {
            throw new Error("Backend did not return a Result ID.");
        }

    } catch (err) {
        console.error("Pipeline Error:", err);
        setStatus(err.message, "error");
    }
}

// 6. EVENT LISTENERS
if (browseBtn && fileInput) {
    browseBtn.addEventListener("click", (e) => {
        e.preventDefault();
        fileInput.click();
    });

    fileInput.addEventListener("change", (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

if (dropZone) {
    // Prevent defaults for drag events
    ["dragenter", "dragover", "dragleave", "drop"].forEach(name => {
        dropZone.addEventListener(name, (e) => {
            e.preventDefault();
            e.stopPropagation();
        });
    });

    // Visual states
    dropZone.addEventListener("dragover", () => dropZone.classList.add("drag-over"));
    dropZone.addEventListener("dragleave", () => dropZone.classList.remove("drag-over"));

    dropZone.addEventListener("drop", (e) => {
        dropZone.classList.remove("drag-over");
        const file = e.dataTransfer.files[0];
        handleFileUpload(file);
    });

    // Make entire zone clickable
    dropZone.addEventListener("click", (e) => {
        if (e.target !== browseBtn) fileInput.click();
    });
}

// 7. FOOTER
const yearEl = document.getElementById("year");
if (yearEl) yearEl.textContent = new Date().getFullYear();