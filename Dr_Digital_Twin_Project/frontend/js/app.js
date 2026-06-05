const PATIENT_ID = 'PAT-1023';

// 捕获前端错误并发送到后端日志接口
window.onerror = function(message, source, lineno, colno, error) {
    fetch('/api/v1/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            level: 'error',
            message: message.toString(),
            url: source,
            line: lineno,
            col: colno,
            error: error ? error.stack : ''
        })
    }).catch(console.error);
    return false;
};

window.onunhandledrejection = function(event) {
    fetch('/api/v1/log', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            level: 'error',
            message: 'Unhandled Promise Rejection: ' + (event.reason ? event.reason.message || event.reason : ''),
            url: window.location.href,
            error: event.reason ? (event.reason.stack || '') : ''
        })
    }).catch(console.error);
};

$(document).ready(function() {
    // 切换男女医生图片
    $('input[type=radio][name=doctorGender]').change(function() {
        const isMale = this.value === 'male';
        const imagePath = isMale ? 'images/3f38645a-9a34-4539-835e-a0138327f26d.jpg' : 'images/d970347c-8030-4035-ab24-f8c63e4a6e84.jpg';
        $('#doctor-static-image').attr('src', imagePath);
        $('#doctor-video-stream').hide();
        $('#doctor-static-image').show();
        $('#avatar-status').text('已切换形象');
    });

    $('#btn-send').click(function() {
        const text = $('#input-text').val().trim();
        if(text) sendInteraction(text);
    });

    $('#input-text').keypress(function(e) {
        if(e.which == 13) $('#btn-send').click();
    });

    // 语音输入 (Web Speech API)
    let recognition;
    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = 'zh-CN';

        recognition.onstart = function() {
            $('#btn-record').removeClass('btn-outline-info').addClass('btn-danger').html('<i class="fas fa-microphone-slash"></i>');
            $('#input-text').attr('placeholder', '正在聆听...');
        };

        recognition.onresult = function(event) {
            let finalTranscript = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {
                if (event.results[i].isFinal) {
                    finalTranscript += event.results[i][0].transcript;
                }
            }
            if (finalTranscript) {
                const currentVal = $('#input-text').val();
                $('#input-text').val(currentVal + finalTranscript);
            }
        };

        recognition.onend = function() {
            $('#btn-record').removeClass('btn-danger').addClass('btn-outline-info').html('<i class="fas fa-microphone"></i>');
            $('#input-text').attr('placeholder', '描述您的症状...');
        };

        recognition.onerror = function(event) {
            console.error("Speech recognition error", event.error);
            $('#btn-record').removeClass('btn-danger').addClass('btn-outline-info').html('<i class="fas fa-microphone"></i>');
            $('#input-text').attr('placeholder', '描述您的症状...');
        };
    }

    $('#btn-record').click(function() {
        if (recognition) {
            if ($('#btn-record').hasClass('btn-danger')) {
                recognition.stop();
            } else {
                recognition.start();
            }
        } else {
            alert("您的浏览器不支持语音识别功能，请使用 Chrome 浏览器。");
        }
    });
});

function formatDoctorReply(text) {
    if (!text) return "";
    // Remove markdown code block syntax
    let formatted = text.replace(/```html/gi, '').replace(/```/g, '');
    // Convert newlines to <br> for HTML rendering
    formatted = formatted.replace(/\n/g, '<br>');
    return formatted.trim();
}

function appendMessage(role, text) {
    const cls = role === 'user' ? 'message user' : 'message doctor';
    const prefix = role === 'user' ? '<strong>您:</strong><br>' : '<strong>数字孪生医生:</strong><br>';
    const displayText = role === 'doctor' ? formatDoctorReply(text) : text;
    $('#chat-history').append(`<div class="${cls}">${prefix}${displayText}</div>`);
    const history = document.getElementById('chat-history');
    history.scrollTop = history.scrollHeight;
}

function sendInteraction(text) {
    $('#input-text').val('');
    $('#btn-send').prop('disabled', true);
    $('#input-text').prop('disabled', true);
    appendMessage('user', text);
    
    // 添加 Loading 提示到聊天框中
    const loadingHtml = `<div id="loading-indicator" class="message doctor"><strong>数字孪生医生:</strong><br><span class="text-warning"><i class="fas fa-spinner fa-spin"></i> <span class="typing-animation">正在为您推演病情并生成全息视频，这可能需要一点时间，请稍候</span></span></div>`;
    $('#chat-history').append(loadingHtml);
    const history = document.getElementById('chat-history');
    history.scrollTop = history.scrollHeight;

    $('#avatar-status').text('大模型推理 & 视频生成中...').removeClass('bg-dark bg-success').addClass('bg-warning text-dark');
    
    // 隐藏之前的视频，展示静态图
    $('#doctor-video-stream').hide();
    $('#doctor-static-image').show();

    const selectedGender = $('input[name=doctorGender]:checked').val();

    $.ajax({
        url: `/api/v1/chat/interact`,
        method: 'POST',
        contentType: 'application/json',
        data: JSON.stringify({
            patient_id: PATIENT_ID,
            text: text,
            doctor_gender: selectedGender,
            use_rag: true
        }),
        success: function(res) {
            handleInteractionResponse(res);
        },
        error: function(err) {
            $('#loading-indicator').remove();
            $('#btn-send').prop('disabled', false);
            $('#input-text').prop('disabled', false);
            $('#avatar-status').text('连接失败').removeClass('bg-warning text-dark').addClass('bg-danger text-white');
            appendMessage('doctor', '网络连接异常，请稍后再试。');
            $('#doctor-static-image').show();
            $('#doctor-video-stream').hide();
        }
    });
}

function handleInteractionResponse(res) {
    $('#loading-indicator').remove();
    $('#btn-send').prop('disabled', false);
    $('#input-text').prop('disabled', false);
    
    if(res.status === 'success') {
        appendMessage('doctor', res.doctor_reply);
        
        const twin = res.twin_data;
        if(twin) {
            $('#metric-fbg').text(twin.fbg || '--');
            $('#metric-sbp').text(twin.sbp || '--');
            $('#metric-risk').text(twin.risk_level || '--');
            if (twin.risk_level && twin.risk_level.includes('高危')) {
                $('#metric-risk').addClass('text-danger').removeClass('text-info text-warning');
            }

            const kgBox = $('#kg-reasoning-box');
            kgBox.empty();
            if(twin.kg_reasoning && twin.kg_reasoning.length > 0) {
                twin.kg_reasoning.forEach(item => {
                    let icon = item.type === 'chronic_alert' ? 'fa-exclamation-circle text-warning' : 'fa-pills text-info';
                    kgBox.append(`<div class="mb-1"><i class="fas ${icon} me-1"></i> ${item.data.join(' ➔ ')}</div>`);
                });
            } else {
                kgBox.html('<div class="text-muted small mt-2"><i class="fas fa-check-circle text-success"></i> 暂无图谱推演数据</div>');
            }
        }

        $('#avatar-status').text('正在播报').removeClass('bg-warning text-dark').addClass('bg-success text-white');
        
        // 播放 SadTalker 生成的视频
        if (res.video_base64) {
            const videoElement = document.getElementById('doctor-video-stream');
            const staticImage = document.getElementById('doctor-static-image');
            
            videoElement.src = `data:${res.mime_type};base64,${res.video_base64}`;
            staticImage.style.display = 'none';
            videoElement.style.display = 'block';
            
            videoElement.onended = function() {
                videoElement.style.display = 'none';
                staticImage.style.display = 'block';
                $('#avatar-status').text('待机中').removeClass('bg-success').addClass('bg-dark');
            };
            
            videoElement.play().catch(e => {
                console.error("Video playback failed:", e);
                fallbackSpeech(res.doctor_reply, res.audio_base64);
            });
        } else {
            fallbackSpeech(res.doctor_reply, res.audio_base64);
        }
    }
}

function fallbackSpeech(text, audioBase64) {
    if (audioBase64) {
        // 如果后端传来了 TTS 生成的纯音频，优先播放真实音频
        const audio = new Audio(`data:audio/wav;base64,${audioBase64}`);
        $('#avatar-status').text('AI 语音播报(兜底)').removeClass('bg-success bg-warning text-dark text-white').addClass('bg-info text-white');
        
        audio.onended = () => {
            $('#avatar-status').text('待机中').removeClass('bg-info').addClass('bg-dark');
        };
        audio.play().catch(e => {
            console.error("Audio playback failed:", e);
            // 连 TTS 语音都播放失败，最后退化到浏览器自带的 TTS
            playBrowserTTS(text);
        });
    } else {
        playBrowserTTS(text);
    }
}

function playBrowserTTS(text) {
    if (!("speechSynthesis" in window)) return;
    window.speechSynthesis.cancel();
    const utter = new SpeechSynthesisUtterance(text.replace(/\[.*?\]/g, ""));
    utter.lang = "zh-CN";
    window.speechSynthesis.speak(utter);
    
    $('#avatar-status').text('浏览器语音播报(兜底)').removeClass('bg-success bg-warning text-dark text-white').addClass('bg-secondary text-white');
    utter.onend = () => {
        $('#avatar-status').text('待机中').removeClass('bg-secondary').addClass('bg-dark');
    };
}
