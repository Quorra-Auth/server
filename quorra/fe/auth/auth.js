let txId = null;

window.onload = async function() {
  await startAqr();
};

async function startAqr() {
  const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
  let args = `client_id=${params.client_id}&scope=${params.scope}`
  if (params.nonce) {
    args = args + `&nonce=${params.nonce}`
  }
  const response = await fetch(`/login/start?${args}`);
  if (!response.ok) throw new Error("Request failed");
  data = await response.json();
  txId = data.tx_id;
  await showQrCode();
  startPolling();
}

async function showQrCode() {
  const payload = { "tx_type": "aqr-oidc-login", "tx_id": txId };
  const response = await fetch("/login/qr", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });
  data = await response.json()
  qr.src = data.qr_image;
  local_link.href = data.link;
}

function startPolling() {
  const pollingUrl = `/tx/transaction`;
  const payload = { "tx_id": txId, "tx_type": "aqr-oidc-login" }

  const encodeGetParams = p =>
    Object.entries(p).map(kv => kv.map(encodeURIComponent).join("=")).join("&");
  const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
  });

  const intervalId = setInterval(() => {
    fetch(pollingUrl, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      })
      .then(response => {
        if (!response.ok) throw new Error("Polling failed");
        return response.json();
      })
      .then(data => {
        console.log("Polling data:", data);
        if (data.state == "identified") {
          // Hide qr_code_div and show identified_div
          if (!qr_div.classList.contains("hidden")) {
            qr_div.classList.add("hidden");
          }
          if (identified_div.classList.contains("hidden")) {
            identified_div.classList.remove("hidden");
          }
        }
        // TODO: rejected state
        else if (data.state == "confirmed") {
          // Hide identified_div and qr_code_div, show finished_div
          if (!qr_div.classList.contains("hidden")) {
            qr_div.classList.add("hidden");
          }
          if (!identified_div.classList.contains("hidden")) {
            identified_div.classList.add("hidden");
          }
          if (finished_div.classList.contains("hidden")) {
            finished_div.classList.remove("hidden");
          }

          clearInterval(intervalId);
          redirectParams = {"code": data.data.oidc_data.code, "state": params.state, "nonce": params.nonce};
          window.location.href = params.redirect_uri + "?" + encodeGetParams(redirectParams);
        }
      })
      .catch(error => {
        console.error("Polling error:", error);
      });
  }, 2000);
}
