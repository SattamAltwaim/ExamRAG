const API_BASE = "http://localhost:8000";

let cameraStream = null;
let capturedImageData = null;

document.addEventListener("DOMContentLoaded", loadCourses);

async function loadCourses() {
    try {
        const res = await fetch(`${API_BASE}/api/courses`);
        const data = await res.json();
        const dropdown = document.getElementById("topic-dropdown");
        data.courses.forEach((topic) => {
            const opt = document.createElement("option");
            opt.value = topic;
            opt.textContent = topic;
            dropdown.appendChild(opt);
        });
    } catch {
        // Backend not running yet — topics will be empty
    }
}

function showSection(name) {
    document.querySelectorAll(".section").forEach((s) => s.classList.remove("active"));
    document.getElementById(`${name}-section`).classList.add("active");
}

async function startCamera() {
    try {
        cameraStream = await navigator.mediaDevices.getUserMedia({
            video: { facingMode: "environment", width: { ideal: 1920 }, height: { ideal: 1080 } },
        });
        const video = document.getElementById("camera-feed");
        video.srcObject = cameraStream;
        video.style.display = "block";
        document.getElementById("camera-placeholder").style.display = "none";
        document.getElementById("btn-start-camera").style.display = "none";
        document.getElementById("btn-capture").style.display = "flex";
    } catch {
        alert("Could not access camera. Please use the upload option instead.");
    }
}

function stopCamera() {
    if (cameraStream) {
        cameraStream.getTracks().forEach((t) => t.stop());
        cameraStream = null;
    }
    const video = document.getElementById("camera-feed");
    video.srcObject = null;
    video.style.display = "none";
}

function captureImage() {
    const video = document.getElementById("camera-feed");
    const canvas = document.getElementById("capture-canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext("2d").drawImage(video, 0, 0);
    capturedImageData = canvas.toDataURL("image/jpeg", 0.85);
    stopCamera();
    showPreview(capturedImageData);
}

function handleFileUpload(event) {
    const file = event.target.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (e) => {
        capturedImageData = e.target.result;
        showPreview(capturedImageData);
    };
    reader.readAsDataURL(file);
}

function showPreview(dataUrl) {
    const preview = document.getElementById("preview-image");
    preview.src = dataUrl;
    preview.style.display = "block";
    document.getElementById("camera-placeholder").style.display = "none";
    document.getElementById("camera-feed").style.display = "none";
    document.getElementById("btn-start-camera").style.display = "none";
    document.getElementById("btn-capture").style.display = "none";
    document.getElementById("btn-upload").style.display = "none";
    document.getElementById("preview-controls").style.display = "block";
}

function retake() {
    capturedImageData = null;
    document.getElementById("preview-image").style.display = "none";
    document.getElementById("preview-image").src = "";
    document.getElementById("camera-placeholder").style.display = "";
    document.getElementById("btn-start-camera").style.display = "";
    document.getElementById("btn-upload").style.display = "";
    document.getElementById("preview-controls").style.display = "none";
    document.getElementById("file-input").value = "";
    stopCamera();
}

async function gradeExam() {
    if (!capturedImageData) return;

    showSection("loading");
    const statusEl = document.getElementById("loading-status");

    const steps = [
        "Reading exam paper...",
        "Extracting questions and answers...",
        "Retrieving course content...",
        "Grading answers...",
        "Preparing results...",
    ];
    let step = 0;
    const statusInterval = setInterval(() => {
        step = Math.min(step + 1, steps.length - 1);
        statusEl.textContent = steps[step];
    }, 4000);

    try {
        const topic = document.getElementById("topic-dropdown").value;
        const res = await fetch(`${API_BASE}/api/grade`, {
            method: "POST",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ image: capturedImageData, course_topic: topic || null }),
        });

        clearInterval(statusInterval);

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            throw new Error(err.detail || "Grading failed");
        }

        const data = await res.json();
        renderResults(data);
        showSection("results");
    } catch (err) {
        clearInterval(statusInterval);
        showSection("upload");
        alert(`Grading failed: ${err.message}`);
    }
}

function renderResults(data) {
    // Student name
    const nameEl = document.getElementById("student-name-display");
    if (data.student_name) {
        nameEl.textContent = data.student_name;
        nameEl.style.display = "block";
    } else {
        nameEl.style.display = "none";
    }

    // Score circle
    const pct = data.percentage;
    const ring = document.getElementById("score-ring");
    const circumference = 339.292;
    const offset = circumference - (pct / 100) * circumference;

    let color = getComputedStyle(document.documentElement).getPropertyValue("--success").trim();
    if (pct < 50) color = getComputedStyle(document.documentElement).getPropertyValue("--danger").trim();
    else if (pct < 70) color = getComputedStyle(document.documentElement).getPropertyValue("--warning").trim();

    ring.style.stroke = color;
    // Trigger animation
    requestAnimationFrame(() => {
        ring.style.strokeDashoffset = offset;
    });

    // Animate percentage number
    animateNumber("score-percentage", 0, Math.round(pct), 1200);

    document.getElementById("score-fraction").textContent = `${data.total_score} / ${data.max_total_score}`;

    // Questions
    const list = document.getElementById("questions-list");
    list.innerHTML = "";

    data.questions.forEach((q) => {
        const ratio = q.score / q.max_score;
        let tier = "high";
        if (ratio < 0.5) tier = "low";
        else if (ratio < 0.7) tier = "mid";

        const demonstrated = q.concepts_demonstrated || [];
        const expected = q.key_concepts_expected || [];
        const missing = expected.filter((c) => !demonstrated.includes(c));

        const card = document.createElement("div");
        card.className = "question-card";
        card.innerHTML = `
            <div class="q-header">
                <span class="q-number">Question ${q.question_number}</span>
                <span class="q-score ${tier}">${q.score} / ${q.max_score}</span>
            </div>
            <div class="q-question">${escapeHtml(q.question_text)}</div>
            <div class="q-answer">${escapeHtml(q.student_answer)}</div>
            <div class="q-feedback">${escapeHtml(q.feedback)}</div>
            <div class="q-concepts">
                ${demonstrated.map((c) => `<span class="concept-tag">${escapeHtml(c)}</span>`).join("")}
                ${missing.map((c) => `<span class="concept-tag missing">${escapeHtml(c)}</span>`).join("")}
            </div>
            ${q.sources_used ? `<div class="q-sources">Sources: ${q.sources_used.join(", ")}</div>` : ""}
        `;
        list.appendChild(card);
    });
}

function animateNumber(elementId, from, to, duration) {
    const el = document.getElementById(elementId);
    const start = performance.now();
    function update(now) {
        const progress = Math.min((now - start) / duration, 1);
        const eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.round(from + (to - from) * eased);
        if (progress < 1) requestAnimationFrame(update);
    }
    requestAnimationFrame(update);
}

function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
}

function gradeAnother() {
    // Reset score animation
    document.getElementById("score-ring").style.strokeDashoffset = 339.292;
    document.getElementById("score-percentage").textContent = "0";
    retake();
    showSection("upload");
}
