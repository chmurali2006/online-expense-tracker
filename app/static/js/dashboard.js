(function () {
  var data = window.dashboardChart || {};
  var axisColor = "#6B6A60";
  var ruleColor = "#DDD5C4";
  var mono = "IBM Plex Mono";
  var sans = "IBM Plex Sans, system-ui, sans-serif";

  if (window.Chart) {
    window.Chart.register({
      id: "pieLabels",
      afterDatasetsDraw: function (chart, args, options) {
        if (!options || !options.enabled) return;

        var slices = chart.getDatasetMeta(0).data;
        if (!slices.length) return;

        var values = chart.data.datasets[0].data.map(Number);
        var total = values.reduce(function (sum, value) { return sum + (value > 0 ? value : 0); }, 0);
        if (!total) return;

        var ctx = chart.ctx;
        var compact = chart.width < 230;
        var nameSize = compact ? 9 : 10;
        var pctSize = compact ? 10 : 11;

        ctx.save();
        ctx.textAlign = "center";
        ctx.textBaseline = "middle";
        ctx.lineJoin = "round";
        ctx.lineWidth = compact ? 2 : 3;
        ctx.strokeStyle = "rgba(24, 24, 21, 0.45)";
        ctx.fillStyle = "#FFFDF8";

        function paint(text, x, y, size, family) {
          if (!text) return;
          ctx.font = "600 " + size + "px " + family;
          ctx.strokeText(text, x, y);
          ctx.fillText(text, x, y);
        }

        slices.forEach(function (arc, index) {
          var value = values[index];
          if (!(value > 0)) return;

          var angle = arc.endAngle - arc.startAngle;
          if (angle < 0.22) return; // hairline slices stay readable in the legend

          var mid = (arc.startAngle + arc.endAngle) / 2;
          var share = Math.round(value / total * 100) + "%";

          if (angle >= 0.65) {
            var name = String(chart.data.labels[index] || "");
            var maxChars = Math.max(4, Math.floor((angle * arc.outerRadius * 0.52) / (nameSize * 0.62)));
            if (name.length > maxChars) name = name.slice(0, maxChars - 1) + "\u2026";
            var r = arc.outerRadius * 0.62;
            var x = arc.x + Math.cos(mid) * r;
            var y = arc.y + Math.sin(mid) * r;
            paint(name, x, y - 7, nameSize, sans);
            paint(share, x, y + 7, pctSize, mono);
          } else {
            var tiny = angle < 0.38;
            var rSmall = arc.outerRadius * (tiny ? 0.8 : 0.72);
            var size = tiny ? Math.max(8, pctSize - 2) : pctSize;
            paint(share, arc.x + Math.cos(mid) * rSmall, arc.y + Math.sin(mid) * rSmall, size, mono);
          }
        });

        ctx.restore();
      }
    });
  }

  function unavailable(box) {
    if (box) box.innerHTML = '<p class="muted small">Chart not available on this load.</p>';
  }

  function dailyChart() {
    var box = document.getElementById("chart-box");
    var canvas = document.getElementById("daily-chart");
    if (!box || !canvas || !window.Chart || !data.labels || !data.values) {
      unavailable(box);
      return;
    }

    new Chart(canvas, {
      type: "bar",
      data: {
        labels: data.labels.map(function (value) { return String(value); }),
        datasets: [{
          label: "Spent",
          data: data.values,
          backgroundColor: "#2F5D50",
          hoverBackgroundColor: "#27493F",
          borderWidth: 0,
          categoryPercentage: 0.9,
          barPercentage: 0.95
        }]
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          legend: { display: false },
          tooltip: {
            displayColors: false,
            callbacks: {
              title: function (items) { return "Day " + items[0].label; },
              label: function (item) { return "\u20B9 " + item.parsed.y.toFixed(2); }
            }
          }
        },
        scales: {
          x: {
            grid: { display: false, color: ruleColor },
            border: { color: ruleColor },
            ticks: {
              color: axisColor,
              font: { family: mono, size: 10 },
              maxTicksLimit: window.innerWidth < 500 ? 8 : 16
            }
          },
          y: {
            beginAtZero: true,
            grid: { color: ruleColor },
            border: { display: false },
            ticks: { color: axisColor, font: { family: mono, size: 10 } }
          }
        }
      }
    });
  }

  function categoryChart() {
    var box = document.getElementById("pie-box");
    var canvas = document.getElementById("category-chart");
    var labels = data.categoryLabels || [];
    if (!box || !canvas || !window.Chart || !labels.length) return;

    new Chart(canvas, {
      type: "pie",
      data: {
        labels: labels,
        datasets: [{
          data: data.categoryValues || [],
          backgroundColor: data.categoryColors || [],
          borderColor: "#FFFDF8",
          borderWidth: 2,
          hoverOffset: 6
        }]
      },
      options: {
        animation: false,
        responsive: true,
        maintainAspectRatio: false,
        plugins: {
          pieLabels: { enabled: true },
          legend: { display: false },
          tooltip: {
            callbacks: {
              label: function (item) {
                var total = item.dataset.data.reduce(function (sum, value) { return sum + value; }, 0);
                var share = total ? Math.round(item.parsed / total * 100) : 0;
                return item.label + ": \u20B9 " + item.parsed.toFixed(2) + " (" + share + "%)";
              }
            }
          }
        }
      }
    });
  }

  dailyChart();
  categoryChart();
})();
