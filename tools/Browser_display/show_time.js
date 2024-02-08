// window.addEventListener("DOMContentLoaded", () => {
//   const messages = document.createElement("ul");
//   document.body.appendChild(messages);

//   const websocket = new WebSocket("ws://localhost:5678/");
//   websocket.onmessage = ({ data }) => {
//     const message = document.createElement("li");
//     const content = document.createTextNode(data);
//     message.appendChild(content);
//     messages.appendChild(message);
//   };
// });



// Creating a new WebSocket connection.
const socket = new WebSocket('ws://localhost:5678/');

window.onload = function() {
  // get the references of the page elements.
  // var form = document.getElementById('form-msg');
  // var txtMsg = document.getElementById('msg');
  // var listMsgs = document.getElementById('msgs');
  const socketStatus = document.getElementById('status');
  // var btnClose = document.getElementById('close');
};

socket.onerror = function(error) {
  console.log('WebSocket error: ' + error);
};

socket.onmessage = ({data}) => {
  document.getElementById("status").textContent = data;
  document.querySelector('#tree-glb').setAttribute('src', data);
  document.querySelector('a-scene').setAttribute('fog','type:linear;far:100')
  document.querySelector('a-scene').removeAttribute('fog')
};


