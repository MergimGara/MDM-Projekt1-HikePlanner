<script>
    import { browser, dev } from "$app/environment";
    import { onMount } from "svelte";
    import { fade, slide } from 'svelte/transition';

    let url = dev ? "http://localhost:5000" : "";
    if (!dev && browser) {
        url = location.protocol + "//" + location.host;
    }

    let downhill = 300;
    let uphill = 700;
    let length = 10000;

    let results = null;
    let loading = false;
    let error = null;

    let debounceId;

    async function predict() {
        loading = true;
        error = null;
        try {
            const params = new URLSearchParams({ downhill, uphill, length });
            let response = await fetch(`${url}/api/predict?${params}`);
            if (!response.ok) throw new Error("Backend nicht erreichbar");
            results = await response.json();
        } catch (e) {
            error = "Fehler bei der Verbindung zum Backend. Bitte prüfe dein Deployment.";
            console.error(e);
        } finally {
            loading = false;
        }
    }

    onMount(() => predict());

    function schedulePredict() {
        if (debounceId) clearTimeout(debounceId);
        debounceId = setTimeout(() => predict(), 300);
    }

    // Hilfsfunktion: Berechnet die Breite des Balkens (max 8h = 100%)
    function getWidth(timeStr) {
        if (!timeStr || timeStr === "n.a.") return 5;
        const parts = timeStr.split(':').map(Number);
        const totalMinutes = parts[0] * 60 + parts[1];
        return Math.min(100, (totalMinutes / 480) * 100); 
    }
</script>

<svelte:head>
    <title>HikePlanner Pro</title>
</svelte:head>

<div class="app-bg min-vh-100 p-3 p-md-5">
    <main class="container py-4">
        <div class="row g-4 justify-content-center">
            <div class="col-lg-11 col-xl-10">
                <div class="glass-card overflow-hidden">
                    <div class="row g-0">
                        
                        <!-- Eingabebereich -->
                        <div class="col-md-5 p-4 p-lg-5 bg-white bg-opacity-40 border-end">
                            <div class="d-flex align-items-center mb-4">
                                <div class="icon-circle me-3">🏔️</div>
                                <h1 class="h3 fw-bold mb-0 text-primary">HikePlanner</h1>
                            </div>
                            
                            <p class="text-muted small mb-4">
                                Berechne präzise Gehzeiten mit Machine Learning und klassischen Formeln.
                            </p>

                            <form class="vstack gap-4" on:submit|preventDefault={predict}>
                                <div class="input-group-custom">
                                    <label class="form-label d-flex justify-content-between">
                                        <span>Abwärts</span> <strong>{downhill} m</strong>
                                    </label>
                                    <input type="range" class="form-range" bind:value={downhill} min="0" max="5000" step="50" on:input={schedulePredict} />
                                </div>

                                <div class="input-group-custom">
                                    <label class="form-label d-flex justify-content-between">
                                        <span>Aufwärts</span> <strong>{uphill} m</strong>
                                    </label>
                                    <input type="range" class="form-range" bind:value={uphill} min="0" max="5000" step="50" on:input={schedulePredict} />
                                </div>

                                <div class="input-group-custom">
                                    <label class="form-label d-flex justify-content-between">
                                        <span>Distanz</span> <strong>{(length/1000).toFixed(1)} km</strong>
                                    </label>
                                    <input type="range" class="form-range" bind:value={length} min="0" max="40000" step="500" on:input={schedulePredict} />
                                </div>
                                
                                <div class="pt-2">
                                    <button class="btn btn-primary w-100 py-2 fw-bold" type="submit" disabled={loading}>
                                        {#if loading}
                                            <span class="spinner-border spinner-border-sm me-2"></span> Berechnung...
                                        {:else}
                                            Berechnen
                                        {/if}
                                    </button>
                                </div>
                            </form>
                        </div>

                        <!-- Ergebnisbereich -->
                        <div class="col-md-7 p-4 p-lg-5 bg-white bg-opacity-70">
                            <div class="d-flex justify-content-between align-items-center mb-4">
                                <h2 class="h5 fw-bold mb-0">Zeitprognosen</h2>
                                {#if loading}
                                    <div class="spinner-grow spinner-grow-sm text-primary" role="status"></div>
                                {/if}
                            </div>

                            {#if error}
                                <div class="alert alert-danger d-flex align-items-center" transition:slide>
                                    <span class="me-2">⚠️</span> {error}
                                </div>
                            {:else if results}
                                <div class="results-grid vstack gap-4" transition:fade>
                                    
                                    <!-- Progress Bar Items -->
                                    {#each [
                                        { label: 'Gradient Boosting (ML)', val: results.time, color: 'gradient' },
                                        { label: 'Linear Regression (ML)', val: results.linear, color: 'linear' },
                                        { label: 'DIN 33466 Standard', val: results.din33466, color: 'din' },
                                        { label: 'SAC-Wanderformel', val: results.sac, color: 'sac' }
                                    ] as item}
                                        <div class="result-item">
                                            <div class="d-flex justify-content-between align-items-end mb-2">
                                                <span class="label text-muted small fw-semibold">{item.label}</span>
                                                <span class="value h5 mb-0 fw-bold">{item.val}</span>
                                            </div>
                                            <div class="progress-track">
                                                <div class="progress-bar-fill {item.color}" style="width: {getWidth(item.val)}%"></div>
                                            </div>
                                        </div>
                                    {/each}

                                </div>
                                
                                <div class="mt-5 p-3 rounded-3 bg-light border-start border-primary border-4">
                                    <p class="small text-muted mb-0">
                                        <strong>Info:</strong> Die ML-Modelle wurden auf über 5000 realen GPX-Tracks trainiert, um Steigungen und Abstiege präziser zu gewichten als starre Formeln.
                                    </p>
                                </div>
                            {:else}
                                <div class="text-center py-5">
                                    <div class="opacity-25 mb-3" style="font-size: 3rem;">🏔️</div>
                                    <p class="text-muted">Ändere die Werte links, um eine Prognose zu erhalten.</p>
                                </div>
                            {/if}
                        </div>

                    </div>
                </div>
            </div>
        </div>
    </main>
</div>
