(function() {
    'use strict';

    var STEPS = [
        {
            id: 'face_photo_initial_data',
            icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>',
            title: 'Face à la caméra',
            instruction: 'Placez votre visage dans le cadre',
            hint: 'Regardez droit, sans bouger',
            wait: 5
        },
        {
            id: 'face_photo_left_data',
            icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M15 3l-6 6 6 6"/></svg>',
            title: 'Tournez à GAUCHE',
            instruction: 'Montrez votre profil gauche',
            hint: 'Tournez la tête vers votre gauche',
            wait: 5
        },
        {
            id: 'face_photo_right_data',
            icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M9 3l6 6-6 6"/></svg>',
            title: 'Tournez à DROITE',
            instruction: 'Montrez votre profil droit',
            hint: 'Tournez la tête vers votre droite',
            wait: 5
        },
        {
            id: 'face_photo_blink_data',
            icon: '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M9 12h.01"/><path d="M15 12h.01"/></svg>',
            title: 'Clignez des yeux',
            instruction: 'Fermez puis ouvrez les yeux',
            hint: 'Un clignement suffit',
            wait: 5
        },
    ];

    var currentStep = 0;
    var video = null;
    var canvas = null;
    var isRunning = false;
    var countdownInterval = null;

    function init() {
        var container = document.getElementById('face-capture-container');
        if (!container) return;

        canvas = document.createElement('canvas');
        canvas.style.display = 'none';
        document.body.appendChild(canvas);

        createHiddenInputs();
        container.innerHTML = buildUI();
        startCamera();

        document.getElementById('start-face-btn').addEventListener('click', function(e) {
            e.preventDefault();
            document.getElementById('start-face-btn').style.display = 'none';
            startCaptureLoop();
        });
    }

    function createHiddenInputs() {
        var form = document.querySelector('.tasker-registration-form') || document.querySelector('form');
        STEPS.forEach(function(step) {
            var inp = document.createElement('input');
            inp.type = 'hidden';
            inp.name = step.id;
            inp.id = 'hidden_' + step.id;
            inp.value = '';
            form.appendChild(inp);
        });
    }

    function buildUI() {
        return (
            '<div class="face-capture-live">' +
                '<div class="live-video-wrap">' +
                    '<video id="fv" autoplay playsinline muted></video>' +
                    '<div class="face-oval"></div>' +
                    '<div class="face-step-overlay" id="face-step-overlay">' +
                        '<div class="step-big-icon" id="step-icon"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg></div>' +
                        '<div class="step-title" id="step-title">Face à la caméra</div>' +
                        '<div class="step-instruction" id="step-instruction">Placez votre visage dans le cadre</div>' +
                        '<div class="step-hint" id="step-hint">Regardez droit, sans bouger</div>' +
                    '</div>' +
                    '<div class="countdown-circle" id="countdown-circle">' +
                        '<div class="countdown-number" id="countdown-number">5</div>' +
                    '</div>' +
                '</div>' +
                '<div class="face-progress-bar">' +
                    '<div class="face-progress-track">' +
                        '<div class="face-progress-fill" id="face-progress-fill"></div>' +
                    '</div>' +
                    '<span id="face-progress-text" class="face-progress-text">0 / 4</span>' +
                '</div>' +
                '<button type="button" id="start-face-btn" class="face-start-btn"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polygon points="5 3 19 12 5 21 5 3"/></svg> Commencer la vérification</button>' +
            '</div>'
        );
    }

    function startCamera() {
        video = document.getElementById('fv');
        if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
            document.getElementById('step-title').textContent = 'Caméra non disponible';
            return;
        }

        navigator.mediaDevices.getUserMedia({
            video: { facingMode: 'user', width: { ideal: 640 }, height: { ideal: 480 } }
        })
        .then(function(s) {
            video.srcObject = s;
        })
        .catch(function() {
            document.getElementById('step-title').textContent = 'Accès caméra refusé';
        });
    }

    function startCaptureLoop() {
        isRunning = true;
        runStep(0);
    }

    function runStep(index) {
        if (!isRunning || index >= 4) {
            completeAll();
            return;
        }

        currentStep = index;
        var step = STEPS[index];
        var overlay = document.getElementById('face-step-overlay');
        var iconEl = document.getElementById('step-icon');
        var titleEl = document.getElementById('step-title');
        var instrEl = document.getElementById('step-instruction');
        var hintEl = document.getElementById('step-hint');
        var countdownEl = document.getElementById('countdown-circle');
        var numberEl = document.getElementById('countdown-number');
        var oval = document.querySelector('.face-oval');

        iconEl.innerHTML = step.icon;
        titleEl.textContent = step.title;
        instrEl.textContent = step.instruction;
        hintEl.textContent = step.hint;

        overlay.style.display = 'flex';
        oval.style.borderColor = '#6366f1';

        countdownEl.style.display = 'none';

        setTimeout(function() {
            if (!isRunning) return;
            startCountdown(step.wait, function() {
                doCapture(index, function() {
                    setTimeout(function() {
                        overlay.style.display = 'none';
                        runStep(index + 1);
                    }, 1000);
                });
            });
        }, 1500);
    }

    function startCountdown(seconds, callback) {
        var countdownEl = document.getElementById('countdown-circle');
        var numberEl = document.getElementById('countdown-number');
        var oval = document.querySelector('.face-oval');

        var remaining = seconds;
        numberEl.textContent = remaining;
        countdownEl.style.display = 'flex';
        oval.style.borderColor = '#f59e0b';

        countdownInterval = setInterval(function() {
            remaining--;
            numberEl.innerHTML = remaining > 0 ? remaining : '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><path d="M23 19a2 2 0 0 1-2 2H3a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h4l2-3h6l2 3h4a2 2 0 0 1 2 2z"/><circle cx="12" cy="13" r="4"/></svg>';

            if (remaining <= 2) {
                countdownEl.style.borderColor = '#ef4444';
                numberEl.style.color = '#ef4444';
            }

            if (remaining <= 0) {
                clearInterval(countdownInterval);
                countdownEl.style.display = 'none';
                if (callback) callback();
            }
        }, 1000);
    }

    function doCapture(index, callback) {
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        var ctx = canvas.getContext('2d');
        ctx.drawImage(video, 0, 0);

        var flash = document.createElement('div');
        flash.className = 'capture-flash-active';
        document.querySelector('.live-video-wrap').appendChild(flash);
        setTimeout(function() { flash.remove(); }, 300);

        var base64 = canvas.toDataURL('image/jpeg', 0.92);

        var hiddenInput = document.getElementById('hidden_' + STEPS[index].id);
        if (hiddenInput) hiddenInput.value = base64;

        var oval = document.querySelector('.face-oval');
        oval.style.borderColor = '#10b981';

        var overlay = document.getElementById('face-step-overlay');
        overlay.style.display = 'flex';
        document.getElementById('step-icon').innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><polyline points="20 6 9 17 4 12"/></svg>';
        document.getElementById('step-title').textContent = 'Capturé !';
        document.getElementById('step-instruction').textContent = '';
        document.getElementById('step-hint').textContent = '';

        updateProgress();

        if (callback) callback();
    }

    function updateProgress() {
        var fill = document.getElementById('face-progress-fill');
        var text = document.getElementById('face-progress-text');
        var pct = ((currentStep + 1) / 4) * 100;
        if (fill) fill.style.width = pct + '%';
        if (text) text.textContent = (currentStep + 1) + ' / 4';
    }

    function completeAll() {
        isRunning = false;
        var overlay = document.getElementById('face-step-overlay');
        overlay.style.display = 'flex';
        document.getElementById('step-icon').innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><path d="M8 14s1.5 2 4 2 4-2 4-2"/><line x1="9" y1="9" x2="9.01" y2="9"/><line x1="15" y1="9" x2="15.01" y2="9"/></svg>';
        document.getElementById('step-title').textContent = 'Vérification terminée !';
        document.getElementById('step-instruction').textContent = '';
        document.getElementById('step-hint').textContent = '';

        var oval = document.querySelector('.face-oval');
        oval.style.borderColor = '#10b981';
        oval.style.boxShadow = '0 0 20px rgba(16, 185, 129, 0.5)';

        var btn = document.querySelector('.face-capture-submit');
        if (btn) btn.style.display = 'block';
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
