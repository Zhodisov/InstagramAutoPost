document.addEventListener('DOMContentLoaded', () => {
  setupWebSocket();
  fetchStats();
  fetchDownloadUploadData();
  fetchProcessingTimeData();
  fetchRecentMedia();
});

async function fetchStats() {
  try {
      const response = await fetch("/api/stats/summary");
      const data = await response.json();
      document.getElementById("total-downloaded").textContent = data.total_downloaded || 0;
      document.getElementById("total-uploaded").textContent = data.total_uploaded || 0;
      document.getElementById("upload-success-rate").textContent = data.upload_success_rate || '0%';
  } catch (error) {
      console.error(error);
  }
}

async function fetchDownloadUploadData() {
  try {
      const response = await fetch("/api/stats/downloads-uploads-per-day");
      const stats = await response.json();

      const dates = stats.map(item => item.date);
      const downloads = stats.map(item => item.downloads);
      const uploads = stats.map(item => item.uploads);

      const ctx = document.getElementById('downloadUploadChart').getContext('2d');
      if (window.downloadUploadChartInstance) {
          window.downloadUploadChartInstance.destroy();
      }
      window.downloadUploadChartInstance = new Chart(ctx, {
          type: 'line',
          data: {
              labels: dates,
              datasets: [
                  {
                      label: 'Téléchargements',
                      data: downloads,
                      backgroundColor: 'rgba(37, 99, 235, 0.2)',
                      borderColor: 'rgba(37, 99, 235, 1)',
                      borderWidth: 2,
                      fill: false,
                      tension: 0.4
                  },
                  {
                      label: 'Uploads',
                      data: uploads,
                      backgroundColor: 'rgba(16, 185, 129, 0.2)',
                      borderColor: 'rgba(16, 185, 129, 1)',
                      borderWidth: 2,
                      fill: false,
                      tension: 0.4
                  }
              ]
          },
          options: {
              scales: {
                  x: {
                      title: {
                          display: true,
                          text: 'Date'
                      }
                  },
                  y: {
                      title: {
                          display: true,
                          text: 'Nombre'
                      },
                      beginAtZero: true,
                      ticks: {
                          stepSize: 1
                      }
                  }
              },
              responsive: true
          }
      });
  } catch (error) {
      console.error(error);
  }
}

async function fetchProcessingTimeData() {
  try {
      const response = await fetch("/api/stats/processing-time-per-day");
      const stats = await response.json();

      const dates = stats.map(item => item.date);
      const processingTimes = stats.map(item => item.average_processing_time);

      const ctx = document.getElementById('processingTimeChart').getContext('2d');
      if (window.processingTimeChartInstance) {
          window.processingTimeChartInstance.destroy();
      }
      window.processingTimeChartInstance = new Chart(ctx, {
          type: 'bar',
          data: {
              labels: dates,
              datasets: [{
                  label: '',
                  data: processingTimes,
                  backgroundColor: 'rgba(234, 179, 8, 0.7)',
                  borderWidth: 1
              }]
          },
          options: {
              scales: {
                  x: {
                      title: {
                          display: true,
                          text: 'Date'
                      }
                  },
                  y: {
                      title: {
                          display: true,
                          text: ''
                      },
                      beginAtZero: true
                  }
              },
              responsive: true
          }
      });
  } catch (error) {
      console.error(error);
  }
}

async function fetchRecentMedia() {
  try {
      const response = await fetch("/api/media/recent");
      const data = await response.json();
      updateMediaTable(data.media);
  } catch (error) {
      console.error(error);
  }
}

function updateMediaTable(mediaList) {
  const tableBody = document.getElementById('media-table-body');
  tableBody.innerHTML = '';
  mediaList.forEach(media => {
      const row = document.createElement('tr');
      row.classList.add('border-b', 'border-gray-200', 'hover:bg-gray-100');
      row.innerHTML = `
          <td class="px-5 py-5 text-sm">${media.media_pk}</td>
          <td class="px-5 py-5 text-sm">${new Date(media.download_date).toLocaleString()}</td>
          <td class="px-5 py-5 text-sm">${media.upload_date ? new Date(media.upload_date).toLocaleString() : 'N/A'}</td>
          <td class="px-5 py-5 text-sm">${media.upload_status}</td>
          <td class="px-5 py-5 text-sm">${media.processing_time ? media.processing_time.toFixed(2) + 's' : 'N/A'}</td>
      `;
      tableBody.appendChild(row);
  });
}
