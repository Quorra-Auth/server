async function getLink() {
  const params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
  });
  return params.link || false;
}

async function createOnboardingLink() {
  const response = await fetch("/onboarding/create", {
    method: "GET",
    headers: {
      "Content-Type": "application/json"
    }
  });

  if (!response.ok) throw new Error("Request failed");

  const data = await response.json();
  return data.link_id;
}

async function startOnboardingTransaction(onboardingLink) {
  const payload = { "link_id": onboardingLink };

  const response = await fetch("/onboarding/init", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) throw new Error("Request failed");

  const data = await response.json();
  return data.tx_id;
}

async function getOnboardingData() {
  const payload = { "tx_type": "onboarding", "tx_id": txId };

  const response = await fetch("/onboarding/qr", {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) throw new Error("Request failed");

  const data = await response.json();
  return data;
}

function startOnboarding() {
  const params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
  });
  document.getElementById("initial").classList.add("hidden");
  document.getElementById("details_form_div").classList.remove("hidden");

  document.getElementById("details_form").addEventListener("submit", async function(e) {
    e.preventDefault();

    const name = document.getElementById("username_input").value;
    const email = document.getElementById("email_input").value;

    const payload = { "tx_id": txId, "data": { "username": name, "email": email }, "tx_type": "onboarding" };

    try {
      const response = await fetch("/onboarding/entry", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (!response.ok) throw new Error("Request failed");

      const result = await response.json();
      const onboardingData = await getOnboardingData();

      document.getElementById("details_form_div").classList.add("hidden");
      document.getElementById("qr_div").classList.remove("hidden");
      document.getElementById("qr").src = onboardingData.qr_image;
      document.getElementById("local_link").href = onboardingData.link;

    } catch (error) {
      console.error(error);
      alert("An error occurred while starting onboarding.");
    }
    startPolling()
  });
}

function startPolling() {
  const pollingUrl = `/tx/transaction`;
  const payload = { "tx_id": txId, "tx_type": "onboarding" }

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
        if (data.state == "finished") {
          // Hide qr_code_div and show identified_div
          clearInterval(intervalId);
          document.getElementById("qr_div").classList.add("hidden");
          document.getElementById("welcome_h1").classList.add("hidden");
          document.getElementById("finished_div").classList.remove("hidden");
        }
      })
      .catch(error => {
        console.error("Polling error:", error);
      });
  }, 2000);
}

let txId = null;

window.onload = async function() {
  let onboardingLink = await getLink();
  let providedLink = onboardingLink || false;

  // If a link wasn't provided, try creating one
  if (!onboardingLink) {
    try {
      onboardingLink = await createOnboardingLink();
    } catch (err) {
      // If registrations are closed, redirect to missing link page
      window.location.href = "missing_link.html";
      return;
    }
  }

  // TODO: If a link was provided by the user we want to confirm if we want to consume it
  if (providedLink) {
    console.log("This link was user-provided");
  }
  txId = await startOnboardingTransaction(onboardingLink);
  // if (started) {
  //   startOnboarding();
  // }
};
