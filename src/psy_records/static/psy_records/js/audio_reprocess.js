// static/psy_records/js/audio_reprocess.js

class AudioReprocessSubmitter {
    constructor() {
        this.form = null;
        this.input = null;
    }

    init() {
        this.form = document.querySelector('form[method="post"]');
        this.input = document.getElementById("reprocess-audio");

        if (!this.form) return;

        this.form.addEventListener("submit", (e) => {
            if (this.input && this.input.files.length > 0) {
                e.preventDefault();
                this.submitWithAudio();
            }
            // se não há arquivo -> cai no fluxo normal (somente texto)
        });
    }

    async submitWithAudio() {
        const file = this.input.files[0];
        if (!file) return;

        this.showStatus("📤 Enviando áudio para reprocessamento...", "loading");

        try {
            const formData = new FormData(this.form);
            formData.append("reprocess_audio", file);
            formData.append("has_reprocess_audio", "true");

            const response = await fetch(this.form.action, {
                method: "POST",
                body: formData,
                headers: { "X-Requested-With": "XMLHttpRequest" }
            });

            if (response.ok) {
                if (response.redirected) {
                    window.location.href = response.url;
                    return;
                }
                const contentType = response.headers.get("content-type");
                if (contentType && contentType.includes("application/json")) {
                    const data = await response.json();
                    this.handleResponse(data);
                } else {
                    const html = await response.text();
                    document.open();
                    document.write(html);
                    document.close();
                }
            } else {
                throw new Error("HTTP erro " + response.status);
            }
        } catch (err) {
            console.error(err);
            this.showStatus("❌ Erro ao reprocessar áudio", "error");
        }
    }

    handleResponse(data) {
        if (data.success) {
            this.showStatus("✅ Prontuário reprocessado com sucesso!", "success");
            setTimeout(() => {
                if (data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                    window.location.reload();
                }
            }, 2000);
        } else {
            this.showStatus(data.message || "Erro no processamento.", "error");
        }
    }

    showStatus(message, type) {
        const status = document.getElementById("submit-status");
        if (!status) return;
        status.textContent = message;
        status.className = "submit-status " + type;
        status.classList.remove("hidden");
    }
}

document.addEventListener("DOMContentLoaded", () => {
    const re = new AudioReprocessSubmitter();
    re.init();
});