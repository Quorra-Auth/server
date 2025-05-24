function startAqr() {
  const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
  let args = `client_id=${params.client_id}`
  if (Object.hasOwn(params, "nonce")) {
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
  let status_h = document.createElement("h2");
  status_h.id = "status_h";
  status_h.textContent = "Scan this QR code on your device";
  document.getElementById("status_container").appendChild(status_h);
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
          status_h.textContent = "Waiting for confirmation on your device...";
        }
        else if (data.state == "authenticated") {
          document.body.removeChild(document.getElementById("user_controls"));
          let status_h = document.getElementById("status_h");
          status_h.textContent = "And you're logged in!";
          clearInterval(intervalId);
          redirectParams = {"code": data.code, "state": params.state, "nonce": params.nonce};
          window.location.href = params.redirect_uri + "?" + encodeGetParams(redirectParams);
        }
      })
      .catch(error => {
        console.error("Polling error:", error);
      });
  }, 5000);
}
