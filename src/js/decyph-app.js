function decyphApp() {
    return {
        // Constants matching Python implementation
        VER: 1,
        LOGN: 18,
        R: 8,
        P: 1,
        KEYLEN: 32,
        SALTLEN: 16,
        NONCELEN: 12,
        MIN_PW_LEN: 14,
        BASE_URL: "https://decyph.me/#",

        // State variables
        currentMode: 'encrypt',
        showAutoDecryptBanner: false,
        alertMessage: '',
        alertType: 'error',
        showAlert: false,
        showLoading: false,
        decryptionProgress: 0,
        progressInterval: null,
        
        // Password timer state
        showPasswordTimer: false,
        passwordTimeLeft: 60,
        passwordProgress: 100,
        passwordTimerInterval: null,
        
        // Encryption progress state
        showEncryptionProgress: false,
        encryptionProgress: 0,
        encryptionInterval: null,

        // Encrypt mode state
        plaintext: '',
        password1: '',
        password2: '',
        passwordStrengthText: '',
        passwordStrengthClass: '',
        showPasswordStrength: false,
        visibilityDuration: 10,
        showEncryptResult: false,
        encryptedData: '',
        shareableLink: '',

        // Decrypt mode state  
        encryptedInput: '',
        decryptPassword: '',

        // Preview mode state
        decryptedTextContent: '',
        countdownInterval: null,
        isTextRevealed: false,
        selectedDuration: 180,
        isDecryptionComplete: false,
        showRevealSection: false,
        showDecryptAgainSection: false,
        showTimerControls: true,
        countdownText: '',
        securityNoticeText: 'The decrypted text will be visible for the selected duration. After the timer expires, the text will be permanently cleared from memory for security. Closing this panel will clear decrypted text and password from memory and clipboard.',
        
        // Clipboard clearing option
        clearClipboard: true,
        
        // Sound notification options
        playEncryptSound: true,
        playDecryptSound: true,
        
        // QR code options
        useBlackQR: false,

        init() {
            this.checkLibraries();
            this.checkForAutoDecrypt();
        },

        // Utility methods
        displayAlert(message, type = 'error') {
            this.alertMessage = message;
            this.alertType = type;
            this.showAlert = true;
        },

        hideAlert() {
            this.showAlert = false;
            this.alertMessage = '';
        },

        setLoading(loading) {
            this.showLoading = loading;
            
            if (loading) {
                this.startProgressBar();
            } else {
                this.stopProgressBar();
            }
        },

        startProgressBar() {
            this.decryptionProgress = 0;
            const duration = 25000; // 15 seconds
            const interval = 100; // Update every 100ms
            const increment = (interval / duration) * 100;
            
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
            }
            
            this.progressInterval = setInterval(() => {
                this.decryptionProgress += increment;
                if (this.decryptionProgress >= 100) {
                    this.decryptionProgress = 100;
                    clearInterval(this.progressInterval);
                }
            }, interval);
        },

        stopProgressBar() {
            if (this.progressInterval) {
                clearInterval(this.progressInterval);
                this.progressInterval = null;
            }
            this.decryptionProgress = 0;
        },

        resetPasswordTimer() {
            // Clear existing timer
            if (this.passwordTimerInterval) {
                clearInterval(this.passwordTimerInterval);
            }

            // Only start timer if passwords have content
            if (!this.password1 && !this.password2) {
                this.showPasswordTimer = false;
                return;
            }

            // Start new timer
            this.passwordTimeLeft = 60;
            this.passwordProgress = 100;
            this.showPasswordTimer = true;

            this.passwordTimerInterval = setInterval(() => {
                this.passwordTimeLeft--;
                this.passwordProgress = (this.passwordTimeLeft / 60) * 100;

                if (this.passwordTimeLeft <= 0) {
                    this.clearPasswords();
                }
            }, 1000);
        },

        clearPasswords() {
            this.password1 = '';
            this.password2 = '';
            this.showPasswordTimer = false;
            this.showPasswordStrength = false;
            
            if (this.passwordTimerInterval) {
                clearInterval(this.passwordTimerInterval);
                this.passwordTimerInterval = null;
            }
        },

        startEncryptionProgress() {
            this.encryptionProgress = 0;
            this.showEncryptionProgress = true;
            const duration = 30000; // 30 seconds
            const interval = 100; // Update every 100ms
            const increment = (interval / duration) * 100;
            
            if (this.encryptionInterval) {
                clearInterval(this.encryptionInterval);
            }
            
            this.encryptionInterval = setInterval(() => {
                this.encryptionProgress += increment;
                if (this.encryptionProgress >= 100) {
                    this.encryptionProgress = 100;
                    clearInterval(this.encryptionInterval);
                }
            }, interval);
        },

        stopEncryptionProgress() {
            if (this.encryptionInterval) {
                clearInterval(this.encryptionInterval);
                this.encryptionInterval = null;
            }
            this.showEncryptionProgress = false;
            this.encryptionProgress = 0;
        },

        // Mode switching
        setMode(mode) {
            // If switching away from decrypt mode with green panel shown, clear like X button
            if (this.currentMode === 'decrypt' && this.isDecryptionComplete && mode !== 'decrypt') {
                this.decryptAgain();
                return;
            }

            // If switching away from encrypt mode with results shown, clear like X button
            if (this.currentMode === 'encrypt' && this.showEncryptResult && mode !== 'encrypt') {
                this.closeEncryptResult();
            }

            // Clear decrypt password when switching away from decrypt mode for security
            if (this.currentMode === 'decrypt' && mode !== 'decrypt') {
                this.decryptPassword = '';
            }

            // Clear encrypt passwords when switching away from encrypt mode for security
            if (this.currentMode === 'encrypt' && mode !== 'encrypt') {
                this.clearPasswords();
            }

            this.currentMode = mode;
            this.hideAlert();
            this.showEncryptResult = false;
            this.isDecryptionComplete = false;
            this.showRevealSection = false;
            this.showDecryptAgainSection = false;
        },

        closeEncryptResult() {
            this.showEncryptResult = false;
            
            // Stop all encryption operations
            this.stopEncryptionProgress();
            this.setLoading(false);
            
            // Clear memory and clipboard based on checkbox state
            this.clearMemoryAndClipboard();
        },

        clearMemoryAndClipboard(preserveDecryptInput = false) {
            // Clear sensitive data from memory
            this.plaintext = '';
            this.encryptedData = '';
            this.shareableLink = '';
            this.decryptedTextContent = '';
            
            // Only clear decrypt input if not preserving it
            if (!preserveDecryptInput) {
                this.encryptedInput = '';
            }
            
            // Always clear clipboard when X is pressed (independent of checkbox)
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText('').catch(() => {
                    // Silently fail if clipboard clearing fails
                });
            }
            
            // Force garbage collection if available
            if (window.gc) {
                window.gc();
            }
        },

        playNotificationSound() {
            try {
                // Create audio context and generate a pleasant ding sound
                const audioContext = new (window.AudioContext || window.webkitAudioContext)();
                const oscillator = audioContext.createOscillator();
                const gainNode = audioContext.createGain();
                
                // Connect oscillator to gain to output
                oscillator.connect(gainNode);
                gainNode.connect(audioContext.destination);
                
                // Configure pleasant ding sound (two-tone chime)
                oscillator.frequency.setValueAtTime(800, audioContext.currentTime);
                oscillator.frequency.setValueAtTime(600, audioContext.currentTime + 0.1);
                
                // Configure volume envelope
                gainNode.gain.setValueAtTime(0, audioContext.currentTime);
                gainNode.gain.linearRampToValueAtTime(0.3, audioContext.currentTime + 0.01);
                gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3);
                
                // Play the sound
                oscillator.start(audioContext.currentTime);
                oscillator.stop(audioContext.currentTime + 0.3);
                
            } catch (error) {
                // Silently fail if audio context not supported
            }
        },

        // Crypto functions
        normalizePassword(password) {
            return new TextEncoder().encode(password.normalize('NFC'));
        },

        isStrongPassword(password) {
            if (password.length < this.MIN_PW_LEN) return false;

            const hasLower = /[a-z]/.test(password);
            const hasUpper = /[A-Z]/.test(password);
            const hasDigit = /\d/.test(password);
            const hasSpecial = /[^a-zA-Z0-9]/.test(password);

            const classes = [hasLower, hasUpper, hasDigit, hasSpecial].filter(Boolean).length;
            return classes >= 3;
        },

        updatePasswordStrength() {
            if (!this.password1) {
                this.showPasswordStrength = false;
                return;
            }

            this.showPasswordStrength = true;

            if (this.isStrongPassword(this.password1)) {
                this.passwordStrengthClass = 'password-strength strong';
                this.passwordStrengthText = '✅ Strong password';
            } else {
                this.passwordStrengthClass = 'password-strength weak';
                const missing = [];
                if (this.password1.length < this.MIN_PW_LEN) missing.push(`at least ${this.MIN_PW_LEN} characters`);
                if (!/[a-z]/.test(this.password1)) missing.push('lowercase letters');
                if (!/[A-Z]/.test(this.password1)) missing.push('uppercase letters');
                if (!/\d/.test(this.password1)) missing.push('numbers');
                if (!/[^a-zA-Z0-9]/.test(this.password1)) missing.push('special characters');

                const classes = [
                    /[a-z]/.test(this.password1),
                    /[A-Z]/.test(this.password1),
                    /\d/.test(this.password1),
                    /[^a-zA-Z0-9]/.test(this.password1)
                ].filter(Boolean).length;

                if (classes < 3) {
                    missing.push('3 different character types');
                }

                this.passwordStrengthText = `❌ Needs: ${missing.join(', ')}`;
            }
        },

        get isEncryptFormValid() {
            return this.plaintext.trim() &&
                this.isStrongPassword(this.password1) &&
                this.password1 === this.password2;
        },

        async deriveKey(password, salt, N, r, p, keylen) {
            const passwordBytes = this.normalizePassword(password);

            if (typeof scrypt === 'undefined' || typeof scrypt.scrypt !== 'function') {
                throw new Error('Scrypt library not loaded. Please refresh the page.');
            }

            try {
                await new Promise(resolve => setTimeout(resolve, 0));
                const key = await scrypt.scrypt(passwordBytes, salt, N, r, p, keylen);
                return new Uint8Array(key);
            } catch (error) {
                throw new Error('Key derivation failed: ' + error.message);
            }
        },

        async encrypt(plaintext, password, visibilityDuration = 10) {
            try {
                this.setLoading(true);

                const salt = crypto.getRandomValues(new Uint8Array(this.SALTLEN));
                const nonce = crypto.getRandomValues(new Uint8Array(this.NONCELEN));

                const key = await this.deriveKey(password, salt, 1 << this.LOGN, this.R, this.P, this.KEYLEN);

                const encoder = new TextEncoder();
                const plaintextBytes = encoder.encode(plaintext);

                const header = new Uint8Array([this.VER, this.LOGN, this.R, this.P]);
                const aad = new Uint8Array(header.length + salt.length + nonce.length);
                aad.set(header);
                aad.set(salt, header.length);
                aad.set(nonce, header.length + salt.length);

                const cryptoKey = await crypto.subtle.importKey(
                    'raw',
                    key,
                    { name: 'AES-GCM' },
                    false,
                    ['encrypt']
                );

                const ciphertext = await crypto.subtle.encrypt(
                    {
                        name: 'AES-GCM',
                        iv: nonce,
                        additionalData: aad
                    },
                    cryptoKey,
                    plaintextBytes
                );

                const blob = new Uint8Array(header.length + salt.length + nonce.length + ciphertext.byteLength);
                blob.set(header);
                blob.set(salt, header.length);
                blob.set(nonce, header.length + salt.length);
                blob.set(new Uint8Array(ciphertext), header.length + salt.length + nonce.length);

                // Use proper URL-safe Base64 encoding to match Python's urlsafe_b64encode
                let base64 = btoa(String.fromCharCode(...blob));
                base64 = base64.replace(/\+/g, '-').replace(/\//g, '_');
                // Keep padding for compatibility with Python's urlsafe_b64decode
                
                return base64;
            } finally {
                this.setLoading(false);
            }
        },

        async decrypt(base64OrUrl, password) {
            try {
                this.setLoading(true);

                const rawBase64 = this.extractBase64FromUrl(base64OrUrl);

                // Convert URL-safe Base64 back to standard Base64 for atob()
                let base64 = rawBase64.replace(/-/g, '+').replace(/_/g, '/');

                const blob = Uint8Array.from(atob(base64), c => c.charCodeAt(0));

                if (blob.length < 4 + this.SALTLEN + this.NONCELEN) {
                    throw new Error('Data too short');
                }

                const header = blob.slice(0, 4);
                if (header[0] !== this.VER) {
                    throw new Error('Invalid version');
                }

                const N = 1 << header[1];
                const r = header[2];
                const p = header[3];

                const salt = blob.slice(4, 4 + this.SALTLEN);
                const nonce = blob.slice(4 + this.SALTLEN, 4 + this.SALTLEN + this.NONCELEN);
                const ciphertext = blob.slice(4 + this.SALTLEN + this.NONCELEN);

                const key = await this.deriveKey(password, salt, N, r, p, this.KEYLEN);

                const aad = blob.slice(0, 4 + this.SALTLEN + this.NONCELEN);

                const cryptoKey = await crypto.subtle.importKey(
                    'raw',
                    key,
                    { name: 'AES-GCM' },
                    false,
                    ['decrypt']
                );

                const plaintext = await crypto.subtle.decrypt(
                    {
                        name: 'AES-GCM',
                        iv: nonce,
                        additionalData: aad
                    },
                    cryptoKey,
                    ciphertext
                );

                const decoder = new TextDecoder();
                const decryptedData = decoder.decode(plaintext);

                // Return plain text with default duration
                return {
                    text: decryptedData,
                    isEncodedDuration: false
                };
            } finally {
                this.setLoading(false);
            }
        },

        extractBase64FromUrl(input) {
            if (input.startsWith('http://') || input.startsWith('https://')) {
                const url = new URL(decodeURIComponent(input));
                const hash = url.hash;
                if (hash.startsWith('#')) {
                    return hash.substring(1);
                }
            }
            return input;
        },

        generateQR(text) {
            const qrContainer = document.getElementById('qrCanvas');
            qrContainer.innerHTML = '';

            try {
                new QRCode(qrContainer, {
                    text: text,
                    width: 256,
                    height: 256,
                    colorDark: this.useBlackQR ? '#000000' : '#2563eb',
                    colorLight: '#ffffff',
                    correctLevel: QRCode.CorrectLevel.L
                });
            } catch (error) {
                console.error('QR Code generation failed:', error);
                qrContainer.innerHTML = '<p style="color: #dc2626;">QR Code generation failed</p>';
            }
        },

        regenerateQR() {
            if (this.shareableLink) {
                this.generateQR(this.shareableLink);
            }
        },

        // Action handlers
        async handleEncrypt() {
            try {
                this.hideAlert();

                // Store password and plaintext before clearing
                const password = this.password1;
                const plaintext = this.plaintext;

                // Clear passwords AND plaintext immediately for security
                // This also stops the password auto-clear timer to prevent unexpected clipboard clearing
                this.clearPasswords();
                this.plaintext = '';
                this.startEncryptionProgress();

                const encrypted = await this.encrypt(plaintext, password, 10); // Default 10 second duration
                const link = this.BASE_URL + encrypted;

                this.encryptedData = encrypted;
                this.shareableLink = link;
                this.showEncryptResult = true;

                this.generateQR(link);

                // Stop encryption progress
                this.stopEncryptionProgress();
                
                // Play sound notification if enabled
                if (this.playEncryptSound) {
                    this.playNotificationSound();
                }
            } catch (error) {
                this.stopEncryptionProgress();
                this.displayAlert('Encryption failed: ' + error.message);
            }
        },

        async handleDecrypt() {
            try {
                this.hideAlert();

                if (!this.encryptedInput.trim() || !this.decryptPassword) {
                    this.displayAlert('Please enter encrypted data and password');
                    return;
                }

                // Store password before clearing
                const password = this.decryptPassword;

                // Clear password immediately for security (before decryption starts)
                this.decryptPassword = '';

                // Transition to preview mode instantly
                this.isDecryptionComplete = true;

                const decryptResult = await this.decrypt(this.encryptedInput, password);

                this.decryptedTextContent = decryptResult.text;
                this.showTimerControls = !decryptResult.isEncodedDuration;

                // Show timer controls and auto-start timer with default duration
                this.showTimerControls = true;
                this.showRevealSection = true;
                this.startCountdown();

                // Play sound notification if enabled
                if (this.playDecryptSound) {
                    this.playNotificationSound();
                }

            } catch (error) {
                this.displayAlert('Decryption failed. Check your password and data.');
                // Reset to decrypt form if decryption fails
                this.isDecryptionComplete = false;
                // Password already cleared above for security
            }
        },

        // Timer functions
        selectDuration(seconds) {
            this.selectedDuration = seconds;

            if (!this.isDecryptionComplete) return;

            // Show reveal section and start countdown (keep timer controls visible)
            this.showRevealSection = true;
            this.startCountdown();
        },

        formatDuration(seconds) {
            if (seconds < 60) {
                return `${seconds} seconds`;
            } else if (seconds < 3600) {
                const minutes = Math.floor(seconds / 60);
                return `${minutes} minute${minutes > 1 ? 's' : ''}`;
            } else {
                const hours = Math.floor(seconds / 3600);
                return `${hours} hour${hours > 1 ? 's' : ''}`;
            }
        },

        startCountdown() {
            let timeLeft = this.selectedDuration;

            if (this.countdownInterval) {
                clearInterval(this.countdownInterval);
            }

            const updateDisplay = () => {
                const minutes = Math.floor(timeLeft / 60);
                const seconds = timeLeft % 60;
                const timeString = `${minutes}:${seconds.toString().padStart(2, '0')}`;

                this.countdownText = `⏰ Text will be cleared in: ${timeString}`;

                if (timeLeft <= 0) {
                    clearInterval(this.countdownInterval);

                    this.burnDecryptedData();
                }

                timeLeft--;
            };

            updateDisplay();

            this.countdownInterval = setInterval(updateDisplay, 1000);
        },

        burnDecryptedData() {
            this.decryptedTextContent = '';
            this.countdownText = '🔥 Text securely cleared from memory';
            this.showDecryptAgainSection = true;
            this.isTextRevealed = false;

            // Clear clipboard for security if option is enabled
            if (this.clearClipboard && navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText('').catch(() => {
                    // Silently fail if clipboard clearing fails
                });
            }

            if (window.gc) {
                window.gc();
            }
        },

        toggleTextReveal() {
            this.isTextRevealed = !this.isTextRevealed;
        },

        decryptAgain() {
            this.showTimerControls = true;
            this.selectedDuration = 180;
            this.isDecryptionComplete = false;
            this.showRevealSection = false;
            this.showDecryptAgainSection = false;
            
            // Stop all decryption operations
            this.stopProgressBar();
            this.setLoading(false);
            
            // Stop countdown timer
            if (this.countdownInterval) {
                clearInterval(this.countdownInterval);
                this.countdownInterval = null;
            }
            
            // Reset text reveal state
            this.isTextRevealed = false;
            
            // Clear memory and clipboard, but preserve decrypt input if from URL
            this.clearMemoryAndClipboard(true);
            
            // Check if we should restore URL-based encrypted input
            this.checkForAutoDecrypt();
        },

        async copyToClipboard(text, event) {
            try {
                await navigator.clipboard.writeText(text);
                
                // Show popup notification
                this.showCopyPopup(event.target);
                
            } catch (error) {
                this.displayAlert('Failed to copy to clipboard');
            }
        },

        showCopyPopup(button) {
            // Create popup element
            const popup = document.createElement('div');
            popup.className = 'copy-popup';
            popup.textContent = 'Copied to clipboard!';
            
            // Position popup relative to button
            const rect = button.getBoundingClientRect();
            popup.style.position = 'fixed';
            popup.style.left = rect.left + (rect.width / 2) + 'px';
            popup.style.top = rect.top - 40 + 'px';
            popup.style.transform = 'translateX(-50%)';
            
            // Add to DOM
            document.body.appendChild(popup);
            
            // Animate in
            setTimeout(() => popup.classList.add('show'), 10);
            
            // Remove after delay
            setTimeout(() => {
                popup.classList.remove('show');
                setTimeout(() => {
                    if (popup.parentNode) {
                        popup.parentNode.removeChild(popup);
                    }
                }, 300);
            }, 2000);
        },

        checkLibraries() {
            if (typeof scrypt === 'undefined' || typeof scrypt.scrypt !== 'function') {
                this.displayAlert('Scrypt library failed to load. Please refresh the page.');
                return false;
            }
            if (typeof QRCode === 'undefined') {
                this.displayAlert('QR Code library failed to load. Please refresh the page.');
                return false;
            }
            return true;
        },

        checkForAutoDecrypt() {
            const url = window.location.href;
            const hashIndex = url.indexOf('#');

            if (hashIndex !== -1) {
                const fragment = url.substring(hashIndex + 1);
                if (fragment && fragment.length > 10) {
                    this.setMode('decrypt');
                    this.showAutoDecryptBanner = true;
                    this.encryptedInput = url;
                }
            }
        }
    }
}
