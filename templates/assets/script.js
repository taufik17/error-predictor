document.getElementById('csvFileInput').addEventListener('change', function (e) {
    const file = e.target.files[0];
    if (!file) {
        return;
    }

    const reader = new FileReader();
    reader.onload = function (e) {
        const text = e.target.result;
        displayCSV(text);
    };
    reader.readAsText(file);
});

function displayCSV(text) {
    const lines = text.split('\n');
    const tableHead = document.getElementById('csvTableHead');
    const tableBody = document.getElementById('csvTableBody');

    tableHead.innerHTML = '';
    tableBody.innerHTML = '';

    if (lines.length > 0) {
        const headers = lines[0].split(',');
        const headerRow = document.createElement('tr');
        headers.forEach(header => {
            const th = document.createElement('th');
            th.textContent = header.trim();
            headerRow.appendChild(th);
        });
        tableHead.appendChild(headerRow);
    }

    for (let i = 1; i < lines.length; i++) {
        const row = lines[i].split(',');
        const tr = document.createElement('tr');
        row.forEach(cell => {
            const td = document.createElement('td');
            td.textContent = cell.trim();
            tr.appendChild(td);
        });
        tableBody.appendChild(tr);
    }
}
