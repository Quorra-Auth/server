GET http://localhost:8080/usermgmt/onboard
HTTP 201
[Captures]
onboarding_token: jsonpath "$.link_id"

# Check that another onboarding link can't be created
GET http://localhost:8080/usermgmt/onboard
HTTP 403

# Finalize the user registration
GET http://localhost:8080/usermgmt/register/{{onboarding_token}}
200


# Will be used for QR polling
#GET http://localhost:8080/usermgmt/onboard
#[Options]
#retry: -1
#HTTP 201