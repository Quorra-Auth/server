window.onload = function() {
  startAqr();
};

function startAqr() {
  const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
  let args = `client_id=${params.client_id}&scope=${params.scope}`
  if (params.nonce) {
    args = args + `&nonce=${params.nonce}`
  }
  fetch(`/login/start?${args}`)
    .then(response => {
      if (!response.ok) {
        throw new Error("Network response was not OK");
      }
      return response.json();
    })
    .then(data => {
      const sessionId = data.session_id;
      showQrCode(sessionId, data.qr_image);

      startPolling(sessionId);

    })
    .catch(error => {
      alert("Fetch error: " + error.message);
    });
}

function showQrCode(sessionId ,qrImage) {
  let stuffContainer = document.getElementById("user_controls")

  let img = document.getElementById("AQR");
  img = document.createElement("img");
  img.id = "AQR";
  img.alt = "AQR code";
  img.src = qrImage;
  stuffContainer.appendChild(img);
  let br = document.createElement("br")
  stuffContainer.appendChild(br)
  let localLink = document.createElement("a");
  localLink.textContent = "Use a local install";
  localLink.href = `quorra+${window.location.origin}/mobile/login?s=${sessionId}`
  stuffContainer.appendChild(localLink);
  let statusHeader = document.createElement("h2");
  statusHeader.id = "status_h";
  statusHeader.textContent = "Scan this QR code on your device";
  document.getElementById("status_container").appendChild(statusHeader);
}

function startPolling(sessionId) {
  const pollingUrl = `/login/fepoll?session=${sessionId}`;
  const encodeGetParams = p =>
    Object.entries(p).map(kv => kv.map(encodeURIComponent).join("=")).join("&");
  const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});

  const intervalId = setInterval(() => {
    fetch(pollingUrl)
      .then(response => {
        if (!response.ok) throw new Error("Polling failed");
        return response.json();
      })
      .then(data => {
        console.log("Polling data:", data);
        if (data.state == "identified") {
          let controls = document.getElementById("user_controls");
          if (controls) {
            document.body.removeChild(controls);
          }
          let statusHeader = document.getElementById("status_h")
          statusHeader.textContent = "Waiting for confirmation on your device...";
        }
        else if (data.state == "authenticated") {
          let statusContainer = document.getElementById("status_container");
          let statusHeader = document.getElementById("status_h");
          statusHeader.textContent = "And you're logged in!";
          let statusSubtitle = document.createElement("h2");
          statusSubtitle.textContent = "We're redirecting you back to the application";
          statusContainer.appendChild(statusSubtitle)

          clearInterval(intervalId);
          redirectParams = {"code": data.code, "state": params.state, "nonce": params.nonce};
          window.location.href = params.redirect_uri + "?" + encodeGetParams(redirectParams);
        }
      })
      .catch(error => {
        console.error("Polling error:", error);
      });
  }, 2000);
}
