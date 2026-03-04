let txId = null;

window.onload = async function() {
  await startAqr();
};

async function findReplace(objClass, text) {
  document.querySelectorAll(`.${objClass}`).forEach(el => {
    el.textContent = text;
  });
}

async function startAqr() {
  const params = new Proxy(new URLSearchParams(window.location.search), {
  get: (searchParams, prop) => searchParams.get(prop),
});
  let args = `client_id=${params.client_id}&scope=${params.scope}`
  if (params.nonce) {
    args = args + `&nonce=${params.nonce}`
  }
  const response = await fetch(`../../processes/login/start?${args}`);
  if (!response.ok) throw new Error("Request failed");
  data = await response.json();
  txId = data.tx_id;
  await findReplace("clientName", params.client_name);
  const url = new URL(params.redirect_uri);
  var urlString = url.origin
  if (url.protocol !== "https:") {
    urlString = `⚠️ ${url.origin} ⚠️`
  }
  await findReplace("redirectURI", urlString);
  await showQrCode();
  startPolling();
}

async function showQrCode() {
  const payload = { "tx_type": "ln-oidc-login", "tx_id": txId };
  const response = await fetch("../../lnurl-auth/qr", {
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
  const pollingUrl = `../../tx/transaction`;
  const payload = { "tx_id": txId, "tx_type": "ln-oidc-login" }

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
        if (data.state == "identified") {
          // Hide qr_code_div and show identified_div
          if (!qr_div.classList.contains("hidden")) {
            showStep("identified_div");
          }
        }
        // TODO: rejected state
        else if (data.state == "confirmed") {
          showStep("finished_div");

          clearInterval(intervalId);
          redirectParams = {"code": data.data.oidc_data.code, "state": params.state, "nonce": params.nonce};
          const redirectAddress = params.redirect_uri + "?" + encodeGetParams(redirectParams);
          manual_redirect.href = redirectAddress;
          window.location.href = redirectAddress;
        }
      })
      .catch(error => {
        console.error("Polling error:", error);
      });
  }, 2000);
}
