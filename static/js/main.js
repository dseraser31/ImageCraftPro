document.addEventListener('DOMContentLoaded', () => {
    // Tab switching
    const tabs = document.querySelectorAll('.tab-btn');
    const tabContents = document.querySelectorAll('.tab-content');

    tabs.forEach(tab => {
        tab.addEventListener('click', () => {
            tabs.forEach(t => t.classList.remove('active'));
            tabContents.forEach(content => content.classList.remove('active'));

            tab.classList.add('active');
            document.getElementById(tab.dataset.tab).classList.add('active');
        });
    });

    // Advanced settings toggle
    const toggleSettingsBtn = document.getElementById('toggle-settings');
    const advancedSettings = document.getElementById('advanced-settings');
    const toggleIcon = toggleSettingsBtn ? toggleSettingsBtn.querySelector('.toggle-icon') : null;

    // التحقق من وجود العناصر
    if (!toggleSettingsBtn || !advancedSettings || !toggleIcon) {
        console.error('One or more elements for Advanced Settings not found:', {
            toggleSettingsBtn,
            advancedSettings,
            toggleIcon
        });
    } else {
        toggleSettingsBtn.addEventListener('click', () => {
            console.log('Toggle settings button clicked'); // Debugging
            advancedSettings.classList.toggle('active');
            const isActive = advancedSettings.classList.contains('active');
            toggleIcon.textContent = isActive ? '▲' : '▼';
            console.log(`Advanced settings is now ${isActive ? 'visible' : 'hidden'}`); // Debugging
        });
    }

    // Range inputs for steps and guidance
    const stepsInput = document.getElementById('steps');
    const stepsValue = document.getElementById('steps-value');
    const guidanceInput = document.getElementById('guidance');
    const guidanceValue = document.getElementById('guidance-value');

    // Ensure initial values are displayed
    if (stepsInput && stepsValue) {
        stepsValue.textContent = stepsInput.value;
        stepsInput.addEventListener('input', () => {
            stepsValue.textContent = stepsInput.value;
            console.log(`Steps updated to: ${stepsInput.value}`); // Debugging
        });
    }

    if (guidanceInput && guidanceValue) {
        guidanceValue.textContent = guidanceInput.value;
        guidanceInput.addEventListener('input', () => {
            guidanceValue.textContent = guidanceInput.value;
            console.log(`Guidance updated to: ${guidanceInput.value}`); // Debugging
        });
    }

    // Model selection
    const modelSelect = document.getElementById('model');
    if (modelSelect) {
        modelSelect.addEventListener('change', () => {
            console.log(`Model selected: ${modelSelect.value}`); // Debugging
        });
    }

    // Size selection
    const sizeSelect = document.getElementById('size');
    if (sizeSelect) {
        sizeSelect.addEventListener('change', () => {
            console.log(`Size selected: ${sizeSelect.value}`); // Debugging
        });
    }

    // Random seed generation
    const randomSeedBtn = document.getElementById('random-seed');
    const seedInput = document.getElementById('seed');

    if (randomSeedBtn && seedInput) {
        randomSeedBtn.addEventListener('click', () => {
            const randomSeed = Math.floor(Math.random() * 1000000);
            seedInput.value = randomSeed;
            console.log(`Random seed generated: ${randomSeed}`); // Debugging
        });

        // Log seed input changes
        seedInput.addEventListener('input', () => {
            console.log(`Seed updated to: ${seedInput.value}`); // Debugging
        });
    }

    // Image upload and preview
    const imageUpload = document.getElementById('image-upload');
    const imagePreview = document.getElementById('image-preview');
    const uploadArea = document.getElementById('upload-area');
    const removeImageBtn = document.getElementById('remove-image');

    if (imageUpload && imagePreview && uploadArea && removeImageBtn) {
        imageUpload.addEventListener('change', (e) => {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = (event) => {
                    imagePreview.src = event.target.result;
                    uploadArea.classList.add('has-image');
                };
                reader.readAsDataURL(file);
            }
        });

        removeImageBtn.addEventListener('click', () => {
            imageUpload.value = '';
            imagePreview.src = '';
            uploadArea.classList.remove('has-image');
        });

        // Drag and drop
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });

        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });

        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const file = e.dataTransfer.files[0];
            if (file && file.type.startsWith('image/')) {
                imageUpload.files = e.dataTransfer.files;
                const reader = new FileReader();
                reader.onload = (event) => {
                    imagePreview.src = event.target.result;
                    uploadArea.classList.add('has-image');
                };
                reader.readAsDataURL(file);
            }
        });
    }

    // Clear cache button
    const clearCacheBtn = document.getElementById('clear-cache-btn');
    if (clearCacheBtn) {
        clearCacheBtn.addEventListener('click', async () => {
            try {
                const response = await fetch('/clear-cache', { method: 'POST' });
                const result = await response.json();
                alert(result.message);
            } catch (error) {
                console.error('Error clearing cache:', error);
                alert('Failed to clear cache');
            }
        });
    }

    // Generate button
    const generateBtn = document.getElementById('generate-btn');
    const loadingContainer = document.getElementById('loading-container');
    const imagesGrid = document.getElementById('images-grid');
    const noResults = document.getElementById('no-results');
    const downloadAllBtn = document.getElementById('download-all');

    if (generateBtn && loadingContainer && imagesGrid && noResults && downloadAllBtn) {
        generateBtn.addEventListener('click', async () => {
            const activeTab = document.querySelector('.tab-btn.active')?.dataset.tab;
            if (!activeTab) {
                console.error('No active tab found');
                return;
            }

            const data = {
                model: modelSelect?.value || 'black-forest-labs/FLUX.1-schnell-Free',
                steps: parseInt(stepsInput?.value) || 4,
                guidance: parseFloat(guidanceInput?.value) || 3.5,
                size: sizeSelect?.value || 'square',
                output_format: 'jpeg'
            };

            // Add seed to the request
            const seed = seedInput?.value ? parseInt(seedInput.value) : Math.floor(Math.random() * 1000000);
            data.seed = seed;

            if (activeTab === 'text-to-image') {
                data.prompt = document.getElementById('prompt')?.value || '';
                data.negative_prompt = document.getElementById('negative-prompt')?.value || '';
            } else {
                data.prompt = document.getElementById('image-prompt')?.value || '';
                data.negative_prompt = document.getElementById('image-negative-prompt')?.value || '';
                const file = imageUpload?.files[0];
                if (file) {
                    const reader = new FileReader();
                    reader.onloadend = async () => {
                        data.image = reader.result.split(',')[1]; // Base64 encoded image
                        await generateImages(data);
                    };
                    reader.readAsDataURL(file);
                    return;
                }
            }

            console.log('Sending request with data:', data); // Debugging
            await generateImages(data);
        });

        async function generateImages(data) {
            if (!data.prompt) {
                alert('Please provide a prompt!');
                return;
            }

            loadingContainer.style.display = 'flex';
            imagesGrid.innerHTML = '';
            noResults.style.display = 'none';
            downloadAllBtn.disabled = true;

            try {
                const response = await fetch('/generate', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });

                const result = await response.json();

                if (response.ok) {
                    const img = document.createElement('img');
                    img.src = `/static/${result.image_path}`;
                    img.alt = 'Generated Image';
                    imagesGrid.appendChild(img);
                    downloadAllBtn.disabled = false;

                    downloadAllBtn.onclick = () => {
                        const link = document.createElement('a');
                        link.href = img.src;
                        link.download = 'generated_image.jpg';
                        link.click();
                    };
                } else {
                    throw new Error(result.error || 'Failed to generate images');
                }
            } catch (error) {
                console.error('Error:', error);
                alert(`Failed to generate images: ${error.message}`);
                noResults.style.display = 'flex';
            } finally {
                loadingContainer.style.display = 'none';
            }
        }
    }
});