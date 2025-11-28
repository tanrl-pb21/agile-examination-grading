<!-- Key JavaScript functions that need to be fixed -->
<script>
async function loadExamData() {
    try {
        console.log('Fetching exam with ID:', examId);
        
        // Verify exam ID exists
        const examResponse = await axios.get(`/exams/${examId}`);
        const exam = examResponse.data;
        
        if (!exam) {
            throw new Error('Exam ID does not exist');
        }
        
        const questionsResponse = await axios.get(`/questions/exam/${examId}`);
        const questions = questionsResponse.data;

        // Try to get submissions, but don't fail if it doesn't work
        let submissions = [];
        try {
            const submissionsResponse = await axios.get(`/submissions/exam/${examId}/students`);
            submissions = submissionsResponse.data || [];
            console.log('Submissions data:', submissions);
        } catch (submissionError) {
            console.warn('Could not load submissions:', submissionError);
            // Continue without submissions data
        }
        
        console.log('Exam data:', exam);
        console.log('Questions data:', questions);
        
        currentExam = transformExamData(exam);
        currentExam.questions = transformQuestions(questions);
        currentExam.submissions = transformSubmissions(submissions);

        currentExam.totalStudents = submissions.length;
        currentExam.submitted = submissions.filter(s => s.status === 'submitted').length;
        currentExam.missed = submissions.filter(s => s.status === 'missed').length;

        renderExamInfo();
        renderQuestionStats();
        renderQuestions();
        renderSubmissionStats();
        renderFilterTabs();
        renderSubmissions();
        
    } catch (error) {
        console.error('Error loading exam:', error);
        if (error.response?.status === 404) {
            alert('Error: The exam ID does not exist. Please check the exam ID and try again.');
        } else {
            alert('Failed to load exam details: ' + (error.response?.data?.detail || error.message));
        }
        window.location.href = '/examManagement';
    }
}

function renderSubmissionStats() {
    if (!currentExam) return;
    const totalStudents = currentExam.totalStudents || 0;
    const submitted = currentExam.submitted || 0;
    const missed = currentExam.missed || 0;
    
    document.getElementById('submissionStats').innerHTML = `
        <div class="stat-card blue"><div class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg></div><div class="stat-content"><span class="stat-number">${totalStudents}</span><span class="stat-label">Total Students</span></div></div>
        <div class="stat-card green"><div class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><polyline points="22 4 12 14.01 9 11.01"/></svg></div><div class="stat-content"><span class="stat-number">${submitted}</span><span class="stat-label">Submitted</span></div></div>
        <div class="stat-card red"><div class="stat-icon"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="12" r="10"/><line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/></svg></div><div class="stat-content"><span class="stat-number">${missed}</span><span class="stat-label">Missed</span></div></div>
    `;
}

function renderFilterTabs() {
    if (!currentExam) return;
    const submissions = currentExam.submissions || [];
    const submitted = submissions.filter(s => s.status === 'submitted').length;
    const missed = submissions.filter(s => s.status === 'missed').length;
    
    document.getElementById('filterTabs').innerHTML = `
        <button class="filter-tab ${currentFilter === 'all' ? 'active' : ''}" onclick="setFilter('all')">All (${submissions.length})</button>
        <button class="filter-tab ${currentFilter === 'submitted' ? 'active' : ''}" onclick="setFilter('submitted')">Submitted (${submitted})</button>
        <button class="filter-tab ${currentFilter === 'missed' ? 'active' : ''}" onclick="setFilter('missed')">Missed (${missed})</button>
    `;
}

function renderSubmissions() {
    if (!currentExam) return;
    
    const submissions = currentExam.submissions || [];
    const search = document.getElementById('submissionSearch')?.value.toLowerCase() || '';
    let filtered = submissions;
    
    // Filter by status
    if (currentFilter !== 'all') {
        filtered = filtered.filter(s => s.status === currentFilter);
    }
    
    // Filter by search
    if (search) {
        filtered = filtered.filter(s => 
            s.studentName.toLowerCase().includes(search) || 
            s.studentId.toLowerCase().includes(search) || 
            s.studentEmail.toLowerCase().includes(search)
        );
    }
    
    const tbody = document.getElementById('submissionsTableBody');
    
    if (filtered.length === 0) {
        tbody.innerHTML = '<tr><td colspan="6" style="text-align:center;padding:40px;color:#6c757d;">No submissions found</td></tr>';
        return;
    }
    
    tbody.innerHTML = filtered.map(s => {
        // Format score display
        let scoreDisplay = '-';
        if (s.score !== null && s.score !== undefined) {
            scoreDisplay = `${s.score}`;
            if (s.percentage) {
                scoreDisplay += ` <span style="color:#6c757d;">(${s.percentage})</span>`;
            }
            if (s.scoreGrade) {
                scoreDisplay += ` <span style="color:#10b981;font-weight:600;">${s.scoreGrade}</span>`;
            }
        }
        
        // Format submission date/time
        let submissionDateTime = '-';
        if (s.submissionDate) {
            submissionDateTime = s.submissionDate;
            if (s.submissionTime) {
                submissionDateTime += ` ${s.submissionTime}`;
            }
        }
        
        // Action button
        let actionButton = '-';
        if (s.status === 'submitted') {
            if (s.score !== null && s.score !== undefined) {
                // Already graded - show view button
                actionButton = `
                    <button class="btn-grade" onclick="goToGrading(${s.id})">
                        <svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'>
                            <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/>
                            <circle cx="12" cy="12" r="3"/>
                        </svg>
                        View
                    </button>
                `;
            } else {
                // Not graded yet - show grade button
                actionButton = `
                    <button class="btn-grade" onclick="goToGrading(${s.id})">
                        <svg viewBox='0 0 24 24' fill='none' stroke='currentColor' stroke-width='2'>
                            <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7"/>
                            <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z"/>
                        </svg>
                        Grade
                    </button>
                `;
            }
        }
        
        return `
            <tr>
                <td>${s.studentId}</td>
                <td>
                    <div class="student-info">
                        <div class="student-avatar ${s.avatarColor}">${s.avatar}</div>
                        <div class="student-details">
                            <span class="student-name">${s.studentName}</span>
                            <span class="student-email">${s.studentEmail}</span>
                        </div>
                    </div>
                </td>
                <td><span class="submit-badge ${s.status}">${s.status.charAt(0).toUpperCase() + s.status.slice(1)}</span></td>
                <td>${submissionDateTime}</td>
                <td>${scoreDisplay}</td>
                <td>${actionButton}</td>
            </tr>
        `;
    }).join('');
}
</script>