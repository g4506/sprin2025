const recordButton = document.getElementById('record');
const stopButton = document.getElementById('stop');
const audioElement = document.getElementById('audio');
const timerDisplay = document.getElementById('timer');
let mediaRecorder;
let audioChunks = [];
let timerInterval;
let startTime;

// Function to format time in MM:SS
function formatTime(seconds) {
    const minutes = Math.floor(seconds / 60);
    return `${minutes}:${(seconds % 60).toString().padStart(2, '0')}`;
}

// Function to handle the "Record" button click
recordButton.addEventListener('click', async () => {
    console.log("Record button clicked");

    try {
        // Request microphone access
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        mediaRecorder = new MediaRecorder(stream);
        audioChunks = [];
        mediaRecorder.start();

        // Start timer
        startTime = Date.now();
        timerInterval = setInterval(() => {
            const elapsed = Math.floor((Date.now() - startTime) / 1000);
            timerDisplay.textContent = formatTime(elapsed);
        }, 1000);

        // Collect audio data as it becomes available
        mediaRecorder.ondataavailable = event => {
            audioChunks.push(event.data);
            console.log("Audio data available:", event.data);
        };

        // When recording stops, create a blob and upload it
        mediaRecorder.onstop = () => {
            console.log("Recording stopped");
            clearInterval(timerInterval);

            const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
            audioElement.src = URL.createObjectURL(audioBlob);

            // Prepare form data to send to the server
            const formData = new FormData();
            formData.append('audio_data', audioBlob, 'recorded_audio.wav');

            // Send the audio data to the server via POST
            fetch('/upload', {
                method: 'POST',
                body: formData,
            }).then(response => {
                if (response.ok) {
                    console.log("Audio uploaded successfully");
                    window.location.reload(); // Reload to display the uploaded audio
                } else {
                    console.error("Error uploading audio");
                }
            }).catch(error => {
                console.error("Error uploading audio:", error);
            });
        };
    } catch (err) {
        console.error('Error accessing microphone:', err);
        alert("Please grant microphone permissions to record audio.");
    }
});

// Function to handle the "Stop" button click
stopButton.addEventListener('click', () => {
    if (mediaRecorder && mediaRecorder.state === 'recording') {
        mediaRecorder.stop();
    }
});
