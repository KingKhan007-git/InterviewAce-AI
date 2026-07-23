// Interview Session Interactive Controller
let currentQuestionIndex = 0;
let totalQuestions = 0;
let timerInterval = null;
let secondsElapsed = 0;

document.addEventListener('DOMContentLoaded', () => {
    const questionCards = document.querySelectorAll('.question-step-card');
    totalQuestions = questionCards.length;

    if (totalQuestions > 0) {
        showQuestion(0);
        startTimer();
    }
});

function showQuestion(index) {
    const cards = document.querySelectorAll('.question-step-card');
    cards.forEach((card, idx) => {
        card.style.display = idx === index ? 'block' : 'none';
    });
    currentQuestionIndex = index;

    // Update Progress Bar
    const percent = Math.round(((index + 1) / totalQuestions) * 100);
    const fill = document.getElementById('sessionProgressFill');
    if (fill) fill.style.width = `${percent}%`;

    const text = document.getElementById('questionCounterText');
    if (text) text.innerText = `Question ${index + 1} of ${totalQuestions}`;

    // Update nav buttons
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    const submitBtn = document.getElementById('submitSessionBtn');

    if (prevBtn) prevBtn.style.display = index === 0 ? 'none' : 'inline-flex';
    if (nextBtn) nextBtn.style.display = index === totalQuestions - 1 ? 'none' : 'inline-flex';
    if (submitBtn) submitBtn.style.display = index === totalQuestions - 1 ? 'inline-flex' : 'none';
}

function nextQuestion() {
    saveCurrentAnswer();
    if (currentQuestionIndex < totalQuestions - 1) {
        showQuestion(currentQuestionIndex + 1);
    }
}

function prevQuestion() {
    saveCurrentAnswer();
    if (currentQuestionIndex > 0) {
        showQuestion(currentQuestionIndex - 1);
    }
}

function saveCurrentAnswer() {
    const interviewId = document.getElementById('interviewIdHidden')?.value;
    const card = document.querySelector(`.question-step-card[data-index="${currentQuestionIndex}"]`);
    if (!card || !interviewId) return;

    const questionId = card.getAttribute('data-question-id');
    const textarea = card.querySelector('textarea');
    const answer = textarea ? textarea.value.trim() : '';

    fetch(`/api/interview/${interviewId}/save-answer`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question_id: questionId, user_answer: answer })
    }).catch(err => console.error('Save progress error:', err));
}

function updateCharCount(textarea) {
    const card = textarea.closest('.question-step-card');
    if (card) {
        const countSpan = card.querySelector('.char-counter');
        if (countSpan) {
            const wordCount = textarea.value.trim() ? textarea.value.trim().split(/\s+/).length : 0;
            countSpan.innerText = `${wordCount} words (${textarea.value.length} characters)`;
        }
    }
}

// Timer Controller
function startTimer() {
    secondsElapsed = 0;
    timerInterval = setInterval(() => {
        secondsElapsed++;
        const mins = Math.floor(secondsElapsed / 60);
        const secs = secondsElapsed % 60;
        const display = `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
        const timerEl = document.getElementById('timerDisplay');
        if (timerEl) timerEl.innerText = display;
    }, 1000);
}

// Submit Full Interview
function submitFullInterview() {
    saveCurrentAnswer();
    const interviewId = document.getElementById('interviewIdHidden')?.value;
    if (!interviewId) return;

    // Collect all answers
    const answers = {};
    document.querySelectorAll('.question-step-card').forEach(card => {
        const qId = card.getAttribute('data-question-id');
        const ans = card.querySelector('textarea')?.value.trim() || '';
        answers[qId] = ans;
    });

    // Display loading overlay
    const overlay = document.getElementById('evalOverlay');
    if (overlay) overlay.style.display = 'flex';

    fetch(`/api/interview/${interviewId}/submit`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ answers: answers })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            window.location.href = data.report_url;
        } else {
            if (overlay) overlay.style.display = 'none';
            alert(data.error || 'Evaluation failed. Please try again.');
        }
    })
    .catch(err => {
        if (overlay) overlay.style.display = 'none';
        alert('Network error submitting interview.');
        console.error(err);
    });
}
