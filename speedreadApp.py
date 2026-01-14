from flask import Flask, render_template_string, request, jsonify
import pypdf
import io
import re
import os

app = Flask(__name__, static_folder='static')

HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>PDF Speed Reader</title>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.min.js"></script>
    <script>
        // Check if PDF.js loaded
        if (typeof pdfjsLib !== 'undefined') {
            pdfjsLib.GlobalWorkerOptions.workerSrc = 'https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/pdf.worker.min.js';
            console.log('PDF.js loaded successfully');
        } else {
            console.error('PDF.js failed to load');
        }
    </script>
    <style>
        :root {
            --bg-primary: #f8f9fa;
            --bg-secondary: #ffffff;
            --bg-tertiary: #fafafa;
            --text-primary: #1a1a1a;
            --text-secondary: #666;
            --border-color: #d0d0d0;
            --accent-color: #2d8659;
            --accent-dark: #1f5a3d;
            --accent-light: #c92a2a;
            --color-red: #c92a2a;
            --color-orange: #d97706;
            --color-yellow: #b8860b;
            --color-green: #059669;
            --color-blue: #2563eb;
            --slider-color: #5b9fb5;
        }
        
        [data-theme="dark"] {
            --bg-primary: #1a1a1a;
            --bg-secondary: #2d2d2d;
            --bg-tertiary: #3a3a3a;
            --text-primary: #e9e9e9;
            --text-secondary: #b0b0b0;
            --border-color: #555;
            --accent-color: #4a9f6f;
            --accent-dark: #2d8659;
            --accent-light: #ff6b6b;
            --color-red: #ff6b6b;
            --color-orange: #fb923c;
            --color-yellow: #eab308;
            --color-green: #10b981;
            --color-blue: #3b82f6;
            --slider-color: #64b5d6;
        }
        
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
            background: linear-gradient(135deg, var(--bg-primary) 0%, var(--bg-tertiary) 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            color: var(--text-primary);
            transition: background 0.3s ease;
            gap: 20px;
        }
        .main-layout {
            display: flex;
            gap: 20px;
            width: 100%;
            max-width: 1400px;
            align-items: flex-start;
            overflow: hidden;
        }
        .container {
            background: var(--bg-secondary);
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            flex: 1;
            min-width: 0;
            padding: 30px 40px;
            transition: background 0.3s ease, box-shadow 0.3s ease;
        }
        .pdf-sidebar {
            width: 300px;
            min-width: 200px;
            max-width: 600px;
            background: var(--bg-secondary);
            border-radius: 16px;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
            padding: 20px;
            max-height: 90vh;
            overflow-y: auto;
            transition: background 0.3s ease, box-shadow 0.3s ease;
            display: none;
        }
        .pdf-sidebar.active {
            display: block;
        }
        .pdf-sidebar h3 {
            margin-bottom: 15px;
            font-size: 16px;
            color: var(--text-primary);
            text-align: center;
        }
        .pdf-page-container {
            position: relative;
            margin-bottom: 15px;
            border: 2px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            background: white;
        }
        .pdf-page-container canvas {
            width: 100%;
            height: auto;
            display: block;
        }
        .pdf-page-label {
            position: absolute;
            top: 5px;
            right: 5px;
            background: rgba(0, 0, 0, 0.7);
            color: white;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 11px;
            font-weight: bold;
        }
        .word-highlight-overlay {
            position: absolute;
            background: rgba(91, 159, 181, 0.4);
            border: 2px solid var(--slider-color);
            pointer-events: none;
            border-radius: 3px;
            transition: all 0.3s ease;
        }
        .pdf-sidebar::-webkit-scrollbar {
            width: 8px;
        }
        .pdf-sidebar::-webkit-scrollbar-track {
            background: var(--bg-tertiary);
            border-radius: 4px;
        }
        .pdf-sidebar::-webkit-scrollbar-thumb {
            background: var(--slider-color);
            border-radius: 4px;
        }
        .pdf-sidebar::-webkit-scrollbar-thumb:hover {
            background: var(--accent-color);
        }
        .logo-section {
            display: flex;
            justify-content: center;
            margin-bottom: 10px;
        }
        .logo {
            height: 180px;
            width: auto;
            border-radius: 8px;
            transition: transform 0.3s ease;
        }
        .logo:hover {
            transform: scale(1.05);
        }
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 15px;
            gap: 12px;
        }
        .upload-section {
            margin: 0;
            padding: 6px 10px;
            border: 2px dashed var(--border-color);
            border-radius: 8px;
            text-align: center;
            background: var(--bg-tertiary);
            transition: all 0.3s ease;
        }
        .upload-section p {
            color: var(--text-secondary);
            margin-top: 2px;
            font-size: 11px;
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
        }
        .color-buttons {
            display: flex;
            gap: 6px;
            justify-content: center;
            margin: 0;
            flex-wrap: nowrap;
        }
        .color-btn {
            padding: 8px 12px;
            border: 3px solid transparent;
            border-radius: 6px;
            cursor: pointer;
            font-weight: 600;
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
            font-size: 12px;
            text-transform: capitalize;
            transition: all 0.3s ease;
            white-space: nowrap;
        }
        .color-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.2);
        }
        .color-btn.active {
            border-color: var(--text-primary);
            box-shadow: 0 0 0 3px var(--bg-secondary);
        }
        .color-btn.red {
            background: var(--color-red);
            color: white;
        }
        .color-btn.orange {
            background: var(--color-orange);
            color: white;
        }
        .color-btn.yellow {
            background: var(--color-yellow);
            color: #1a1a1a;
        }
        .color-btn.green {
            background: var(--color-green);
            color: white;
        }
        .color-btn.blue {
            background: var(--color-blue);
            color: white;
        }
            background: var(--bg-tertiary);
            border: 2px solid var(--border-color);
            border-radius: 8px;
            padding: 8px 12px;
            cursor: pointer;
            font-size: 14px;
            color: var(--text-primary);
            transition: all 0.3s ease;
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
            font-weight: 600;
            white-space: nowrap;
        }
        .controls {
            margin: 50px 0 40px 0;
        }
        .control-group {
            margin: 30px 0;
        }
        label {
            display: block;
            margin-bottom: 12px;
            font-weight: 600;
            color: var(--text-primary);
            font-size: 14px;
            text-transform: uppercase;
            letter-spacing: 0.5px;
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
        }
        input[type="range"] {
            width: 100%;
            height: 8px;
            border-radius: 4px;
            background: linear-gradient(to right, var(--border-color) 0%, var(--border-color) 100%);
            outline: none;
            -webkit-appearance: none;
            appearance: none;
        }
        input[type="range"]::-webkit-slider-thumb {
            -webkit-appearance: none;
            appearance: none;
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--slider-color);
            cursor: pointer;
            box-shadow: 0 2px 8px rgba(91, 159, 181, 0.3);
            transition: box-shadow 0.2s ease;
        }
        input[type="range"]::-webkit-slider-thumb:hover {
            box-shadow: 0 4px 12px rgba(91, 159, 181, 0.5);
        }
        input[type="range"]::-moz-range-thumb {
            width: 24px;
            height: 24px;
            border-radius: 50%;
            background: var(--slider-color);
            cursor: pointer;
            border: none;
            box-shadow: 0 2px 8px rgba(91, 159, 181, 0.3);
            transition: box-shadow 0.2s ease;
        }
        input[type="range"]::-moz-range-thumb:hover {
            box-shadow: 0 4px 12px rgba(91, 159, 181, 0.5);
        }
        .slider-label {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 8px;
        }
        .jump-to-word {
            display: flex;
            gap: 8px;
            align-items: center;
            margin-top: 10px;
        }
        .jump-to-word input {
            width: 80px;
            padding: 6px 8px;
            border: 2px solid var(--border-color);
            border-radius: 6px;
            background: var(--bg-tertiary);
            color: var(--text-primary);
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
            font-size: 12px;
            transition: border-color 0.3s ease;
        }
        .jump-to-word input:focus {
            outline: none;
            border-color: var(--slider-color);
        }
        .jump-to-word button {
            padding: 6px 12px;
            font-size: 12px;
            background: var(--slider-color);
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
            font-weight: 600;
            transition: opacity 0.3s ease;
        }
        .jump-to-word button:hover {
            opacity: 0.9;
        }
        .buttons {
            display: flex;
            gap: 12px;
            justify-content: center;
            margin: 40px 0;
        }
        button {
            padding: 14px 36px;
            font-size: 16px;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            font-weight: 600;
            transition: all 0.3s ease;
            letter-spacing: 0.5px;
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
        }
        #playPauseBtn {
            background: linear-gradient(135deg, var(--accent-color) 0%, var(--accent-dark) 100%);
            color: white;
            min-width: 120px;
            box-shadow: 0 4px 12px rgba(45, 134, 89, 0.3);
        }
        #playPauseBtn:hover:not(:disabled) {
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(45, 134, 89, 0.4);
        }
        #playPauseBtn:disabled {
            background: var(--border-color);
            cursor: not-allowed;
            box-shadow: none;
        }
        .info {
            text-align: center;
            color: var(--text-secondary);
            margin: 25px 0;
            font-size: 15px;
            font-weight: 500;
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
        }
        .stats-section {
            margin: 12px 0;
            padding: 12px;
            background: var(--bg-tertiary);
            border-radius: 12px;
            border: 1px solid var(--border-color);
        }
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 8px;
        }
        .stat-item {
            text-align: center;
            padding: 8px;
        }
        .stat-value {
            font-size: 18px;
            font-weight: 700;
            color: var(--accent-color);
            margin-bottom: 2px;
        }
        .stat-label {
            font-size: 10px;
            color: var(--text-secondary);
            text-transform: uppercase;
            letter-spacing: 0.3px;
            font-weight: 600;
        }
        #wordDisplay {
            font-size: 96px;
            min-height: 140px;
            margin: 25px 0 15px 0;
            font-weight: 600;
            color: var(--text-primary);
            font-family: 'Bahnschrift', 'DIN Alternate', 'Franklin Gothic Medium', 'Nimbus Sans Narrow', sans-serif-condensed, sans-serif;
            letter-spacing: 1px;
            position: relative;
            display: flex;
            align-items: center;
            justify-content: center;
            line-height: 1.2;
            transition: color 0.3s ease;
        }
        .word-container {
            display: inline-block;
            white-space: nowrap;
        }
        .orp {
            color: var(--accent-light);
            font-weight: 700;
        }
    </style>
</head>
<body>
    <div class="main-layout">
        <div class="container">
            <div class="logo-section">
                <img id="logoImage" src="/static/speedread_logo.png" alt="Speed Reader Logo" class="logo">
            </div>
        
        <div class="header">
            <div class="upload-section">
                <input type="file" id="pdfFile" accept=".pdf">
                <p>Upload a PDF to begin</p>
            </div>
            <div class="color-buttons">
                <button class="color-btn red active" data-color="0">Red</button>
                <button class="color-btn orange" data-color="1">Orange</button>
                <button class="color-btn yellow" data-color="2">Yellow</button>
                <button class="color-btn green" data-color="3">Green</button>
                <button class="color-btn blue" data-color="4">Blue</button>
            </div>
            <button class="theme-toggle" id="themeToggle">🌙 Dark Mode</button>
        </div>

        <div id="readerSection" class="hidden">
            <div id="statsSection" class="stats-section hidden">
                <div class="stats-grid">
                    <div class="stat-item">
                        <div class="stat-value" id="statTotalWords">0</div>
                        <div class="stat-label">Total Words</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="statUniqueWords">0</div>
                        <div class="stat-label">Unique Words</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="statDiversity">0%</div>
                        <div class="stat-label">Lexical Diversity</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="statAvgWordLen">0</div>
                        <div class="stat-label">Avg Word Length</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="statAvgSentenceLen">0</div>
                        <div class="stat-label">Avg Sentence Length</div>
                    </div>
                    <div class="stat-item">
                        <div class="stat-value" id="statReadingLevel">0</div>
                        <div class="stat-label">Reading Level</div>
                    </div>
                </div>
            </div>
            
            <div id="wordDisplay">Ready</div>
            
            <div class="info">
                <span>Word <span id="currentWord">0</span> of <span id="totalWords">0</span></span>
            </div>

            <div class="buttons">
                <button id="playPauseBtn" disabled>Play</button>
            </div>

            <div class="controls">
                <div class="control-group">
                    <div class="slider-label">
                        <label for="wpmSlider">Speed: <span id="wpmValue">300</span> WPM</label>
                    </div>
                    <input type="range" id="wpmSlider" min="50" max="1000" value="300" step="10">
                </div>

                <div class="control-group">
                    <div class="slider-label">
                        <label for="fontSizeSlider">Text Size: <span id="fontSizeValue">96</span>px</label>
                    </div>
                    <input type="range" id="fontSizeSlider" min="48" max="150" value="96" step="2">
                </div>

                <div class="control-group">
                    <div class="slider-label">
                        <label for="positionSlider">Position: <span id="positionValue">1</span> / <span id="totalWordsLabel">0</span></label>
                    </div>
                    <input type="range" id="positionSlider" min="0" max="100" value="0" step="1">
                    <div class="jump-to-word">
                        <label for="jumpInput" style="font-size: 12px; margin: 0;">Jump to word:</label>
                        <input type="number" id="jumpInput" placeholder="Word #" min="1">
                        <button id="jumpBtn">Go</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <script>
        let words = [];
        let currentIndex = 0;
        let isPlaying = false;
        let intervalId = null;
        let wpm = 300;
        let currentColorIndex = 0;
        const colorNames = ['red', 'orange', 'yellow', 'green', 'blue'];
        const colors = {
            red: 'var(--color-red)',
            orange: 'var(--color-orange)',
            yellow: 'var(--color-yellow)',
            green: 'var(--color-green)',
            blue: 'var(--color-blue)'
        };

        const pdfFile = document.getElementById('pdfFile');
        const wordDisplay = document.getElementById('wordDisplay');
        const playPauseBtn = document.getElementById('playPauseBtn');
        const wpmSlider = document.getElementById('wpmSlider');
        const wpmValue = document.getElementById('wpmValue');
        const positionSlider = document.getElementById('positionSlider');
        const currentWordSpan = document.getElementById('currentWord');
        const totalWordsSpan = document.getElementById('totalWords');
        const readerSection = document.getElementById('readerSection');
        const statsSection = document.getElementById('statsSection');
        const fontSizeSlider = document.getElementById('fontSizeSlider');
        const fontSizeValue = document.getElementById('fontSizeValue');
        const positionValue = document.getElementById('positionValue');
        const totalWordsLabel = document.getElementById('totalWordsLabel');
        const jumpInput = document.getElementById('jumpInput');
        const jumpBtn = document.getElementById('jumpBtn');

        // PDF Preview variables
        let pdfDoc = null;
        let pdfPages = [];
        let wordPositions = [];
        const pdfSidebar = document.getElementById('pdfSidebar');
        const pdfPagesContainer = document.getElementById('pdfPagesContainer');

        // Color buttons
        const colorButtons = document.querySelectorAll('.color-btn');
        const savedColorIndex = localStorage.getItem('highlightColorIndex') || '0';
        currentColorIndex = parseInt(savedColorIndex);
        
        // Set active button on load
        colorButtons.forEach(btn => {
            if (btn.dataset.color === savedColorIndex) {
                btn.classList.add('active');
            }
        });
        
        colorButtons.forEach(btn => {
            btn.addEventListener('click', () => {
                colorButtons.forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
                currentColorIndex = parseInt(btn.dataset.color);
                localStorage.setItem('highlightColorIndex', currentColorIndex);
                updateDisplay();
            });
        });

        pdfFile.addEventListener('change', async (e) => {
            const file = e.target.files[0];
            if (!file) return;

            const formData = new FormData();
            formData.append('pdf', file);

            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                
                if (data.words && data.words.length > 0) {
                    words = data.words;
                    currentIndex = 0;
                    updateDisplay();
                    readerSection.classList.remove('hidden');
                    statsSection.classList.remove('hidden');
                    playPauseBtn.disabled = false;
                    positionSlider.max = words.length - 1;
                    totalWordsSpan.textContent = words.length;
                    totalWordsLabel.textContent = words.length;
                    jumpInput.max = words.length;
                    
                    // Calculate and display statistics
                    calculateAndDisplayStats(data.words, data.originalText);
                    
                    // Render PDF preview (completely optional, non-blocking)
                    setTimeout(() => {
                        if (typeof renderPDFPreview === 'function') {
                            renderPDFPreview(file).catch(err => {
                                console.error('PDF preview failed:', err);
                            });
                        }
                    }, 100);
                } else {
                    alert('No text found in PDF');
                }
            } catch (error) {
                alert('Error processing PDF: ' + error.message);
            }
        });

        playPauseBtn.addEventListener('click', () => {
            if (isPlaying) {
                pause();
            } else {
                play();
            }
        });

        wpmSlider.addEventListener('input', (e) => {
            wpm = parseInt(e.target.value);
            wpmValue.textContent = wpm;
            if (isPlaying) {
                pause();
                play();
            }
        });

        fontSizeSlider.addEventListener('input', (e) => {
            const fontSize = parseInt(e.target.value);
            fontSizeValue.textContent = fontSize;
            wordDisplay.style.fontSize = fontSize + 'px';
        });

        positionSlider.addEventListener('input', (e) => {
            currentIndex = parseInt(e.target.value);
            positionValue.textContent = currentIndex + 1;
            updateDisplay();
        });

        jumpBtn.addEventListener('click', () => {
            const jumpTo = parseInt(jumpInput.value);
            if (jumpTo && jumpTo > 0 && jumpTo <= words.length) {
                currentIndex = jumpTo - 1;
                positionSlider.value = currentIndex;
                positionValue.textContent = currentIndex + 1;
                updateDisplay();
                jumpInput.value = '';
            } else {
                alert('Please enter a valid word number between 1 and ' + words.length);
            }
        });

        jumpInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                jumpBtn.click();
            }
        });

        function play() {
            isPlaying = true;
            playPauseBtn.textContent = 'Pause';
            const msPerWord = 60000 / wpm;
            
            intervalId = setInterval(() => {
                if (currentIndex >= words.length - 1) {
                    pause();
                    return;
                }
                currentIndex++;
                updateDisplay();
            }, msPerWord);
        }

        function pause() {
            isPlaying = false;
            playPauseBtn.textContent = 'Play';
            if (intervalId) {
                clearInterval(intervalId);
                intervalId = null;
            }
        }

        function updateDisplay() {
            if (words.length > 0) {
                const word = words[currentIndex];
                const orpIndex = calculateORP(word);
                
                // Split word into three parts: before ORP, ORP letter, after ORP
                const before = word.substring(0, orpIndex);
                const orp = word.charAt(orpIndex);
                const after = word.substring(orpIndex + 1);
                
                const currentColor = colorNames[currentColorIndex];
                const colorValue = getComputedStyle(document.documentElement).getPropertyValue(`--color-${currentColor}`).trim();
                wordDisplay.innerHTML = `<div class="word-container"><span>${before}</span><span class="orp" style="color: ${colorValue};">${orp}</span><span>${after}</span></div>`;
                
                // Calculate offset to center the ORP letter
                setTimeout(() => {
                    const container = wordDisplay.querySelector('.word-container');
                    const orpElement = wordDisplay.querySelector('.orp');
                    if (container && orpElement) {
                        const containerRect = wordDisplay.getBoundingClientRect();
                        const orpRect = orpElement.getBoundingClientRect();
                        const orpCenter = orpRect.left + orpRect.width / 2;
                        const containerCenter = containerRect.left + containerRect.width / 2;
                        const offset = containerCenter - orpCenter;
                        container.style.transform = `translateX(${offset}px)`;
                    }
                }, 0);
                
                positionSlider.value = currentIndex;
                currentWordSpan.textContent = currentIndex + 1;
                
                // Update PDF highlight
                highlightCurrentWord();
            }
        }

        function calculateORP(word) {
            // Remove leading punctuation to find the actual word start
            let leadingPunct = 0;
            while (leadingPunct < word.length && /[^\w]/.test(word[leadingPunct])) {
                leadingPunct++;
            }
            
            // Calculate ORP position (approximately 1/3 into the word for optimal recognition)
            const effectiveLength = word.length - leadingPunct;
            let orpPosition;
            
            if (effectiveLength <= 1) {
                orpPosition = 0;
            } else if (effectiveLength <= 5) {
                orpPosition = 1;
            } else if (effectiveLength <= 9) {
                orpPosition = 2;
            } else if (effectiveLength <= 13) {
                orpPosition = 3;
            } else {
                orpPosition = 4;
            }
            
            return leadingPunct + orpPosition;
        }

        function calculateAndDisplayStats(wordList, originalText) {
            const totalWords = wordList.length;
            const uniqueWords = new Set(wordList.map(w => w.toLowerCase())).size;
            const lexicalDiversity = ((uniqueWords / totalWords) * 100).toFixed(1);
            
            const avgWordLength = (wordList.reduce((sum, w) => sum + w.length, 0) / totalWords).toFixed(1);
            
            // Detect sentences (rough estimate)
            const sentences = originalText.split(/[.!?]+/).filter(s => s.trim().length > 0).length || 1;
            const avgSentenceLength = (totalWords / sentences).toFixed(1);
            
            // Flesch-Kincaid grade level estimate
            const syllables = wordList.reduce((sum, w) => sum + countSyllables(w), 0);
            const readingLevel = Math.max(0, (0.39 * (totalWords / sentences) + 11.8 * (syllables / totalWords) - 15.59).toFixed(1));
            
            document.getElementById('statTotalWords').textContent = totalWords.toLocaleString();
            document.getElementById('statUniqueWords').textContent = uniqueWords.toLocaleString();
            document.getElementById('statDiversity').textContent = lexicalDiversity + '%';
            document.getElementById('statAvgWordLen').textContent = avgWordLength;
            document.getElementById('statAvgSentenceLen').textContent = avgSentenceLength;
            document.getElementById('statReadingLevel').textContent = readingLevel;
        }

        function countSyllables(word) {
            word = word.toLowerCase();
            let count = 0;
            const vowels = 'aeiouy';
            let previousWasVowel = false;

            for (let char of word) {
                const isVowel = vowels.includes(char);
                if (isVowel && !previousWasVowel) {
                    count++;
                }
                previousWasVowel = isVowel;
            }

            if (word.endsWith('e')) count--;
            if (word.endsWith('le') && word.length > 2 && !vowels.includes(word[word.length - 3])) count++;
            
            return Math.max(1, count);
        }

        // PDF Preview Functions
        async function renderPDFPreview(file) {
            try {
                console.log('Starting PDF preview render...');
                
                // Check if PDF.js is available
                if (typeof pdfjsLib === 'undefined') {
                    console.error('PDF.js library not loaded');
                    return;
                }
                
                const pdfSidebar = document.getElementById('pdfSidebar');
                const pdfPagesContainer = document.getElementById('pdfPagesContainer');
                
                if (!pdfSidebar || !pdfPagesContainer) {
                    console.error('PDF sidebar elements not found');
                    return;
                }
                
                const arrayBuffer = await file.arrayBuffer();
                pdfDoc = await pdfjsLib.getDocument({data: arrayBuffer}).promise;
                console.log('PDF loaded, pages:', pdfDoc.numPages);
                
                pdfPagesContainer.innerHTML = '';
                pdfPages = [];
                
                // Show sidebar immediately
                pdfSidebar.classList.add('active');
                
                // Render all pages
                for (let pageNum = 1; pageNum <= pdfDoc.numPages; pageNum++) {
                    try {
                        const page = await pdfDoc.getPage(pageNum);
                        const scale = 0.5; // Scale down for sidebar
                        const viewport = page.getViewport({scale: scale});
                        
                        const pageContainer = document.createElement('div');
                        pageContainer.className = 'pdf-page-container';
                        pageContainer.id = `pdf-page-${pageNum}`;
                        
                        const canvas = document.createElement('canvas');
                        const context = canvas.getContext('2d');
                        canvas.height = viewport.height;
                        canvas.width = viewport.width;
                        
                        const pageLabel = document.createElement('div');
                        pageLabel.className = 'pdf-page-label';
                        pageLabel.textContent = `Page ${pageNum}`;
                        
                        pageContainer.appendChild(canvas);
                        pageContainer.appendChild(pageLabel);
                        pdfPagesContainer.appendChild(pageContainer);
                        
                        const renderContext = {
                            canvasContext: context,
                            viewport: viewport
                        };
                        await page.render(renderContext).promise;
                        
                        // Get text content for word position mapping
                        try {
                            const textContent = await page.getTextContent();
                            pdfPages.push({
                                pageNum: pageNum,
                                textContent: textContent,
                                viewport: viewport,
                                scale: scale
                            });
                        } catch (textErr) {
                            console.warn(`Could not get text for page ${pageNum}:`, textErr);
                            // Continue without text content for this page
                        }
                    } catch (pageErr) {
                        console.error(`Error rendering page ${pageNum}:`, pageErr);
                        // Continue with next page
                    }
                }
                
                console.log('PDF rendering complete');
                
                // Initial highlight
                highlightCurrentWord();
                
            } catch (error) {
                console.error('Error rendering PDF preview:', error);
                // Don't show alert, just log - app should continue working
            }
        }

        function highlightCurrentWord() {
            if (!pdfDoc || words.length === 0 || pdfPages.length === 0) {
                console.log('Highlight skipped - not ready');
                return;
            }
            
            try {
                // Remove existing highlights
                document.querySelectorAll('.word-highlight-overlay').forEach(el => el.remove());
                
                let wordCount = 0;
                let found = false;
                
                // Search through pages to find current word position
                for (let pageData of pdfPages) {
                    if (found) break;
                    
                    const textItems = pageData.textContent.items;
                    
                    for (let item of textItems) {
                        if (!item.str || item.str.trim().length === 0) continue;
                        
                        const itemWords = item.str.trim().split(/\s+/).filter(w => w.length > 0);
                        
                        for (let i = 0; i < itemWords.length; i++) {
                            if (wordCount === currentIndex) {
                                // Found the current word, highlight it
                                const pageContainer = document.getElementById(`pdf-page-${pageData.pageNum}`);
                                if (!pageContainer) continue;
                                
                                const highlight = document.createElement('div');
                                highlight.className = 'word-highlight-overlay';
                                
                                // Calculate position using transform matrix
                                const tx = item.transform[4] * pageData.scale;
                                const ty = pageData.viewport.height - (item.transform[5] * pageData.scale);
                                const height = item.height * pageData.scale;
                                const totalWidth = item.width * pageData.scale;
                                const wordWidth = totalWidth / itemWords.length;
                                const left = tx + (wordWidth * i);
                                
                                highlight.style.left = left + 'px';
                                highlight.style.top = (ty - height) + 'px';
                                highlight.style.width = wordWidth + 'px';
                                highlight.style.height = height + 'px';
                                
                                pageContainer.appendChild(highlight);
                                
                                // Scroll to current page
                                pageContainer.scrollIntoView({behavior: 'smooth', block: 'center'});
                                
                                found = true;
                                break;
                            }
                            wordCount++;
                        }
                        
                        if (found) break;
                    }
                }
                
                if (!found) {
                    console.log('Word position not found in PDF');
                }
            } catch (error) {
                console.error('Error highlighting word:', error);
            }
        }

        // Dark mode toggle
        const themeToggle = document.getElementById('themeToggle');
        const htmlElement = document.documentElement;
        const logoImage = document.getElementById('logoImage');
        const savedTheme = localStorage.getItem('theme') || 'light';
        
        function updateLogo(theme) {
            if (theme === 'dark') {
                logoImage.src = '/static/speedread_logo_dark.png';
            } else {
                logoImage.src = '/static/speedread_logo.png';
            }
        }
        
        if (savedTheme === 'dark') {
            htmlElement.setAttribute('data-theme', 'dark');
            themeToggle.textContent = '☀️ Light Mode';
            updateLogo('dark');
        }
        
        themeToggle.addEventListener('click', () => {
            const currentTheme = htmlElement.getAttribute('data-theme');
            const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
            htmlElement.setAttribute('data-theme', newTheme);
            localStorage.setItem('theme', newTheme);
            themeToggle.textContent = newTheme === 'dark' ? '☀️ Light Mode' : '🌙 Dark Mode';
            updateLogo(newTheme);
        });
    </script>
    
        </div>
        
        <!-- PDF Preview Sidebar -->
        <div class="pdf-sidebar" id="pdfSidebar">
            <h3>PDF Preview</h3>
            <div id="pdfPagesContainer"></div>
        </div>
    
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/upload', methods=['POST'])
def upload():
    if 'pdf' not in request.files:
        return jsonify({'error': 'No file uploaded'}), 400
    
    file = request.files['pdf']
    
    try:
        # Read PDF
        pdf_reader = pypdf.PdfReader(io.BytesIO(file.read()))
        
        # Extract text from all pages
        text = ''
        for page in pdf_reader.pages:
            text += page.extract_text() + ' '
        
        # Split into words (remove extra whitespace and split)
        words = re.findall(r'\S+', text)
        
        return jsonify({'words': words, 'originalText': text})
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))