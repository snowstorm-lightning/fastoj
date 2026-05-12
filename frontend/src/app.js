const API_BASE = '/api/v1';

const state = {
    token: localStorage.getItem('token'),
    username: localStorage.getItem('username'),
    page: 1,
    pageSize: 20,
    totalPages: 1,
    problemsLoaded: false,
    problemsRequestKey: '',
    currentProblem: null,
    currentSubmissionId: null,
    editor: null,
    monacoLoading: null,
    monacoReady: false,
};

document.addEventListener('DOMContentLoaded', () => {
    initFallbackEditor();
    updateAuthUi();
    loadProblems();
});

function initFallbackEditor() {
    const fallback = document.getElementById('code-input');
    fallback.value = getCodeTemplate('python', null);
    fallback.style.display = 'block';
}

function loadScript(src) {
    return new Promise((resolve, reject) => {
        const existing = document.querySelector(`script[src="${src}"]`);
        if (existing) {
            existing.addEventListener('load', resolve, {once: true});
            existing.addEventListener('error', reject, {once: true});
            return;
        }
        const script = document.createElement('script');
        script.src = src;
        script.async = true;
        script.onload = resolve;
        script.onerror = reject;
        document.head.appendChild(script);
    });
}

function ensureEditor() {
    const fallback = document.getElementById('code-input');
    if (state.editor) {
        return Promise.resolve(state.editor);
    }
    if (state.monacoLoading) {
        return state.monacoLoading;
    }

    state.monacoLoading = loadScript('https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs/loader.js')
        .then(() => new Promise((resolve, reject) => {
            if (!window.require) {
                reject(new Error('Monaco loader is unavailable'));
                return;
            }
            window.require.config({paths: {vs: 'https://cdn.jsdelivr.net/npm/monaco-editor@0.45.0/min/vs'}});
            window.require(['vs/editor/editor.main'], () => {
                const monacoTarget = document.getElementById('monaco-editor');
                monacoTarget.style.display = 'block';
                state.editor = monaco.editor.create(monacoTarget, {
                    value: fallback.value,
                    language: toMonacoLanguage(document.getElementById('language-select').value),
                    theme: 'vs',
                    automaticLayout: true,
                    minimap: {enabled: false},
                    fontSize: 14,
                    tabSize: 4,
                    scrollBeyondLastLine: false,
                    renderWhitespace: 'selection',
                });
                state.monacoReady = true;
                fallback.style.display = 'none';
                resolve(state.editor);
            }, reject);
        }))
        .catch((error) => {
            console.warn('Monaco failed to load, using textarea editor.', error);
            fallback.style.display = 'block';
            return null;
        });

    return state.monacoLoading;
}

function getEditorValue() {
    return state.editor ? state.editor.getValue() : document.getElementById('code-input').value;
}

function setEditorValue(value, language) {
    const fallback = document.getElementById('code-input');
    fallback.value = value;
    if (state.editor) {
        state.editor.setValue(value);
        monaco.editor.setModelLanguage(state.editor.getModel(), toMonacoLanguage(language));
    }
}

function toMonacoLanguage(language) {
    return {
        python: 'python',
        javascript: 'javascript',
        typescript: 'typescript',
        c: 'c',
        cpp: 'cpp',
        java: 'java',
        golang: 'go',
    }[language] || 'plaintext';
}

function updateAuthUi() {
    document.querySelectorAll('.auth-only').forEach((node) => {
        node.style.display = state.token ? 'inline-flex' : 'none';
    });
    document.querySelectorAll('.guest-only').forEach((node) => {
        node.style.display = state.token ? 'none' : 'inline-flex';
    });
    document.getElementById('current-user').textContent = state.username ? `当前用户：${state.username}` : '未登录';
}

function showSection(section) {
    document.querySelectorAll('.section').forEach((node) => node.classList.remove('active'));
    const target = document.getElementById(`section-${section}`);
    if (target) {
        target.classList.add('active');
    }
    if (section === 'problems' && !state.problemsLoaded) loadProblems();
    if (section === 'status') loadSubmissions();
}

async function apiFetch(path, options = {}) {
    const headers = {'Content-Type': 'application/json', ...(options.headers || {})};
    if (state.token) {
        headers.Authorization = `Bearer ${state.token}`;
    }
    const response = await fetch(`${API_BASE}${path}`, {...options, headers});
    const text = await response.text();
    const data = text ? JSON.parse(text) : null;
    if (!response.ok) {
        const detail = data?.detail || data?.error?.message || response.statusText;
        throw new Error(Array.isArray(detail) ? detail.map((item) => item.msg).join('; ') : detail);
    }
    return data;
}

function applyProblemFilters(event) {
    event.preventDefault();
    state.page = 1;
    loadProblems();
}

function resetProblemFilters() {
    document.getElementById('filter-keyword').value = '';
    document.getElementById('filter-difficulty').value = '';
    document.getElementById('filter-tags').value = '';
    state.page = 1;
    loadProblems();
}

function changeProblemPage(delta) {
    const next = state.page + delta;
    if (next < 1 || next > state.totalPages) return;
    state.page = next;
    loadProblems();
}

async function loadProblems() {
    const container = document.getElementById('problems-list');
    const params = new URLSearchParams({
        page: String(state.page),
        page_size: String(state.pageSize),
    });
    const keyword = document.getElementById('filter-keyword')?.value.trim();
    const difficulty = document.getElementById('filter-difficulty')?.value;
    const tags = document.getElementById('filter-tags')?.value.trim();
    if (keyword) params.set('keyword', keyword);
    if (difficulty) params.set('difficulty', difficulty);
    if (tags) params.set('tags', tags);
    const requestKey = params.toString();
    if (state.problemsLoaded && state.problemsRequestKey === requestKey) {
        return;
    }

    container.innerHTML = '<div class="empty-state">加载中...</div>';

    try {
        const payload = await apiFetch(`/problems?${params.toString()}`);
        state.problemsLoaded = true;
        state.problemsRequestKey = requestKey;
        const problems = payload.data || [];
        state.totalPages = Math.max(payload.pagination?.total_pages || 1, 1);
        document.getElementById('page-indicator').textContent =
            `第 ${state.page} / ${state.totalPages} 页，共 ${payload.pagination?.total || 0} 题`;

        if (!problems.length) {
            container.innerHTML = '<div class="empty-state">暂无符合条件的题目。</div>';
            return;
        }

        container.innerHTML = problems.map((problem) => `
            <button class="problem-row" type="button" onclick="openProblem('${problem.id}')">
                <span class="problem-main">
                    <strong>${escapeHtml(problem.title)}</strong>
                    <span>${escapeHtml(problem.slug)}</span>
                </span>
                <span class="tag-list">${(problem.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join('')}</span>
                <span class="difficulty ${problem.difficulty}">${difficultyText(problem.difficulty)}</span>
                <span class="ac-rate">${Math.round((problem.ac_rate || 0) * 100)}%</span>
            </button>
        `).join('');
    } catch (error) {
        container.innerHTML = `<div class="empty-state error">${escapeHtml(error.message)}</div>`;
    }
}

async function openProblem(problemId) {
    writeTerminal('正在加载题目...');
    try {
        const payload = await apiFetch(`/problems/${problemId}`);
        state.currentProblem = payload.data;
        renderProblem(state.currentProblem);
        const language = document.getElementById('language-select').value;
        setEditorValue(getCodeTemplate(language, state.currentProblem), language);
        showSection('workspace');
        ensureEditor();
        loadSolution(problemId, language);
    } catch (error) {
        writeTerminal(`加载题目失败：${error.message}`, true);
    }
}

function renderProblem(problem) {
    document.getElementById('workspace-title').innerHTML = `
        <strong>${escapeHtml(problem.title)}</strong>
        <span class="difficulty ${problem.difficulty}">${difficultyText(problem.difficulty)}</span>
    `;

    const cases = (problem.sample_testcases || []).map((tc, index) => `
        <div class="case-block">
            <h3>公开用例 ${index + 1}</h3>
            <label>输入</label>
            <pre>${escapeHtml(tc.input)}</pre>
            <label>期望输出</label>
            <pre>${escapeHtml(tc.output)}</pre>
        </div>
    `).join('');

    document.getElementById('problem-detail-content').innerHTML = `
        <div class="problem-header">
            <h1>${escapeHtml(problem.title)}</h1>
            <div class="meta-line">
                <span class="difficulty ${problem.difficulty}">${difficultyText(problem.difficulty)}</span>
                <span>${problem.time_limit} ms</span>
                <span>${problem.memory_limit} MB</span>
                <span>通过率 ${Math.round((problem.ac_rate || 0) * 100)}%</span>
            </div>
            <div class="tag-list">${(problem.tags || []).map((tag) => `<span>${escapeHtml(tag)}</span>`).join('')}</div>
        </div>
        <div class="markdown">${renderMarkdown(problem.description || '')}</div>
        ${cases || '<div class="empty-state">暂无公开用例。</div>'}
        ${problem.hint ? `<details class="solution-panel"><summary>提示</summary><div>${renderMarkdown(problem.hint)}</div></details>` : ''}
        <details class="solution-panel" id="solution-panel">
            <summary>官方题解</summary>
            <div id="solution-content">正在加载...</div>
        </details>
    `;
}

async function loadSolution(problemId, language) {
    const target = document.getElementById('solution-content');
    if (!target) return;

    try {
        const payload = await apiFetch(`/problems/${problemId}/solutions?language=${encodeURIComponent(language)}`);
        const solution = (payload.data || [])[0];
        if (!solution) {
            target.innerHTML = '<div class="empty-state">当前语言暂无官方题解。</div>';
            return;
        }
        target.innerHTML = `
            <div class="markdown">${renderMarkdown(solution.explanation || '')}</div>
            <pre class="solution-code">${escapeHtml(solution.code || '')}</pre>
            <div class="complexity">
                <span>时间复杂度：${escapeHtml(solution.time_complexity || '-')}</span>
                <span>空间复杂度：${escapeHtml(solution.space_complexity || '-')}</span>
            </div>
        `;
    } catch (error) {
        target.innerHTML = `<div class="empty-state error">${escapeHtml(error.message)}</div>`;
    }
}

function changeLanguage() {
    const language = document.getElementById('language-select').value;
    setEditorValue(getCodeTemplate(language, state.currentProblem), language);
    if (state.currentProblem) {
        loadSolution(state.currentProblem.id, language);
    }
}

async function runCode() {
    await createSubmission('/submissions/run', '运行公开用例');
}

async function submitCode() {
    await createSubmission('/submissions', '提交完整评测');
}

async function createSubmission(path, label) {
    if (!state.token) {
        showSection('login');
        return;
    }
    if (!state.currentProblem) {
        writeTerminal('请先选择题目。', true);
        return;
    }

    const language = document.getElementById('language-select').value;
    writeTerminal(`${label}：Pending`);
    try {
        const payload = await apiFetch(path, {
            method: 'POST',
            body: JSON.stringify({
                problem_id: state.currentProblem.id,
                code: getEditorValue(),
                language,
            }),
        });
        state.currentSubmissionId = payload.id;
        renderSubmission(payload);
        pollSubmission(payload.id);
    } catch (error) {
        writeTerminal(`${label}失败：${error.message}`, true);
    }
}

async function pollSubmission(submissionId) {
    for (let i = 0; i < 60; i += 1) {
        try {
            const payload = await apiFetch(`/submissions/${submissionId}`, {headers: {'Content-Type': 'application/json'}});
            renderSubmission(payload);
            if (payload.status === 'finished') return;
        } catch (error) {
            writeTerminal(`获取评测结果失败：${error.message}`, true);
            return;
        }
        await new Promise((resolve) => setTimeout(resolve, 1000));
    }
    writeTerminal('评测仍在队列中，请稍后在提交记录中查看。');
}

function renderSubmission(submission) {
    const lines = [
        `状态：${statusText(submission.result || submission.status)}`,
        `分数：${submission.score ?? 0}`,
        `耗时：${submission.execute_time ?? 0} ms`,
        `内存：${submission.memory_used ?? 0} MB`,
    ];
    if (submission.error_message) {
        lines.push('', submission.error_message);
    }
    if (submission.testcase_results?.length) {
        lines.push('', '公开用例结果：');
        submission.testcase_results.forEach((tc, index) => {
            lines.push(`用例 ${index + 1}: ${statusText(tc.status)} ${tc.execute_time ?? 0}ms`);
            if (tc.status !== 'ac') {
                lines.push(`输入: ${tc.input ?? ''}`);
                lines.push(`期望: ${tc.expected_output ?? ''}`);
                lines.push(`实际: ${tc.actual_output ?? ''}`);
            }
        });
    }
    writeTerminal(lines.join('\n'), submission.result && submission.result !== 'ac');
}

async function loadSubmissions() {
    const container = document.getElementById('submissions-list');
    if (!state.token) {
        container.innerHTML = '<div class="empty-state">请先登录。</div>';
        return;
    }
    container.innerHTML = '<div class="empty-state">加载中...</div>';
    try {
        const payload = await apiFetch('/submissions');
        const submissions = payload.data || [];
        if (!submissions.length) {
            container.innerHTML = '<div class="empty-state">暂无提交记录。</div>';
            return;
        }
        container.innerHTML = submissions.map((submission) => `
            <button class="submission-row" type="button" onclick="showSubmission('${submission.id}')">
                <span>
                    <strong>${escapeHtml(submission.problem?.title || '未知题目')}</strong>
                    <small>${new Date(submission.created_at).toLocaleString()}</small>
                </span>
                <span>${escapeHtml(submission.language)}</span>
                <span class="status ${submission.result || submission.status}">${statusText(submission.result || submission.status)}</span>
                <span>${submission.score ?? 0} 分</span>
            </button>
        `).join('');
    } catch (error) {
        container.innerHTML = `<div class="empty-state error">${escapeHtml(error.message)}</div>`;
    }
}

async function showSubmission(submissionId) {
    try {
        const submission = await apiFetch(`/submissions/${submissionId}`);
        state.currentSubmissionId = submissionId;
        renderSubmission(submission);
        showSection('workspace');
    } catch (error) {
        document.getElementById('submissions-list').innerHTML = `<div class="empty-state error">${escapeHtml(error.message)}</div>`;
    }
}

async function register(event) {
    event.preventDefault();
    try {
        await apiFetch('/auth/register', {
            method: 'POST',
            body: JSON.stringify({
                username: document.getElementById('register-username').value.trim(),
                email: document.getElementById('register-email').value.trim(),
                password: document.getElementById('register-password').value,
            }),
        });
        showSection('login');
    } catch (error) {
        alert(`注册失败：${error.message}`);
    }
}

async function login(event) {
    event.preventDefault();
    const form = new FormData();
    const username = document.getElementById('login-username').value.trim();
    form.append('username', username);
    form.append('password', document.getElementById('login-password').value);

    try {
        const response = await fetch(`${API_BASE}/auth/login`, {method: 'POST', body: form});
        const payload = await response.json();
        if (!response.ok) throw new Error(payload.detail || response.statusText);
        state.token = payload.access_token;
        state.username = username;
        localStorage.setItem('token', state.token);
        localStorage.setItem('username', username);
        updateAuthUi();
        showSection('problems');
    } catch (error) {
        alert(`登录失败：${error.message}`);
    }
}

function logout() {
    state.token = null;
    state.username = null;
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    updateAuthUi();
    showSection('problems');
}

function clearTerminal() {
    writeTerminal('');
}

function writeTerminal(message, isError = false) {
    const terminal = document.getElementById('terminal-output');
    if (!terminal) return;
    terminal.textContent = message || '暂无输出。';
    terminal.classList.toggle('error', Boolean(isError));
}

function getCodeTemplate(language, problem) {
    const slug = problem?.slug || '';
    const templates = {
        python: {
            'two-sum': `import ast
import json
import sys

def two_sum(nums, target):
    seen = {}
    for i, num in enumerate(nums):
        need = target - num
        if need in seen:
            return [seen[need], i]
        seen[num] = i
    return []

nums = ast.literal_eval(sys.stdin.readline())
target = int(sys.stdin.readline())
print(json.dumps(two_sum(nums, target), separators=(',', ':')))`,
            'longest-substring-without-repeating': `import sys

def length_of_longest_substring(s):
    left = 0
    seen = {}
    ans = 0
    for right, ch in enumerate(s):
        if ch in seen and seen[ch] >= left:
            left = seen[ch] + 1
        seen[ch] = right
        ans = max(ans, right - left + 1)
    return ans

print(length_of_longest_substring(sys.stdin.readline().strip()))`,
            'add-two-numbers': `import ast
import json
import sys

def add_two_numbers(a, b):
    carry = 0
    out = []
    for i in range(max(len(a), len(b))):
        total = carry
        if i < len(a):
            total += a[i]
        if i < len(b):
            total += b[i]
        out.append(total % 10)
        carry = total // 10
    if carry:
        out.append(carry)
    return out

l1 = ast.literal_eval(sys.stdin.readline())
l2 = ast.literal_eval(sys.stdin.readline())
print(json.dumps(add_two_numbers(l1, l2), separators=(',', ':')))`,
            default: `import sys

def solve(data):
    return data

print(solve(sys.stdin.read()))`,
        },
        javascript: {
            default: `const fs = require('fs');
const input = fs.readFileSync(0, 'utf8').trim().split(/\\n/);

function solve(lines) {
  return lines.join('\\n');
}

console.log(solve(input));`,
        },
        typescript: {
            default: `import fs from 'fs';
const input = fs.readFileSync(0, 'utf8').trim().split(/\\n/);

function solve(lines: string[]): string {
  return lines.join('\\n');
}

console.log(solve(input));`,
        },
        c: {
            default: `#include <stdio.h>

int main(void) {
    return 0;
}`,
        },
        cpp: {
            default: `#include <bits/stdc++.h>
using namespace std;

int main() {
    ios::sync_with_stdio(false);
    cin.tie(nullptr);
    return 0;
}`,
        },
        java: {
            default: `import java.io.*;

public class Main {
    public static void main(String[] args) throws Exception {
    }
}`,
        },
        golang: {
            default: `package main

func main() {
}`,
        },
    };

    return templates[language]?.[slug] || templates[language]?.default || '';
}

function renderMarkdown(markdown) {
    return escapeHtml(markdown)
        .replace(/```([\s\S]*?)```/g, '<pre>$1</pre>')
        .replace(/^### (.*)$/gm, '<h3>$1</h3>')
        .replace(/^## (.*)$/gm, '<h2>$1</h2>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<code>$1</code>')
        .replace(/\n/g, '<br>');
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#039;');
}

function difficultyText(value) {
    return {easy: '简单', medium: '中等', hard: '困难'}[value] || value || '未知';
}

function statusText(value) {
    return {
        pending: '等待中',
        judging: '评测中',
        finished: '已完成',
        ac: '通过',
        wa: '答案错误',
        tle: '超时',
        mle: '内存超限',
        ce: '编译错误',
        re: '运行错误',
        se: '系统错误',
    }[value] || value || '未知';
}
