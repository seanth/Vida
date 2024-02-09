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



// //Creating a new WebSocket connection.
// const socket = new WebSocket('ws://localhost:5678/');

// window.onload = function() {
//   // get the references of the page elements.
//   // var form = document.getElementById('form-msg');
//   // var txtMsg = document.getElementById('msg');
//   // var listMsgs = document.getElementById('msgs');
//   const socketStatus = document.getElementById('status');
//   // var btnClose = document.getElementById('close');
// };

// socket.onerror = function(error) {
//   console.log('WebSocket error: ' + error);
// };

//Creating a new WebSocket connection.
const socket = new WebSocket('ws://localhost:5678/');

socket.onmessage = (event) => {
  let blob = event.data;
  let reader = new FileReader();
  
  reader.addEventListener('loadend', () => {
    let arrayBuffer = reader.result;
    let model = document.querySelector('a-asset-item#model');
    console.log(arrayBuffer);
    model.setAttribute('src', arrayBuffer);
    document.querySelector('a-scene').setAttribute('fog')
    document.querySelector('a-scene').removeAttribute('fog')

  });
  reader.readAsArrayBuffer(blob);
  

};


