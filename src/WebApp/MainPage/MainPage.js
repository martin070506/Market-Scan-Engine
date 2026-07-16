import { auth, API_BASE } from "../../env_Files/firebase.js";

auth.onAuthStateChanged(async (user) => {
    if (!user) {
        // No user is signed in, redirect to login
        window.location.href = "../LoginPage/login.html";
    } else {
        // User is logged in! Update UI safely
        const sessionNameEl = document.getElementById("User-Session-Name");
        if (sessionNameEl) {
            sessionNameEl.textContent = `User: ${user.email}`;
        }
        else {
            console.error("User-Session-Name element not found in the DOM.");
        }


    }
});

async function logout() {
    try {
        await auth.signOut();
        // Clear application state flags safely
        sessionStorage.removeItem("username");
        sessionStorage.removeItem("DidUserScanBool");
        localStorage.removeItem("resultId");

        // Redirect to login page
        window.location.href = "../LoginPage/login.html";
    } catch (error) {
        console.error("Error signing out:", error);
        alert("Failed to log out. Please try again.");
    }
}

const username = sessionStorage.getItem("username");
sessionStorage.removeItem("DidUserScanBool"); // Clear this flag on main page load
const sessionNameEl = document.getElementById("User-Session-Name");
if (sessionNameEl) {
    sessionNameEl.textContent = `User: ${username}`;
}

// 1. CONFIGURATION


// 2. UI ELEMENTS
const dropZone = document.getElementById("drop-zone");
const fileInput = document.getElementById("file-input");
const browseBtn = document.getElementById("browse-btn");
const statusEl = document.getElementById("upload-status");
const revealElements = document.querySelectorAll(".reveal");

const logoutBtn = document.getElementById("logout-btn");
if (logoutBtn) {
    logoutBtn.addEventListener("click", logout);
}

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
    statusEl.style.display = "block";

    let className = "status-loading";
    if (type === "error") className = "status-error";
    else if (type === "success") className = "status-success";

    // 1. Clean out the old HTML content completely
    statusEl.replaceChildren();

    // 2. Build the structural elements programmatically
    const wrapper = document.createElement("div");
    wrapper.className = `status-wrapper ${className}`;

    // 3. SECURE: textContent safely escapes raw text, preventing XSS
    wrapper.textContent = message;

    statusEl.appendChild(wrapper);
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

        //Check for rate limit of uploading response first
        if (uploadResponse.status === 429) {
            alert("Too many requests from this device! Please wait a minute before analyzing more tickers.");
            return;
        }

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
        //Check for rate limit of running logic response first
        if (runResponse.status === 429) {
            alert("Too many requests from this device! Please wait a minute before analyzing more tickers.");
            return;
        }

        if (!runResponse.ok) {
            throw new Error("Pattern recognition failed.");
        }

        const data = await runResponse.json();

        if (data.result_id) {
            setStatus("Success! Redirecting to Terminal...", "success");
            localStorage.setItem("resultId", JSON.stringify(data.result_id));

            // Short delay so user sees the success message
            setTimeout(() => {
                sessionStorage.setItem("DidUserScanBool", true);
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