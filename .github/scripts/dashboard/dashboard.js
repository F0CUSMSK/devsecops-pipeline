/* ============================================
   DevSecOps Security Dashboard — v2.0 JS
   Enterprise SOC Interactions
   ============================================ */

document.addEventListener('DOMContentLoaded', () => {
  initAnimatedCounters();
  initDonutChart();
  initSeverityBar();
  initCollapsiblePanels();
  initTableRowAnimations();
});

/* ---------- Animated Counters ---------- */
function initAnimatedCounters() {
  const counters = document.querySelectorAll('[data-counter]');

  counters.forEach((el) => {
    const target = parseInt(el.getAttribute('data-counter'), 10);
    if (isNaN(target) || target === 0) {
      el.textContent = '0';
      return;
    }

    el.textContent = '0';

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            animateValue(el, 0, target, 1400);
            observer.unobserve(el);
          }
        });
      },
      { threshold: 0.2 }
    );

    observer.observe(el);
  });
}

function animateValue(element, start, end, duration) {
  const startTime = performance.now();

  function easeOutQuart(t) {
    return 1 - Math.pow(1 - t, 4);
  }

  function step(currentTime) {
    const elapsed = currentTime - startTime;
    const progress = Math.min(elapsed / duration, 1);
    const value = Math.round(start + (end - start) * easeOutQuart(progress));

    element.textContent = value.toLocaleString();

    if (progress < 1) {
      requestAnimationFrame(step);
    }
  }

  requestAnimationFrame(step);
}

/* ---------- Donut Chart ---------- */
function initDonutChart() {
  const chart = document.getElementById('donut-chart');
  if (!chart) return;

  const critical = parseInt(chart.dataset.critical || '0', 10);
  const high     = parseInt(chart.dataset.high || '0', 10);
  const medium   = parseInt(chart.dataset.medium || '0', 10);
  const low      = parseInt(chart.dataset.low || '0', 10);
  const total    = critical + high + medium + low;

  if (total === 0) return;

  const radius = 55;
  const circumference = 2 * Math.PI * radius;
  const segments = [
    { className: 'donut-seg--critical', value: critical, color: '#dc2626' },
    { className: 'donut-seg--high',     value: high,     color: '#ea580c' },
    { className: 'donut-seg--medium',   value: medium,   color: '#ca8a04' },
    { className: 'donut-seg--low',      value: low,      color: '#16a34a' },
  ];

  let offset = 0;

  segments.forEach((seg) => {
    const circle = chart.querySelector('.' + seg.className);
    if (!circle) return;

    const pct = seg.value / total;
    const segLength = pct * circumference;

    // Set initial state (hidden)
    circle.setAttribute('stroke-dasharray', `0 ${circumference}`);
    circle.setAttribute('stroke-dashoffset', -offset);
    circle.setAttribute('stroke', seg.color);

    // Animate in after a delay
    requestAnimationFrame(() => {
      setTimeout(() => {
        circle.style.transition = 'stroke-dasharray 0.8s cubic-bezier(0.22, 1, 0.36, 1)';
        circle.setAttribute('stroke-dasharray', `${segLength} ${circumference - segLength}`);
      }, 400);
    });

    offset += segLength;
  });

  // Update percentages in legend
  const legendItems = document.querySelectorAll('.donut-legend__pct');
  const values = [critical, high, medium, low];
  legendItems.forEach((item, i) => {
    const pct = total > 0 ? ((values[i] / total) * 100).toFixed(0) : 0;
    item.textContent = pct + '%';
  });

  // Percentage in stat cards
  const pctElements = document.querySelectorAll('[data-pct-of]');
  pctElements.forEach((el) => {
    const value = parseInt(el.getAttribute('data-pct-of'), 10);
    if (!isNaN(value) && total > 0) {
      const pct = ((value / total) * 100).toFixed(1);
      el.textContent = pct + '% of total';
    }
  });
}

/* ---------- Severity Distribution Bar ---------- */
function initSeverityBar() {
  const bar = document.getElementById('severity-bar');
  if (!bar) return;

  const segments = bar.querySelectorAll('.severity-bar__segment');

  // Animate widths from 0 after a delay
  setTimeout(() => {
    segments.forEach((seg) => {
      const targetFlex = seg.getAttribute('data-flex');
      if (targetFlex) {
        seg.style.flex = targetFlex;
      }
    });
  }, 600);
}

/* ---------- Collapsible Findings Panels ---------- */
function initCollapsiblePanels() {
  const panels = document.querySelectorAll('.findings-panel');

  panels.forEach((panel) => {
    const head = panel.querySelector('.findings-panel__head');
    if (!head) return;

    head.addEventListener('click', () => {
      panel.classList.toggle('findings-panel--collapsed');
    });

    // Keyboard accessibility
    head.setAttribute('tabindex', '0');
    head.setAttribute('role', 'button');
    head.addEventListener('keydown', (e) => {
      if (e.key === 'Enter' || e.key === ' ') {
        e.preventDefault();
        panel.classList.toggle('findings-panel--collapsed');
      }
    });
  });
}

/* ---------- Table Row Stagger Animation ---------- */
function initTableRowAnimations() {
  const tables = document.querySelectorAll('.findings-table');

  tables.forEach((table) => {
    const rows = table.querySelectorAll('tbody tr');

    rows.forEach((row) => {
      row.style.opacity = '0';
      row.style.transform = 'translateY(6px)';
      row.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
    });

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            const visibleRows = entry.target.querySelectorAll('tbody tr');
            visibleRows.forEach((row, i) => {
              setTimeout(() => {
                row.style.opacity = '1';
                row.style.transform = 'translateY(0)';
              }, i * 35);
            });
            observer.unobserve(entry.target);
          }
        });
      },
      { threshold: 0.05 }
    );

    observer.observe(table);
  });
}
