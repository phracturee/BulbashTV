/**
 * Favorites Modal - единый стиль для всех страниц
 * Подключается после itemsData
 */

let currentItemId = null;

function toggleFavorite(id) {
    showFolderSelectionModal(id);
}

function showFolderSelectionModal(itemId) {
    // Сохраняем itemId для последующего использования
    window.currentItemId = itemId;
    
    // Always fetch fresh data from server
    Promise.all([
        fetch('/api/favorites/folders').then(r => r.json()),
        fetch(`/api/favorites/check/${itemId}`).then(r => r.json())
    ])
    .then(([foldersData, checkData]) => {
        const currentFolders = checkData.folders || [];
        const isFavorite = currentFolders.length > 0 && !currentFolders.includes('watched');

        // Update heart icon based on actual favorite status
        const btn = document.querySelector(`.favorite-btn[onclick*="toggleFavorite(${itemId})"]`);
        if (btn) {
            if (isFavorite) {
                btn.classList.add('active');
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                }
            } else {
                btn.classList.remove('active');
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
            }
        }

        // Remove existing modal
        const existingModal = document.getElementById('folderSelectionModal');
        if (existingModal) existingModal.remove();

        const modal = document.createElement('div');
        modal.id = 'folderSelectionModal';
        modal.className = 'modal folder-selection-modal';

        let foldersHtml = '';
        foldersData.folders.forEach(folder => {
            // Skip "watched" folder - it's handled separately
            if (folder.id === 'watched') return;

            const isInFolder = currentFolders.includes(folder.id);
            foldersHtml += `
                <div class="folder-option ${isInFolder ? 'in-folder' : ''}" 
                     data-folder-id="${folder.id}" 
                     data-item-id="${itemId}"
                     style="display: flex; align-items: center; gap: 15px; padding: 15px; background: #000000; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s; border: 1px solid ${isInFolder ? 'var(--accent)' : 'transparent'};"
                     onmouseover="if (!this.classList.contains('in-folder')) this.style.border='1px solid var(--accent)'"
                     onmouseout="if (!this.classList.contains('in-folder')) this.style.border='1px solid transparent'">
                    <i class="fas fa-folder${isInFolder ? '' : '-open'}" style="color: var(--accent); font-size: 1.5rem;"></i>
                    <div class="folder-option-info" style="flex: 1;">
                        <h4 style="margin: 0 0 5px 0; color: var(--text-color);">${folder.name}</h4>
                        <span style="color: #888; font-size: 0.85rem;">${folder.item_count} элементов</span>
                    </div>
                    ${isInFolder ? '<i class="fas fa-check" style="color: var(--accent);"></i>' : ''}
                </div>
            `;
        });

        // Add "Watched" button before "Create new folder"
        const isWatched = currentFolders.includes('watched');
        foldersHtml += `
            <div class="folder-option watched-option ${isWatched ? 'in-folder' : ''}" data-folder-id="watched" data-item-id="${itemId}" style="display: flex; align-items: center; gap: 15px; padding: 15px; background: #000000; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s; border: 1px solid ${isWatched ? 'var(--accent)' : 'transparent'};"
                     onmouseover="if (!this.classList.contains('in-folder')) this.style.border='1px solid var(--accent)'"
                     onmouseout="if (!this.classList.contains('in-folder')) this.style.border='1px solid transparent'">
                <i class="fas fa-eye" style="color: #4CAF50; font-size: 1.5rem;"></i>
                <div class="folder-option-info" style="flex: 1;">
                    <h4 style="margin: 0 0 5px 0; color: var(--text-color);">Просмотренное</h4>
                    <span style="color: #888; font-size: 0.85rem;">${isWatched ? 'Отметить как непросмотренное' : 'Отметить как просмотренное'}</span>
                </div>
                ${isWatched ? '<i class="fas fa-check" style="color: #4CAF50;"></i>' : ''}
            </div>
        `;

        // Add "Create new folder" option at the end
        foldersHtml += `
            <div class="folder-option create-new-folder" data-folder-id="new" data-item-id="${itemId}" style="display: flex; align-items: center; gap: 15px; padding: 15px; background: #000000; border-radius: 10px; margin-bottom: 10px; cursor: pointer; transition: all 0.3s; border: 2px dashed var(--accent);" onclick="showCreateFolderInput('${itemId}')">
                <i class="fas fa-plus-circle" style="color: var(--accent); font-size: 1.5rem;"></i>
                <div class="folder-option-info" style="flex: 1;">
                    <h4 style="margin: 0 0 5px 0; color: var(--text-color);">Создать новую папку</h4>
                    <span style="color: #888; font-size: 0.85rem;">0 элементов</span>
                </div>
            </div>
        `;

        modal.innerHTML = `
            <div class="modal-content" style="background: #000000; border: 1px solid var(--accent); border-radius: 15px; padding: 30px; max-width: 600px;">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                    <h3 style="color: var(--accent); margin: 0; font-size: 1.3rem;"><i class="fas fa-folder-plus"></i> Добавить в папку</h3>
                    <button onclick="closeFolderModal()" style="background: none; color: #fff; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;" onmouseover="this.style.background='rgba(255,255,255,0.1)';this.style.color='var(--accent)'" onmouseout="this.style.background='none';this.style.color='#fff'">
                        <i class="fas fa-times"></i>
                    </button>
                </div>
                <div class="folder-list">
                    ${foldersHtml}
                </div>
            </div>
        `;

        document.body.appendChild(modal);

        // Add click handlers to folder options
        modal.querySelectorAll('.folder-option').forEach(option => {
            option.addEventListener('click', function(e) {
                const folderId = this.dataset.folderId;
                const itemId = this.dataset.itemId;
                
                if (folderId === 'new') {
                    // Create new folder - handled by onclick
                } else if (folderId === 'watched') {
                    if (typeof toggleWatched === 'function') {
                        toggleWatched(itemId);
                        closeFolderModal();
                    }
                } else {
                    handleFolderOptionClick(e, folderId, itemId);
                }
            });
        });

        // Close on outside click
        modal.addEventListener('click', function(e) {
            if (e.target === this) closeFolderModal();
        });
    });
}

// Handle folder option click
function handleFolderOptionClick(event, folderId, itemId) {
    event.stopPropagation();
    
    const option = event.currentTarget;
    
    // Check current state
    fetch(`/api/favorites/check/${itemId}?t=${Date.now()}`)
    .then(r => r.json())
    .then(checkData => {
        const currentFolders = checkData.folders || [];
        const isInFolder = currentFolders.includes(folderId);
        
        const item = typeof itemsData !== 'undefined' ? itemsData[itemId] : null;
        if (!item) return;
        
        if (isInFolder) {
            // Remove from folder
            fetch(`/api/favorites/remove/${itemId}?folder_id=${folderId}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showNotification('Удалено из папки', 'info');
                    updateFolderModalUI(itemId);
                }
            })
            .catch(err => {
                console.error('Error removing:', err);
                showNotification('Ошибка при удалении', 'error');
            });
        } else {
            // Add to folder
            fetch('/api/favorites/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({...item, folder_id: folderId})
            })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showNotification(`Добавлено в "${data.folder_name}"!`, 'success');
                    updateFolderModalUI(itemId);
                } else {
                    showNotification(data.message || 'Ошибка', 'error');
                }
            })
            .catch(err => {
                console.error('Error adding:', err);
                showNotification('Ошибка при добавлении', 'error');
            });
        }
    })
    .catch(err => {
        console.error('Error checking status:', err);
        showNotification('Ошибка проверки статуса', 'error');
    });
}

// Update folder modal UI
function updateFolderModalUI(itemId) {
    fetch(`/api/favorites/check/${itemId}?t=${Date.now()}`)
    .then(r => r.json())
    .then(checkData => {
        const currentFolders = checkData.folders || [];
        
        // Update all folder options
        document.querySelectorAll('.folder-option').forEach(option => {
            const folderId = option.getAttribute('data-folder-id');
            if (!folderId) return;
            
            const isInFolder = currentFolders.includes(folderId);
            
            // Update classes and styles
            option.classList.toggle('in-folder', isInFolder);
            option.style.border = isInFolder ? '1px solid var(--accent)' : '1px solid transparent';
            
            // Update folder icon
            const folderIcon = option.querySelector('.fa-folder');
            if (folderIcon) {
                folderIcon.className = `fas fa-folder${isInFolder ? '' : '-open'}`;
            }
            
            // Add/remove checkmark
            let checkIcon = option.querySelector('.fa-check');
            if (isInFolder) {
                if (!checkIcon) {
                    checkIcon = document.createElement('i');
                    checkIcon.className = 'fas fa-check';
                    checkIcon.style.color = 'var(--accent)';
                    option.appendChild(checkIcon);
                }
            } else if (checkIcon) {
                checkIcon.remove();
            }
        });
        
        // Update heart icon on page
        const buttons = document.querySelectorAll(`button[onclick*="toggleFavorite(${itemId})"]`);
        const isFavorite = currentFolders.length > 0 && !currentFolders.includes('watched');
        buttons.forEach(btn => {
            if (isFavorite) {
                btn.classList.add('active');
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.remove('far');
                    icon.classList.add('fas');
                }
            } else {
                btn.classList.remove('active');
                const icon = btn.querySelector('i');
                if (icon) {
                    icon.classList.remove('fas');
                    icon.classList.add('far');
                }
            }
        });
    });
}

// Show create folder input modal
function showCreateFolderInput(itemId) {
    // Close current folder modal
    const modal = document.getElementById('folderSelectionModal');
    if (modal) modal.remove();
    
    // Create new modal for folder name input
    const createModal = document.createElement('div');
    createModal.id = 'createFolderModal';
    createModal.className = 'modal';
    createModal.innerHTML = `
        <div class="modal-content" style="background: #000000; border: 1px solid var(--accent); border-radius: 15px; padding: 30px; max-width: 500px; width: 90%;">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">
                <h3 style="color: var(--accent); margin: 0; font-size: 1.3rem;"><i class="fas fa-folder-plus"></i> Создать новую папку</h3>
                <button onclick="closeCreateFolderModal()" style="background: none; color: #fff; border: none; width: 40px; height: 40px; border-radius: 50%; cursor: pointer; transition: all 0.3s; display: flex; align-items: center; justify-content: center; font-size: 1.5rem;" onmouseover="this.style.background='rgba(255,255,255,0.1)';this.style.color='var(--accent)'" onmouseout="this.style.background='none';this.style.color='#fff'">
                    <i class="fas fa-times"></i>
                </button>
            </div>
            <input type="text" id="newFolderNameInput" placeholder="Название папки" maxlength="50" autofocus style="width: 100%; padding: 15px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); border-radius: 10px; color: var(--text-color); font-family: var(--font); font-size: 1rem; margin-bottom: 20px; box-sizing: border-box;">
            <div class="modal-buttons" style="display: flex; gap: 10px; justify-content: flex-end;">
                <button onclick="submitNewFolder('${itemId}')" class="btn-primary" style="background: var(--accent); color: #000; border: none; padding: 12px 30px; border-radius: 20px; cursor: pointer; transition: all 0.3s; font-weight: 600; width: 100%;">Создать</button>
            </div>
        </div>
    `;
    
    document.body.appendChild(createModal);
    
    // Focus on input
    setTimeout(() => {
        document.getElementById('newFolderNameInput').focus();
    }, 100);
    
    // Submit on Enter
    document.getElementById('newFolderNameInput').addEventListener('keypress', function(e) {
        if (e.key === 'Enter') submitNewFolder(itemId);
    });
    
    // Close on outside click
    createModal.addEventListener('click', function(e) {
        if (e.target === this) closeCreateFolderModal();
    });
}

// Close create folder modal
function closeCreateFolderModal() {
    const modal = document.getElementById('createFolderModal');
    if (modal) {
        modal.remove();
        // Return to folder list
        setTimeout(() => {
            if (window.currentItemId) {
                showFolderSelectionModal(window.currentItemId);
            }
        }, 100);
    }
}

// Close folder modal
function closeFolderModal() {
    const modal = document.getElementById('folderSelectionModal');
    if (modal) modal.remove();
}

// Submit new folder
function submitNewFolder(itemId) {
    const name = document.getElementById('newFolderNameInput').value.trim();
    if (!name) {
        showNotification('Введите название папки', 'error');
        return;
    }

    fetch('/api/favorites/folders', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ name: name })
    })
    .then(r => r.json())
    .then(data => {
        if (data.success) {
            // Close create modal
            closeCreateFolderModal();
            
            // Save itemId for later
            window.currentItemId = itemId;
            
            // Add item to new folder
            const item = typeof itemsData !== 'undefined' ? itemsData[itemId] : null;
            if (!item) return;
            
            fetch('/api/favorites/add', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({...item, folder_id: data.folder_id})
            })
            .then(r => r.json())
            .then(addData => {
                if (addData.success) {
                    showNotification(`Добавлено в "${data.name}"!`, 'success');
                    // Update heart icon
                    if (typeof updateHeartIcon === 'function') {
                        updateHeartIcon(itemId, true);
                    }
                }
            })
            .catch(err => {
                console.error('Error adding to folder:', err);
            });
        } else {
            showNotification(data.message || 'Ошибка', 'error');
        }
    })
    .catch(err => {
        console.error('Error creating folder:', err);
        showNotification('Ошибка при создании', 'error');
    });
}
