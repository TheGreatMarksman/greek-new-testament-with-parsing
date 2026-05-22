async function loadCSV() {
  const response = await fetch("/greek_new_testament_with_parsing/greek_new_testament_with_parsing.csv");
  // console.log("Fetch response:", response);
  const text = await response.text();
  // console.log("CSV text:", text);

  const rows = text.trim().split("\n").map(r => r.split(","));

  const headers = rows[0];
  const data = rows.slice(1);

  // Build header
  const thead = document.querySelector("#csvTable thead");
  thead.innerHTML =
    "<tr>" + headers.map(h => `<th>${h}</th>`).join("") + "</tr>";

  // Build body
  const tbody = document.querySelector("#csvTable tbody");
  tbody.innerHTML = data
    .map(row => "<tr>" + row.map(c => `<td>${c}</td>`).join("") + "</tr>")
    .join("");

  // Activate DataTables
  $("#csvTable").DataTable({ 
    pageLength: 25,
    responsive: true
  });
}

loadCSV();