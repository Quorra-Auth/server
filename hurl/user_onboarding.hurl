# Wait for the main service healthcheck
GET http://localhost:8080/health
[Options]
retry: -1
HTTP 200

# Wait for crypto support healthcheck
GET http://localhost:8085/health
[Options]
retry: -1
HTTP 200

# Create one onboarding link
GET http://localhost:8080/onboarding/init
HTTP 201
[Captures]
onboarding_token: jsonpath "$.link_id"

# Send the user details
POST http://localhost:8080/onboarding/register
{
 "link_id": "{{ onboarding_token }}",
 "username": "hurl",
 "email": "hurl@hurl.dev"
}
HTTP 200
[Captures]
mobile_registration_link: jsonpath "$.link"

# Get the mobile token
POST http://localhost:8085/utils/parameter
{
 "uri": "{{ mobile_registration_link }}",
 "parameter": "t"
}
HTTP 200
[Captures]
mobile_registration_token: jsonpath "$.result"

# Generate a new key pair
GET http://localhost:8085/ed25519/generate
HTTP 200
[Captures]
pubkey: jsonpath "$.public_key"
privkey: jsonpath "$.private_key"

# Register a new authenticator device
POST http://localhost:8080/mobile/register
x-registration-token: {{ mobile_registration_token }}
{
 "pubkey": "{{ pubkey }}",
 "name": "hurl"
}
HTTP 201