// Groww Pulse API Integration Logic

document.addEventListener('DOMContentLoaded', () => {
    // Note: We use relative URLs since the frontend is served by the same FastAPI backend
    const API_BASE = '/api';

    // Elements
    const btnGenerate = document.getElementById('btn-generate');
    const statusText = document.getElementById('generation-status');
    const errorText = document.getElementById('generation-error');
    
    const dashboard = document.getElementById('pulse-dashboard');
    const metadataLabel = document.getElementById('pulse-metadata');
    const pulseContent = document.getElementById('pulse-content');
    
    const emailForm = document.getElementById('email-form');
    const btnSendEmail = document.getElementById('btn-send-email');
    const emailStatus = document.getElementById('email-status');

    // Global state holding the last generated markdown (to send to email phase)
    let currentPulseMarkdown = "";

    // 1. Generate Pulse
    btnGenerate.addEventListener('click', async () => {
        // UI Loading State
        btnGenerate.disabled = true;
        btnGenerate.querySelector('.btn-text').textContent = 'Analyzing...';
        btnGenerate.querySelector('.btn-loader').classList.remove('hidden');
        statusText.classList.remove('hidden');
        errorText.classList.add('hidden');
        dashboard.classList.add('hidden');

        try {
            // Call the unified backend pipeline endpoint
            const response = await fetch(`${API_BASE}/generate-pulse`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || `Server error: ${response.status}`);
            }

            const data = await response.json();
            
            // On Success: Set UI State
            currentPulseMarkdown = data.pulse_markdown;
            
            // Parse Markdown to HTML for display using Marked.js
            pulseContent.innerHTML = marked.parse(currentPulseMarkdown);
            
            // Set metadata using the generated timestamp
            const dateStr = new Date(data.generated_at).toLocaleDateString('en-GB', {
                day: 'numeric', month: 'short', year: 'numeric'
            });
            metadataLabel.textContent = `Week of ${dateStr}  |  ${data.total_reviews} reviews analysed`;

            // Reveal Dashboard
            dashboard.classList.remove('hidden');

            // Scroll to it smoothly
            dashboard.scrollIntoView({ behavior: 'smooth' });

        } catch (error) {
            console.error('Generation Error:', error);
            errorText.textContent = `Pipeline Check Failed: ${error.message}. Please check backend logs.`;
            errorText.classList.remove('hidden');
        } finally {
            // Restore btn
            btnGenerate.disabled = false;
            btnGenerate.querySelector('.btn-text').textContent = 'Regenerate Pulse';
            btnGenerate.querySelector('.btn-loader').classList.add('hidden');
            statusText.classList.add('hidden');
        }
    });

    // 2. Dispatch Email
    emailForm.addEventListener('submit', async (e) => {
        e.preventDefault(); // prevent native form submission
        
        const emailInput = document.getElementById('recipient-email').value;
        if (!emailInput || !emailInput.includes('@')) return;

        // UI Loading State
        btnSendEmail.disabled = true;
        btnSendEmail.querySelector('.btn-loader').classList.remove('hidden');
        emailStatus.classList.add('hidden');
        emailStatus.className = 'status-container hidden'; // Reset classes

        try {
            const response = await fetch(`${API_BASE}/send-email`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    recipient_email: emailInput,
                    markdown_content: currentPulseMarkdown
                })
            });

            if (!response.ok) {
                const errData = await response.json();
                throw new Error(errData.detail || 'Failed to send email');
            }

            // Success UI
            emailStatus.textContent = `🚀 Report securely dispatched to ${emailInput}!`;
            emailStatus.classList.add('status-success');
            emailStatus.classList.remove('hidden');
            
            // Clear input
            document.getElementById('recipient-email').value = '';

        } catch (error) {
            console.error('Email Error:', error);
            emailStatus.textContent = `Error: ${error.message}`;
            emailStatus.classList.add('error-text');
            emailStatus.classList.remove('hidden');
        } finally {
            btnSendEmail.disabled = false;
            btnSendEmail.querySelector('.btn-loader').classList.add('hidden');
        }
    });
});
