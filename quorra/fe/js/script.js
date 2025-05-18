function startAqr() {
  fetch('/login/aqr/start')
    .then(response => {
      if (!response.ok) {
        throw new Error('Network response was not OK');
      }
      return response.json();
    })
    .then(data => {
      const sessionId = data.session_id;
      console.log('Got session ID:', sessionId);
      let loginButton = document.getElementById('login_b')
      document.getElementById('stuff').removeChild(loginButton);
      showQrCode(sessionId);

      startPolling(sessionId);

    })
    .catch(error => {
      alert('Fetch error: ' + error.message);
    });
}

function showQrCode(sessionId) {
  const imageUrl = `/login/aqr/code?session=${sessionId}`;
  let stuffContainer = document.getElementById('stuff')

  let img = document.getElementById('AQR');
  img = document.createElement('img');
  img.id = 'AQR';
  img.alt = 'AQR code';
  img.src = imageUrl;
  stuffContainer.appendChild(img);
  let br = document.createElement('br')
  stuffContainer.appendChild(br)
  let localLink = document.createElement('a');
  localLink.textContent = 'Use a local install';
  localLink.href = `quorra+${window.location.origin}/mobile/login?s=${sessionId}`
  stuffContainer.appendChild(localLink);
}

function startPolling(sessionId) {
  const pollingUrl = `/login/aqr/poll?session=${sessionId}`;

  function poll() {
    fetch(pollingUrl)
      .then(response => {
        if (!response.ok) throw new Error('Polling failed');
        return response.json();
      })
      .then(data => {
        console.log('Polling data:', data);
        if (data.state == 'identified') {
          if (!document.getElementById('status_thingy')) {
            console.log('something');
            let status_thingy = document.createElement('h2');
            status_thingy.id = 'status_thingy';
            status_thingy.textContent = `We got you! You're ${data.device_id}! You're also known as ${data.device_name}!`;
            document.getElementById('stuff').appendChild(status_thingy);
          }
        }
      })
      .catch(error => {
        console.error('Polling error:', error);
      });
  }

  poll(); // Initial poll immediately

  // Poll every 5 seconds
  setInterval(poll, 5000);
}
