let currentStream = null;
let currentDeviceId = null;
let currentImageBlob = null; // Store the current image for chat

async function getCameras() {
    const devices = await navigator.mediaDevices.enumerateDevices();
    return devices.filter(device => device.kind === 'videoinput');
}

async function startCamera(deviceId) {
    if (currentStream) {
        currentStream.getTracks().forEach(track => track.stop());
    }
    const constraints = {
        video: deviceId ? { deviceId: { exact: deviceId } } : true
    };
    const stream = await navigator.mediaDevices.getUserMedia(constraints);
    document.getElementById('video').srcObject = stream;
    currentStream = stream;
    currentDeviceId = deviceId;
}

async function populateCameraList() {
    const cameras = await getCameras();
    const select = document.getElementById('cameraSelect');
    select.innerHTML = '';
    cameras.forEach(cam => {
        const option = document.createElement('option');
        option.value = cam.deviceId;
        option.text = cam.label || `Camera ${select.length + 1}`;
        select.appendChild(option);
    });
    if (cameras.length > 0) {
        select.value = cameras[0].deviceId;
    }
}

document.getElementById('switchCamera').onclick = async () => {
    const select = document.getElementById('cameraSelect');
    await startCamera(select.value);
};

document.getElementById('cameraSelect').onchange = async (e) => {
    await startCamera(e.target.value);
};

document.getElementById('capture').onclick = async () => {
    const video = document.getElementById('video');
    const canvas = document.getElementById('canvas');
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext('2d');
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.toBlob(async (blob) => {
        await sendImage(blob);
    }, 'image/jpeg');
};

document.getElementById('imageUpload').onchange = async (e) => {
    const file = e.target.files[0];
    if (file) {
        await sendImage(file);
    }
};

async function sendImage(blobOrFile) {
    // Store the current image for chat functionality
    currentImageBlob = blobOrFile;
    
    const formData = new FormData();
    formData.append('image', blobOrFile);
    document.getElementById('resultContent').innerText = 'Analyzing...';
    try {
        const res = await fetch('/analyze', {
            method: 'POST',
            body: formData
        });
        const data = await res.json();
        if (data.error) {
            document.getElementById('resultContent').innerText = 'Error: ' + data.error;
        } else {
            document.getElementById('resultContent').innerText =
                `Age: ${data.age}\nGender: ${data.gender}\nClothing: ${data.clothing}\nEnvironment: ${data.environment}`;
            
            // Show chat interface after successful analysis
            document.getElementById('chatContainer').style.display = 'block';
            clearChatMessages();
            addChatMessage('ai', 'Image analyzed! You can now ask me questions about this image.');
        }
    } catch (err) {
        document.getElementById('resultContent').innerText = 'Error: ' + err;
    }
}

// Chat functionality
function addChatMessage(type, message) {
    const chatMessages = document.getElementById('chatMessages');
    const messageDiv = document.createElement('div');
    messageDiv.className = `chat-message ${type}`;
    messageDiv.textContent = message;
    chatMessages.appendChild(messageDiv);
    chatMessages.scrollTop = chatMessages.scrollHeight;
}

function clearChatMessages() {
    document.getElementById('chatMessages').innerHTML = '';
}

async function sendChatMessage(message) {
    if (!currentImageBlob) {
        addChatMessage('ai', 'Please analyze an image first before starting a chat.');
        return;
    }
    
    // Add user message
    addChatMessage('user', message);
    
    // Add loading message
    const loadingDiv = document.createElement('div');
    loadingDiv.className = 'chat-message loading';
    loadingDiv.textContent = 'Thinking...';
    document.getElementById('chatMessages').appendChild(loadingDiv);
    document.getElementById('chatMessages').scrollTop = document.getElementById('chatMessages').scrollHeight;
    
    try {
        const formData = new FormData();
        formData.append('image', currentImageBlob);
        formData.append('message', message);
        
        const res = await fetch('/chat', {
            method: 'POST',
            body: formData
        });
        
        const data = await res.json();
        
        // Remove loading message
        loadingDiv.remove();
        
        if (data.error) {
            addChatMessage('ai', 'Sorry, I encountered an error: ' + data.error);
        } else {
            addChatMessage('ai', data.response);
        }
    } catch (err) {
        loadingDiv.remove();
        addChatMessage('ai', 'Sorry, I encountered an error: ' + err.message);
    }
}

// Chat event listeners
document.getElementById('sendMessage').onclick = async () => {
    const input = document.getElementById('chatInput');
    const message = input.value.trim();
    if (message) {
        input.value = '';
        await sendChatMessage(message);
    }
};

document.getElementById('chatInput').onkeypress = async (e) => {
    if (e.key === 'Enter') {
        const message = e.target.value.trim();
        if (message) {
            e.target.value = '';
            await sendChatMessage(message);
        }
    }
};

document.getElementById('clearChat').onclick = () => {
    clearChatMessages();
    if (currentImageBlob) {
        addChatMessage('ai', 'Chat cleared! You can ask me questions about the current image.');
    }
};

window.onload = async () => {
    await populateCameraList();
    const select = document.getElementById('cameraSelect');
    if (select.value) {
        await startCamera(select.value);
    }
};
