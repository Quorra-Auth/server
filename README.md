# Here be dragons

This project is in its very early stages. Tame your expectations and excercise caution.

## What is this?

Quorra is an OIDC compatible IDP (identity provider).

While other providers either use a password, WebAuthn, OTPs or a combination of the three, Quorra uses asymetric encryption. The private key is stored on a device running one of Quorra's authenticator apps.

It doesn't aim to be a replacement for other identity providers, instead Quorra is meant to be used *alongisde* other more full-featured IDPs like [Authentik](https://goauthentik.io/), [Zitadel](https://zitadel.com/), [Keyloak](https://keycloak.org/), [Dex](https://dexidp.io/), etc.

As such, Quorra only implements a fairly minimal set of OIDC features and doesn't provide any access controls. It wasn't created to plug directly into your applications, it is to be used as an external identity provider for your existing IDP.

For simple use-cases without the need for fine-grained access policies it can be used as a standalone IDP.

## Can I see?

TODO: Add a video

## Who is it for?

Quorra is for everyone, but the main target audience are home users and self-hosters.

## What about the mobile app?

As a starting point we provide apps for two platforms:

* [Voucher](https://github.com/k8ieone/voucher) is a client for Linux written in Python and GTK4/Libadwaita
* [Flare](https://github.com/Quorra-Auth/flare) is a client for Android written in Flutter

We hope developers will pick up development of their own authenticator apps for Quorra.

The API is documented using OpenAPI and we try to keep it simple.

## How does it work?

Everything in Quorra is based either on short-term random secrets or asymetric encryption. No magic involved.

## Is this safe?

This project is not ready for production use yet and it is too early to start chasing down potential security issues. Anything can change at any point.

## How do I deploy this?

TODO

If you're ready to start playing with Quorra...
