const socket = new WebSocket(
    "ws://" + window.location.host + "/ws/video/"
);

const localVideo = document.getElementById("localVideo");
const remoteVideo = document.getElementById("remoteVideo");

let localStream;
let peer;

const iceServers = {
    iceServers: [
        { urls: "stun:stun.l.google.com:19302" }
    ]
};

function showStatus(text){
    const status = document.getElementById("status");
    status.innerText = text;
    status.style.opacity = 1;

    setTimeout(()=>{
        status.style.opacity = 0;
    },2000);
}

function startCamera(){

navigator.mediaDevices.getUserMedia({
    video:true,
    audio:true
})
.then(stream=>{

    localStream = stream;
    localVideo.srcObject = stream;

    localVideo.style.transform = "scale(1)";
    localVideo.style.opacity = 1;

    showStatus("Camera Ready 📷");

})
.catch(()=>{
    showStatus("Camera Error");
})

}

function createPeer(){

peer = new RTCPeerConnection(iceServers);

localStream.getTracks().forEach(track=>{
    peer.addTrack(track, localStream);
});

peer.ontrack = event=>{
    remoteVideo.srcObject = event.streams[0];

    remoteVideo.style.opacity = 1;
    remoteVideo.style.transform = "scale(1)";
};

peer.onicecandidate = event=>{
    if(event.candidate){

        socket.send(JSON.stringify({
            type:"candidate",
            candidate:event.candidate
        }))

    }
}

}

socket.onopen = ()=>{
    showStatus("Connected to server ⚡")
}

socket.onmessage = async (event)=>{

const data = JSON.parse(event.data);

if(data.type === "offer"){

    createPeer();

    await peer.setRemoteDescription(
        new RTCSessionDescription(data.offer)
    );

    const answer = await peer.createAnswer();
    await peer.setLocalDescription(answer);

    socket.send(JSON.stringify({
        type:"answer",
        answer:answer
    }));

}

if(data.type === "answer"){

    await peer.setRemoteDescription(
        new RTCSessionDescription(data.answer)
    );

}

if(data.type === "candidate"){

    try{
        await peer.addIceCandidate(data.candidate);
    }catch(e){}

}

}

async function startCall(){

createPeer();

const offer = await peer.createOffer();
await peer.setLocalDescription(offer);

socket.send(JSON.stringify({
    type:"offer",
    offer:offer
}));

showStatus("Searching for stranger 🔍")

}

document.getElementById("next").onclick = ()=>{

remoteVideo.style.opacity = 0;
remoteVideo.srcObject = null;

if(peer){
    peer.close();
}

startCall();

}

startCamera();

setTimeout(()=>{
    startCall();
},2000);