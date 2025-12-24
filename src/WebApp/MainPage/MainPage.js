// Reveal-on-scroll using IntersectionObserver
const revealElements = document.querySelectorAll(".reveal");
const API_BASE = "https://market-scan-engine.onrender.com";
const observer = new IntersectionObserver(
    (entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add("visible");
                observer.unobserve(entry.target);
            }
        });
    },
    {
        threshold: 0.18
    }
);

revealElements.forEach((el) => observer.observe(el));

// Footer year
const yearEl = document.getElementById("year");
if (yearEl) {
    yearEl.textContent = new Date().getFullYear();
}

// Upload logic
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-btn");
const statusEl = document.getElementById("upload-status");

// Helpers
function setStatus(message, type = "info") {
    if (!statusEl) return;
    let className = "";
    if (type === "error") className = "status-error";
    else if (type === "success") className = "status-success";
    else if (type === "loading") className = "status-loading";

    statusEl.innerHTML = `<span class="${className}">${message}</span>`;
}

function isCsvFile(file) {
    if (!file) return false;
    const name = file.name.toLowerCase();
    const type = file.type.toLowerCase();
    return name.endsWith(".csv") || type === "text/csv" || type === "application/vnd.ms-excel";
}

// Handle dropzone visual state
function setDragOver(isOver) {
    if (!dropZone) return;
    if (isOver) dropZone.classList.add("drag-over");
    else dropZone.classList.remove("drag-over");
}

// File upload (client-side)
async function uploadFile(file) {
    if (!file) return;

    if (!isCsvFile(file)) {
        setStatus("Please upload a .csv file.", "error");
        return;
    }

    setStatus(`Uploading "${file.name}"…`, "loading");

    const formData = new FormData();
    formData.append("file", file);

    try {
        const response = await fetch(`${API_BASE}/upload`, {
            method: "POST",
            body: formData
        });

        const result = await response.json().catch(() => ({}));

        if (!response.ok) {
            setStatus(result.error || `Server error (${response.status})`, "error");
            return;
        }

        if (!result.success) {
            setStatus(result.error || "Upload failed (invalid CSV).", "error");
            return;
        }

        setStatus(result.message || "Upload complete.", "success");

        await callPythonWithFile(formData);

    } catch (err) {
        console.error(err);
        setStatus("Upload failed. Please try again or check the server.", "error");
    }
}


async function callPythonWithFile(formData) {
    console.log("Got HERE")
    const response = await fetch(`${API_BASE}/run_logic`, {
        method: "POST",
        body: formData
    });
    const data = await response.json().catch(() => ({}));
    localStorage.setItem(("scanResult"), JSON.stringify(data.Cup_Handle));
    window.location.href = "../ResultPage/Result.html";


}

// Browse button click opens file dialog
if (browseBtn && fileInput) {
    browseBtn.addEventListener("click", () => {
        fileInput.click();
    });

    fileInput.addEventListener("change", (e) => {
        const file = e.target.files && e.target.files[0];
        if (file) {
            uploadFile(file);
        }
        fileInput.value = ""; // reset
    });
}

// Drag & drop handling
if (dropZone && fileInput) {
    ["dragenter", "dragover"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            setDragOver(true);
        });
    });

    ["dragleave", "drop"].forEach((eventName) => {
        dropZone.addEventListener(eventName, (e) => {
            e.preventDefault();
            e.stopPropagation();
            setDragOver(false);
        });
    });

    dropZone.addEventListener("drop", (e) => {
        const dt = e.dataTransfer;
        const file = dt && dt.files && dt.files[0];
        if (file) {
            uploadFile(file);
        }
    });

    // Also allow click on the entire drop zone to open file dialog
    dropZone.addEventListener("click", () => {
        fileInput.click();
    });
}


