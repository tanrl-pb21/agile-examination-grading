const exams = [
    {
      id: "EX001",
      title: "Software Engineering Midterm",
      start: "2025-01-10 09:00",
      end: "2025-01-10 11:00",
      status: "Upcoming",
    },
    {
      id: "EX002",
      title: "Database System Final",
      start: "2025-01-12 13:00",
      end: "2025-01-12 15:00",
      status: "Completed",
    },
    {
      id: "EX003",
      title: "Web Development Quiz",
      start: "2025-01-20 08:30",
      end: "2025-01-20 09:00",
      status: "Active",
    }
  ];
  
  function loadExamTable() {
    const table = document.getElementById("examTable");
    table.innerHTML = "";
  
    exams.forEach(exam => {
      const row = `
        <tr class="hover:bg-gray-50">
          <td class="p-3 border">${exam.id}</td>
          <td class="p-3 border">${exam.title}</td>
          <td class="p-3 border">${exam.start}</td>
          <td class="p-3 border">${exam.end}</td>
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
  }
  
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
  
  // Add Exam Button
  document.getElementById("addExamBtn").onclick = () => {
    alert("Add Exam Clicked");
  };
  
  loadExamTable();
  