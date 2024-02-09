const socket = new WebSocket('ws://localhost:5678/');

socket.onmessage = (event) => {
  let theEntity = document.querySelector('a-entity#forestModel');
  theEntity.setAttribute('gltf-model', event.data);
};


