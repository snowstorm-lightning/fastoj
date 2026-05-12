// FastOJ Web UI JavaScript

const API_BASE = '/api/v1';
let token = localStorage.getItem('token');
let currentUser = null;
let currentProblem = null;

// Initialize
document.addEventListener('DOMContentLoaded', () => {
    checkAuth();
    loadProblems();
});

// Authentication
function checkAuth() {
    token = localStorage.getItem('token');
    currentUser = localStorage.getItem('username');

    if (token) {
        document.getElementById('btn-login').style.display = 'none';
        document.getElementById('btn-register').style.display = 'none';
        document.getElementById('btn-submit').style.display = 'inline-block';
        document.getElementById('btn-status').style.display = 'inline-block';
        document.getElementById('btn-logout').style.display = 'inline-block';
    } else {
        document.getElementById('btn-login').style.display = 'inline-block';
        document.getElementById('btn-register').style.display = 'inline-block';
        document.getElementById('btn-submit').style.display = 'none';
        document.getElementById('btn-status').style.display = 'none';
        document.getElementById('btn-logout').style.display = 'none';
    }
}

async function register(event) {
    event.preventDefault();
    const username = document.getElementById('register-username').value;
    const email = document.getElementById('register-email').value;
    const password = document.getElementById('register-password').value;

    try {
        const response = await fetch(`${API_BASE}/auth/register`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({username, email, password})
        });

        const data = await response.json();
        if (response.ok) {
            alert('注册成功！请登录。');
            showSection('login');
        } else {
            alert('注册失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('注册失败: ' + error.message);
    }
}

async function login(event) {
    event.preventDefault();
    const username = document.getElementById('login-username').value;
    const password = document.getElementById('login-password').value;

    try {
        const formData = new FormData();
        formData.append('username', username);
        formData.append('password', password);

        const response = await fetch(`${API_BASE}/auth/login`, {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        if (response.ok) {
            token = data.access_token;
            currentUser = username;
            localStorage.setItem('token', token);
            localStorage.setItem('username', username);
            checkAuth();
            showSection('problems');
            alert('登录成功！');
        } else {
            alert('登录失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('登录失败: ' + error.message);
    }
}

function logout() {
    token = null;
    currentUser = null;
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    checkAuth();
    showSection('problems');
}

// Navigation
function showSection(section) {
    // Hide all sections
    document.querySelectorAll('.section').forEach(s => s.style.display = 'none');

    // Show target section
    const target = document.getElementById(`section-${section}`);
    if (target) {
        target.style.display = 'block';
    }

    // Load data for section
    switch(section) {
        case 'problems':
            loadProblems();
            break;
        case 'status':
            loadSubmissions();
            break;
    }
}

// Problems
async function loadProblems() {
    const container = document.getElementById('problems-list');
    container.innerHTML = '<p class="loading">加载中...</p>';

    try {
        const response = await fetch(`${API_BASE}/problems`);
        const data = await response.json();

        if (data.success && data.data.length > 0) {
            container.innerHTML = data.data.map(problem => {
                const diff = problem.difficulty || 'easy';
                return `
                <div class="problem-card" onclick="showProblem('${problem.id}')">
                    <h3>${problem.title || '未知题目'}</h3>
                    <span class="difficulty ${diff.toLowerCase()}">${getDifficultyText(problem.difficulty)}</span>
                    <div class="tags">
                        ${(problem.tags || []).map(tag => `<span class="tag">${tag}</span>`).join('')}
                    </div>
                    <div class="problem-meta">
                        <span>通过率: ${((problem.ac_rate || 0) * 100).toFixed(1)}%</span>
                        <span>提交: ${problem.total_submissions || 0}</span>
                    </div>
                </div>
            `}).join('');
        } else {
            container.innerHTML = '<p class="loading">暂无题目</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="error">加载失败: ${error.message}</p>`;
    }
}

function getDifficultyText(difficulty) {
    if (!difficulty) return '未知';
    const map = {easy: '简单', medium: '中等', hard: '困难'};
    return map[difficulty.toLowerCase()] || difficulty;
}

async function showProblem(problemId) {
    currentProblem = problemId;

    try {
        const response = await fetch(`${API_BASE}/problems/${problemId}`);
        const data = await response.json();

        if (response.ok && data && data.data) {
            const problem = data.data;
            const content = document.getElementById('problem-detail-content');
            content.innerHTML = `
                <div class="problem-detail">
                    <div class="problem-detail-header">
                        <h2>${problem.title || '未知题目'}</h2>
                        <span class="difficulty ${(problem.difficulty || 'easy').toLowerCase()}">${getDifficultyText(problem.difficulty)}</span>
                        <div class="problem-meta-row">
                            <span class="problem-meta-item">时间限制: <span>${problem.time_limit || 1000}ms</span></span>
                            <span class="problem-meta-item">内存限制: <span>${problem.memory_limit || 256}MB</span></span>
                        </div>
                    </div>

                    <div class="description">
                        ${formatDescription(problem.description || '')}
                    </div>

                    ${problem.sample_testcases && problem.sample_testcases.length > 0 ? `
                        <h3 style="margin:1.5rem 0 1rem;">示例调用</h3>
                        ${problem.sample_testcases.map(tc => `
                            <div class="sample-io">
                                <h4>调用:</h4>
                                <pre class="code-call">${tc.input || ''}</pre>
                                <h4>期望输出:</h4>
                                <pre class="code-output">${tc.output || ''}</pre>
                            </div>
                        `).join('')}
                    ` : ''}

                    ${problem.hint ? `
                        <div class="sample-io">
                            <h4>提示:</h4>
                            <p>${problem.hint}</p>
                        </div>
                    ` : ''}

                    <button class="submit-btn" onclick="goToSubmit('${problem.id}')">🚀 提交代码</button>
                </div>
            `;

            showSection('problem-detail');
        } else {
            alert('加载题目失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('加载题目失败: ' + error.message);
    }
}

function formatDescription(desc) {
    // Simple markdown-like formatting
    return desc
        .replace(/##\s+(.+)/g, '<h3>$1</h3>')
        .replace(/###\s+(.+)/g, '<h4>$1</h4>')
        .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/```(\w+)?\n([\s\S]+?)```/g, '<pre><code>$2</code></pre>')
        .replace(/\n/g, '<br>');
}

function goToSubmit(problemId) {
    currentProblem = problemId;
    loadProblemTemplate(problemId);
    showSection('submit');
}

async function loadProblemTemplate(problemId) {
    const problemInfo = document.getElementById('submit-problem-info');
    const codeInput = document.getElementById('code-input');

    try {
        const response = await fetch(`${API_BASE}/problems/${problemId}`);
        const data = await response.json();

        if (response.ok && data.data) {
            const problem = data.data;
            const template = getCodeTemplate(problem);

            problemInfo.innerHTML = `
                <div class="problem-badge">
                    <span class="difficulty ${(problem.difficulty || 'easy').toLowerCase()}">${getDifficultyText(problem.difficulty)}</span>
                    <strong>${problem.title}</strong>
                </div>
            `;

            codeInput.value = template;
        }
    } catch (error) {
        problemInfo.innerHTML = `<p style="color:var(--danger);">加载模板失败</p>`;
    }
}

function getCodeTemplate(problem) {
    // Extract function signature from description
    const desc = problem.description || '';
    const match = desc.match(/```python\n([\s\S]*?)\n```/);

    if (match) {
        // Clean up the function signature and add pass
        let func = match[1].trim();
        // Remove existing implementation if any (keep just the signature with pass)
        func = func.replace(/\s*->[\s\S]*$/, '');  // Remove return type hint
        func = func.replace(/\s*:\s*$/, ': pass');  // Add pass if missing

        if (!func.endsWith('pass') && !func.includes('{')) {
            // Add pass for Python
            func = func.split('\n').map(line => {
                if (line.trim() && !line.trim().startsWith('def ') && !line.trim().startsWith('class ') && !line.trim().startsWith('#')) {
                    return '    ' + line;
                }
                return line;
            }).join('\n');

            if (!func.includes('\n    ')) {
                func += '\n    pass';
            }
        }
        return func;
    }

    // Fallback templates based on problem slug
    const slug = problem.slug || '';
    const templates = {
        'two-sum': `def twoSum(nums: list[int], target: int) -> list[int]:
    pass`,
        'add-two-numbers': `class ListNode:
    def __init__(self, val=0, next=None):
        self.val = val
        self.next = next

def addTwoNumbers(l1: ListNode, l2: ListNode) -> ListNode:
    pass`,
        'longest-substring-without-repeating': `def lengthOfLongestSubstring(s: str) -> int:
    pass`,
    };

    return templates[slug] || `# Write your code here\npass`;
}

// Submit Code
async function submitCode(event) {
    event.preventDefault();

    if (!token) {
        alert('请先登录');
        showSection('login');
        return;
    }

    const code = document.getElementById('code-input').value;
    const language = document.getElementById('language-select').value;

    if (!currentProblem) {
        alert('请先选择题目');
        return;
    }

    try {
        const response = await fetch(`${API_BASE}/submissions/run`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify({
                problem_id: currentProblem,
                code: code,
                language: language
            })
        });

        const data = await response.json();
        if (response.ok) {
            alert('提交成功！');
            showSection('status');
        } else {
            alert('提交失败: ' + (data.detail || '未知错误'));
        }
    } catch (error) {
        alert('提交失败: ' + error.message);
    }
}

// Submissions
async function loadSubmissions() {
    if (!token) {
        document.getElementById('submissions-list').innerHTML = '<p class="error">请先登录</p>';
        return;
    }

    const container = document.getElementById('submissions-list');
    container.innerHTML = '<p class="loading">加载中...</p>';

    try {
        const response = await fetch(`${API_BASE}/submissions`, {
            headers: {'Authorization': `Bearer ${token}`}
        });

        const data = await response.json();
        if (data.success && data.data.length > 0) {
            container.innerHTML = data.data.map(sub => {
                const hasError = sub.error_message && sub.result !== 'ac';
                return `
                <div class="submission-item ${hasError ? 'has-error' : ''}" onclick="showSubmissionResult('${sub.id}')">
                    <div class="submission-info">
                        <span class="submission-status ${sub.result || sub.status}">${getStatusText(sub.result || sub.status)}</span>
                        <span>${sub.language}</span>
                        <span>${new Date(sub.created_at).toLocaleString()}</span>
                    </div>
                    <div>
                        <span>分数: ${sub.score}</span>
                        ${hasError ? `<div class="error-hint">点击查看错误详情</div>` : ''}
                    </div>
                </div>
            `}).join('');
        } else {
            container.innerHTML = '<p class="loading">暂无提交记录</p>';
        }
    } catch (error) {
        container.innerHTML = `<p class="error">加载失败: ${error.message}</p>`;
    }
}

function getStatusText(status) {
    const map = {
        'ac': '通过',
        'wa': '答案错误',
        'tle': '超时',
        'mle': '内存超限',
        're': '运行时错误',
        'ce': '编译错误',
        'pending': '等待中',
        'judging': '评测中',
        'finished': '已完成'
    };
    return map[status] || status;
}

async function showSubmissionResult(submissionId) {
    try {
        const response = await fetch(`${API_BASE}/submissions/${submissionId}`, {
            headers: {'Authorization': `Bearer ${token}`}
        });

        const data = await response.json();
        if (response.ok) {
            const sub = data;
            const content = document.getElementById('result-content');

            let testcaseResults = '';
            if (sub.testcase_results && sub.testcase_results.length > 0) {
                testcaseResults = sub.testcase_results.map(tc => `
                    <div class="submission-item">
                        <div class="submission-info">
                            <span class="submission-status ${tc.status}">${getStatusText(tc.status)}</span>
                            <span>${tc.is_hidden ? '(隐藏)' : ''}</span>
                        </div>
                        <span>时间: ${tc.execute_time || 0}ms | 内存: ${tc.memory_used || 0}MB</span>
                    </div>
                    ${tc.input ? `<pre style="background:#f8f9fa;padding:1rem;margin:0.5rem 0;border-radius:4px;">输入: ${tc.input}</pre>` : ''}
                    ${tc.expected_output ? `<pre style="background:#f8f9fa;padding:1rem;margin:0.5rem 0;border-radius:4px;">期望输出: ${tc.expected_output}</pre>` : ''}
                    ${tc.actual_output ? `<pre style="background:#f8f9fa;padding:1rem;margin:0.5rem 0;border-radius:4px;">实际输出: ${tc.actual_output}</pre>` : ''}
                `).join('');
            }

            content.innerHTML = `
                <div class="result-summary">
                    <div class="stat-card">
                        <div class="value">${getStatusText(sub.result || sub.status)}</div>
                        <div class="label">结果</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${sub.score}</div>
                        <div class="label">分数</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${sub.execute_time || 0}ms</div>
                        <div class="label">执行时间</div>
                    </div>
                    <div class="stat-card">
                        <div class="value">${sub.memory_used || 0}MB</div>
                        <div class="label">内存使用</div>
                    </div>
                </div>

                ${sub.error_message ? `<div class="error-box"><strong>错误信息:</strong><pre>${sub.error_message}</pre></div>` : ''}

                <h3>测试结果</h3>
                ${testcaseResults || '<p>无测试结果</p>'}
            `;

            showSection('result');
        } else {
            alert('加载失败');
        }
    } catch (error) {
        alert('加载失败: ' + error.message);
    }
}
