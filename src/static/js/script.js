document.getElementById('expense-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = document.getElementById('amount').value;
    const merchant = document.getElementById('merchant').value;
    const description = document.getElementById('description').value;
    const resultDiv = document.getElementById('result');
    const loadingDiv = document.getElementById('loading');
    
    loadingDiv.style.display = 'block';
    resultDiv.innerHTML = '';
    
    try {
        const response = await fetch('/api/classify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount, merchant, description })
        });
        const data = await response.json();
        if (data.error) {
            resultDiv.className = 'result error';
            resultDiv.innerText = data.error;
            return;
        }
        resultDiv.className = 'result success';
        resultDiv.innerText = `Category: ${data.category}`;
        await saveExpense(data);
        loadExpenses();
    } finally {
        loadingDiv.style.display = 'none';
    }
});

document.getElementById('image-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const imageInput = document.getElementById('image');
    const resultDiv = document.getElementById('result');
    const loadingDiv = document.getElementById('loading');
    const editForm = document.getElementById('edit-form');
    
    if (!imageInput.files[0]) {
        resultDiv.className = 'result error';
        resultDiv.innerText = 'Select an image';
        return;
    }
    
    loadingDiv.style.display = 'block';
    resultDiv.innerHTML = '';
    
    try {
        const formData = new FormData();
        formData.append('image', imageInput.files[0]);
        const response = await fetch('/api/classify_image', { method: 'POST', body: formData });
        const data = await response.json();
        if (data.error) {
            resultDiv.className = 'result error';
            resultDiv.innerText = data.error;
            return;
        }
        resultDiv.className = 'result success';
        resultDiv.innerHTML = `Extracted Data:<br>`;
        document.getElementById('edit-amount').value = data.amount.toFixed(2);
        document.getElementById('edit-merchant').value = data.merchant;
        document.getElementById('edit-description').value = data.description;
        document.getElementById('edit-category').value = data.category;
        editForm.style.display = 'block';
    } finally {
        loadingDiv.style.display = 'none';
    }
});

document.getElementById('edit-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const amount = document.getElementById('edit-amount').value;
    const merchant = document.getElementById('edit-merchant').value;
    const description = document.getElementById('edit-description').value;
    const category = document.getElementById('edit-category').value;
    const resultDiv = document.getElementById('result');
    const editForm = document.getElementById('edit-form');
    
    const data = { amount: parseFloat(amount), merchant, description, category };
    const response = await fetch('/api/save_expense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
    if (response.ok) {
        resultDiv.innerHTML = 'Edits saved successfully.';
        await loadExpenses();
        editForm.style.display = 'none';
    } else {
        resultDiv.className = 'result error';
        resultDiv.innerText = 'Failed to save edits.';
    }
});

document.getElementById('recommend-btn').addEventListener('click', async () => {
    const recommendDiv = document.getElementById('recommendations');
    const response = await fetch('/api/recommendations');
    const data = await response.json();
    recommendDiv.innerHTML = '<ul>' + data.recommendations.map(tip => `<li class="recommendation-tip">${tip}</li>`).join('') + '</ul>';
});

async function saveExpense(data) {
    await fetch('/api/save_expense', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(data)
    });
}

async function loadExpenses() {
    const response = await fetch('/api/get_expenses');
    const expenses = await response.json();
    const tbody = document.getElementById('expense-body');
    tbody.innerHTML = '';
    expenses.forEach(expense => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td>${parseFloat(expense.amount).toFixed(2)}</td>
            <td>${expense.merchant}</td>
            <td>${expense.description}</td>
            <td>${expense.category}</td>
        `;
        tbody.appendChild(row);
    });
}

window.onload = loadExpenses;