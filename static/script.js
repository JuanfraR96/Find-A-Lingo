document.addEventListener("DOMContentLoaded", async () => {
    const filtersContainer = document.getElementById("filtersContainer");
    const scrapeForm = document.getElementById("scrapeForm");
    const loadingOverlay = document.getElementById("loadingOverlay");

    // Fetch filters from backend
    try {
        const response = await fetch("/api/filters");
        const filters = await response.json();
        renderFilters(filters);
    } catch (e) {
        console.error("Error loading filters:", e);
        filtersContainer.innerHTML = "<p class='error'>Failed to load filters.</p>";
    }

    function renderFilters(filters) {
        // Create containers
        const basicFiltersGrid = document.createElement("div");
        basicFiltersGrid.className = "basic-filters-grid";
        
        const advancedFiltersContainer = document.createElement("div");
        advancedFiltersContainer.className = "advanced-filters-container";
        
        for (const [key, filter] of Object.entries(filters)) {
            const group = document.createElement("div");
            group.className = "filter-group";

            if (filter.type === "select" || filter.type === "text") {
                const label = document.createElement("label");
                label.className = "group-label";
                label.textContent = filter.label;
                group.appendChild(label);

                if (filter.type === "select") {
                    const select = document.createElement("select");
                    select.name = key;
                    
                    const defaultOpt = document.createElement("option");
                    defaultOpt.value = "";
                    defaultOpt.textContent = "Any";
                    select.appendChild(defaultOpt);

                    filter.options.forEach(opt => {
                        const option = document.createElement("option");
                        option.value = opt.value;
                        option.textContent = opt.label;
                        select.appendChild(option);
                    });
                    group.appendChild(select);
                } else if (filter.type === "text") {
                    const textInput = document.createElement("input");
                    textInput.type = "text";
                    textInput.name = key;
                    textInput.className = "text-input";
                    textInput.placeholder = "Enter " + filter.label;
                    group.appendChild(textInput);
                }
                basicFiltersGrid.appendChild(group);
                
            } else if (filter.type === "checkboxes") {
                // Create Accordion for checkboxes to save space
                const accordion = document.createElement("div");
                accordion.className = "accordion";
                
                const accordionHeader = document.createElement("div");
                accordionHeader.className = "accordion-header";
                accordionHeader.innerHTML = `<span>${filter.label}</span> <i class="arrow down"></i>`;
                
                const accordionContent = document.createElement("div");
                accordionContent.className = "accordion-content";

                const checkboxGroup = document.createElement("div");
                checkboxGroup.className = "checkbox-group";

                filter.options.forEach(opt => {
                    const lbl = document.createElement("label");
                    lbl.className = "checkbox-label";
                    
                    const inp = document.createElement("input");
                    inp.type = "checkbox";
                    inp.name = key;
                    inp.value = opt.name;
                    
                    const text = document.createTextNode(opt.label);
                    
                    lbl.appendChild(inp);
                    lbl.appendChild(text);
                    checkboxGroup.appendChild(lbl);
                });
                
                accordionContent.appendChild(checkboxGroup);
                accordion.appendChild(accordionHeader);
                accordion.appendChild(accordionContent);
                
                // Toggle logic
                accordionHeader.addEventListener("click", () => {
                    accordion.classList.toggle("active");
                    const arrow = accordionHeader.querySelector(".arrow");
                    if (accordion.classList.contains("active")) {
                        arrow.classList.remove("down");
                        arrow.classList.add("up");
                    } else {
                        arrow.classList.remove("up");
                        arrow.classList.add("down");
                    }
                });
                
                advancedFiltersContainer.appendChild(accordion);
            }
        }
        
        filtersContainer.appendChild(basicFiltersGrid);
        
        if (advancedFiltersContainer.children.length > 0) {
            const advancedTitle = document.createElement("h3");
            advancedTitle.className = "advanced-title";
            advancedTitle.textContent = "Advanced Filters";
            filtersContainer.appendChild(advancedTitle);
            filtersContainer.appendChild(advancedFiltersContainer);
        }
    }

    scrapeForm.addEventListener("submit", async (e) => {
        e.preventDefault();
        
        // Gather data
        const formData = new FormData(scrapeForm);
        const data = {};
        
        // Handle selects and checkboxes
        for (const [key, value] of formData.entries()) {
            if (!value) continue;
            // if it's a checkbox group, value is the actual target name
            // Wait, we need to distinguish selects and checkboxes
            const inputType = scrapeForm.querySelector(`[name="${key}"]`).type;
            if (inputType === "checkbox" || inputType === "select-one" || !inputType) {
                // If it's a checkbox group, the name is shared across multiple checkboxes
                // Let's manually collect
            }
        }
        
        // Manual collection for easier structure
        const selects = scrapeForm.querySelectorAll("select");
        selects.forEach(s => {
            if (s.value) {
                data[s.name] = s.value;
            }
        });
        
        const texts = scrapeForm.querySelectorAll("input[type='text']");
        texts.forEach(t => {
            if (t.value.trim()) {
                data[t.name] = t.value.trim();
            }
        });
        
        const checkboxes = scrapeForm.querySelectorAll("input[type='checkbox']:checked");
        // group by group name
        checkboxes.forEach(cb => {
            if (!data[cb.name]) data[cb.name] = [];
            data[cb.name].push(cb.value);
        });

        // Generate dynamic filename
        let filterLabels = [];
        selects.forEach(s => {
            if (s.value && s.options[s.selectedIndex].text !== "Any") {
                filterLabels.push(s.options[s.selectedIndex].text.toLowerCase().replace(/[^a-z0-9]/g, '-'));
            }
        });
        texts.forEach(t => {
            if (t.value.trim()) {
                filterLabels.push(t.value.trim().toLowerCase().replace(/[^a-z0-9]/g, '-'));
            }
        });
        
        let prefix = filterLabels.length > 0 ? filterLabels.join('-') : "results";
        // truncate if too long
        if (prefix.length > 30) prefix = prefix.substring(0, 30);
        
        const today = new Date();
        const dd = String(today.getDate()).padStart(2, '0');
        const mm = String(today.getMonth() + 1).padStart(2, '0');
        const yy = String(today.getFullYear()).slice(-2);
        const filename = `${prefix}-${dd}-${mm}-${yy}.xlsx`;

        // Show loading overlay (kitten animation)
        loadingOverlay.classList.remove("hidden");

        const submitBtn = document.getElementById("submitBtn");
        const submitSpan = submitBtn.querySelector("span");
        const originalText = submitSpan.textContent;
        
        submitSpan.textContent = "Generando...";
        submitBtn.disabled = true;
        submitBtn.classList.add("loading");

        try {
            const response = await fetch("/api/scrape", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify(data)
            });

            if (response.ok) {
                const blob = await response.blob();
                const url = window.URL.createObjectURL(blob);
                const a = document.createElement("a");
                a.style.display = "none";
                a.href = url;
                a.download = filename;
                document.body.appendChild(a);
                a.click();
                window.URL.revokeObjectURL(url);
            } else {
                alert("An error occurred during extraction.");
            }
        } catch (error) {
            console.error("Scraping error:", error);
            alert("Failed to extract data.");
        } finally {
            loadingOverlay.classList.add("hidden");
            submitSpan.textContent = originalText;
            submitBtn.disabled = false;
            submitBtn.classList.remove("loading");
        }
    });
});
