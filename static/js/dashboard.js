// Dashboard Chart.js Analytics Controller
document.addEventListener('DOMContentLoaded', () => {
    const trendCtx = document.getElementById('scoreTrendChart');
    const roleCtx = document.getElementById('roleScoreChart');

    if (!trendCtx || !roleCtx) return;

    fetch('/api/dashboard/analytics')
        .then(res => res.json())
        .then(data => {
            // Theme dependent color scheme
            const isDark = document.documentElement.getAttribute('data-theme') !== 'light';
            const textColor = isDark ? '#94a3b8' : '#64748b';
            const gridColor = isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';

            // Line Chart: Score History Trend
            new Chart(trendCtx, {
                type: 'line',
                data: {
                    labels: data.trend_labels.length > 0 ? data.trend_labels : ['No Data'],
                    datasets: [{
                        label: 'Overall Score (0-100)',
                        data: data.trend_scores.length > 0 ? data.trend_scores : [0],
                        borderColor: '#6366f1',
                        backgroundColor: 'rgba(99, 102, 241, 0.15)',
                        borderWidth: 3,
                        tension: 0.35,
                        fill: true,
                        pointBackgroundColor: '#22d3ee',
                        pointRadius: 5,
                        pointHoverRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });

            // Bar Chart: Average Score by Role
            new Chart(roleCtx, {
                type: 'bar',
                data: {
                    labels: data.role_labels.length > 0 ? data.role_labels : ['Web Dev', 'Python', 'Java', 'HR'],
                    datasets: [{
                        label: 'Avg Score',
                        data: data.role_averages.length > 0 ? data.role_averages : [75, 80, 85, 90],
                        backgroundColor: [
                            'rgba(99, 102, 241, 0.7)',
                            'rgba(34, 211, 238, 0.7)',
                            'rgba(52, 211, 153, 0.7)',
                            'rgba(251, 191, 36, 0.7)'
                        ],
                        borderRadius: 8
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            min: 0,
                            max: 100,
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        },
                        x: {
                            ticks: { color: textColor },
                            grid: { color: gridColor }
                        }
                    },
                    plugins: {
                        legend: { display: false }
                    }
                }
            });
        })
        .catch(err => console.error('Error loading dashboard analytics:', err));
});
