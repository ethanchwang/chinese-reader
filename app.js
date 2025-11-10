// API endpoint - will be set up with Python backend
const API_BASE_URL = 'http://localhost:5000/api';

// Sample text
const SAMPLE_TEXT = '中国政府周日宣布将暂停对五种关键矿物的出口管制，为期一年。这些矿物是制造某些半导体以及炸药、穿甲弹、电池和核反应堆所必需的。\n\n中国商务部发布的这份公告澄清了10月30日特朗普总统与中国领导人习近平在韩国举行会晤后，双方政府各自发表的声明中存在的一个关键差异。\n\n会后，中国方面表示同意暂停一系列关于稀土金属及锂离子电池、半导体和太阳能电池板制造设备的出口管制规定，期限为一年。商务部于上周五暂停了这些管制措施。\n\n然而，中国在峰会后的声明并未提及放宽去年12月商务部对另外五种关键材料（虽非稀土金属）所实施的出口限制。白宫声明则称，中国还同意发放所谓的"通用许可"，以便更容易获得这些矿物。';

// Saved vocabulary for Anki export
let savedVocab = [];

// Update export button count
function updateExportButton() {
    const exportBtn = document.getElementById('export-vocab-btn');
    if (exportBtn) {
        exportBtn.textContent = `Export Vocab (${savedVocab.length})`;
    }
}

// Try Sample button click handler
document.getElementById('try-sample-btn').addEventListener('click', () => {
    const textarea = document.getElementById('chinese-text');
    textarea.value = SAMPLE_TEXT;
    // Focus the textarea so user can see the text
    textarea.focus();
    // Scroll to top of textarea
    textarea.scrollTop = 0;
});

// Process button click handler
document.getElementById('process-btn').addEventListener('click', async () => {
    const text = document.getElementById('chinese-text').value;
    
    if (!text.trim()) {
        alert('Please enter some Chinese text.');
        return;
    }
    
    try {
        // Send text to Python backend for processing (preserve line breaks)
        const response = await fetch(`${API_BASE_URL}/process`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ text: text })
        });
        
        if (!response.ok) {
            throw new Error('Failed to process text');
        }
        
        const data = await response.json();
        displayProcessedText(data.phrases);
    } catch (error) {
        console.error('Error:', error);
        // Fallback: process locally for demo purposes
        alert('Backend not available. Using demo mode. Please start the Python server.');
        displayProcessedTextDemo(text);
    }
});

// Display processed text with hoverable phrases
function displayProcessedText(phrases) {
    const readingArea = document.getElementById('reading-area');
    readingArea.innerHTML = '';
    
    let consecutiveNewlines = 0;
    
    phrases.forEach((phrase, index) => {
        // Handle newlines - create a <br> element instead of a span
        if (phrase.text === '\n' || phrase.text === '\r\n' || phrase.text === '\r') {
            consecutiveNewlines++;
            readingArea.appendChild(document.createElement('br'));
            
            // If we have multiple consecutive newlines (paragraph break), add extra spacing
            if (consecutiveNewlines >= 2) {
                const spacer = document.createElement('div');
                spacer.className = 'paragraph-spacer';
                readingArea.appendChild(spacer);
            }
            return;
        }
        
        // Reset consecutive newlines counter when we hit non-newline text
        consecutiveNewlines = 0;
        
        const span = document.createElement('span');
        span.className = 'phrase';
        span.textContent = phrase.text;
        span.dataset.pinyin = phrase.pinyin || '';
        span.dataset.definition = phrase.definition || '';
        span.dataset.index = index;
        
        // Add click event listener if there's pinyin or definition
        if (phrase.pinyin || phrase.definition) {
            span.classList.add('clickable');
            span.addEventListener('click', (e) => {
                showPhraseDetails(phrase, e.target);
            });
        }
        
        readingArea.appendChild(span);
    });
}

// Show phrase details in the right panel
function showPhraseDetails(phrase, clickedElement) {
    const detailsPanel = document.getElementById('phrase-details');
    detailsPanel.innerHTML = '';
    
    // Remove active class from all phrases
    document.querySelectorAll('.phrase').forEach(p => {
        p.classList.remove('active');
    });
    
    // Add active class to clicked phrase
    if (clickedElement) {
        clickedElement.classList.add('active');
    }
    
    // Phrase text
    const phraseText = document.createElement('div');
    phraseText.className = 'phrase-text';
    phraseText.textContent = phrase.text;
    detailsPanel.appendChild(phraseText);
    
    // Save button
    const saveBtn = document.createElement('button');
    saveBtn.className = 'save-vocab-btn';
    saveBtn.textContent = 'Save to Vocab';
    
    // Check if already saved
    const isSaved = savedVocab.some(v => v.text === phrase.text);
    if (isSaved) {
        saveBtn.textContent = 'Saved ✓';
        saveBtn.classList.add('saved');
    }
    
    saveBtn.addEventListener('click', () => {
        saveVocabItem(phrase, saveBtn);
    });
    detailsPanel.appendChild(saveBtn);
    
    // Check if we have all_entries (multiple pronunciations)
    if (phrase.all_entries && phrase.all_entries.length > 0) {
        // Display each entry separately
        phrase.all_entries.forEach((entry, index) => {
            const detailItem = document.createElement('div');
            detailItem.className = 'phrase-detail-item';
            
            // Pinyin
            if (entry.pinyin) {
                const pinyinDiv = document.createElement('div');
                pinyinDiv.className = 'pinyin';
                pinyinDiv.textContent = entry.pinyin;
                detailItem.appendChild(pinyinDiv);
            }
            
            // Definition
            if (entry.definition) {
                const defDiv = document.createElement('div');
                defDiv.className = 'definition';
                defDiv.textContent = entry.definition;
                detailItem.appendChild(defDiv);
            }
            
            // Add separator between entries (except for last one)
            if (index < phrase.all_entries.length - 1) {
                const separator = document.createElement('div');
                separator.className = 'entry-separator';
                detailsPanel.appendChild(separator);
            }
            
            detailsPanel.appendChild(detailItem);
        });
    } else {
        // Fallback to single entry display
        const detailItem = document.createElement('div');
        detailItem.className = 'phrase-detail-item';
        
        // Pinyin
        if (phrase.pinyin && phrase.pinyin !== '[Not found]') {
            const pinyinDiv = document.createElement('div');
            pinyinDiv.className = 'pinyin';
            pinyinDiv.textContent = phrase.pinyin;
            detailItem.appendChild(pinyinDiv);
        }
        
        // Definition
        if (phrase.definition && phrase.definition !== '[Not found]') {
            const defDiv = document.createElement('div');
            defDiv.className = 'definition';
            defDiv.textContent = phrase.definition;
            detailItem.appendChild(defDiv);
        }
        
        // If no valid data, show message
        if ((!phrase.pinyin || phrase.pinyin === '[Not found]') && 
            (!phrase.definition || phrase.definition === '[Not found]')) {
            const noData = document.createElement('div');
            noData.className = 'definition';
            noData.textContent = 'No definition found for this phrase.';
            noData.style.color = '#666';
            detailItem.appendChild(noData);
        }
        
        detailsPanel.appendChild(detailItem);
    }
}

// Save vocab item
function saveVocabItem(phrase, button) {
    // Check if already saved
    const existingIndex = savedVocab.findIndex(v => v.text === phrase.text);
    
    if (existingIndex >= 0) {
        // Remove if already saved
        savedVocab.splice(existingIndex, 1);
        button.textContent = 'Save to Vocab';
        button.classList.remove('saved');
    } else {
        // Add to saved vocab
        const vocabItem = {
            text: phrase.text,
            pinyin: phrase.pinyin || '',
            definition: phrase.definition || '',
            all_entries: phrase.all_entries || []
        };
        savedVocab.push(vocabItem);
        button.textContent = 'Saved ✓';
        button.classList.add('saved');
    }
    
    updateExportButton();
}

// Export vocab to Anki CSV
function exportVocabToAnki() {
    if (savedVocab.length === 0) {
        alert('No vocabulary saved yet. Click "Save to Vocab" on phrases to add them.');
        return;
    }
    
    // Create CSV content
    let csvContent = '';
    
    savedVocab.forEach(item => {
        // Question: Just the Chinese characters
        const question = item.text;
        
        // Answer: All pinyin on first line (semicolon-separated), then definition
        let answer = '';
        
        // Get all unique pinyin from all_entries
        let allPinyin = [];
        let allDefinitions = [];
        
        if (item.all_entries && item.all_entries.length > 0) {
            item.all_entries.forEach(entry => {
                if (entry.pinyin && entry.pinyin !== '[Not found]' && !allPinyin.includes(entry.pinyin)) {
                    allPinyin.push(entry.pinyin);
                }
                if (entry.definition && entry.definition !== '[Not found]' && !allDefinitions.includes(entry.definition)) {
                    allDefinitions.push(entry.definition);
                }
            });
        } else if (item.pinyin && item.pinyin !== '[Not found]') {
            // Fallback to single pinyin if all_entries not available
            allPinyin = [item.pinyin];
        }
        
        // Build answer: pinyin on first line (space-separated), then each definition on separate lines
        if (allPinyin.length > 0) {
            answer = allPinyin.join(' ');
        }
        
        // Add each definition on a separate line
        if (allDefinitions.length > 0) {
            if (answer) {
                answer += '\n' + allDefinitions.join('\n');
            } else {
                answer = allDefinitions.join('\n');
            }
        } else if (item.definition && item.definition !== '[Not found]') {
            // Fallback to item.definition if all_entries not available
            if (answer) {
                answer += '\n' + item.definition;
            } else {
                answer = item.definition;
            }
        }
        
        if (!answer) {
            answer = 'No definition';
        }
        
        // Tags: "chinese" and "vocab"
        const tags = 'chinese vocab';
        
        // Escape CSV fields: quote if contains comma, semicolon, newline, or quote
        const escapeCSV = (str) => {
            if (!str) return '';
            // Quote if contains comma, semicolon, newline, or quote
            if (str.includes(',') || str.includes(';') || str.includes('\n') || str.includes('"')) {
                // Escape quotes by doubling them
                return '"' + str.replace(/"/g, '""') + '"';
            }
            return str;
        };
        
        csvContent += `${escapeCSV(question)};${escapeCSV(answer)};${escapeCSV(tags)}\n`;
    });
    
    // Create download link
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const link = document.createElement('a');
    const url = URL.createObjectURL(blob);
    link.setAttribute('href', url);
    link.setAttribute('download', `anki_vocab_${new Date().toISOString().split('T')[0]}.csv`);
    link.style.visibility = 'hidden';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}

// Export button handler (initialize when script loads)
const exportBtn = document.getElementById('export-vocab-btn');
if (exportBtn) {
    exportBtn.addEventListener('click', exportVocabToAnki);
    updateExportButton();
}

// Demo mode - simple character-by-character processing
function displayProcessedTextDemo(text) {
    const readingArea = document.getElementById('reading-area');
    readingArea.innerHTML = '';
    
    // Simple regex to match Chinese characters
    const chineseRegex = /[\u4e00-\u9fff]+/g;
    let lastIndex = 0;
    let match;
    
    while ((match = chineseRegex.exec(text)) !== null) {
        // Add text before Chinese phrase
        if (match.index > lastIndex) {
            const textNode = document.createTextNode(text.substring(lastIndex, match.index));
            readingArea.appendChild(textNode);
        }
        
        // Create phrase span
        const span = document.createElement('span');
        span.className = 'phrase';
        span.textContent = match[0];
        span.dataset.pinyin = '[Demo Mode - Backend Required]';
        span.dataset.definition = 'Please start the Python server for full functionality.';
        
        span.classList.add('clickable');
        span.addEventListener('click', (e) => {
            showPhraseDetails({
                text: match[0],
                pinyin: '[Demo Mode - Backend Required]',
                definition: 'Please start the Python server for full functionality.'
            }, e.target);
        });
        
        readingArea.appendChild(span);
        lastIndex = match.index + match[0].length;
    }
    
    // Add remaining text
    if (lastIndex < text.length) {
        const textNode = document.createTextNode(text.substring(lastIndex));
        readingArea.appendChild(textNode);
    }
}

