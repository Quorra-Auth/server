function verifyParameters() {
  const params = new Proxy(new URLSearchParams(window.location.search), {
    get: (searchParams, prop) => searchParams.get(prop),
  });
  if (!params.link) {
    window.location.href = "missing_link.html";
  }
}

window.onload = function() {
  verifyParameters();
};

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

    const payload = { "username": name, "email": email, "link_id": params.link };

      fetch("/onboarding/register", {
        method: "POST",
        headers: {
          "Content-Type": "application/json"
        },
        body: JSON.stringify(payload)
      })
      .then(response => {
        if (!response.ok) throw new Error("Request failed");
        return response.json();
      })
      .then(data => {
        document.getElementById("details_form_div").classList.add("hidden");
        document.getElementById("qr_div").classList.remove("hidden");
        document.getElementById("qr").src = data.qr_image;
        document.getElementById("local_link").href = data.link;
      })
  });
}
