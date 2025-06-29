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
  AQR.src = qrImage;
  local_link.href = `quorra+${window.location.origin}/mobile/login?s=${sessionId}`;
}

function startPolling(sessionId) {
  const pollingUrl = `/login/fepoll?session=${sessionId}`;
  const encodeGetParams = p =>
    Object.entries(p).map(kv => kv.map(encodeURIComponent).join("=")).join("&");
  const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
  let qrCodeDiv = document.getElementById("qr_code_div");
  let identifiedDiv = document.getElementById("identified_div");
  let finishedDiv = document.getElementById("finished_div");

  const intervalId = setInterval(() => {
    fetch(pollingUrl)
      .then(response => {
        if (!response.ok) throw new Error("Polling failed");
        return response.json();
      })
      .then(data => {
        console.log("Polling data:", data);
        if (data.state == "identified") {
          // Hide qr_code_div and show identified_div
          if (!qrCodeDiv.classList.contains("hidden")) {
            qrCodeDiv.classList.add("hidden");
          }
          if (identifiedDiv.classList.contains("hidden")) {
            identifiedDiv.classList.remove("hidden");
          }
        }

        else if (data.state == "authenticated") {
          // Hide identified_div and qr_code_div, show finished_div
          if (!qrCodeDiv.classList.contains("hidden")) {
            qrCodeDiv.classList.add("hidden");
          }
          if (!identifiedDiv.classList.contains("hidden")) {
            identifiedDiv.classList.add("hidden");
          }
          if (finishedDiv.classList.contains("hidden")) {
            finishedDiv.classList.remove("hidden");
          }

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
