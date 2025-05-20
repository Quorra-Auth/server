function startAqr() {
  fetch("/login/aqr/start")
    .then(response => {
      if (!response.ok) {
        throw new Error("Network response was not OK");
      }
      return response.json();
    })
    .then(data => {
      const sessionId = data.session_id;
      let loginButton = document.getElementById("login_b")
      document.getElementById("user_controls").removeChild(loginButton);
      showQrCode(sessionId);

      startPolling(sessionId);

    })
    .catch(error => {
      alert("Fetch error: " + error.message);
    });
}

function showQrCode(sessionId) {
  const imageUrl = `/login/aqr/code?session=${sessionId}`;
  let stuffContainer = document.getElementById("user_controls")

  let img = document.getElementById("AQR");
  img = document.createElement("img");
  img.id = "AQR";
  img.alt = "AQR code";
  img.src = imageUrl;
  stuffContainer.appendChild(img);
  let br = document.createElement("br")
  stuffContainer.appendChild(br)
  let localLink = document.createElement("a");
  localLink.textContent = "Use a local install";
  localLink.href = `quorra+${window.location.origin}/mobile/login?s=${sessionId}`
  stuffContainer.appendChild(localLink);
}

function startPolling(sessionId) {
  const pollingUrl = `/login/aqr/poll?session=${sessionId}`;

  const intervalId = setInterval(() => {
    fetch(pollingUrl)
      .then(response => {
        if (!response.ok) throw new Error("Polling failed");
        return response.json();
      })
      .then(data => {
        console.log("Polling data:", data);
        if (data.state == "identified") {
          if (!document.getElementById("status_h")) {
            let status_h = document.createElement("h2");
            status_h.id = "status_h";
            let device_identifier = data.device_id;
            if (data.device_name !== null) {
              device_identifier = data.device_name;
            }
            let msg = `Waiting for confirmation on ${device_identifier}...`;
            status_h.textContent = msg;
            document.getElementById("status_container").appendChild(status_h);
          }
        }
        else if (data.state == "authenticated") {
          document.body.removeChild(document.getElementById("user_controls"));
          let status_h = document.getElementById("status_h");
          status_h.textContent = "And you're logged in!";
          let user_h = document.createElement("h3");
          user_h.textContent = `Your UID: ${data.user_id}`;
          document.getElementById("status_container").appendChild(user_h);
          clearInterval(intervalId);
        }
      })
      .catch(error => {
        console.error("Polling error:", error);
      });
  }, 5000);
}
