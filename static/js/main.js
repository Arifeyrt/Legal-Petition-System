function showStep(stepId) {
    document.querySelectorAll('.step-container').forEach(container => {
        container.classList.remove('active');
    });
    document.getElementById(stepId).classList.add('active');
}

function addStatusMessage(message, type = 'success') {
    const container = document.getElementById('status-container');
    const messageDiv = document.createElement('div');
    messageDiv.className = `status-message status-${type}`;
    messageDiv.textContent = message;
    container.appendChild(messageDiv);
}

function clearStatusMessages() {
    document.getElementById('status-container').innerHTML = '';
}

async function submitStep1() {
    clearStatusMessages();
    const category = document.getElementById('category').value;
    if (!category) {
        addStatusMessage('Lütfen bir kategori seçin', 'error');
        return;
    }

    try {
        const response = await fetch('/step1', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `category=${encodeURIComponent(category)}`
        });

        const data = await response.json();
        
        if (data.success) {
            data.messages.forEach(msg => {
                const type = msg.includes('❌') ? 'error' : 
                           msg.includes('⚠️') ? 'warning' : 'success';
                addStatusMessage(msg, type);
            });
            
            showStep('step2');
        } else {
            data.details?.forEach(msg => {
                const type = msg.includes('❌') ? 'error' : 
                           msg.includes('⚠️') ? 'warning' : 'success';
                addStatusMessage(msg, type);
            });
        }
    } catch (error) {
        addStatusMessage('Bir hata oluştu: ' + error.message, 'error');
    }
}

async function submitStep2() {
    clearStatusMessages();
    const childStatus = document.getElementById('child_status').value;
    if (!childStatus) {
        addStatusMessage('Lütfen çocuk durumunu belirtin', 'error');
        return;
    }

    try {
        const response = await fetch('/step2', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `child_status=${encodeURIComponent(childStatus)}`
        });

        const data = await response.json();
        
        if (data.success) {
            showStep('step3');
        } else {
            addStatusMessage(data.message, 'error');
        }
    } catch (error) {
        addStatusMessage('Bir hata oluştu: ' + error.message, 'error');
    }
}

async function submitStep3() {
    clearStatusMessages();
    const alimonyStatus = document.getElementById('alimony_status').value;
    if (!alimonyStatus) {
        addStatusMessage('Lütfen nafaka durumunu belirtin', 'error');
        return;
    }

    try {
        const response = await fetch('/step3', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/x-www-form-urlencoded',
            },
            body: `alimony_status=${encodeURIComponent(alimonyStatus)}`
        });

        const data = await response.json();
        
        if (data.success) {
            showStep('step4');
            document.getElementById('alimony_details').style.display = 
                alimonyStatus === 'talep_ediliyor' ? 'block' : 'none';
            document.getElementById('children_details').style.display = 
                document.getElementById('child_status').value === 'var' ? 'block' : 'none';
        } else {
            addStatusMessage(data.message, 'error');
        }
    } catch (error) {
        addStatusMessage('Bir hata oluştu: ' + error.message, 'error');
    }
}

function updateChildrenFields() {
    const count = parseInt(document.getElementById('children_count').value) || 0;
    const container = document.getElementById('children_fields');
    container.innerHTML = '';

    for (let i = 0; i < count; i++) {
        container.innerHTML += `
            <div class="card mb-3">
                <div class="card-body">
                    <h6 class="card-title">${i + 1}. Çocuk</h6>
                    <div class="mb-2">
                        <label class="form-label">Ad Soyad:</label>
                        <input type="text" class="form-control" id="child_name_${i}" required>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Doğum Yılı:</label>
                        <input type="number" class="form-control" id="child_birth_year_${i}" 
                               min="1990" max="${new Date().getFullYear()}" required>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Nafaka Miktarı (TL):</label>
                        <input type="number" class="form-control" id="child_nafaka_${i}" required>
                    </div>
                    <div class="mb-2">
                        <label class="form-label">Velayet:</label>
                        <select class="form-select" id="child_velayet_${i}" required>
                            <option value="">Seçiniz...</option>
                            <option value="davaci">Davacı</option>
                            <option value="davali">Davalı</option>
                        </select>
                    </div>
                </div>
            </div>
        `;
    }
}

async function submitStep4() {
    clearStatusMessages();
    
    const formData = new FormData();
    
    const fields = [
        'davaci_adi_soyadi', 'davaci_tc', 'davaci_adres',
        'davali_adi_soyadi', 'davali_tc', 'davali_adres',
        'mahkeme_sehri', 'marriage_date'
    ];

    for (const field of fields) {
        const value = document.getElementById(field).value;
        if (!value) {
            addStatusMessage(`Lütfen ${field.replace(/_/g, ' ')} alanını doldurun`, 'error');
            return;
        }
        formData.append(field, value);
    }

    if (document.getElementById('alimony_details').style.display !== 'none') {
        const nafakaMiktari = document.getElementById('nafaka_miktari').value;
        const tazminatMiktari = document.getElementById('tazminat_miktari').value;
        if (!nafakaMiktari) {
            addStatusMessage('Lütfen nafaka miktarını belirtin', 'error');
            return;
        }
        if (!tazminatMiktari) {
            addStatusMessage('Lütfen manevi tazminat miktarını belirtin', 'error');
            return;
        }
        formData.append('nafaka_miktari', nafakaMiktari);
        formData.append('tazminat_miktari', tazminatMiktari);
    }

    if (document.getElementById('children_details').style.display !== 'none') {
        const childrenCount = parseInt(document.getElementById('children_count').value) || 0;
        formData.append('children_count', childrenCount);

        for (let i = 0; i < childrenCount; i++) {
            const name = document.getElementById(`child_name_${i}`).value;
            const birthYear = document.getElementById(`child_birth_year_${i}`).value;
            const nafaka = document.getElementById(`child_nafaka_${i}`).value;
            const velayet = document.getElementById(`child_velayet_${i}`).value;
            
            if (!name || !birthYear || !nafaka || !velayet) {
                addStatusMessage(`Lütfen ${i + 1}. çocuk için tüm bilgileri doldurun`, 'error');
                return;
            }
            
            formData.append(`child_name_${i}`, name);
            formData.append(`child_birth_year_${i}`, birthYear);
            formData.append(`child_nafaka_${i}`, nafaka);
            formData.append(`child_velayet_${i}`, velayet);
        }
    }

    try {
        const response = await fetch('/step4', {
            method: 'POST',
            body: formData
        });

        const data = await response.json();
        
        if (data.success) {
            document.getElementById('petition-text').textContent = data.dilekce;
            document.getElementById('result-container').style.display = 'block';
            document.getElementById('result-container').scrollIntoView({ behavior: 'smooth' });
        } else {
            addStatusMessage(data.message, 'error');
        }
    } catch (error) {
        addStatusMessage('Bir hata oluştu: ' + error.message, 'error');
    }
}
