import axios from 'axios';
import axiosRetry from 'axios-retry';

// Setup axios-retry to retry failed requests up to 3 times with exponential backoff
axiosRetry(axios, {
  retries: 3,
  retryDelay: axiosRetry.exponentialDelay,
  shouldResetTimeout: true,
});

async function loadExamTable() {
  const table = document.getElementById("examTable");
  table.innerHTML = "";

  try {
    const response = await axios.get('/exams');  // Axios handles JSON parsing automatically
    const exams = response.data;

    exams.forEach(exam => {
      const row = `
        <tr class="hover:bg-gray-50">
          <td class="p-3 border">${exam.id}</td>
          <td class="p-3 border">${exam.title}</td>
          <td class="p-3 border">${exam.start_time}</td>
          <td class="p-3 border">${exam.end_time}</td>
          <td class="p-3 border">
            <span class="px-2 py-1 rounded text-white text-sm ${getStatusColor(exam.status)}">
              ${exam.status}
            </span>
          </td>
          <td class="p-3 border text-center">
            <button onclick="viewExam('${exam.id}')"
                    class="text-blue-500 hover:underline mr-2">View</button>

            <button onclick="editExam('${exam.id}')"
                    class="text-yellow-600 hover:underline mr-2">Edit</button>

            <button onclick="deleteExam('${exam.id}')"
                    class="text-red-600 hover:underline">Delete</button>
          </td>
        </tr>
      `;
      table.innerHTML += row;
    });

  } catch (error) {
    console.error(error);
    table.innerHTML = `<tr><td colspan="6" class="text-center p-3">Failed to load exams</td></tr>`;
  }
}

// your other helper functions remain unchanged
function getStatusColor(status) {
  switch (status) {
    case "Active": return "bg-green-600";
    case "Upcoming": return "bg-blue-600";
    case "Completed": return "bg-gray-600";
    default: return "bg-black";
  }
}

function viewExam(id) {
  alert("View exam: " + id);
}

function editExam(id) {
  alert("Edit exam: " + id);
}

function deleteExam(id) {
  const confirmDelete = confirm(`Are you sure you want to delete exam ${id}?`);
  if (confirmDelete) alert("Deleted exam " + id);
}

document.getElementById("addExamBtn").onclick = () => {
  alert("Add Exam Clicked");
};

loadExamTable();
