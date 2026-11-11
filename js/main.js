const PREFERS_REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
const PACKAGES = ['maldisuite', 'maldiamrkit', 'maldibatchkit', 'maldideepkit'];

document.addEventListener('DOMContentLoaded', function() {
    initThemeToggle();
    initNavigation();
    initReveal();
    initCopyButtons();
    initSpectrumCursor();
    initTabs();
    loadVersions();
    loadResults();
    loadPublications();
    loadRoadmap();
});

function el(tag, className, text) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (text !== undefined && text !== null) node.textContent = String(text);
    return node;
}

async function fetchJson(url, timeoutMs) {
    const controller = new AbortController();
    const timer = setTimeout(function() { controller.abort(); }, timeoutMs || 8000);
    try {
        const response = await fetch(url, { signal: controller.signal });
        if (!response.ok) {
            throw new Error('HTTP ' + response.status + ' for ' + url);
        }
        return await response.json();
    } finally {
        clearTimeout(timer);
    }
}

function isDarkTheme() {
    const forced = document.documentElement.getAttribute('data-theme');
    if (forced) return forced === 'dark';
    return window.matchMedia('(prefers-color-scheme: dark)').matches;
}

function initThemeToggle() {
    const toggle = document.querySelector('.theme-toggle');
    const notify = function() {
        document.dispatchEvent(new CustomEvent('themechange'));
    };

    window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', notify);
    if (!toggle) return;

    toggle.addEventListener('click', function() {
        const next = isDarkTheme() ? 'light' : 'dark';
        document.documentElement.setAttribute('data-theme', next);
        try {
            localStorage.setItem('maldisuite-theme', next);
        } catch (e) {
            // Storage unavailable: the choice lasts for this page view only
        }
        notify();
    });
}

function initNavigation() {
    const header = document.getElementById('header');
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.getElementById('nav-menu');

    const onScroll = function() {
        header.classList.toggle('scrolled', window.scrollY > 8);
    };
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });

    if (navToggle && navMenu) {
        const setOpen = function(open) {
            navMenu.classList.toggle('open', open);
            navToggle.setAttribute('aria-expanded', String(open));
        };

        navToggle.addEventListener('click', function() {
            setOpen(!navMenu.classList.contains('open'));
        });

        navMenu.querySelectorAll('.nav-link').forEach(function(link) {
            link.addEventListener('click', function() { setOpen(false); });
        });

        document.addEventListener('click', function(event) {
            if (!navToggle.contains(event.target) && !navMenu.contains(event.target)) {
                setOpen(false);
            }
        });

        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape' && navMenu.classList.contains('open')) {
                setOpen(false);
                navToggle.focus();
            }
        });
    }

    if (!('IntersectionObserver' in window)) return;
    const links = Array.from(document.querySelectorAll('.nav-link[href^="#"]'));
    const byId = {};
    links.forEach(function(link) {
        byId[link.getAttribute('href').slice(1)] = link;
    });

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (!entry.isIntersecting) return;
            links.forEach(function(link) { link.classList.remove('active'); });
            const active = byId[entry.target.id];
            if (active) active.classList.add('active');
        });
    }, { rootMargin: '-45% 0px -50% 0px' });

    document.querySelectorAll('main section[id]').forEach(function(section) {
        observer.observe(section);
    });
}

function initReveal() {
    const items = document.querySelectorAll('.reveal');

    if (PREFERS_REDUCED_MOTION || !('IntersectionObserver' in window)) {
        items.forEach(function(item) { item.classList.add('is-visible'); });
        return;
    }

    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(function(entry) {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

    items.forEach(function(item) { observer.observe(item); });
}

function showToast(message) {
    const existing = document.querySelector('.toast');
    if (existing) existing.remove();

    const toast = el('div', 'toast', message);
    toast.setAttribute('role', 'status');
    document.body.appendChild(toast);
    requestAnimationFrame(function() { toast.classList.add('show'); });
    setTimeout(function() {
        toast.classList.remove('show');
        setTimeout(function() { toast.remove(); }, 300);
    }, 2200);
}

async function copyToClipboard(text, message) {
    try {
        await navigator.clipboard.writeText(text);
        showToast(message || 'Copied to clipboard');
        return true;
    } catch (err) {
        const area = document.createElement('textarea');
        area.value = text;
        area.setAttribute('readonly', '');
        area.style.position = 'fixed';
        area.style.left = '-9999px';
        document.body.appendChild(area);
        area.select();
        let ok = false;
        try {
            ok = document.execCommand('copy');
        } catch (e) {
            ok = false;
        }
        document.body.removeChild(area);
        showToast(ok ? (message || 'Copied to clipboard') : 'Copy failed, select the text manually');
        return ok;
    }
}

function initCopyButtons() {
    document.querySelectorAll('.copy-btn').forEach(function(button) {
        button.addEventListener('click', async function() {
            const targetId = button.getAttribute('data-copy-target');
            const text = targetId
                ? document.getElementById(targetId).textContent
                : button.getAttribute('data-copy');
            if (!text) return;
            const ok = await copyToClipboard(text.trim() + (targetId ? '\n' : ''), targetId ? 'Script copied' : 'Command copied');
            if (!ok) return;
            button.classList.add('copied');
            if (button.classList.contains('copy-btn-text')) button.textContent = 'Copied';
            setTimeout(function() {
                button.classList.remove('copied');
                if (button.classList.contains('copy-btn-text')) button.textContent = 'Copy';
            }, 1500);
        });
    });
}

function initSpectrumCursor() {
    const plot = document.getElementById('spectrum-plot');
    if (!plot) return;
    const cursor = plot.querySelector('.sp-cursor');
    const readout = plot.querySelector('.sp-readout');

    plot.addEventListener('pointermove', function(event) {
        const box = plot.getBoundingClientRect();
        const frac = Math.min(1, Math.max(0, (event.clientX - box.left) / box.width));
        cursor.style.left = (frac * 100) + '%';
        cursor.classList.toggle('flip', frac > 0.72);
        readout.textContent = 'm/z ' + Math.round(2000 + frac * 18000).toLocaleString('en-US');
        plot.classList.add('is-hover');
    });

    plot.addEventListener('pointerleave', function() {
        plot.classList.remove('is-hover');
    });
}

function initTabs() {
    const tabs = Array.from(document.querySelectorAll('.tabs .tab'));

    const select = function(tab, focus) {
        tabs.forEach(function(t) {
            const selected = t === tab;
            t.setAttribute('aria-selected', String(selected));
            t.tabIndex = selected ? 0 : -1;
            document.getElementById(t.getAttribute('aria-controls')).hidden = !selected;
        });
        if (focus) tab.focus();
        hideTooltip();
    };

    tabs.forEach(function(tab, index) {
        tab.addEventListener('click', function() { select(tab, false); });
        tab.addEventListener('keydown', function(event) {
            let next = null;
            if (event.key === 'ArrowRight') next = tabs[(index + 1) % tabs.length];
            if (event.key === 'ArrowLeft') next = tabs[(index - 1 + tabs.length) % tabs.length];
            if (next) {
                event.preventDefault();
                select(next, true);
            }
        });
    });
}

function compareVersions(a, b) {
    const pa = String(a).split('.').map(function(x) { return parseInt(x, 10) || 0; });
    const pb = String(b).split('.').map(function(x) { return parseInt(x, 10) || 0; });
    for (let i = 0; i < Math.max(pa.length, pb.length); i++) {
        const d = (pa[i] || 0) - (pb[i] || 0);
        if (d !== 0) return d;
    }
    return 0;
}

async function loadVersions() {
    const results = await Promise.all(PACKAGES.map(function(name) {
        return fetchJson('https://pypi.org/pypi/' + name + '/json', 6000)
            .then(function(data) { return data && data.info ? data.info.version : null; })
            .catch(function() { return null; });
    }));

    const versions = {};
    PACKAGES.forEach(function(name, i) { versions[name] = results[i]; });

    if (versions.maldisuite) {
        document.getElementById('latest-version').textContent = 'v' + versions.maldisuite;
    }

    document.querySelectorAll('.pkg-version[data-package]').forEach(function(badge) {
        const version = versions[badge.getAttribute('data-package')];
        if (version) badge.textContent = 'v' + version;
    });

    let live = 0;
    document.querySelectorAll('.compat-latest[data-package]').forEach(function(cell) {
        const version = versions[cell.getAttribute('data-package')];
        if (!version) return;
        live++;
        cell.textContent = version;
        const newer = compareVersions(version, cell.getAttribute('data-max')) >= 0;
        const flag = el('span', 'compat-flag', newer ? '↑ newer than the pin' : '✓ within the pin');
        cell.appendChild(flag);
    });

    const note = document.getElementById('compat-note');
    if (note) {
        note.textContent = live
            ? 'Latest versions read live from PyPI.'
            : 'PyPI did not answer: showing the versions known at release time.';
    }
}

function oklchToRgb(L, C, hue) {
    const h = hue * Math.PI / 180;
    const a = C * Math.cos(h);
    const b = C * Math.sin(h);
    const l = Math.pow(L + 0.3963377774 * a + 0.2158037573 * b, 3);
    const m = Math.pow(L - 0.1055613458 * a - 0.0638541728 * b, 3);
    const s = Math.pow(L - 0.0894841775 * a - 1.2914855480 * b, 3);
    const linear = [
        4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s,
        -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s,
        -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    ];
    return linear.map(function(x) {
        x = Math.min(1, Math.max(0, x));
        const v = x <= 0.0031308 ? 12.92 * x : 1.055 * Math.pow(x, 1 / 2.4) - 0.055;
        return Math.round(v * 255);
    });
}

function luminance(rgb) {
    const c = rgb.map(function(v) {
        v /= 255;
        return v <= 0.04045 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4);
    });
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2];
}

function contrastRatio(y1, y2) {
    return (Math.max(y1, y2) + 0.05) / (Math.min(y1, y2) + 0.05);
}

const INK_DARK = [0, 0, 0];
const INK_LIGHT = [255, 255, 255];

function sequentialColor(t) {
    t = Math.min(1, Math.max(0, t));
    const rgb = isDarkTheme()
        ? oklchToRgb(0.3 + 0.5 * t, 0.03 + 0.09 * t, 205)
        : oklchToRgb(0.965 - 0.53 * t, 0.025 + 0.095 * t, 215);
    const y = luminance(rgb);
    const ink = contrastRatio(y, luminance(INK_DARK)) >= contrastRatio(y, luminance(INK_LIGHT)) ? INK_DARK : INK_LIGHT;
    return { bg: 'rgb(' + rgb.join(',') + ')', fg: 'rgb(' + ink.join(',') + ')' };
}

const AUROC_MIN = 0.5;
const AUROC_MAX = 1.0;

function aurocToT(value) {
    return (value - AUROC_MIN) / (AUROC_MAX - AUROC_MIN);
}

const tooltip = { node: null };

function showTooltip(target, build) {
    if (!tooltip.node) tooltip.node = document.getElementById('chart-tooltip');
    const node = tooltip.node;
    node.replaceChildren();
    build(node);
    node.hidden = false;

    const box = target.getBoundingClientRect();
    const tip = node.getBoundingClientRect();
    let left = box.left + box.width / 2 - tip.width / 2;
    left = Math.max(8, Math.min(left, window.innerWidth - tip.width - 8));
    let top = box.top - tip.height - 10;
    if (top < 8) top = box.bottom + 10;
    node.style.left = left + 'px';
    node.style.top = top + 'px';
}

function hideTooltip() {
    if (tooltip.node) tooltip.node.hidden = true;
}

function bindTooltip(target, build) {
    const show = function() { showTooltip(target, build); };
    target.addEventListener('pointerenter', show);
    target.addEventListener('focus', show);
    target.addEventListener('pointerleave', hideTooltip);
    target.addEventListener('blur', hideTooltip);
}

function tooltipRows(node, rows) {
    const list = el('dl', 'tt-rows');
    rows.forEach(function(row) {
        list.appendChild(el('dt', null, row[0]));
        list.appendChild(el('dd', null, row[1]));
    });
    node.appendChild(list);
}

function fmt(value, digits) {
    return value === null || value === undefined ? 'n/a' : Number(value).toFixed(digits === undefined ? 3 : digits);
}

function buildSegmented(container, options, onSelect) {
    container.replaceChildren();
    const buttons = options.map(function(option, index) {
        const button = el('button', null, option.label);
        button.type = 'button';
        button.setAttribute('role', 'radio');
        button.setAttribute('aria-checked', String(index === 0));
        button.tabIndex = index === 0 ? 0 : -1;
        container.appendChild(button);
        return button;
    });

    const select = function(index, focus) {
        buttons.forEach(function(b, i) {
            b.setAttribute('aria-checked', String(i === index));
            b.tabIndex = i === index ? 0 : -1;
        });
        if (focus) buttons[index].focus();
        onSelect(options[index].value);
    };

    buttons.forEach(function(button, index) {
        button.addEventListener('click', function() { select(index, false); });
        button.addEventListener('keydown', function(event) {
            let next = null;
            if (event.key === 'ArrowRight' || event.key === 'ArrowDown') next = (index + 1) % buttons.length;
            if (event.key === 'ArrowLeft' || event.key === 'ArrowUp') next = (index - 1 + buttons.length) % buttons.length;
            if (next !== null) {
                event.preventDefault();
                select(next, true);
            }
        });
    });

    select(0, false);
}

function shortSpecies(name) {
    const parts = String(name).split(' ');
    return parts.length > 1 ? parts[0].charAt(0) + '. ' + parts.slice(1).join(' ') : name;
}

async function loadResults() {
    const heatmap = document.getElementById('heatmap');
    const bars = document.getElementById('batch-bars');
    if (!heatmap || !bars) return;

    let data;
    try {
        data = await fetchJson('data/results.json');
    } catch (error) {
        console.error('Error loading results:', error);
        heatmap.appendChild(el('p', 'chart-note', 'The benchmark data could not be loaded.'));
        return;
    }

    const clf = data.classification;
    let currentTask = 0;
    const renderHeatmap = function() {
        renderAurocTable(heatmap, clf, clf.tasks[currentTask]);
        updateRampLegend();
    };

    buildSegmented(document.getElementById('task-picker'), clf.tasks.map(function(task, i) {
        return { label: shortSpecies(task.species) + ' / ' + task.drug, value: i };
    }), function(index) {
        currentTask = index;
        renderHeatmap();
    });

    const experiments = data.batchCorrection.experiments;
    buildSegmented(document.getElementById('experiment-picker'), experiments.map(function(exp, i) {
        return { label: exp.title, value: i };
    }), function(index) {
        renderBatchBars(bars, experiments[index]);
    });

    document.addEventListener('themechange', renderHeatmap);
}

function updateRampLegend() {
    const bar = document.querySelector('.ramp-bar');
    if (!bar) return;
    const stops = [0, 0.25, 0.5, 0.75, 1].map(function(t) {
        return sequentialColor(t).bg + ' ' + (t * 100) + '%';
    });
    bar.style.setProperty('--ramp', 'linear-gradient(90deg, ' + stops.join(', ') + ')');
}

function renderAurocTable(container, clf, task) {
    const table = el('table', 'heatmap');
    const caption = el('caption', 'visually-hidden',
        'Mean AUROC of each classifier at each DRIAMS site, ' + task.species + ' / ' + task.drug);
    table.appendChild(caption);

    const best = {};
    clf.sites.forEach(function(site) {
        const cells = task.cells[site];
        if (!cells) return;
        let top = null;
        Object.keys(cells).forEach(function(id) {
            if (top === null || cells[id].auroc > cells[top].auroc) top = id;
        });
        best[site] = top;
    });

    const thead = el('thead');
    const headRow = el('tr');
    const corner = el('th');
    corner.appendChild(el('span', 'visually-hidden', 'Classifier'));
    headRow.appendChild(corner);
    clf.sites.forEach(function(site) {
        const th = el('th');
        const parts = site.split('-');
        if (parts.length > 1) {
            th.appendChild(el('span', 'site-prefix', parts.slice(0, -1).join('-') + '-'));
        }
        th.appendChild(document.createTextNode(parts[parts.length - 1]));
        th.scope = 'col';
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = el('tbody');
    clf.classifiers.forEach(function(classifier) {
        const row = el('tr');
        const th = el('th', null, classifier.label);
        th.scope = 'row';
        row.appendChild(th);

        clf.sites.forEach(function(site) {
            const metrics = task.cells[site] && task.cells[site][classifier.id];
            if (!metrics) {
                row.appendChild(el('td', 'na', 'n/a'));
                return;
            }
            const color = sequentialColor(aurocToT(metrics.auroc));
            const td = el('td', 'has-value');
            td.tabIndex = 0;
            td.style.backgroundColor = color.bg;
            td.style.color = color.fg;
            td.appendChild(el('span', 'cell-value', fmt(metrics.auroc, 2)));
            td.appendChild(el('span', 'cell-sd', '±' + fmt(metrics.aurocSd, 2)));
            if (best[site] === classifier.id) {
                const star = el('span', 'cell-best', '★');
                star.setAttribute('aria-hidden', 'true');
                td.appendChild(star);
                td.appendChild(el('span', 'visually-hidden', ' best at this site'));
            }
            bindTooltip(td, function(node) {
                node.appendChild(el('p', 'tt-title', classifier.label + ' · ' + site));
                node.appendChild(el('p', 'tt-main', 'AUROC ' + fmt(metrics.auroc) + ' ± ' + fmt(metrics.aurocSd)));
                tooltipRows(node, [
                    ['Balanced accuracy', fmt(metrics.balancedAccuracy)],
                    ['MCC', fmt(metrics.mcc)],
                    ['VME', fmt(metrics.vme)],
                    ['ME', fmt(metrics.me)],
                    ['Fits', String(metrics.fits)]
                ]);
            });
            row.appendChild(td);
        });
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    container.replaceChildren(table);
}

const BATCH_METRICS = [
    { key: 'kbet_acceptance', label: 'kBET acceptance' },
    { key: 'lisi_batch_normalized', label: 'LISI, batch (normalised)' },
    { key: 'species_preservation', label: 'Species preservation' }
];

function renderBatchBars(container, experiment) {
    const metrics = BATCH_METRICS.filter(function(metric) {
        return experiment.methods.some(function(m) { return m[metric.key] !== null; });
    });
    const baseline = experiment.methods.find(function(m) { return m.uncorrected; });
    const others = experiment.methods.filter(function(m) { return !m.uncorrected; })
        .sort(function(a, b) { return (b.kbet_acceptance || 0) - (a.kbet_acceptance || 0); });
    const rows = baseline ? [baseline].concat(others) : others;

    const table = el('table', 'bars');
    table.appendChild(el('caption', 'visually-hidden',
        'Batch-mixing metrics of each corrector, ' + experiment.title + ', ' + experiment.detail + ', DRIAMS sites A to D'));

    const thead = el('thead');
    const headRow = el('tr');
    const first = el('th', null, 'Corrector');
    first.scope = 'col';
    headRow.appendChild(first);
    metrics.forEach(function(metric) {
        const th = el('th', null, metric.label);
        th.scope = 'col';
        headRow.appendChild(th);
    });
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = el('tbody');
    rows.forEach(function(method) {
        const row = el('tr', method.uncorrected ? 'is-baseline' : null);
        const th = el('th', null, method.uncorrected ? 'Uncorrected' : method.label);
        th.scope = 'row';
        th.title = method.uncorrected ? 'Uncorrected' : method.label;
        row.appendChild(th);

        metrics.forEach(function(metric) {
            const value = method[metric.key];
            const td = el('td');
            td.setAttribute('data-label', metric.label);
            const cell = el('div', 'bar-cell');
            const track = el('div', 'bar-track');
            const bar = el('span', 'bar');
            bar.style.width = (Math.max(0, Math.min(1, value || 0)) * 100) + '%';
            track.appendChild(bar);
            if (baseline && baseline[metric.key] !== null && !method.uncorrected) {
                const ref = el('span', 'bar-ref');
                ref.style.left = (baseline[metric.key] * 100) + '%';
                track.appendChild(ref);
            }
            cell.appendChild(track);
            cell.appendChild(el('span', 'bar-value', fmt(value)));
            td.appendChild(cell);

            if (value !== null) {
                td.tabIndex = 0;
                bindTooltip(td, function(node) {
                    node.appendChild(el('p', 'tt-title', (method.uncorrected ? 'Uncorrected' : method.label) + ' · ' + metric.label));
                    node.appendChild(el('p', 'tt-main', fmt(value)));
                    if (baseline && !method.uncorrected && baseline[metric.key] !== null) {
                        const delta = value - baseline[metric.key];
                        tooltipRows(node, [['vs uncorrected', (delta >= 0 ? '+' : '−') + fmt(Math.abs(delta))]]);
                    }
                });
            }
            row.appendChild(td);
        });
        tbody.appendChild(row);
    });
    table.appendChild(tbody);
    container.replaceChildren(table);
}

function initials(given) {
    return String(given || '').split(/[\s-]+/).filter(Boolean).map(function(part) {
        return part.charAt(0).toUpperCase() + '.';
    }).join(' ');
}

function shortAuthors(authors) {
    const list = authors.slice(0, 3).map(function(a) {
        return a.family + ', ' + initials(a.given);
    });
    return list.join(', ') + (authors.length > 3 ? ' et al.' : '');
}

function fullAuthors(authors) {
    return authors.map(function(a) { return a.given + ' ' + a.family; }).join(', ');
}

async function loadPublications() {
    const container = document.getElementById('publications');
    if (!container) return;

    let data;
    try {
        data = await fetchJson('data/publications.json');
    } catch (error) {
        console.error('Error loading publications:', error);
        return;
    }

    const publications = (data.publications || []).slice().sort(function(a, b) {
        return (b.featured ? 1 : 0) - (a.featured ? 1 : 0) || String(b.year || '').localeCompare(String(a.year || ''));
    });

    container.replaceChildren.apply(container, publications.map(createPublicationCard));
}

function createPublicationCard(paper) {
    const card = el('article', 'paper' + (paper.featured ? ' paper-featured' : ''));
    const authors = paper.authors || [];

    const meta = el('div', 'paper-meta');
    if (paper.kind) meta.appendChild(el('span', 'paper-kind', paper.kind));
    if (paper.status) meta.appendChild(el('span', 'paper-status', paper.status));
    meta.appendChild(el('span', null, [paper.journal, paper.year].filter(Boolean).join(' · ')));
    card.appendChild(meta);

    card.appendChild(el('h3', 'paper-title', paper.title));
    card.appendChild(el('p', 'paper-authors', paper.doi ? shortAuthors(authors) : fullAuthors(authors)));

    if (paper.doi) {
        const journal = el('p', 'paper-journal');
        journal.appendChild(el('em', null, paper.journal));
        journal.appendChild(document.createTextNode(
            (paper.volume ? ' ' + paper.volume : '') + (paper.pages ? ', ' + paper.pages : '') + ' (' + paper.year + ')'));
        card.appendChild(journal);
    }

    if (paper.note) card.appendChild(el('p', 'paper-note', paper.note));

    if (paper.doi) {
        const actions = el('div', 'paper-actions');
        const read = el('a', 'btn btn-primary', 'Read the paper');
        read.href = 'https://doi.org/' + paper.doi;
        read.target = '_blank';
        read.rel = 'noopener';
        actions.appendChild(read);

        const toggle = el('button', 'btn btn-ghost', 'Cite');
        toggle.type = 'button';
        toggle.setAttribute('aria-expanded', 'false');
        actions.appendChild(toggle);
        card.appendChild(actions);

        const panel = createCitePanel(paper);
        panel.hidden = true;
        card.appendChild(panel);

        toggle.addEventListener('click', function() {
            const open = panel.hidden;
            panel.hidden = !open;
            toggle.setAttribute('aria-expanded', String(open));
        });
    }

    return card;
}

const CITE_FORMATS = [
    { id: 'bibtex', label: 'BibTeX' },
    { id: 'apa', label: 'APA' },
    { id: 'ris', label: 'RIS' }
];

function createCitePanel(paper) {
    const panel = el('div', 'cite-panel');
    const tabs = el('div', 'cite-tabs');
    tabs.setAttribute('role', 'tablist');
    tabs.setAttribute('aria-label', 'Citation format');
    const body = el('pre', 'cite-body');
    let format = 'bibtex';

    const buttons = CITE_FORMATS.map(function(f) {
        const button = el('button', 'cite-tab', f.label);
        button.type = 'button';
        button.setAttribute('role', 'tab');
        button.addEventListener('click', function() {
            format = f.id;
            render();
        });
        tabs.appendChild(button);
        return button;
    });

    const copy = el('button', 'cite-copy', 'Copy');
    copy.type = 'button';
    copy.addEventListener('click', function() {
        copyToClipboard(formatCitation(paper, format), 'Citation copied');
    });
    tabs.appendChild(copy);

    const render = function() {
        body.textContent = formatCitation(paper, format);
        buttons.forEach(function(button, i) {
            button.setAttribute('aria-selected', String(CITE_FORMATS[i].id === format));
        });
    };

    panel.appendChild(tabs);
    panel.appendChild(body);
    render();
    return panel;
}

function formatCitation(paper, format) {
    const authors = paper.authors || [];
    const doiUrl = 'https://doi.org/' + paper.doi;

    if (format === 'bibtex') {
        return '@article{' + (paper.bibKey || 'maldisuite' + paper.year) + ',\n' +
            '  title   = {' + paper.title + '},\n' +
            '  author  = {' + authors.map(function(a) { return a.family + ', ' + a.given; }).join(' and ') + '},\n' +
            '  journal = {' + paper.journal + '},\n' +
            (paper.volume ? '  volume  = {' + paper.volume + '},\n' : '') +
            (paper.pages ? '  pages   = {' + paper.pages + '},\n' : '') +
            '  year    = {' + paper.year + '},\n' +
            '  doi     = {' + paper.doi + '}\n' +
            '}';
    }

    if (format === 'apa') {
        const names = authors.map(function(a) { return a.family + ', ' + initials(a.given); });
        let authorText = names[0] || '';
        if (names.length === 2) {
            authorText = names[0] + ', & ' + names[1];
        } else if (names.length > 2 && names.length <= 20) {
            authorText = names.slice(0, -1).join(', ') + ', & ' + names[names.length - 1];
        } else if (names.length > 20) {
            authorText = names.slice(0, 19).join(', ') + ', ... ' + names[names.length - 1];
        }
        return authorText + ' (' + paper.year + '). ' + paper.title + '. ' + paper.journal +
            (paper.volume ? ', ' + paper.volume : '') + (paper.pages ? ', ' + paper.pages : '') + '. ' + doiUrl;
    }

    return ['TY  - JOUR']
        .concat(authors.map(function(a) { return 'AU  - ' + a.family + ', ' + a.given; }))
        .concat([
            'TI  - ' + paper.title,
            'JO  - ' + paper.journal,
            paper.volume ? 'VL  - ' + paper.volume : null,
            paper.pages ? 'SP  - ' + paper.pages : null,
            'PY  - ' + paper.year,
            'DO  - ' + paper.doi,
            'UR  - ' + doiUrl,
            'ER  - '
        ].filter(Boolean))
        .join('\n');
}

const STATUS_LABELS = {
    released: 'Released',
    development: 'In development',
    planned: 'Planned'
};

const ROADMAP_STAGES = [
    { key: 'latest', label: 'Latest release', status: 'released' },
    { key: 'now', label: 'Now', status: 'development' },
    { key: 'next', label: 'Next', status: 'planned' },
    { key: 'later', label: 'Later', status: 'planned' }
];
const STAGE_KEYS = ROADMAP_STAGES.map(function(stage) { return stage.key; });

async function loadRoadmap() {
    const container = document.getElementById('roadmap-lanes');
    if (!container) return;

    let lanes;
    try {
        lanes = (await fetchJson('data/roadmap.json')).lanes || [];
    } catch (error) {
        console.error('Error loading roadmap:', error);
        return;
    }

    container.replaceChildren.apply(container, lanes.map(function(lane) {
        const row = el('div', 'lane' + (lane.package && lane.package !== 'suite' ? ' pkg-' + lane.package : ''));
        const name = el('h3', 'lane-name');
        if (lane.changelog) {
            const link = el('a', null, lane.name);
            link.href = lane.changelog;
            link.target = '_blank';
            link.rel = 'noopener';
            name.appendChild(link);
        } else {
            name.textContent = lane.name;
        }
        row.appendChild(name);

        const releases = lane.releases || [];
        ROADMAP_STAGES.forEach(function(stage) {
            const items = releases.filter(function(release) {
                return (STAGE_KEYS.indexOf(release.stage) >= 0 ? release.stage : 'later') === stage.key;
            });
            const cell = el('div', 'lane-stage ' + stage.key + (items.length ? '' : ' empty'));
            if (items.length) {
                cell.appendChild(el('p', 'lane-stage-label', stage.label));
                const track = el('ol', 'lane-track');
                items.forEach(function(release) {
                    const item = el('li', 'milestone ' + stage.status);
                    const mark = el('span', 'status-mark ' + stage.status);
                    mark.setAttribute('aria-hidden', 'true');
                    item.appendChild(mark);
                    item.appendChild(el('span', 'milestone-theme', release.theme));
                    item.appendChild(el('span', 'milestone-version', release.version));
                    item.appendChild(el('span', 'visually-hidden', ' (' + STATUS_LABELS[stage.status] + ')'));
                    track.appendChild(item);
                });
                cell.appendChild(track);
            }
            row.appendChild(cell);
        });
        return row;
    }));
}
